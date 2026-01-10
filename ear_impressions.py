"""
Ear Impressions Portal Backend
Provides API endpoints for bulk downloading ear impression files from Manufacturing Orders.
"""

from flask import Blueprint, jsonify, request, Response
import xmlrpc.client
import os
from dotenv import load_dotenv
import logging
import jwt
from functools import wraps
import base64
import io
import zipfile
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Create blueprint
ear_impressions_bp = Blueprint('ear_impressions', __name__)

# Odoo Configuration
ODOO_URL = os.getenv('DECILO_ODOO_URL')
ODOO_DB = os.getenv('DECILO_ODOO_DB')
ODOO_USERNAME = os.getenv('DECILO_ODOO_USERNAME')
ODOO_API_KEY = os.getenv('DECILO_ODOO_API_KEY')

# JWT Configuration
JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'your-secret-key')

# Designer matching table: maps portal user emails to Odoo x_studio_3d_designer values
# This can be extended or loaded from a config file/database
DESIGNER_MATCHING = {
    # Example: 'portal_user@example.com': ['Designer Name in Odoo', 'Alternative Name']
}


def get_odoo_common():
    """Get Odoo common endpoint"""
    try:
        common = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/common', allow_none=True)
        return common
    except Exception as e:
        logger.error(f"Failed to connect to Odoo common endpoint: {str(e)}")
        raise


def get_odoo_models():
    """Get Odoo models endpoint"""
    try:
        models = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/object', allow_none=True)
        return models
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


def get_designer_values_for_user(user_email: str) -> list:
    """
    Get the list of x_studio_3d_designer values that match the logged-in user.
    Uses the DESIGNER_MATCHING table to map portal users to designer names.
    """
    user_email_lower = user_email.lower() if user_email else ''
    
    # Check if user has a specific mapping
    if user_email_lower in DESIGNER_MATCHING:
        return DESIGNER_MATCHING[user_email_lower]
    
    # Default: return empty list (user can filter from all available designers)
    return []


@ear_impressions_bp.route('/ear-impressions-api/designers', methods=['GET'])
@token_required
def get_available_designers(current_user):
    """
    Get all unique values from x_studio_3d_designer field across MOs.
    This allows the frontend to populate the filter dropdown.
    """
    logger.info("Received request for /ear-impressions-api/designers")
    try:
        uid = get_uid()
        models = get_odoo_models()

        # Build domain for MOs with relevant operations (AND condition)
        # x_studio_operation must contain BOTH 'To Do' AND 'Design 3D'
        domain = [
            ('x_studio_operation', 'ilike', 'To Do'),
            ('x_studio_operation', 'ilike', 'Design 3D')
        ]

        # Fetch all MOs with the designer field
        mo_ids = models.execute_kw(
            ODOO_DB, uid, ODOO_API_KEY,
            'mrp.production', 'search',
            [domain],
            {'order': 'id desc'}
        )

        designers = set()
        if mo_ids:
            mo_records = models.execute_kw(
                ODOO_DB, uid, ODOO_API_KEY,
                'mrp.production', 'read',
                [mo_ids],
                {'fields': ['x_studio_3d_designer']}
            )
            for rec in mo_records:
                designer = rec.get('x_studio_3d_designer')
                if designer:
                    # Handle if it's a many2one tuple or a string
                    if isinstance(designer, (list, tuple)):
                        designers.add(designer[1] if len(designer) > 1 else str(designer[0]))
                    else:
                        designers.add(str(designer))

        # Get designers matched to current user
        user_designers = get_designer_values_for_user(current_user.get('email'))

        return jsonify({
            'designers': sorted(list(designers)),
            'user_matched_designers': user_designers
        })

    except Exception as e:
        error_msg = f"Error fetching designers: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return jsonify({'error': error_msg}), 500


@ear_impressions_bp.route('/ear-impressions-api/manufacturing-orders', methods=['GET'])
@token_required
def get_manufacturing_orders(current_user):
    """
    Get list of Manufacturing Orders matching the filters:
    - x_studio_operation contains BOTH 'To Do' AND 'Design 3D'
    - Optionally filtered by x_studio_3d_designer
    """
    logger.info("Received request for /ear-impressions-api/manufacturing-orders")
    try:
        designer_filter = request.args.get('designer')
        search_query = request.args.get('search')
        has_files_filter = request.args.get('has_files', '').lower()
        limit = request.args.get('limit', type=int, default=100)
        offset = request.args.get('offset', type=int, default=0)

        uid = get_uid()
        models = get_odoo_models()

        # Build domain: x_studio_operation must contain BOTH 'To Do' AND 'Design 3D'
        domain = [
            ('x_studio_operation', 'ilike', 'To Do'),
            ('x_studio_operation', 'ilike', 'Design 3D')
        ]

        # Add designer filter if specified
        if designer_filter:
            domain.append(('x_studio_3d_designer', 'ilike', designer_filter))

        # Add search filter on MO name
        if search_query:
            domain.append(('name', 'ilike', search_query))

        # Add filter for MOs with ear impression files
        if has_files_filter == 'true':
            # Must have at least one ear impression file (left OR right)
            domain.extend([
                '|',
                ('x_studio_left_ear_impression_file', '!=', False),
                ('x_studio_right_ear_impression_file', '!=', False)
            ])

        # Search for MOs
        mo_ids = models.execute_kw(
            ODOO_DB, uid, ODOO_API_KEY,
            'mrp.production', 'search',
            [domain],
            {'order': 'id desc', 'limit': limit, 'offset': offset}
        )

        total_count = models.execute_kw(
            ODOO_DB, uid, ODOO_API_KEY,
            'mrp.production', 'search_count',
            [domain]
        )

        if not mo_ids:
            return jsonify({'orders': [], 'total': 0, 'offset': offset, 'limit': limit})

        # Read MO fields including ear impression files
        mo_fields = [
            'name',
            'state',
            'x_studio_operation',
            'x_studio_3d_designer',
            'x_studio_left_ear_impression_file',
            'x_studio_right_ear_impression_file',
            'origin',
            'date_start',
            'product_id'
        ]

        # Check which fields exist before reading
        try:
            available_fields = models.execute_kw(
                ODOO_DB, uid, ODOO_API_KEY,
                'mrp.production', 'fields_get',
                [mo_fields]
            )
            # Filter to only existing fields
            mo_fields = [f for f in mo_fields if f in available_fields]
        except Exception:
            pass

        mo_records = models.execute_kw(
            ODOO_DB, uid, ODOO_API_KEY,
            'mrp.production', 'read',
            [mo_ids],
            {'fields': mo_fields}
        )

        # Format response
        orders = []
        for rec in mo_records:
            designer = rec.get('x_studio_3d_designer')
            designer_name = None
            if designer:
                if isinstance(designer, (list, tuple)):
                    designer_name = designer[1] if len(designer) > 1 else str(designer[0])
                else:
                    designer_name = str(designer)

            product = rec.get('product_id')
            product_name = None
            if product:
                if isinstance(product, (list, tuple)):
                    product_name = product[1] if len(product) > 1 else str(product[0])
                else:
                    product_name = str(product)

            # Check if ear impression files exist
            left_file = rec.get('x_studio_left_ear_impression_file')
            right_file = rec.get('x_studio_right_ear_impression_file')

            orders.append({
                'id': rec.get('id'),
                'name': rec.get('name'),
                'state': rec.get('state'),
                'operation': rec.get('x_studio_operation'),
                'designer': designer_name,
                'origin': rec.get('origin'),
                'date_start': rec.get('date_start'),
                'product': product_name,
                'has_left_ear': bool(left_file),
                'has_right_ear': bool(right_file),
            })

        return jsonify({
            'orders': orders,
            'total': total_count,
            'offset': offset,
            'limit': limit
        })

    except Exception as e:
        error_msg = f"Error fetching manufacturing orders: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return jsonify({'error': error_msg}), 500


@ear_impressions_bp.route('/ear-impressions-api/download', methods=['POST'])
@token_required
def bulk_download_ear_impressions(current_user):
    """
    Bulk download ear impression files from selected MOs.
    Expects a JSON body with: {"mo_ids": [1, 2, 3], "sides": ["left", "right"]}
    Returns a ZIP file containing all the ear impression files.
    """
    logger.info("Received request for /ear-impressions-api/download")
    try:
        data = request.get_json()
        mo_ids = data.get('mo_ids', [])
        sides = data.get('sides', ['left', 'right'])

        if not mo_ids:
            return jsonify({'error': 'No manufacturing orders selected'}), 400

        uid = get_uid()
        models = get_odoo_models()

        # Determine which file fields to read
        file_fields = ['name']
        if 'left' in sides:
            file_fields.append('x_studio_left_ear_impression_file')
        if 'right' in sides:
            file_fields.append('x_studio_right_ear_impression_file')

        # Also try to get filename fields if they exist
        filename_fields = []
        try:
            all_fields = models.execute_kw(
                ODOO_DB, uid, ODOO_API_KEY,
                'mrp.production', 'fields_get',
                [[]]
            )
            if 'x_studio_left_ear_impression_file_filename' in all_fields:
                filename_fields.append('x_studio_left_ear_impression_file_filename')
            if 'x_studio_right_ear_impression_file_filename' in all_fields:
                filename_fields.append('x_studio_right_ear_impression_file_filename')
        except Exception:
            pass

        fields_to_read = file_fields + filename_fields

        # Read MO records
        mo_records = models.execute_kw(
            ODOO_DB, uid, ODOO_API_KEY,
            'mrp.production', 'read',
            [mo_ids],
            {'fields': fields_to_read}
        )

        if not mo_records:
            return jsonify({'error': 'No manufacturing orders found'}), 404

        # Create ZIP file in memory
        zip_buffer = io.BytesIO()
        files_added = 0

        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for rec in mo_records:
                mo_name = rec.get('name', f"MO_{rec.get('id')}")
                # Sanitize MO name for folder
                safe_mo_name = "".join(c if c.isalnum() or c in ('-', '_') else '_' for c in mo_name)

                if 'left' in sides:
                    left_data = rec.get('x_studio_left_ear_impression_file')
                    if left_data:
                        try:
                            left_bytes = base64.b64decode(left_data)
                            left_filename = rec.get('x_studio_left_ear_impression_file_filename', 'left_ear.stl')
                            zip_file.writestr(f"{safe_mo_name}/{left_filename}", left_bytes)
                            files_added += 1
                        except Exception as e:
                            logger.warning(f"Could not decode left ear file for {mo_name}: {e}")

                if 'right' in sides:
                    right_data = rec.get('x_studio_right_ear_impression_file')
                    if right_data:
                        try:
                            right_bytes = base64.b64decode(right_data)
                            right_filename = rec.get('x_studio_right_ear_impression_file_filename', 'right_ear.stl')
                            zip_file.writestr(f"{safe_mo_name}/{right_filename}", right_bytes)
                            files_added += 1
                        except Exception as e:
                            logger.warning(f"Could not decode right ear file for {mo_name}: {e}")

        if files_added == 0:
            return jsonify({'error': 'No ear impression files found in selected orders'}), 404

        zip_buffer.seek(0)

        # Generate filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"ear_impressions_{timestamp}.zip"

        return Response(
            zip_buffer.getvalue(),
            mimetype='application/zip',
            headers={
                'Content-Disposition': f'attachment; filename="{filename}"',
                'Content-Type': 'application/zip'
            }
        )

    except Exception as e:
        error_msg = f"Error downloading ear impressions: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return jsonify({'error': error_msg}), 500


@ear_impressions_bp.route('/ear-impressions-api/download-single', methods=['GET'])
@token_required
def download_single_ear_impression(current_user):
    """
    Download a single ear impression file from a specific MO.
    Query params: mo_id, side (left/right)
    """
    logger.info("Received request for /ear-impressions-api/download-single")
    try:
        mo_id = request.args.get('mo_id', type=int)
        side = (request.args.get('side') or '').lower()

        if not mo_id:
            return jsonify({'error': 'mo_id is required'}), 400
        if side not in ['left', 'right']:
            return jsonify({'error': 'side must be "left" or "right"'}), 400

        uid = get_uid()
        models = get_odoo_models()

        file_field = f'x_studio_{side}_ear_impression_file'
        filename_field = f'x_studio_{side}_ear_impression_file_filename'

        fields = ['name', file_field]
        try:
            available = models.execute_kw(
                ODOO_DB, uid, ODOO_API_KEY,
                'mrp.production', 'fields_get',
                [[filename_field]]
            )
            if filename_field in available:
                fields.append(filename_field)
        except Exception:
            pass

        records = models.execute_kw(
            ODOO_DB, uid, ODOO_API_KEY,
            'mrp.production', 'read',
            [mo_id],
            {'fields': fields}
        )

        if not records:
            return jsonify({'error': 'Manufacturing order not found'}), 404

        rec = records[0]
        file_data = rec.get(file_field)

        if not file_data:
            return jsonify({'error': 'File not found'}), 404

        try:
            file_bytes = base64.b64decode(file_data)
        except Exception:
            return jsonify({'error': 'Invalid file data'}), 500

        mo_name = rec.get('name', f'MO_{mo_id}')
        filename = rec.get(filename_field) or f"{mo_name}_{side}_ear.stl"

        return Response(
            file_bytes,
            headers={
                'Content-Type': 'application/octet-stream',
                'Content-Disposition': f'attachment; filename="{filename}"'
            }
        )

    except Exception as e:
        error_msg = f"Error downloading ear impression: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return jsonify({'error': error_msg}), 500


# Server action ID for "Set Operation to 3D Printing"
SERVER_ACTION_3D_PRINTING = 1131


@ear_impressions_bp.route('/ear-impressions-api/mark-done', methods=['POST'])
@token_required
def mark_mo_done(current_user):
    """
    Mark one or more MOs as done by triggering the server action
    '[Custom] #2 Set Operation to 3D Printing' (ID: 1131)
    
    Expects JSON body: {"mo_ids": [1, 2, 3]}
    """
    logger.info("Received request for /ear-impressions-api/mark-done")
    try:
        data = request.get_json()
        mo_ids = data.get('mo_ids', [])

        if not mo_ids:
            return jsonify({'error': 'No manufacturing orders specified'}), 400

        # Ensure mo_ids is a list
        if isinstance(mo_ids, int):
            mo_ids = [mo_ids]

        uid = get_uid()
        models = get_odoo_models()

        # Verify the MOs exist
        existing_ids = models.execute_kw(
            ODOO_DB, uid, ODOO_API_KEY,
            'mrp.production', 'search',
            [[('id', 'in', mo_ids)]]
        )

        if not existing_ids:
            return jsonify({'error': 'No valid manufacturing orders found'}), 404

        # Execute the server action on the MOs
        # Server actions are triggered via ir.actions.server run() method
        try:
            # Set the context with active_ids to specify which records to act on
            context = {
                'active_model': 'mrp.production',
                'active_ids': existing_ids,
                'active_id': existing_ids[0] if existing_ids else False,
            }

            # Run the server action
            result = models.execute_kw(
                ODOO_DB, uid, ODOO_API_KEY,
                'ir.actions.server', 'run',
                [[SERVER_ACTION_3D_PRINTING]],
                {'context': context}
            )

            logger.info(f"Server action {SERVER_ACTION_3D_PRINTING} executed on MOs: {existing_ids}, result: {result}")

            return jsonify({
                'success': True,
                'message': f'Successfully marked {len(existing_ids)} order(s) as done',
                'mo_ids': existing_ids
            })

        except Exception as action_error:
            logger.error(f"Failed to execute server action: {str(action_error)}", exc_info=True)
            return jsonify({'error': f'Failed to execute action: {str(action_error)}'}), 500

    except Exception as e:
        error_msg = f"Error marking MO as done: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return jsonify({'error': error_msg}), 500


@ear_impressions_bp.route('/ear-impressions-api/mark-done/<int:mo_id>', methods=['POST'])
@token_required
def mark_single_mo_done(current_user, mo_id):
    """
    Mark a single MO as done by triggering the server action.
    Convenience endpoint for single MO operations.
    """
    logger.info(f"Received request for /ear-impressions-api/mark-done/{mo_id}")
    try:
        uid = get_uid()
        models = get_odoo_models()

        # Verify the MO exists
        existing = models.execute_kw(
            ODOO_DB, uid, ODOO_API_KEY,
            'mrp.production', 'search',
            [[('id', '=', mo_id)]]
        )

        if not existing:
            return jsonify({'error': 'Manufacturing order not found'}), 404

        # Execute the server action
        context = {
            'active_model': 'mrp.production',
            'active_ids': [mo_id],
            'active_id': mo_id,
        }

        result = models.execute_kw(
            ODOO_DB, uid, ODOO_API_KEY,
            'ir.actions.server', 'run',
            [[SERVER_ACTION_3D_PRINTING]],
            {'context': context}
        )

        logger.info(f"Server action {SERVER_ACTION_3D_PRINTING} executed on MO {mo_id}, result: {result}")

        return jsonify({
            'success': True,
            'message': 'Successfully marked order as done',
            'mo_id': mo_id
        })

    except Exception as e:
        error_msg = f"Error marking MO as done: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return jsonify({'error': error_msg}), 500

