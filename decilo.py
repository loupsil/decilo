from flask import Blueprint, jsonify, request, Response, g
import xmlrpc.client
import os
from dotenv import load_dotenv
import logging
import jwt
from datetime import datetime, timedelta
from functools import wraps
import base64
import imghdr
import json
import time

#  Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Create blueprint
decilo_bp = Blueprint('decilo', __name__)

# Odoo Configuration
ODOO_URL = os.getenv('DECILO_ODOO_URL')
ODOO_DB = os.getenv('DECILO_ODOO_DB')
ODOO_USERNAME = os.getenv('DECILO_ODOO_USERNAME')
ODOO_API_KEY = os.getenv('DECILO_ODOO_API_KEY')

# JWT Configuration
JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'your-secret-key')  # Change in production
JWT_EXPIRATION_HOURS = 24

# Simple in-memory caches to cut down on repeated Odoo RPCs
VARIANT_TEMPLATE_CACHE_TTL = 30 * 60  # 30 minutes
VARIANT_IMAGE_CACHE_TTL = 30 * 60
VARIANT_TEMPLATE_CACHE = {}
VARIANT_IMAGE_CACHE = {}

# Language mapping helpers
# Default locale for the application (UI shorthand and Odoo code)
DEFAULT_UI_LOCALE = 'fr'
DEFAULT_ODOO_LOCALE = 'fr_BE'

UI_TO_ODOO_LANG = {
    'en': 'en_US',
    'fr': 'fr_BE',  # use installed FR locale
    # Prefer nl_BE because nl_NL is not installed on the instance
    'nl': 'nl_BE',
}

ODOO_TO_UI_LANG = {
    'en_US': 'en',
    'en_GB': 'en',
    'fr_FR': 'fr',
    'fr_BE': 'fr',
    'nl_NL': 'nl',
    'nl_BE': 'nl',
}

def normalize_to_odoo_locale(locale_value):
    """Normalize various locale inputs to an Odoo-friendly locale code."""
    if not locale_value:
        return DEFAULT_ODOO_LOCALE
    val = str(locale_value).strip()
    lower_val = val.lower()

    # If already an Odoo code
    for v in UI_TO_ODOO_LANG.values():
        if lower_val == v.lower():
            return v

    # If UI shorthand
    mapped = UI_TO_ODOO_LANG.get(lower_val)
    if mapped:
        return mapped

    # Accept formats like en-us, fr-be
    if '-' in lower_val:
        normalized = lower_val.replace('-', '_')
        for v in UI_TO_ODOO_LANG.values():
            if normalized == v.lower():
                return v

    return DEFAULT_ODOO_LOCALE

def normalize_to_ui_language(locale_value):
    """Normalize an Odoo locale to UI shorthand (en/fr/nl)."""
    if not locale_value:
        return DEFAULT_UI_LOCALE
    val = str(locale_value).strip()
    lower_val = val.lower().replace('-', '_')
    for odoo_lang, ui_lang in ODOO_TO_UI_LANG.items():
        if lower_val == odoo_lang.lower():
            return ui_lang
    if lower_val in UI_TO_ODOO_LANG:
        return lower_val
    return DEFAULT_UI_LOCALE

def get_request_locale():
    """Return the current request locale (Odoo code)."""
    return getattr(g, 'decilo_locale', DEFAULT_ODOO_LOCALE)

def create_token(user_data):
    """Create a JWT token for the user"""
    try:
        payload = {
            'email': user_data['email'],
            'name': user_data['name'],
            'id': user_data['id'],
            'exp': datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
        }
        if user_data.get('lang'):
            payload['lang'] = user_data['lang']
        token = jwt.encode(payload, JWT_SECRET_KEY, algorithm='HS256')
        return token
    except Exception as e:
        logger.error(f"Error creating token: {str(e)}")
        raise

def token_required(f):
    """Decorator to check valid token"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        auth_header = request.headers.get('Authorization')

        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]

        if not token:
            return jsonify({'error': 'Token is missing'}), 401

        try:
            data = jwt.decode(token, JWT_SECRET_KEY, algorithms=['HS256'])
            current_user = data
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token'}), 401

        return f(current_user, *args, **kwargs)
    return decorated

def get_odoo_common():
    """Get Odoo common endpoint"""
    try:
        common = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/common', allow_none=True)
        return common
    except Exception as e:
        logger.error(f"Failed to connect to Odoo common endpoint: {str(e)}")
        raise

class OdooModelsProxy:
    """Wraps the Odoo models proxy to inject request locale into context."""
    def __init__(self, models_proxy, locale_provider):
        self._models = models_proxy
        self._locale_provider = locale_provider

    def execute_kw(self, db, uid, pwd, model, method, args=None, kwargs=None):
        args = args or []
        kwargs = kwargs or {}
        context = kwargs.get('context')
        if not isinstance(context, dict):
            context = {}
        context = {**context}
        lang = self._locale_provider()
        if lang:
            context.setdefault('lang', lang)
        kwargs['context'] = context
        return self._models.execute_kw(db, uid, pwd, model, method, args, kwargs)

    def __getattr__(self, item):
        return getattr(self._models, item)

def get_odoo_models():
    """Get Odoo models endpoint with locale-aware wrapper"""
    try:
        base_models = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/object', allow_none=True)
        return OdooModelsProxy(base_models, get_request_locale)
    except Exception as e:
        logger.error(f"Failed to connect to Odoo models endpoint: {str(e)}")
        raise

def get_uid():
    """Get Odoo user ID"""
    try:
        common = get_odoo_common()
        uid = common.authenticate(ODOO_DB, ODOO_USERNAME, ODOO_API_KEY, {})
        if not uid:
            raise Exception("Authentication failed")
        return uid
    except Exception as e:
        logger.error(f"Failed to authenticate with Odoo: {str(e)}")
        raise

@decilo_bp.before_app_request
def set_request_locale():
    """Middleware-style hook to determine locale for the current request."""
    locale = None

    # Header or query param override
    header_locale = request.headers.get('X-Locale') or request.args.get('locale')
    if header_locale:
        locale = header_locale

    # Fallback to JWT claim (without failing the request on decode issues)
    if not locale:
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            try:
                payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=['HS256'], options={'verify_exp': False})
                locale = payload.get('lang')
            except Exception:
                locale = None

    g.decilo_locale = normalize_to_odoo_locale(locale)
    logger.info(f"[locale] Selected locale for request: {g.decilo_locale}")

@decilo_bp.route('/decilo-api/customer-login', methods=['POST'])
def customer_login():
    logger.info("Received request for /decilo-api/customer-login")
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return jsonify({'error': 'Email and password are required'}), 400

        try:
            # Get UID
            uid = get_uid()
            
            # Get models connection
            models = get_odoo_models()
            
            # Search for user
            user_ids = models.execute_kw(
                ODOO_DB, uid, ODOO_API_KEY,
                'res.users',
                'search',
                [[('login', '=', email)]],
                {'limit': 1}
            )
            
            if not user_ids:
                return jsonify({'error': 'Email not found', 'code': 'email_not_found'}), 401

            # Try to authenticate
            auth_uid = get_odoo_common().authenticate(ODOO_DB, email, password, {})
            
            if not auth_uid:
                return jsonify({'error': 'Invalid password', 'code': 'invalid_password'}), 401

            # Get user info
            user = models.execute_kw(
                ODOO_DB, uid, ODOO_API_KEY,
                'res.users',
                'read',
                [auth_uid],
                {'fields': ['name', 'email', 'partner_id', 'lang']}
            )[0]

            user_lang = normalize_to_ui_language(user.get('lang'))

            # Create user data
            user_data = {
                'id': user['partner_id'][0],
                'name': user['name'],
                'email': user['email'] or email,
                'lang': user_lang
            }

            # Create JWT token
            token = create_token(user_data)

            return jsonify({
                'token': token,
                'user': user_data
            })

        except xmlrpc.client.Fault as e:
            logger.error(f"Odoo fault: {str(e)}")
            return jsonify({'error': 'Authentication failed', 'code': 'auth_failed'}), 401

    except Exception as e:
        error_msg = f"Error in customer login: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return jsonify({'error': error_msg, 'code': 'unknown_error'}), 500


@decilo_bp.route('/decilo-api/customer-signup', methods=['POST'])
def customer_signup():
    logger.info("Received request for /decilo-api/customer-signup")
    try:
        data = request.get_json()
        name = data.get('name')
        email = data.get('email')
        password = data.get('password')

        if not all([name, email, password]):
            return jsonify({'error': 'Name, email and password are required'}), 400

        try:
            # Get UID
            uid = get_uid()
            
            # Get models connection
            models = get_odoo_models()
            
            # Check if user exists
            existing_users = models.execute_kw(
                ODOO_DB, uid, ODOO_API_KEY,
                'res.users',
                'search_count',
                [[('login', '=', email)]]
            )
            
            if existing_users:
                return jsonify({'error': 'Email already exists', 'code': 'email_exists'}), 409

            # Create user
            user_id = models.execute_kw(
                ODOO_DB, uid, ODOO_API_KEY,
                'res.users',
                'create',
                [{
                    'name': name,
                    'login': email,
                    'email': email,
                    'password': password,
                    'groups_id': [(6, 0, [9])]  # Portal group
                }]
            )

            # Get created user info
            user = models.execute_kw(
                ODOO_DB, uid, ODOO_API_KEY,
                'res.users',
                'read',
                [user_id],
                {'fields': ['name', 'email', 'partner_id']}
            )[0]

            # Create user data
            user_data = {
                'id': user['partner_id'][0],
                'name': user['name'],
                'email': user['email']
            }

            return jsonify(user_data)

        except xmlrpc.client.Fault as e:
            logger.error(f"Odoo fault: {str(e)}")
            return jsonify({'error': 'Registration failed', 'code': 'registration_failed'}), 400

    except Exception as e:
        error_msg = f"Error in customer signup: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return jsonify({'error': error_msg, 'code': 'unknown_error'}), 500

from abc import ABC, abstractmethod

class OdooClient(ABC):
    """Abstract base class for Odoo API operations"""
    
    @abstractmethod
    def authenticate(self):
        """Authenticate with Odoo and return UID"""
        pass
    
    @abstractmethod
    def search_products(self, domain=None, fields=None, offset=0, limit=None, order=None):
        """Search for products based on domain criteria"""
        pass
    
    @abstractmethod
    def read_product(self, product_id, fields=None):
        """Read product details by ID"""
        pass
        
    @abstractmethod
    def get_product_variants(self, product_id):
        """Get variant information for a product"""
        pass

class OdooXMLRPCClient(OdooClient):
    """XML-RPC implementation of Odoo API operations"""
    
    def __init__(self, url, db, username, api_key):
        self.url = url
        self.db = db
        self.username = username
        self.api_key = api_key
        self._uid = None
        self._models = None
    
    def authenticate(self):
        if not self._uid:
            common = xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/common', allow_none=True)
            self._uid = common.authenticate(self.db, self.username, self.api_key, {})
            if not self._uid:
                raise Exception("Authentication failed")
        return self._uid
    
    def _get_models(self):
        # Always create a fresh proxy to avoid stale HTTP connections causing transport errors
        return OdooModelsProxy(
            xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/object', allow_none=True),
            get_request_locale
        )
    
    def search_products(self, domain=None, fields=None, offset=0, limit=None, order=None, include_variants=False):
        uid = self.authenticate()
        models = self._get_models()
        
        if domain is None:
            domain = []
        if fields is None:
            # Skinny payload for list view; images are fetched separately
            fields = [
                'name',
                'list_price',
                'default_code',
                'categ_id',
                'description_sale',
                'description_ecommerce',
                'x_studio_is_published_b2audio'
            ]
            if include_variants:
                fields.append('attribute_line_ids')
        elif include_variants and 'attribute_line_ids' not in fields:
            fields.append('attribute_line_ids')
            
        # First get product IDs
        product_ids = models.execute_kw(
            self.db, uid, self.api_key,
            'product.template',
            'search',
            [domain],
            {
                'offset': offset,
                'limit': limit,
                'order': order
            }
        )
        
        if not product_ids:
            return []
            
        # Then read the product data
        products = models.execute_kw(
            self.db, uid, self.api_key,
            'product.template',
            'read',
            [product_ids],
            {'fields': fields}
        )
        
        if not include_variants:
            return products

        # Add variant information for each product when requested
        for product in products:
            if not product.get('attribute_line_ids'):
                product['variants'] = []
                continue

            attr_lines = models.execute_kw(
                self.db, uid, self.api_key,
                'product.template.attribute.line',
                'read',
                [product['attribute_line_ids']],
                {'fields': ['attribute_id', 'value_ids']}
            )
            
            variants = []
            for line in attr_lines:
                values = models.execute_kw(
                    self.db, uid, self.api_key,
                    'product.attribute.value',
                    'read',
                    [line['value_ids']],
                    {'fields': ['name']}
                )
                
                variants.append({
                    'attribute': line['attribute_id'][1],  # [1] contains the name
                    'values': [val['name'] for val in values]
                })
            
            product['variants'] = variants
        
        return products
    
    def read_product(self, product_id, fields=None, include_image=True):
        uid = self.authenticate()
        models = self._get_models()

        if fields is None:
            fields = ['name', 'list_price', 'description_ecommerce', 'default_code', 'attribute_line_ids', 'categ_id', 'x_studio_is_published_b2audio']
            if include_image:
                fields.append('image_1920')
        elif not include_image and 'image_1920' in fields:
            fields = [f for f in fields if f != 'image_1920']
            
        # First get the product with basic fields and attribute lines
        product = models.execute_kw(
            self.db, uid, self.api_key,
            'product.template',
            'read',
            [product_id],
            {'fields': fields}
        )
        
        if not product:
            return None
            
        product = product[0]
        
        # If product has attribute lines, get the variants information
        if product.get('attribute_line_ids'):
            # Get attribute lines details in one call
            attr_lines = models.execute_kw(
                self.db, uid, self.api_key,
                'product.template.attribute.line',
                'read',
                [product['attribute_line_ids']],
                {'fields': ['attribute_id', 'value_ids']}
            )

            # Collect all value_ids to batch fetch values once
            all_value_ids = []
            for line in attr_lines:
                all_value_ids.extend(line.get('value_ids', []))
            unique_value_ids = list(set(all_value_ids))

            values_by_id = {}
            if unique_value_ids:
                value_records = models.execute_kw(
                    self.db, uid, self.api_key,
                    'product.attribute.value',
                    'read',
                    [unique_value_ids],
                    {'fields': ['name']}
                )
                values_by_id = {rec['id']: rec['name'] for rec in value_records}

            variants = []
            for line in attr_lines:
                variants.append({
                    'attribute': line['attribute_id'][1],  # [1] contains the name
                    'values': [values_by_id[val_id] for val_id in line.get('value_ids', []) if val_id in values_by_id]
                })
            
            # Add variants to product data
            product['variants'] = variants
        else:
            product['variants'] = []
            
        return product
        
    def get_product_variants(self, product_id):
        """Get variant information for a product"""
        uid = self.authenticate()
        models = self._get_models()
        
        # First get the product template with attribute lines
        product = models.execute_kw(
            self.db, uid, self.api_key,
            'product.template',
            'read',
            [product_id],
            {'fields': ['name', 'attribute_line_ids']}
        )
        
        if not product or not product[0]['attribute_line_ids']:
            return []
            
        # Get attribute lines details
        attr_lines = models.execute_kw(
            self.db, uid, self.api_key,
            'product.template.attribute.line',
            'read',
            [product[0]['attribute_line_ids']],
            {'fields': ['attribute_id', 'value_ids']}
        )
        
        variants = []
        for line in attr_lines:
            # Get attribute values
            values = models.execute_kw(
                self.db, uid, self.api_key,
                'product.attribute.value',
                'read',
                [line['value_ids']],
                {'fields': ['name']}
            )
            
            variants.append({
                'attribute': line['attribute_id'][1],
                'values': [val['name'] for val in values]
            })
            
        return variants

    def _image_field_for_size(self, size):
        """Map friendly size name to Odoo image field"""
        size_map = {
            'thumb': 'image_256',
            'small': 'image_512',
            'medium': 'image_512',
            'large': 'image_1024',
            'full': 'image_1920',
            'original': 'image_1920'
        }
        return size_map.get(size, 'image_512')

    def get_product_images(self, product_ids, size='medium'):
        """Fetch images for a list of product IDs, preserving input order"""
        if not product_ids:
            return []

        uid = self.authenticate()
        models = self._get_models()
        size_field = self._image_field_for_size(size)

        records = models.execute_kw(
            self.db, uid, self.api_key,
            'product.template',
            'read',
            [product_ids],
            {'fields': [size_field]}
        )

        # Map by id to rebuild in requested order
        by_id = {rec['id']: rec.get(size_field) for rec in records}
        images = []
        for pid in product_ids:
            images.append({
                'id': pid,
                'image': by_id.get(pid)
            })
        return images

def resolve_variant_product(models, uid, product_template_id, selected_variants):
    """Resolve product.product ID for a template + selected variant names."""
    variant_product_id = None
    ptav_ids = []

    def get_attribute_id(attribute_name: str):
        attr_ids = models.execute_kw(
            ODOO_DB, uid, ODOO_API_KEY,
            'product.attribute', 'search',
            [[('name', '=', attribute_name)]],
            {'limit': 1}
        )
        return attr_ids[0] if attr_ids else None

    def get_attribute_value_id(attribute_id: int, value_name: str):
        value_ids = models.execute_kw(
            ODOO_DB, uid, ODOO_API_KEY,
            'product.attribute.value', 'search',
            [[('name', '=', value_name), ('attribute_id', '=', attribute_id)]],
            {'limit': 1}
        )
        return value_ids[0] if value_ids else None

    def get_ptav_id(product_template_id: int, product_attribute_value_id: int):
        ptav_ids_found = models.execute_kw(
            ODOO_DB, uid, ODOO_API_KEY,
            'product.template.attribute.value', 'search',
            [[('product_tmpl_id', '=', product_template_id), ('product_attribute_value_id', '=', product_attribute_value_id)]],
            {'limit': 1}
        )
        return ptav_ids_found[0] if ptav_ids_found else None

    if not selected_variants:
        tmpl_rec = models.execute_kw(
            ODOO_DB, uid, ODOO_API_KEY,
            'product.template', 'read',
            [product_template_id],
            {'fields': ['product_variant_id']}
        )
        if tmpl_rec and tmpl_rec[0].get('product_variant_id'):
            variant_product_id = tmpl_rec[0]['product_variant_id'][0]
    else:
        for attribute_name, value_name in selected_variants.items():
            attr_id = get_attribute_id(attribute_name)
            if not attr_id:
                return None, ptav_ids, f"Unknown attribute: {attribute_name}"

            val_id = get_attribute_value_id(attr_id, value_name)
            if not val_id:
                return None, ptav_ids, f"Unknown value '{value_name}' for attribute '{attribute_name}'"

            ptav_id = get_ptav_id(product_template_id, val_id)
            if not ptav_id:
                return None, ptav_ids, f"Option '{attribute_name}: {value_name}' not available for this product"
            ptav_ids.append(ptav_id)

        candidate_ids = models.execute_kw(
            ODOO_DB, uid, ODOO_API_KEY,
            'product.product', 'search',
            [[('product_tmpl_id', '=', product_template_id)]],
        )

        if candidate_ids:
            candidates = models.execute_kw(
                ODOO_DB, uid, ODOO_API_KEY,
                'product.product', 'read',
                [candidate_ids],
                {'fields': ['product_template_attribute_value_ids', 'display_name']}
            )
            needed = set(ptav_ids)

            for c in candidates:
                c_vals = set(c.get('product_template_attribute_value_ids', []))
                if needed.issubset(c_vals):
                    variant_product_id = c['id']
                    break

    return variant_product_id, ptav_ids, None

def get_template_variant_cache(models, uid, product_template_id):
    """Build or return cached per-template data for fast variant resolution."""
    now = time.time()
    locale = get_request_locale()
    cache_key = (product_template_id, locale)
    cached = VARIANT_TEMPLATE_CACHE.get(cache_key)
    if cached and cached.get('expires_at', 0) > now:
        return cached

    # Fetch all PTAVs for the template
    ptav_ids = models.execute_kw(
        ODOO_DB, uid, ODOO_API_KEY,
        'product.template.attribute.value', 'search',
        [[('product_tmpl_id', '=', product_template_id)]]
    )
    ptav_records = models.execute_kw(
        ODOO_DB, uid, ODOO_API_KEY,
        'product.template.attribute.value', 'read',
        [ptav_ids],
        {'fields': ['id', 'product_attribute_value_id']}
    ) if ptav_ids else []

    # Gather PAV metadata for name/attribute resolution
    pav_ids = set()
    for rec in ptav_records or []:
        pav = rec.get('product_attribute_value_id')
        pav_id = pav[0] if isinstance(pav, (list, tuple)) else pav
        if pav_id:
            pav_ids.add(pav_id)

    pav_records = models.execute_kw(
        ODOO_DB, uid, ODOO_API_KEY,
        'product.attribute.value', 'read',
        [list(pav_ids)],
        {'fields': ['id', 'name', 'attribute_id']}
    ) if pav_ids else []
    pav_meta = {rec['id']: rec for rec in pav_records or []}

    attr_ids = {rec['attribute_id'][0] for rec in pav_records or [] if rec.get('attribute_id')}
    attr_records = models.execute_kw(
        ODOO_DB, uid, ODOO_API_KEY,
        'product.attribute', 'read',
        [list(attr_ids)],
        {'fields': ['id', 'name']}
    ) if attr_ids else []
    attr_name_by_id = {rec['id']: rec.get('name') for rec in attr_records or []}

    # Build map: (attribute_name, value_name) -> PTAV id (lowercased for lookup)
    attr_val_to_ptav = {}
    for rec in ptav_records or []:
        pav = rec.get('product_attribute_value_id')
        pav_id = pav[0] if isinstance(pav, (list, tuple)) else pav
        pav_info = pav_meta.get(pav_id, {})
        attr_id = pav_info.get('attribute_id')
        attr_id = attr_id[0] if isinstance(attr_id, (list, tuple)) else attr_id
        attr_name = attr_name_by_id.get(attr_id, '')
        val_name = pav_info.get('name', '')
        key = (attr_name.strip().lower(), val_name.strip().lower())
        if key[0] and key[1]:
            attr_val_to_ptav[key] = rec['id']

    # Cache candidate variants once
    candidate_ids = models.execute_kw(
        ODOO_DB, uid, ODOO_API_KEY,
        'product.product', 'search',
        [[('product_tmpl_id', '=', product_template_id)]],
    )
    candidate_records = models.execute_kw(
        ODOO_DB, uid, ODOO_API_KEY,
        'product.product', 'read',
        [candidate_ids],
        {'fields': ['product_template_attribute_value_ids']}
    ) if candidate_ids else []
    candidates = [{
        'id': rec['id'],
        'ptavs': set(rec.get('product_template_attribute_value_ids', []))
    } for rec in candidate_records or []]

    cached = {
        'attr_val_to_ptav': attr_val_to_ptav,
        'candidates': candidates,
        'expires_at': now + VARIANT_TEMPLATE_CACHE_TTL
    }
    VARIANT_TEMPLATE_CACHE[cache_key] = cached
    return cached

def resolve_variant_from_cache(models, uid, product_template_id, selected_variants):
    """Resolve variant using cached per-template metadata to avoid extra RPCs."""
    cache = get_template_variant_cache(models, uid, product_template_id)
    needed_ptavs = []
    attr_val_to_ptav = cache.get('attr_val_to_ptav', {})
    candidates = cache.get('candidates', [])

    # No selections: use template default variant if possible
    if not selected_variants:
        tmpl_rec = models.execute_kw(
            ODOO_DB, uid, ODOO_API_KEY,
            'product.template', 'read',
            [product_template_id],
            {'fields': ['product_variant_id']}
        )
        if tmpl_rec and tmpl_rec[0].get('product_variant_id'):
            return tmpl_rec[0]['product_variant_id'][0], needed_ptavs, None
        # Fall back to first candidate as a last resort
        if candidates:
            return candidates[0].get('id'), needed_ptavs, None

    for attr_name, val_name in (selected_variants or {}).items():
        key = (str(attr_name).strip().lower(), str(val_name).strip().lower())
        ptav = attr_val_to_ptav.get(key)
        if not ptav:
            return None, needed_ptavs, f"Option '{attr_name}: {val_name}' not available for this product"
        needed_ptavs.append(ptav)

    needed = set(needed_ptavs)
    for c in candidates:
        ptavs = c.get('ptavs') or set()
        if needed.issubset(ptavs):
            return c['id'], needed_ptavs, None

    return None, needed_ptavs, "Could not resolve product variant for the selected options"

# Initialize the Odoo client
odoo_client = OdooXMLRPCClient(ODOO_URL, ODOO_DB, ODOO_USERNAME, ODOO_API_KEY)

@decilo_bp.route('/decilo-api/products', methods=['GET'])
@token_required
def get_products(current_user):
    """Get list of products with optional filtering"""
    try:
        # Get query parameters
        limit = request.args.get('limit', type=int)
        offset = request.args.get('offset', type=int, default=0)
        order = request.args.get('order', 'name asc')
        search = request.args.get('search')
        category_id = request.args.get('category_id', type=int)

        logger.info(f"🔍 GET_PRODUCTS called with params - limit: {limit}, offset: {offset}, search: {search}, category_id: {category_id}")

        # Build domain - filter for Ear Tips categories and published products only
        domain = [
            ('sale_ok', '=', True),  # Only show products that can be sold
            ('x_studio_is_published_b2audio', '=', True)  # Only show products published for B2Audio
        ]

        # Add category filter if provided
        if category_id:
            domain.append(('categ_id', '=', category_id))

        if search:
            domain.append(('name', 'ilike', search))

        logger.info(f"📋 Search domain: {domain}")

        # Get products
        products = odoo_client.search_products(
            domain=domain,
            offset=offset,
            limit=limit,
            order=order
        )

        logger.info(f"📦 Found {len(products)} products matching domain")
        for i, product in enumerate(products):
            logger.info(f"   Product {i+1}: id={product.get('id')}, name='{product.get('name')}', category='{product.get('categ_id', ['?', '?'])[1]}'")

        # Get all categories for filtering
        uid = get_uid()
        models = get_odoo_models()

        # Get categories that have products
        logger.info(f"🏷️ Extracting category IDs from products...")
        category_ids_from_products = list(set([p.get('categ_id', [0])[0] for p in products if p.get('categ_id')]))
        logger.info(f"📌 Category IDs found in products: {category_ids_from_products}")

        category_ids = models.execute_kw(
            ODOO_DB, uid, ODOO_API_KEY,
            'product.category', 'search',
            [[('id', 'in', category_ids_from_products)]],
            {'order': 'complete_name'}
        )

        logger.info(f"🏷️ Retrieved {len(category_ids)} category IDs: {category_ids}")

        categories = []
        if category_ids:
            category_records = models.execute_kw(
                ODOO_DB, uid, ODOO_API_KEY,
                'product.category', 'read',
                [category_ids],
                {'fields': ['id', 'name', 'complete_name', 'parent_id']}
            )
            categories = category_records
            logger.info(f"📂 Categories: {[(c.get('id'), c.get('name'), c.get('complete_name')) for c in categories]}")

        logger.info(f"✅ Returning {len(products)} products and {len(categories)} categories")
        return jsonify({
            'products': products,
            'categories': categories,
            'total': len(products),
            'offset': offset
        })

    except Exception as e:
        error_msg = f"Error fetching products: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return jsonify({'error': error_msg, 'code': 'unknown_error'}), 500


@decilo_bp.route('/decilo-api/products/default-variants', methods=['GET'])
@token_required
def get_default_variant_ids(current_user):
    """
    Get default variant product IDs for all published products.
    Used for background prefetching to enable instant image loading on click.

    Returns:
        { "variants": { product_template_id: variant_product_id, ... } }
    """
    try:
        uid = get_uid()
        models = get_odoo_models()

        # Get all published product IDs
        domain = [
            ('sale_ok', '=', True),
            ('x_studio_is_published_b2audio', '=', True)
        ]

        product_ids = models.execute_kw(
            ODOO_DB, uid, ODOO_API_KEY,
            'product.template', 'search',
            [domain]
        )

        if not product_ids:
            return jsonify({'variants': {}})

        # Get products with attribute_line_ids in one call
        products = models.execute_kw(
            ODOO_DB, uid, ODOO_API_KEY,
            'product.template', 'read',
            [product_ids],
            {'fields': ['id', 'attribute_line_ids']}
        )

        # Collect all attribute line IDs for batch fetch
        all_attr_line_ids = []
        for p in products:
            all_attr_line_ids.extend(p.get('attribute_line_ids', []))

        # Batch fetch all attribute lines
        attr_lines_by_id = {}
        if all_attr_line_ids:
            attr_lines = models.execute_kw(
                ODOO_DB, uid, ODOO_API_KEY,
                'product.template.attribute.line', 'read',
                [list(set(all_attr_line_ids))],
                {'fields': ['id', 'attribute_id', 'value_ids']}
            )
            attr_lines_by_id = {al['id']: al for al in attr_lines}

        # Collect all value IDs for batch fetch
        all_value_ids = []
        for al in attr_lines_by_id.values():
            all_value_ids.extend(al.get('value_ids', []))

        # Batch fetch all attribute values
        values_by_id = {}
        if all_value_ids:
            values = models.execute_kw(
                ODOO_DB, uid, ODOO_API_KEY,
                'product.attribute.value', 'read',
                [list(set(all_value_ids))],
                {'fields': ['id', 'name']}
            )
            values_by_id = {v['id']: v['name'] for v in values}

        # Now resolve default variant for each product
        result = {}
        for product in products:
            product_id = product['id']
            attr_line_ids = product.get('attribute_line_ids', [])

            if not attr_line_ids:
                # No variants - use template's default variant
                variant_id, _, _ = resolve_variant_from_cache(models, uid, product_id, {})
                if variant_id:
                    result[product_id] = variant_id
                continue

            # Compute default selections (first value of each attribute, skip ear impression)
            default_selections = {}
            for line_id in attr_line_ids:
                line = attr_lines_by_id.get(line_id, {})
                attr_name = line.get('attribute_id', [0, ''])[1]
                value_ids = line.get('value_ids', [])

                # Skip ear impression attributes
                if 'ear impression' in attr_name.lower():
                    continue

                # Get first value
                if value_ids:
                    first_value = values_by_id.get(value_ids[0], '')
                    if first_value:
                        default_selections[attr_name] = first_value

            # Resolve variant
            variant_id, _, err = resolve_variant_from_cache(models, uid, product_id, default_selections)
            if variant_id:
                result[product_id] = variant_id

        return jsonify({'variants': result})

    except Exception as e:
        error_msg = f"Error fetching default variants: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return jsonify({'error': error_msg, 'code': 'unknown_error'}), 500


@decilo_bp.route('/decilo-api/product-images', methods=['GET'])
@token_required
def get_product_images_endpoint(current_user):
    """
    Fetch images for a list of product IDs in the order provided.
    Query params:
      - ids: comma-separated product IDs (required)
      - size: thumb | small | medium | large | full | original (default: medium)
    """
    try:
        ids_param = request.args.get('ids')
        size = request.args.get('size', 'medium')

        if not ids_param:
            return jsonify({'error': 'ids query parameter is required'}), 400

        try:
            product_ids = [int(pid) for pid in ids_param.split(',') if pid.strip()]
        except ValueError:
            return jsonify({'error': 'ids must be comma-separated integers'}), 400

        if not product_ids:
            return jsonify({'error': 'ids must contain at least one product id'}), 400

        images = odoo_client.get_product_images(product_ids, size=size)
        return jsonify({
            'size': size,
            'count': len(images),
            'images': images
        })

    except Exception as e:
        error_msg = f"Error fetching product images: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return jsonify({'error': error_msg, 'code': 'unknown_error'}), 500


@decilo_bp.route('/decilo-api/products/prefetch', methods=['POST'])
@token_required
def prefetch_products(current_user):
    """
    Pre-warm caches for a list of products to enable instant loading when clicked.
    Fetches product details, variants, default variant images, and exclusions.

    Request body:
    {
        "product_ids": [1, 2, 3, ...],
        "image_sizes": ["medium", "full"]  // optional, defaults to ["medium"]
    }

    Returns summary of what was prefetched.
    """
    try:
        payload = request.get_json(silent=True) or {}
        product_ids = payload.get('product_ids', [])
        image_sizes = payload.get('image_sizes', ['medium'])

        if not product_ids:
            return jsonify({'error': 'product_ids is required'}), 400

        if not isinstance(product_ids, list):
            return jsonify({'error': 'product_ids must be an array'}), 400

        # Limit to prevent abuse
        max_products = 20
        if len(product_ids) > max_products:
            product_ids = product_ids[:max_products]

        uid = get_uid()
        models = get_odoo_models()
        now = time.time()

        prefetched = []
        errors = []

        for product_id in product_ids:
            try:
                product_result = {
                    'product_id': product_id,
                    'details': False,
                    'variants': False,
                    'exclusions': False,
                    'images': []
                }

                # 1. Fetch and cache product details + variants
                product = odoo_client.read_product(product_id, include_image=False)
                if product:
                    product_result['details'] = True
                    variants = odoo_client.get_product_variants(product_id)
                    if variants:
                        product_result['variants'] = True

                        # 2. Compute default variant selections (first value of each attribute, except Ear Impression Type)
                        default_selections = {}
                        for variant in variants:
                            attr_name = variant.get('attribute', '')
                            values = variant.get('values', [])
                            # Skip Ear Impression Type - it's user-selected
                            if 'ear impression' in attr_name.lower():
                                continue
                            if values:
                                default_selections[attr_name] = values[0]

                        # 3. Pre-warm template variant cache (used by resolve_variant_from_cache)
                        get_template_variant_cache(models, uid, product_id)

                        # 4. Prefetch variant images for default selections
                        if default_selections:
                            for size in image_sizes:
                                try:
                                    cache_key = (product_id, size, json.dumps(sorted(default_selections.items())))

                                    # Check if already cached
                                    cached = VARIANT_IMAGE_CACHE.get(cache_key)
                                    if cached and cached.get('expires_at', 0) > now:
                                        product_result['images'].append({'size': size, 'cached': True})
                                        continue

                                    # Resolve variant and fetch image
                                    variant_product_id, ptav_ids, err = resolve_variant_from_cache(
                                        models, uid, product_id, default_selections
                                    )

                                    if not err and variant_product_id:
                                        size_field = odoo_client._image_field_for_size(size)
                                        variant_image = models.execute_kw(
                                            ODOO_DB, uid, ODOO_API_KEY,
                                            'product.product', 'read',
                                            [[variant_product_id]],
                                            {'fields': [size_field]}
                                        )

                                        image_b64 = None
                                        if variant_image and variant_image[0].get(size_field):
                                            image_b64 = variant_image[0].get(size_field)

                                        # Fallback to template image
                                        if not image_b64:
                                            template_images = odoo_client.get_product_images([product_id], size=size)
                                            if template_images and template_images[0].get('image'):
                                                image_b64 = template_images[0].get('image')

                                        if image_b64:
                                            # Cache the full payload
                                            image_url = f"data:image/png;base64,{image_b64}"
                                            cached_payload = {
                                                'product_id': product_id,
                                                'variant_product_id': variant_product_id,
                                                'image': image_url,
                                                'ptav_ids': ptav_ids,
                                                'source': 'variant' if variant_image and variant_image[0].get(size_field) else 'product',
                                                'size': size
                                            }
                                            VARIANT_IMAGE_CACHE[cache_key] = {
                                                'payload': cached_payload,
                                                'expires_at': now + VARIANT_IMAGE_CACHE_TTL,
                                                'image': image_b64
                                            }
                                            product_result['images'].append({'size': size, 'cached': False, 'fetched': True})
                                        else:
                                            product_result['images'].append({'size': size, 'fetched': False, 'reason': 'no_image'})
                                    else:
                                        product_result['images'].append({'size': size, 'fetched': False, 'reason': err or 'no_variant'})
                                except Exception as img_err:
                                    product_result['images'].append({'size': size, 'error': str(img_err)})

                # 5. Pre-warm exclusions cache by calling the exclusion logic
                try:
                    ptav_ids = models.execute_kw(
                        ODOO_DB, uid, ODOO_API_KEY,
                        'product.template.attribute.value', 'search',
                        [[('product_tmpl_id', '=', product_id)]],
                        {'order': 'id asc'}
                    )
                    if ptav_ids:
                        product_result['exclusions'] = True
                except Exception:
                    pass

                prefetched.append(product_result)

            except Exception as prod_err:
                errors.append({'product_id': product_id, 'error': str(prod_err)})

        return jsonify({
            'prefetched': prefetched,
            'errors': errors,
            'total': len(prefetched),
            'requested': len(product_ids)
        })

    except Exception as e:
        error_msg = f"Error in prefetch: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return jsonify({'error': error_msg, 'code': 'unknown_error'}), 500


@decilo_bp.route('/decilo-api/products/<int:product_id>/image', methods=['GET'])
@token_required
def get_product_image(current_user, product_id):
    """Fetch a single product image at the requested size"""
    try:
        size = request.args.get('size', 'medium')
        images = odoo_client.get_product_images([product_id], size=size)
        image_data = images[0]['image'] if images else None

        if not image_data:
            return jsonify({'error': 'Image not found', 'code': 'not_found'}), 404

        binary = base64.b64decode(image_data)
        image_type = imghdr.what(None, h=binary) or 'png'
        mimetype = f'image/{image_type}'

        return Response(binary, mimetype=mimetype)

    except Exception as e:
        error_msg = f"Error fetching image for product {product_id}: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return jsonify({'error': error_msg, 'code': 'unknown_error'}), 500


@decilo_bp.route('/decilo-api/variant-image/<int:variant_product_id>', methods=['GET'])
@token_required
def get_variant_image_by_id(current_user, variant_product_id):
    """
    Fetch image for a specific variant product by its ID.
    This is the fast path - no variant resolution needed, just one RPC.

    Query params:
        size: thumb | small | medium | large | full (default: medium)

    Returns: Binary image data with appropriate MIME type
    """
    try:
        size = request.args.get('size', 'medium')
        uid = get_uid()
        models = get_odoo_models()

        # Map size to Odoo field
        size_field = odoo_client._image_field_for_size(size)

        # Single RPC to get the image
        variant_data = models.execute_kw(
            ODOO_DB, uid, ODOO_API_KEY,
            'product.product', 'read',
            [[variant_product_id]],
            {'fields': [size_field]}
        )

        if not variant_data or not variant_data[0].get(size_field):
            return jsonify({'error': 'Image not found', 'code': 'not_found'}), 404

        image_b64 = variant_data[0][size_field]
        binary = base64.b64decode(image_b64)
        image_type = imghdr.what(None, h=binary) or 'png'
        mimetype = f'image/{image_type}'

        return Response(binary, mimetype=mimetype)

    except Exception as e:
        error_msg = f"Error fetching variant image {variant_product_id}: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return jsonify({'error': error_msg, 'code': 'unknown_error'}), 500


@decilo_bp.route('/decilo-api/products/<int:product_id>', methods=['GET'])
@token_required
def get_product(current_user, product_id):
    """Get detailed information about a specific product.

    Simplified endpoint - returns product with variants in ~1 RPC.
    Use /variant-image/<id> for images and /products/<id>/variant-exclusions for exclusions.

    Query params:
        include_image: bool - include product template image (default: false)
    """
    try:
        include_image_param = request.args.get('include_image', 'false').lower()
        include_image = include_image_param in ['true', '1', 'yes']

        # read_product already fetches variants internally - no need for separate call
        product = odoo_client.read_product(product_id, include_image=include_image)

        if not product:
            return jsonify({'error': 'Product not found', 'code': 'not_found'}), 404

        # Product already includes 'variants' from read_product
        return jsonify(product)

    except Exception as e:
        error_msg = f"Error fetching product {product_id}: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return jsonify({'error': error_msg, 'code': 'unknown_error'}), 500

@decilo_bp.route('/decilo-api/customer-password-reset', methods=['POST'])
def customer_password_reset():
    logger.info("Received request for /decilo-api/customer-password-reset")
    try:
        data = request.get_json()
        email = data.get('email')
        
        if not email:
            return jsonify({'error': 'Email address is required'}), 400

        try:
            # Get UID
            uid = get_uid()
            
            # Get models connection
            models = get_odoo_models()
            
            # Search for user
            user_ids = models.execute_kw(
                ODOO_DB, uid, ODOO_API_KEY,
                'res.users',
                'search',
                [[('login', '=', email)]],
                {'limit': 1}
            )
            
            if not user_ids:
                return jsonify({'error': 'Email not found', 'code': 'email_not_found'}), 404

            # Reset password
            models.execute_kw(
                ODOO_DB, uid, ODOO_API_KEY,
                'res.users',
                'action_reset_password',
                [user_ids]
            )

            return jsonify({'message': 'Password reset email has been sent'})

        except xmlrpc.client.Fault as e:
            logger.error(f"Odoo fault: {str(e)}")
            return jsonify({'error': 'Password reset failed', 'code': 'reset_failed'}), 400

    except Exception as e:
        error_msg = f"Error in password reset: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return jsonify({'error': error_msg, 'code': 'unknown_error'}), 500


@decilo_bp.route('/decilo-api/patient-contacts', methods=['GET'])
@token_required
def get_patient_contacts(current_user):
    """Fetch patient contacts for the logged-in user (referring contact)"""
    logger.info("Received request for /decilo-api/patient-contacts")
    try:
        uid = get_uid()
        models = get_odoo_models()

        # Search for patient contacts where x_studio_referring_contact = current user's partner_id
        patient_ids = models.execute_kw(
            ODOO_DB, uid, ODOO_API_KEY,
            'res.partner', 'search',
            [[
                ('x_studio_referring_contact', '=', current_user['id']),
                ('type', '=', 'contact')  # Only contact type partners (not companies)
            ]]
        )

        if not patient_ids:
            return jsonify({'patients': [], 'total': 0})

        # Read patient details - Odoo only has 'name' field in "SURNAME Firstname" format
        patients = models.execute_kw(
            ODOO_DB, uid, ODOO_API_KEY,
            'res.partner', 'read',
            [patient_ids],
            {'fields': ['id', 'name', 'email', 'phone']}
        )

        # Transform to expected format
        transformed_patients = []
        for patient in patients:
            full_name = patient.get('name', '')
            name_parts = full_name.rsplit(' ', 1) if full_name else ['', '']

            transformed_patients.append({
                'id': patient['id'],
                'name': full_name,
                'email': patient.get('email', ''),
                'phone': patient.get('phone', '')
            })

        return jsonify({
            'patients': transformed_patients,
            'total': len(transformed_patients)
        })

    except Exception as e:
        error_msg = f"Error fetching patient contacts: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return jsonify({'error': error_msg, 'code': 'unknown_error'}), 500


@decilo_bp.route('/decilo-api/patient-contacts', methods=['POST'])
@token_required
def create_patient_contact(current_user):
    """Create a new patient contact for the logged-in user"""
    logger.info("Received request for POST /decilo-api/patient-contacts")
    try:
        data = request.get_json()
        first_name = data.get('firstName', '').strip()
        last_name = data.get('lastName', '').strip()
        email = data.get('email', '').strip()
        phone = data.get('phone', '').strip()

        if not first_name and not last_name:
            return jsonify({'error': 'First name or last name is required'}), 400

        uid = get_uid()
        models = get_odoo_models()

        # Prepare patient data - Odoo only uses 'name' field in format "Firstname LASTNAME"
        full_name = ""
        if first_name and last_name:
            full_name = f"{first_name} {last_name.upper()}"
        elif first_name:
            full_name = first_name
        elif last_name:
            full_name = last_name.upper()

        patient_data = {
            'type': 'contact',
            'name': full_name,
            'x_studio_referring_contact': current_user['id'],  # Link to logged-in user
        }

        if email:
            patient_data['email'] = email
        if phone:
            patient_data['phone'] = phone

        # Create the patient contact
        patient_id = models.execute_kw(
            ODOO_DB, uid, ODOO_API_KEY,
            'res.partner', 'create',
            [patient_data]
        )

        # Read the created patient for response
        created_patient = models.execute_kw(
            ODOO_DB, uid, ODOO_API_KEY,
            'res.partner', 'read',
            [patient_id],
            {'fields': ['id', 'name', 'email', 'phone']}
        )[0]

        # Parse the name field to extract first and last names
        full_name = created_patient.get('name', '')
        name_parts = full_name.rsplit(' ', 1) if full_name else ['', '']

        # Transform to expected format
        response_patient = {
            'id': created_patient['id'],
            'name': full_name,
            'firstName': name_parts[0] if len(name_parts) > 1 else '',
            'lastName': name_parts[1].lower() if len(name_parts) > 1 and name_parts[1] else '',
            'email': created_patient.get('email', ''),
            'phone': created_patient.get('phone', '')
        }

        return jsonify(response_patient), 201

    except Exception as e:
        error_msg = f"Error creating patient contact: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return jsonify({'error': error_msg, 'code': 'unknown_error'}), 500


@decilo_bp.route('/decilo-api/orders', methods=['GET'])
@token_required
def get_customer_orders(current_user):
    """Fetch sales orders for the logged-in customer (by partner_id) sorted by most recent date."""
    logger.info("Received request for /decilo-api/orders")
    try:
        # Query params
        limit = request.args.get('limit', type=int)
        offset = request.args.get('offset', type=int, default=0)
        status = request.args.get('status')  # optional filter by friendly status
        search = request.args.get('search')  # optional search by order name or product

        # Map friendly status to Odoo states
        status_map = {
            'Processing': ['draft', 'sent', 'sale'],
            'Shipped': [],  # Would require stock pickings; leave empty to not filter
            'Delivered': ['done'],
            'Cancelled': ['cancel']
        }

        # Build domain using partner_id from JWT
        domain = [('partner_id', '=', current_user['id'])]

        # Apply status filter if provided and mapped
        if status and status in status_map and status_map[status]:
            domain[0].append(('state', 'in', status_map[status]))

        # Note: searching by product requires joining lines; we handle it post-fetch if provided

        # Connect to Odoo
        uid = get_uid()
        models = get_odoo_models()

        # Search for order ids ordered by date_order desc
        # Build options without None values to avoid XML-RPC None marshaling
        search_options = {
            'offset': offset,
            'order': 'date_order desc'
        }
        if limit is not None:
            search_options['limit'] = limit

        order_ids = models.execute_kw(
            ODOO_DB, uid, ODOO_API_KEY,
            'sale.order', 'search',
            [domain],
            search_options
        )

        if not order_ids:
            return jsonify({'orders': [], 'total': 0, 'offset': offset})

        # Read orders basic fields
        order_fields = ['name', 'date_order', 'state', 'amount_total', 'amount_tax', 'amount_untaxed', 'order_line', 'partner_shipping_id', 'x_studio_patient']
        orders = models.execute_kw(
            ODOO_DB, uid, ODOO_API_KEY,
            'sale.order', 'read',
            [order_ids],
            {'fields': order_fields}
        )

        # Fetch related manufacturing orders (mrp.production) by origin = sale order name
        origin_to_mo_data = {}
        order_names = [o.get('name') for o in orders if o.get('name')]
        if order_names:
            mo_ids = models.execute_kw(
                ODOO_DB, uid, ODOO_API_KEY,
                'mrp.production', 'search',
                [[('origin', 'in', order_names)]],
                {'order': 'id desc'}
            )
            if mo_ids:
                mo_records = models.execute_kw(
                    ODOO_DB, uid, ODOO_API_KEY,
                    'mrp.production', 'read',
                    [mo_ids],
                    {'fields': ['origin', 'state', 'name']}
                )
                # Keep the latest data per origin (ids sorted desc ensures first is latest)
                for rec in mo_records:
                    origin = rec.get('origin')
                    state = rec.get('state')
                    name = rec.get('name')
                    if origin and origin not in origin_to_mo_data:
                        origin_to_mo_data[origin] = {'state': state, 'name': name}

        # Collect all line ids and shipping partner ids for batch reads
        all_line_ids = []
        shipping_partner_ids = []
        patient_ids = []
        for o in orders:
            all_line_ids.extend(o.get('order_line', []))
            if o.get('partner_shipping_id'):
                shipping_partner_ids.append(o['partner_shipping_id'][0])
            if o.get('x_studio_patient'):
                xp = o['x_studio_patient']
                patient_id = xp[0] if isinstance(xp, (list, tuple)) else xp
                if patient_id:
                    patient_ids.append(patient_id)

        # Read lines
        lines_by_id = {}
        if all_line_ids:
            line_fields = ['product_id', 'name', 'product_uom_qty', 'price_unit', 'price_subtotal']
            line_records = models.execute_kw(
                ODOO_DB, uid, ODOO_API_KEY,
                'sale.order.line', 'read',
                [list(set(all_line_ids))],
                {'fields': line_fields}
            )
            lines_by_id = {rec['id']: rec for rec in line_records}

        # Read shipping partners
        partners_by_id = {}
        if shipping_partner_ids:
            partner_fields = ['name', 'street', 'city', 'zip', 'country_id']
            partner_records = models.execute_kw(
                ODOO_DB, uid, ODOO_API_KEY,
                'res.partner', 'read',
                [list(set(shipping_partner_ids))],
                {'fields': partner_fields}
            )
            partners_by_id = {rec['id']: rec for rec in partner_records}

        # Read patients with custom ID field
        patients_by_id = {}
        if patient_ids:
            patient_fields = ['name', 'x_studio_id_custom']
            patient_records = models.execute_kw(
                ODOO_DB, uid, ODOO_API_KEY,
                'res.partner', 'read',
                [list(set(patient_ids))],
                {'fields': patient_fields}
            )
            patients_by_id = {rec['id']: rec for rec in patient_records}

        def map_state_to_status(state: str) -> str:
            if state in ['done']:
                return 'Delivered'
            if state in ['cancel']:
                return 'Cancelled'
            # "sent", "draft", "sale" -> Processing
            return 'Processing'

        # Build response orders
        response_orders = []
        for o in orders:
            shipping = None
            patient = None
            if o.get('partner_shipping_id'):
                sp_id = o['partner_shipping_id'][0]
                p = partners_by_id.get(sp_id)
                if p:
                    shipping = {
                        'street': p.get('street'),
                        'city': p.get('city'),
                        'postalCode': p.get('zip'),
                        'country': p.get('country_id')[1] if p.get('country_id') else None
                    }

            # Map products from lines
            products = []
            for lid in o.get('order_line', []):
                lr = lines_by_id.get(lid)
                if not lr:
                    continue
                products.append({
                    'id': lr['product_id'][0] if lr.get('product_id') else None,
                    'name': lr.get('name'),
                    'specifications': None,
                    'quantity': lr.get('product_uom_qty'),
                    'price': lr.get('price_unit')
                })

            # Optional search filter by order name or product name (client-side like)
            if search:
                q = str(search).lower()
                if not (
                    (o.get('name') and q in o['name'].lower()) or
                    any((p.get('name') and q in p['name'].lower()) for p in products)
                ):
                    continue

            # Build patient object from x_studio_patient m2o if present
            if o.get('x_studio_patient'):
                xp = o['x_studio_patient']
                patient_id = None
                if isinstance(xp, (list, tuple)) and len(xp) >= 2:
                    patient_id = xp[0]
                    patient = {'id': patient_id, 'name': xp[1]}
                elif isinstance(xp, int):
                    patient_id = xp
                    patient = {'id': patient_id, 'name': None}
                
                # Add the custom ID if available
                if patient_id and patient_id in patients_by_id:
                    patient_data = patients_by_id[patient_id]
                    if patient_data.get('x_studio_id_custom'):
                        patient['customId'] = patient_data['x_studio_id_custom']

            mo_data = origin_to_mo_data.get(o.get('name'))
            response_orders.append({
                'id': o['id'],
                'number': o.get('name'),
                'date': o.get('date_order'),
                'status': map_state_to_status(o.get('state')),
                'manufacturing_state': mo_data.get('state') if mo_data else None,
                'manufacturing_order_number': mo_data.get('name') if mo_data else None,
                'products': products,
                'subtotal': o.get('amount_untaxed'),
                'shipping': None,
                'tax': o.get('amount_tax'),
                'total': o.get('amount_total'),
                'paymentMethod': None,
                'shippingMethod': None,
                'shippingAddress': shipping,
                'patient': patient
            })

        # Ensure date descending in case of later filtering
        response_orders.sort(key=lambda x: x.get('date') or '', reverse=True)

        return jsonify({'orders': response_orders, 'total': len(response_orders), 'offset': offset})

    except Exception as e:
        error_msg = f"Error fetching customer orders: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return jsonify({'error': error_msg, 'code': 'unknown_error'}), 500


@decilo_bp.route('/decilo-api/orders/<int:order_id>', methods=['GET'])
@token_required
def get_order_details(current_user, order_id):
    """Fetch detailed information for a specific sale order, including product details for each line."""
    logger.info(f"Received request for /decilo-api/orders/{order_id}")
    try:
        uid = get_uid()
        models = get_odoo_models()

        # Read the order and verify it belongs to the current partner
        order_fields = ['name', 'date_order', 'state', 'partner_id', 'x_studio_patient', 'order_line', 'amount_total', 'amount_tax', 'amount_untaxed', 'x_studio_notes']
        orders = models.execute_kw(
            ODOO_DB, uid, ODOO_API_KEY,
            'sale.order', 'read',
            [order_id],
            {'fields': order_fields}
        )

        if not orders:
            return jsonify({'error': 'Order not found', 'code': 'not_found'}), 404

        order = orders[0]

        # Security: ensure the order belongs to the logged-in partner
        if not order.get('partner_id') or order['partner_id'][0] != current_user['id']:
            return jsonify({'error': 'Forbidden', 'code': 'forbidden'}), 403

        # Read order lines
        line_fields = ['product_id', 'name', 'product_uom_qty', 'price_unit', 'price_subtotal']
        line_ids = order.get('order_line', [])
        lines = []
        products_product_ids = []
        if line_ids:
            line_records = models.execute_kw(
                ODOO_DB, uid, ODOO_API_KEY,
                'sale.order.line', 'read',
                [line_ids],
                {'fields': line_fields}
            )
            lines = line_records
            # Collect product.product ids
            for lr in line_records:
                if lr.get('product_id'):
                    products_product_ids.append(lr['product_id'][0])

        # Map product.product -> template and details
        product_id_to_details = {}
        if products_product_ids:
            # Read product.product to get template ids and display name
            product_product_fields = ['display_name', 'default_code', 'product_tmpl_id']
            product_products = models.execute_kw(
                ODOO_DB, uid, ODOO_API_KEY,
                'product.product', 'read',
                [list(set(products_product_ids))],
                {'fields': product_product_fields}
            )
            tmpl_ids = [pp['product_tmpl_id'][0] for pp in product_products if pp.get('product_tmpl_id')]

            tmpl_id_to_data = {}
            if tmpl_ids:
                tmpl_fields = ['image_1920', 'description_ecommerce', 'name']
                tmpls = models.execute_kw(
                    ODOO_DB, uid, ODOO_API_KEY,
                    'product.template', 'read',
                    [list(set(tmpl_ids))],
                    {'fields': tmpl_fields}
                )
                tmpl_id_to_data = {t['id']: t for t in tmpls}

            for pp in product_products:
                tmpl = tmpl_id_to_data.get(pp['product_tmpl_id'][0]) if pp.get('product_tmpl_id') else None
                product_id_to_details[pp['id']] = {
                    'id': pp['id'],
                    'name': pp.get('display_name'),
                    'code': pp.get('default_code'),
                    'image_1920': (tmpl.get('image_1920') if tmpl else None),
                    'description': (tmpl.get('description_ecommerce') if tmpl else None) or None
                }

        # Build detailed lines
        detailed_lines = []
        for lr in lines:
            product_info = None
            if lr.get('product_id'):
                product_info = product_id_to_details.get(lr['product_id'][0])
            detailed_lines.append({
                'id': lr['id'],
                'name': lr.get('name'),
                'quantity': lr.get('product_uom_qty'),
                'price': lr.get('price_unit'),
                'subtotal': lr.get('price_subtotal'),
                'product': product_info
            })

        def map_state_to_status(state: str) -> str:
            if state in ['done']:
                return 'Delivered'
            if state in ['cancel']:
                return 'Cancelled'
            return 'Processing'

        # Build response with partner data
        partner = None
        patient = None
        if order.get('partner_id'):
            pid = order['partner_id'][0]
            pname = order['partner_id'][1] if isinstance(order['partner_id'], (list, tuple)) and len(order['partner_id']) > 1 else None
            partner = {'id': pid, 'name': pname}
        if order.get('x_studio_patient'):
            p2 = order['x_studio_patient']
            pat_id = p2[0] if isinstance(p2, (list, tuple)) else p2
            pat_name = p2[1] if isinstance(p2, (list, tuple)) and len(p2) > 1 else None
            patient = {'id': pat_id, 'name': pat_name}

        response = {
            'id': order['id'],
            'number': order.get('name'),
            'date': order.get('date_order'),
            'status': map_state_to_status(order.get('state')),
            'subtotal': order.get('amount_untaxed'),
            'tax': order.get('amount_tax'),
            'total': order.get('amount_total'),
            'lines': detailed_lines,
            'partner': partner,
            'patient': patient,
        }

        # Read notes from Odoo
        notes_field = 'x_studio_notes'
        if notes_field in order:
            response['notes'] = order[notes_field]

        return jsonify(response)

    except Exception as e:
        error_msg = f"Error fetching order {order_id} details: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return jsonify({'error': error_msg, 'code': 'unknown_error'}), 500


@decilo_bp.route('/decilo-api/patient-ear-impressions', methods=['GET'])
@token_required
def get_patient_ear_impressions(current_user):
    """Return availability and filenames of patient's stored ear impression binaries."""
    logger.info("Received request for /decilo-api/patient-ear-impressions")
    try:
        patient_id = request.args.get('patient_id', type=int)
        if not patient_id:
            return jsonify({'error': 'patient_id is required'}), 400

        uid = get_uid()
        models = get_odoo_models()

        # Read partner fields including optional filename studio fields if present
        fields = ['name', 'x_studio_left_ear_impression', 'x_studio_right_ear_impression']
        # Try to read companion filename fields (ignore if not present)
        try:
            available = models.execute_kw(
                ODOO_DB, uid, ODOO_API_KEY,
                'res.partner', 'fields_get',
                [['x_studio_left_ear_impression_filename', 'x_studio_right_ear_impression_filename']]
            ) or {}
            if 'x_studio_left_ear_impression_filename' in available:
                fields.append('x_studio_left_ear_impression_filename')
            if 'x_studio_right_ear_impression_filename' in available:
                fields.append('x_studio_right_ear_impression_filename')
        except Exception:
            pass

        recs = models.execute_kw(
            ODOO_DB, uid, ODOO_API_KEY,
            'res.partner', 'read',
            [patient_id],
            {'fields': fields}
        )
        if not recs:
            return jsonify({'error': 'Patient not found'}), 404

        rec = recs[0]
        left_exists = bool(rec.get('x_studio_left_ear_impression'))
        right_exists = bool(rec.get('x_studio_right_ear_impression'))
        left_filename = rec.get('x_studio_left_ear_impression_filename') or ('left_ear_impression' if left_exists else None)
        right_filename = rec.get('x_studio_right_ear_impression_filename') or ('right_ear_impression' if right_exists else None)

        return jsonify({
            'patient': {'id': patient_id, 'name': rec.get('name')},
            'left': {'exists': left_exists, 'filename': left_filename},
            'right': {'exists': right_exists, 'filename': right_filename}
        })
    except Exception as e:
        error_msg = f"Error fetching patient ear impressions: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return jsonify({'error': error_msg, 'code': 'unknown_error'}), 500


@decilo_bp.route('/decilo-api/patient-ear-impressions/download', methods=['GET'])
@token_required
def download_patient_ear_impression(current_user):
    """Download left or right ear impression binary for a patient as an attachment."""
    try:
        patient_id = request.args.get('patient_id', type=int)
        side = (request.args.get('side') or '').lower()
        if not patient_id or side not in ['left', 'right']:
            return jsonify({'error': 'patient_id and side (left|right) are required'}), 400

        uid = get_uid()
        models = get_odoo_models()

        # Security: ensure the patient belongs to current user if needed? Skipping strict check; relying on portal visibility.
        # Read fields including optional filename
        bin_field = f"x_studio_{side}_ear_impression"
        name_field = f"x_studio_{side}_ear_impression_filename"
        fields = ['name', bin_field]
        try:
            available = models.execute_kw(
                ODOO_DB, uid, ODOO_API_KEY,
                'res.partner', 'fields_get',
                [[name_field]]
            ) or {}
            if name_field in available:
                fields.append(name_field)
        except Exception:
            pass

        recs = models.execute_kw(
            ODOO_DB, uid, ODOO_API_KEY,
            'res.partner', 'read',
            [patient_id],
            {'fields': fields}
        )
        if not recs:
            return jsonify({'error': 'Patient not found'}), 404

        rec = recs[0]
        b64data = rec.get(bin_field)
        if not b64data:
            return jsonify({'error': 'File not found'}), 404

        try:
            file_bytes = base64.b64decode(b64data)
        except Exception:
            return jsonify({'error': 'Invalid file data'}), 500

        filename = rec.get(name_field) or f"{side}_ear_impression.bin"

        headers = {
            'Content-Type': 'application/octet-stream',
            'Content-Disposition': f'attachment; filename="{filename}"'
        }
        return Response(file_bytes, headers=headers)
    except Exception as e:
        error_msg = f"Error downloading ear impression: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return jsonify({'error': error_msg, 'code': 'unknown_error'}), 500


@decilo_bp.route('/decilo-api/orders/<int:order_id>/ear-impressions', methods=['GET'])
@token_required
def get_order_ear_impressions(current_user, order_id: int):
    """Return ear impression availability/filenames for the order's linked patient (x_studio_patient)."""
    logger.info(f"Received request for /decilo-api/orders/{order_id}/ear-impressions")
    try:
        uid = get_uid()
        models = get_odoo_models()

        # Read order with patient link
        order_fields = ['x_studio_patient']
        orders = models.execute_kw(
            ODOO_DB, uid, ODOO_API_KEY,
            'sale.order', 'read',
            [order_id],
            {'fields': order_fields}
        )
        if not orders:
            return jsonify({'error': 'Order not found'}), 404
        order = orders[0]

        patient_m2o = order.get('x_studio_patient')
        if not patient_m2o:
            return jsonify({'patient': None, 'left': {'exists': False}, 'right': {'exists': False}})

        patient_id = patient_m2o[0] if isinstance(patient_m2o, (list, tuple)) else patient_m2o

        # Reuse logic by reading partner fields directly
        fields = ['name', 'x_studio_left_ear_impression', 'x_studio_right_ear_impression']
        try:
            available = models.execute_kw(
                ODOO_DB, uid, ODOO_API_KEY,
                'res.partner', 'fields_get',
                [['x_studio_left_ear_impression_filename', 'x_studio_right_ear_impression_filename']]
            ) or {}
            if 'x_studio_left_ear_impression_filename' in available:
                fields.append('x_studio_left_ear_impression_filename')
            if 'x_studio_right_ear_impression_filename' in available:
                fields.append('x_studio_right_ear_impression_filename')
        except Exception:
            pass

        recs = models.execute_kw(
            ODOO_DB, uid, ODOO_API_KEY,
            'res.partner', 'read',
            [patient_id],
            {'fields': fields}
        )
        if not recs:
            return jsonify({'error': 'Patient not found'}), 404

        rec = recs[0]
        left_exists = bool(rec.get('x_studio_left_ear_impression'))
        right_exists = bool(rec.get('x_studio_right_ear_impression'))
        left_filename = rec.get('x_studio_left_ear_impression_filename') or ('left_ear_impression' if left_exists else None)
        right_filename = rec.get('x_studio_right_ear_impression_filename') or ('right_ear_impression' if right_exists else None)

        return jsonify({
            'patient': {'id': patient_id, 'name': rec.get('name')},
            'left': {'exists': left_exists, 'filename': left_filename},
            'right': {'exists': right_exists, 'filename': right_filename}
        })
    except Exception as e:
        error_msg = f"Error fetching order ear impressions: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return jsonify({'error': error_msg, 'code': 'unknown_error'}), 500


@decilo_bp.route('/decilo-api/products/<int:product_id>/variant-exclusions', methods=['GET'])
@token_required
def get_product_variant_exclusions(current_user, product_id: int):
    """Return forbidden combinations grouped by the PTAV that declares exclusions.

    Output shape:
    {
      "product_id": <template_id>,
      "exclusions": [
        { "value": "<PTAV base value name>", "excluded_values": ["<name>", "<name>", ...] },
        ...
      ]
    }
    """
    logger.info(f"Received request for /decilo-api/products/{product_id}/variant-exclusions")
    try:
        uid = get_uid()
        models = get_odoo_models()

        # Find all product.template.attribute.value (PTAV) for this template to get exclusion record ids
        ptav_ids = models.execute_kw(
            ODOO_DB, uid, ODOO_API_KEY,
            'product.template.attribute.value', 'search',
            [[('product_tmpl_id', '=', product_id)]],
            {'order': 'id asc'}
        )

        if not ptav_ids:
            return jsonify({'product_id': product_id, 'exclusions': []})

        ptavs = models.execute_kw(
            ODOO_DB, uid, ODOO_API_KEY,
            'product.template.attribute.value', 'read',
            [ptav_ids],
            {'fields': ['exclude_for', 'product_attribute_value_id']}
        )
        exclusion_ids = set()
        ptav_base_pav_ids = []
        for r in ptavs:
            for eid in (r.get('exclude_for') or []):
                exclusion_ids.add(eid)
            pav = r.get('product_attribute_value_id')
            pav_id = pav[0] if isinstance(pav, (list, tuple)) else pav
            if pav_id:
                ptav_base_pav_ids.append(pav_id)
        if not exclusion_ids:
            return jsonify({'product_id': product_id, 'exclusions': []})

        # Read exclusion records to get the value_ids involved per exclusion
        exclusions_raw = models.execute_kw(
            ODOO_DB, uid, ODOO_API_KEY,
            'product.template.attribute.exclusion', 'read',
            [list(exclusion_ids)],
            {'fields': ['product_tmpl_id', 'value_ids']}
        )
        # Keep only exclusions for this product template to avoid cross-template mixups
        ex_by_id = {}
        for ex in exclusions_raw or []:
            tmpl = ex.get('product_tmpl_id')
            tmpl_id = tmpl[0] if isinstance(tmpl, (list, tuple)) else tmpl
            if tmpl_id == product_id:
                ex_by_id[ex.get('id')] = ex
        # Resolve names for base PAVs (declaring PTAVs' own PAV)
        base_pav_meta = {}
        if ptav_base_pav_ids:
            base_pavs = models.execute_kw(
                ODOO_DB, uid, ODOO_API_KEY,
                'product.attribute.value', 'read',
                [list(set(ptav_base_pav_ids))],
                {'fields': ['name']}
            ) or []
            base_pav_meta = {v['id']: v.get('name') for v in base_pavs}

        # Collect all ids inside exclusion value_ids to resolve to names
        all_value_ids = set()
        for ex in ex_by_id.values():
            vids = ex.get('value_ids') or []
            for vid in vids:
                all_value_ids.add(vid if isinstance(vid, int) else (vid[0] if isinstance(vid, (list, tuple)) else None))
        all_value_ids = {vid for vid in all_value_ids if vid}

        # Build mapping prefering PTAV->PAV name resolution to avoid cross-model id collisions
        pav_name_by_id = {}
        ptav_to_pav = {}
        if all_value_ids:
            # First attempt: treat all ids as PTAV ids
            ptav_read = models.execute_kw(
                ODOO_DB, uid, ODOO_API_KEY,
                'product.template.attribute.value', 'read',
                [list(all_value_ids)],
                {'fields': ['product_attribute_value_id']}
            ) or []
            pav_ids_from_ptav = []
            for r in ptav_read:
                pav = r.get('product_attribute_value_id')
                pav_id = pav[0] if isinstance(pav, (list, tuple)) else pav
                if pav_id:
                    ptav_to_pav[r['id']] = pav_id
                    pav_ids_from_ptav.append(pav_id)
            # Read names for PAV ids gathered via PTAV
            if pav_ids_from_ptav:
                pavs_from_ptav = models.execute_kw(
                    ODOO_DB, uid, ODOO_API_KEY,
                    'product.attribute.value', 'read',
                    [list(set(pav_ids_from_ptav))],
                    {'fields': ['name']}
                ) or []
                for v in pavs_from_ptav:
                    pav_name_by_id[v['id']] = v.get('name')

            # Fallback: any ids not present as PTAV keys might actually be direct PAV ids
            unresolved_ids = [vid for vid in all_value_ids if vid not in ptav_to_pav]
            if unresolved_ids:
                pavs_direct = models.execute_kw(
                    ODOO_DB, uid, ODOO_API_KEY,
                    'product.attribute.value', 'read',
                    [unresolved_ids],
                    {'fields': ['name']}
                ) or []
                for v in pavs_direct:
                    pav_name_by_id[v['id']] = v.get('name')

        # Build grouped exclusions: value (base) -> excluded value names
        result_exclusions = []
        # Create helper: given id that may be PAV or PTAV, resolve name
        def resolve_value_name(unknown_id):
            # If it's a PTAV id, map to PAV and resolve name
            pav = ptav_to_pav.get(unknown_id)
            if pav:
                return pav_name_by_id.get(pav)
            # Else, treat as direct PAV id
            return pav_name_by_id.get(unknown_id)

        # For each PTAV that declares exclusions, map to its base PAV name
        for r in ptavs:
            ex_ids = r.get('exclude_for') or []
            if not ex_ids:
                continue
            pav = r.get('product_attribute_value_id')
            pav_id = pav[0] if isinstance(pav, (list, tuple)) else pav
            base_name = base_pav_meta.get(pav_id)
            if not base_name:
                continue
            excluded_names = []
            for ex_id in ex_ids:
                # find corresponding exclusion record
                ex_rec = ex_by_id.get(ex_id)
                if not ex_rec:
                    continue
                for vid in (ex_rec.get('value_ids') or []):
                    norm_vid = vid if isinstance(vid, int) else (vid[0] if isinstance(vid, (list, tuple)) else None)
                    name = resolve_value_name(norm_vid) if norm_vid else None
                    if name:
                        excluded_names.append(name)
            # unique and keep order
            seen = set()
            dedup = []
            for n in excluded_names:
                if n not in seen:
                    seen.add(n)
                    dedup.append(n)
            result_exclusions.append({'value': base_name, 'excluded_values': dedup})
        logger.info(f"Result exclusions: {result_exclusions}")
        return jsonify({'product_id': product_id, 'exclusions': result_exclusions})

    except Exception as e:
        error_msg = f"Error fetching variant exclusions for product {product_id}: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return jsonify({'error': error_msg, 'code': 'unknown_error'}), 500

@decilo_bp.route('/decilo-api/products/<int:product_id>/variant-image', methods=['POST'])
@token_required
def get_variant_image(current_user, product_id: int):
    """Return the variant-specific image (or fallback template image) for a selection."""
    try:
        uid = get_uid()
        models = get_odoo_models()
        payload = request.get_json(silent=True) or {}
        selected_variants = payload.get('selected_variants') or {}
        if selected_variants and not isinstance(selected_variants, dict):
            return jsonify({'error': 'selected_variants must be a JSON object'}), 400

        size = payload.get('size', 'full')
        cache_key = (product_id, size, json.dumps(sorted(selected_variants.items())))
        now = time.time()

        # Fast path: reuse fully cached payload for this selection/size
        cached_payload = VARIANT_IMAGE_CACHE.get(cache_key)
        if cached_payload and cached_payload.get('expires_at', 0) > now and cached_payload.get('payload'):
            return jsonify(cached_payload['payload'])

        # Resolve variant using cached template metadata to avoid repeated RPCs
        variant_product_id, ptav_ids, variant_error = resolve_variant_from_cache(models, uid, product_id, selected_variants)
        if variant_error:
            return jsonify({'error': variant_error}), 400

        size_field = odoo_client._image_field_for_size(size)
        image_b64 = None
        source = 'variant'

        # Check variant-level image cache
        variant_cache_key = (variant_product_id, size_field)
        variant_cached = VARIANT_IMAGE_CACHE.get(variant_cache_key)
        if variant_cached and variant_cached.get('expires_at', 0) > now:
            image_b64 = variant_cached.get('image')

        if variant_product_id and not image_b64:
            variant_image = models.execute_kw(
                ODOO_DB, uid, ODOO_API_KEY,
                'product.product', 'read',
                [[variant_product_id]],
                {'fields': [size_field]}
            )
            if variant_image and variant_image[0].get(size_field):
                image_b64 = variant_image[0].get(size_field)
                VARIANT_IMAGE_CACHE[variant_cache_key] = {
                    'image': image_b64,
                    'expires_at': now + VARIANT_IMAGE_CACHE_TTL,
                    'payload': None
                }

        if not image_b64:
            source = 'product'
            template_cache_key = ('template', product_id, size_field)
            template_cached = VARIANT_IMAGE_CACHE.get(template_cache_key)
            if template_cached and template_cached.get('expires_at', 0) > now:
                image_b64 = template_cached.get('image')
            else:
                template_images = odoo_client.get_product_images([product_id], size=size)
                if template_images and template_images[0].get('image'):
                    image_b64 = template_images[0].get('image')
                    VARIANT_IMAGE_CACHE[template_cache_key] = {
                        'image': image_b64,
                        'expires_at': now + VARIANT_IMAGE_CACHE_TTL,
                        'payload': None
                    }

        if not image_b64:
            return jsonify({'error': 'Image not found', 'variant_product_id': variant_product_id}), 404

        image_url = f"data:image/png;base64,{image_b64}"
        payload = {
            'product_id': product_id,
            'variant_product_id': variant_product_id,
            'image': image_url,
            'ptav_ids': ptav_ids,
            'source': source,
            'size': size
        }

        VARIANT_IMAGE_CACHE[cache_key] = {
            'payload': payload,
            'expires_at': now + VARIANT_IMAGE_CACHE_TTL,
            'image': image_b64
        }
        return jsonify(payload)
    except Exception as e:
        error_msg = f"Error fetching variant image for product {product_id}: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return jsonify({'error': error_msg, 'code': 'unknown_error'}), 500

@decilo_bp.route('/decilo-api/orders/<int:order_id>/ear-impressions/download', methods=['GET'])
@token_required
def download_order_ear_impression(current_user, order_id: int):
    """Download left or right ear impression by following sale.order -> x_studio_patient."""
    try:
        side = (request.args.get('side') or '').lower()
        if side not in ['left', 'right']:
            return jsonify({'error': 'side (left|right) is required'}), 400

        uid = get_uid()
        models = get_odoo_models()

        # Get patient from order
        order_fields = ['x_studio_patient']
        orders = models.execute_kw(
            ODOO_DB, uid, ODOO_API_KEY,
            'sale.order', 'read',
            [order_id],
            {'fields': order_fields}
        )
        if not orders or not orders[0].get('x_studio_patient'):
            return jsonify({'error': 'Patient not linked to order'}), 404
        patient_id = orders[0]['x_studio_patient'][0]

        # Read patient binary
        bin_field = f"x_studio_{side}_ear_impression"
        name_field = f"x_studio_{side}_ear_impression_filename"
        fields = ['name', bin_field]
        try:
            available = models.execute_kw(
                ODOO_DB, uid, ODOO_API_KEY,
                'res.partner', 'fields_get',
                [[name_field]]
            ) or {}
            if name_field in available:
                fields.append(name_field)
        except Exception:
            pass

        recs = models.execute_kw(
            ODOO_DB, uid, ODOO_API_KEY,
            'res.partner', 'read',
            [patient_id],
            {'fields': fields}
        )
        if not recs:
            return jsonify({'error': 'Patient not found'}), 404
        rec = recs[0]
        b64data = rec.get(bin_field)
        if not b64data:
            return jsonify({'error': 'File not found'}), 404

        file_bytes = base64.b64decode(b64data)
        filename = rec.get(name_field) or f"{side}_ear_impression.bin"
        headers = {
            'Content-Type': 'application/octet-stream',
            'Content-Disposition': f'attachment; filename="{filename}"'
        }
        return Response(file_bytes, headers=headers)
    except Exception as e:
        error_msg = f"Error downloading order ear impression: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return jsonify({'error': error_msg, 'code': 'unknown_error'}), 500
        
@decilo_bp.route('/decilo-api/orders', methods=['POST'])
@token_required
def create_order(current_user):
    """Create a sale order for the logged-in partner with product/variant, add chatter and attach docs."""
    logger.info("Received request for POST /decilo-api/orders")
    try:
        uid = get_uid()
        models = get_odoo_models()

        # Expect multipart form-data
        form = request.form
        files = request.files

        try:
            product_template_id = int(form.get('product_template_id')) if form.get('product_template_id') else None
        except ValueError:
            product_template_id = None

        if not product_template_id:
            return jsonify({'error': 'product_template_id is required'}), 400

        selected_variants_raw = form.get('selected_variants')
        selected_variants = {}
        if selected_variants_raw:
            try:
                selected_variants = json.loads(selected_variants_raw)
            except Exception:
                return jsonify({'error': 'selected_variants must be a JSON object'}), 400

        notes = form.get('notes') or ''
        patient_id = form.get('patientId')  # Optional existing patient ID
        patient_first_name = form.get('patientFirstName') or ''
        patient_last_name = form.get('patientLastName') or ''
        audiolog = form.get('audiolog') or ''
        auditive_center_name = form.get('auditiveCenterName') or ''

        # Handle patient information - either use existing patient or create/use manual entry
        patient_info = None
        if patient_id:
            # Fetch existing patient details
            try:
                patient_records = models.execute_kw(
                    ODOO_DB, uid, ODOO_API_KEY,
                    'res.partner', 'read',
                    [int(patient_id)],
                    {'fields': ['id', 'name', 'email', 'phone', 'x_studio_id_custom']}
                )
                if patient_records:
                    patient_info = patient_records[0]
                    # Parse the name field to extract first and last names
                    full_name = patient_info.get('name', '')
                    name_parts = full_name.rsplit(' ', 1) if full_name else ['', '']
                    patient_first_name = name_parts[0] if len(name_parts) > 1 else ''
                    patient_last_name = name_parts[1].lower() if len(name_parts) > 1 and name_parts[1] else ''
                else:
                    return jsonify({'error': 'Patient not found'}), 400
            except Exception as e:
                logger.error(f"Error fetching patient {patient_id}: {str(e)}")
                return jsonify({'error': 'Error fetching patient information'}), 400
        else:
            # No existing patient selected, check if we should create new patient or use manual entry
            if patient_first_name or patient_last_name:
                # Create a new patient contact in Odoo - only 'name' field in "Firstname LASTNAME" format
                try:
                    # Format name as "Firstname LASTNAME"
                    full_name = ""
                    if patient_first_name and patient_last_name:
                        full_name = f"{patient_first_name} {patient_last_name.upper()}"
                    elif patient_first_name:
                        full_name = patient_first_name
                    elif patient_last_name:
                        full_name = patient_last_name.upper()

                    patient_data = {
                        'type': 'contact',
                        'name': full_name,
                        'x_studio_referring_contact': current_user['id'],  # Link to logged-in user
                    }

                    # Create the patient contact
                    new_patient_id = models.execute_kw(
                        ODOO_DB, uid, ODOO_API_KEY,
                        'res.partner', 'create',
                        [patient_data]
                    )

                    # Fetch the created patient for patient_info
                    created_patient = models.execute_kw(
                        ODOO_DB, uid, ODOO_API_KEY,
                        'res.partner', 'read',
                        [new_patient_id],
                        {'fields': ['id', 'name', 'email', 'phone', 'x_studio_id_custom']}
                    )[0]

                    patient_info = created_patient

                except Exception as e:
                    logger.error(f"Error creating new patient: {str(e)}")
                    # Fall back to using manual entry if creation fails
                    patient_info = {
                        'name': f"{patient_first_name} {patient_last_name}".strip(),
                        'first_name': patient_first_name,
                        'last_name': patient_last_name
                    }
            else:
                patient_info = None

        # Resolve correct product.product (variant) for the template and selected variant values
        variant_product_id, ptav_ids, variant_error = resolve_variant_product(
            models, uid, product_template_id, selected_variants
        )
        if variant_error:
            return jsonify({'error': variant_error}), 400

        if not variant_product_id:
            logger.error(f"❌ Could not resolve product variant. Needed PTAVs: {ptav_ids}")
            return jsonify({'error': 'Could not resolve product variant for the selected options'}), 400

        # Create sale order
        order_vals = {
            'partner_id': current_user['id'],
            'order_line': [(0, 0, {
                'product_id': variant_product_id,
                'product_uom_qty': 1,
            })]
        }
        # If we have a patient contact in Odoo, link it to the order's Studio field
        if patient_info and patient_info.get('id'):
            order_vals['x_studio_patient'] = patient_info['id']
        # Store notes on the order level in x_studio_notes field
        if notes:
            order_vals['x_studio_notes'] = notes

        order_id = models.execute_kw(
            ODOO_DB, uid, ODOO_API_KEY,
            'sale.order', 'create', [order_vals]
        )

        # Ensure the patient contact is tagged with "B2Audio" after order creation
        try:
            if patient_info and patient_info.get('id'):
                # Find or create the tag in res.partner.category
                tag_name = 'B2Audio'
                tag_ids = models.execute_kw(
                    ODOO_DB, uid, ODOO_API_KEY,
                    'res.partner.category', 'search',
                    [[('name', '=', tag_name)]],
                    {'limit': 1}
                )
                if tag_ids:
                    tag_id = tag_ids[0]
                else:
                    tag_id = models.execute_kw(
                        ODOO_DB, uid, ODOO_API_KEY,
                        'res.partner.category', 'create',
                        [{'name': tag_name}]
                    )

                # Add the tag to the patient contact (do not remove existing tags)
                models.execute_kw(
                    ODOO_DB, uid, ODOO_API_KEY,
                    'res.partner', 'write',
                    [[patient_info['id']], {'category_id': [(4, tag_id)]}]
                )
        except Exception as e:
            logger.warning(f"Failed to tag patient with B2Audio: {str(e)}")

        # Automatically confirm the sale order
        models.execute_kw(
            ODOO_DB, uid, ODOO_API_KEY,
            'sale.order', 'action_confirm',
            [order_id]
        )

        # Post chatter message with additional info (formatted HTML)
        # Read variant display name for clarity
        variant_display = None
        try:
            pp = models.execute_kw(
                ODOO_DB, uid, ODOO_API_KEY,
                'product.product', 'read',
                [variant_product_id],
                {'fields': ['display_name']}
            )
            if pp and pp[0].get('display_name'):
                variant_display = pp[0]['display_name']
        except Exception:
            variant_display = None

        list_items = []
        if variant_display:
            list_items.append(f"<li><b>Product</b>: {variant_display}</li>")
        if patient_info:
            patient_name = patient_info.get('name', '')
            if patient_info.get('id'):
                patient_name += f" (ID: {patient_info['id']})"
            list_items.append(f"<li><b>Patient</b>: {patient_name}</li>")
        if audiolog:
            list_items.append(f"<li><b>Audiolog</b>: {audiolog}</li>")
        if auditive_center_name:
            list_items.append(f"<li><b>Auditive Center</b>: {auditive_center_name}</li>")
        if selected_variants:
            variants_str = ", ".join([f"{k}: {v}" for k, v in selected_variants.items()])
            list_items.append(f"<li><b>Selected Options</b>: {variants_str}</li>")
        if notes:
            list_items.append(f"<li><b>Notes</b>: {notes}</li>")

        if list_items:
            body = f"<p>Order created via portal with the following details:</p><ul>{''.join(list_items)}</ul>"
        else:
            body = "Order created via portal."

        # Post message on sale order
        models.execute_kw(
            ODOO_DB, uid, ODOO_API_KEY,
            'sale.order', 'message_post',
            [order_id],
            {
            'body': body,
            'body_is_html': True,                # keep HTML rendering
            'message_type': 'comment',
            'subtype_xmlid': 'mail.mt_note',     # 🔑 internal note
            }
        )

        # Post same message on patient contact if patient_info has ID
        if patient_info and patient_info.get('id'):
            models.execute_kw(
                ODOO_DB, uid, ODOO_API_KEY,
                'res.partner', 'message_post',
                [patient_info['id']],
                {
                'body': body,
                'body_is_html': True,
                'message_type': 'comment',
                'subtype_xmlid': 'mail.mt_note',
                }
            )

        # Attach uploaded documents to the order and prepare patient binary field updates
        attachment_ids = []
        impression_b64_by_side = {
            'right': None,
            'left': None
        }
        impression_filename_by_side = {
            'right': None,
            'left': None
        }
        # Determine patient custom ID (if available) for filename prefixing
        patient_custom_id = None
        if patient_info and patient_info.get('x_studio_id_custom'):
            try:
                patient_custom_id = str(patient_info.get('x_studio_id_custom'))
            except Exception:
                patient_custom_id = None

        for key in ['rightImpressionDoc', 'leftImpressionDoc']:
            file = files.get(key)
            if file and getattr(file, 'filename', None):
                file_bytes = file.read()
                if file_bytes:
                    datas_b64 = base64.b64encode(file_bytes).decode('ascii')
                    # Derive side and suffix
                    if key == 'rightImpressionDoc':
                        side = 'right'
                        suffix = '_R'
                    else:
                        side = 'left'
                        suffix = '_L'

                    # Compute final filename: [custom_id_]originalBase+suffix+ext
                    try:
                        base, ext = os.path.splitext(file.filename)
                        composed_base = f"{base}{suffix}"
                        final_name = f"{patient_custom_id}_{composed_base}{ext}" if patient_custom_id else f"{composed_base}{ext}"
                    except Exception:
                        # Fallback to original filename if something goes wrong
                        final_name = file.filename

                    # Keep a copy for contact binary fields and filenames
                    impression_b64_by_side[side] = datas_b64
                    impression_filename_by_side[side] = final_name
                    # Create attachment on sale order
                    att_id = models.execute_kw(
                        ODOO_DB, uid, ODOO_API_KEY,
                        'ir.attachment', 'create',
                        [{
                            'name': final_name,
                            'res_model': 'sale.order',
                            'res_id': order_id,
                            'type': 'binary',
                            'datas': datas_b64,
                            'mimetype': file.mimetype or 'application/octet-stream',
                        }]
                    )
                    attachment_ids.append(att_id)

        if attachment_ids:
            # Post a message linking the attachments (expects a plain list of IDs)
            models.execute_kw(
                ODOO_DB, uid, ODOO_API_KEY,
                'sale.order', 'message_post',
                [order_id],
                {'body': 'Attached impression documents.', 'attachment_ids': attachment_ids}
            )
            
        # Also update patient contact binary fields if available
        if patient_info and patient_info.get('id'):
            partner_vals = {}
            if impression_b64_by_side['left']:
                partner_vals['x_studio_left_ear_impression'] = impression_b64_by_side['left']
            if impression_b64_by_side['right']:
                partner_vals['x_studio_right_ear_impression'] = impression_b64_by_side['right']

            # Attempt to also set companion filename fields if they exist
            companion_fields = [
                'x_studio_left_ear_impression_filename',
                'x_studio_right_ear_impression_filename'
            ]
            existing = {}
            try:
                existing = models.execute_kw(
                    ODOO_DB, uid, ODOO_API_KEY,
                    'res.partner', 'fields_get',
                    [companion_fields]
                ) or {}
            except Exception:
                existing = {}

            if 'x_studio_left_ear_impression_filename' in existing and impression_filename_by_side['left']:
                partner_vals['x_studio_left_ear_impression_filename'] = impression_filename_by_side['left']
            if 'x_studio_right_ear_impression_filename' in existing and impression_filename_by_side['right']:
                partner_vals['x_studio_right_ear_impression_filename'] = impression_filename_by_side['right']

            if partner_vals:
                models.execute_kw(
                    ODOO_DB, uid, ODOO_API_KEY,
                    'res.partner', 'write',
                    [[patient_info['id']], partner_vals]
                )

            # Also post attachments message on patient contact if patient_info has ID
            if patient_info and patient_info.get('id'):
                models.execute_kw(
                    ODOO_DB, uid, ODOO_API_KEY,
                    'res.partner', 'message_post',
                    [patient_info['id']],
                    {'body': 'Attached impression documents.', 'attachment_ids': attachment_ids}
                )

        # Read order basic info for response
        order = models.execute_kw(
            ODOO_DB, uid, ODOO_API_KEY,
            'sale.order', 'read',
            [order_id],
            {'fields': ['id', 'name', 'date_order', 'amount_total', 'state']}
        )[0]

        return jsonify({'order': order}), 201

    except Exception as e:
        error_msg = f"Error creating order: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return jsonify({'error': error_msg, 'code': 'unknown_error'}), 500
