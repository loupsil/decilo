<template>
  <div class="product-catalog">
    <div class="catalog-header">
      <h1>decilo Products</h1>
      <p class="subtitle">Explore our collection of professional decilo products </p>
    </div>

    <div class="catalog-content">
      <!-- Left Sidebar for Categories -->
      <div class="categories-sidebar">
        <!-- Search Bar at the top -->
        <div class="sidebar-search">
          <div class="search-bar">
            <svg class="search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="11" cy="11" r="8"></circle>
              <path d="m21 21-4.35-4.35"></path>
            </svg>
            <input
              type="text"
              v-model="searchQuery"
              placeholder="Search products..."
              @input="filterProducts"
            >
          </div>
        </div>

        <div class="categories-section">
          <div class="categories-header">
            <h3>Categories</h3>
          </div>
          <div class="categories-list">
            <label class="category-checkbox-item">
              <input
                type="checkbox"
                :checked="selectedCategories.length === 0"
                @change="toggleAllCategories"
              >
              <span class="checkmark"></span>
              All Categories
            </label>
            <label
              v-for="category in categories"
              :key="category.id"
              class="category-checkbox-item"
            >
              <input
                type="checkbox"
                :checked="selectedCategories.includes(category.name)"
                @change="toggleCategory(category.name)"
              >
              <span class="checkmark"></span>
              {{ category.name }}
            </label>
          </div>
        </div>
      </div>

      <!-- Main Content Area -->
      <div class="main-content">
        <div class="products-grid" ref="productsGrid">
      <div v-if="isLoading" class="loading-overlay">
        <div class="loading-spinner"></div>
      </div>
      
      <div v-else-if="filteredProducts.length === 0" class="no-products">
        <p>No products found</p>
      </div>

      <template v-else>
        <div v-for="product in paginatedProducts" :key="product.id" class="product-card">
          <div class="product-image" @click="showProductDetails(product)">
            <img :src="product.image_url" :alt="product.name">
            <div class="image-overlay">
              <span>Order</span>
            </div>
          </div>
            <div class="product-details">
              <h3>{{ product.name }}</h3>
              <div class="product-category">
                <span class="category-badge">{{ product.category }}</span>
              </div>
              <p class="product-description">{{ product.description }}</p>
              <div class="product-actions">
                <button class="details-btn" @click="showProductDetails(product)">Order</button>
              </div>
            </div>
        </div>
      </template>
    </div>
    </div>
    </div>

    <!-- Pagination -->
    <div v-if="filteredProducts.length > itemsPerPage" class="pagination">
      <button
        :disabled="currentPage === 1"
        @click="changePage(currentPage - 1)"
        class="page-btn"
      >
        Previous
      </button>

      <div class="page-numbers">
        <button
          v-for="page in Math.ceil(filteredProducts.length / itemsPerPage)"
          :key="page"
          :class="['page-number', { active: currentPage === page }]"
          @click="changePage(page)"
        >
          {{ page }}
        </button>
      </div>
      
      <button
        :disabled="currentPage >= Math.ceil(filteredProducts.length / itemsPerPage)"
        @click="changePage(currentPage + 1)"
        class="page-btn"
      >
        Next
      </button>
    </div>

    <!-- Checkout Fullscreen -->
    <DeciloCheckout
      v-if="selectedProduct"
      :selectedProduct="selectedProduct"
      :selectedVariants="selectedVariants"
      @close="closeModal"
      @variant-selected="handleVariantSelection"
      @go-to-orders="viewOrders"
      @show-error="$emit('show-error', $event)"
      @token-expired="$emit('token-expired')"
    />
  </div>
</template>

<script>
import DeciloCheckout from './decilo_checkout.vue'

// Simple in-memory cache for product list responses (persists for the session)
const productCache = new Map()

// Click outside directive
const clickOutside = {
  bind(el, binding, vnode) {
    el.clickOutsideEvent = function(event) {
      if (!(el === event.target || el.contains(event.target))) {
        vnode.context[binding.expression]();
      }
    };
    document.body.addEventListener('click', el.clickOutsideEvent);
  },
  unbind(el) {
    document.body.removeEventListener('click', el.clickOutsideEvent);
  }
};

export default {
  name: 'DeciloProductCatalog',
  components: {
    DeciloCheckout
  },
  directives: {
    'click-outside': clickOutside
  },
  data() {
    return {
      products: [],
      categories: [],
      searchQuery: '',
      selectedProduct: null,
      isLoading: false,
      currentPage: 1,
      itemsPerPage: 100,
      totalProducts: 0,
      searchTimeout: null,
      selectedVariants: {},
      selectedCategories: [],
    }
  },
  computed: {
    filteredProducts() {
      let filtered = this.products

      // Filter products that are published for B2Audio
      filtered = filtered.filter(product => product.x_studio_is_published_b2audio === true)

      // Apply category filter
      if (this.selectedCategories.length > 0) {
        filtered = filtered.filter(product => this.selectedCategories.includes(product.category))
      }

      // Apply search filter
      if (this.searchQuery) {
        const query = this.searchQuery.toLowerCase()
        filtered = filtered.filter(product =>
          product.name.toLowerCase().includes(query) ||
          product.description.toLowerCase().includes(query)
        )
      }

      return filtered
    },
    paginatedProducts() {
      const start = (this.currentPage - 1) * this.itemsPerPage
      const end = start + this.itemsPerPage
      return this.filteredProducts.slice(start, end)
    }
  },
  created() {
    this.fetchProducts()
  },
  methods: {
    getCacheKey() {
      // Build a stable cache key from current query params
      return JSON.stringify({
        searchQuery: this.searchQuery || '',
        currentPage: this.currentPage || 1,
        itemsPerPage: this.itemsPerPage || 20,
        selectedCategories: this.selectedCategories || []
      })
    },
    async fetchProducts() {
      console.log('🔍 Fetching products with params:', {
        searchQuery: this.searchQuery,
        currentPage: this.currentPage,
        itemsPerPage: this.itemsPerPage,
        selectedCategory: this.selectedCategory
      })
      
      const cacheKey = this.getCacheKey()
      console.log('🔑 Cache key:', cacheKey)
      console.log('💾 Cache size:', productCache.size)
      
      if (productCache.has(cacheKey)) {
        console.log('✅ ✅ ✅ USING CACHED PRODUCTS for key:', cacheKey)
        const cached = productCache.get(cacheKey)
        this.products = cached.products
        this.totalProducts = cached.totalProducts
        this.categories = cached.categories || []
        this.selectedCategories = cached.selectedCategories || []
        console.log('📊 Cached data loaded:', {
          productsCount: this.products.length,
          categoriesCount: this.categories.length,
          categories: this.categories.map(c => c.name)
        })
        this.isLoading = false
        return
      }

      this.isLoading = true
      try {
        // Get auth token from localStorage
        const token = localStorage.getItem('decilo_token')
        if (!token) {
          console.warn('❌ No auth token found - Please log in first')
          throw new Error('Authentication required - Please log in first')
        }

        // Check if token is expired before making the request
        if (this.isTokenExpired(token)) {
          this.handleTokenExpired()
          return
        }

        console.log('🔑 Found auth token')

        // Prepare query parameters
        const params = new URLSearchParams()
        if (this.searchQuery) {
          params.append('search', this.searchQuery)
        }
        if (this.currentPage) {
          params.append('offset', (this.currentPage - 1) * this.itemsPerPage)
        }
        params.append('limit', this.itemsPerPage)
        
        const url = `/decilo-api/products?${params.toString()}`
        console.log('📡 Making API request to:', url)
        
        // Make API request
        const response = await fetch(url, {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        })

        if (!response.ok) {
          if (response.status === 401) {
            // Token expired or invalid, handle it
            this.handleTokenExpired()
            return
          }
          const error = await response.json()
          throw new Error(error.error || 'Failed to fetch products')
        }

        const data = await response.json()
        console.log('📦 Received raw API response:', {
          totalProducts: data.total,
          numberOfProducts: data.products.length,
          categoriesCount: data.categories ? data.categories.length : 0,
          apiCategories: data.categories ? data.categories.map(c => ({ id: c.id, name: c.name, complete_name: c.complete_name })) : []
        })

        // Transform the Odoo data to match our component's structure
        this.products = data.products.map(product => {
          // Extract short name from full category path (e.g., "Goods / Ear Tips" -> "Ear Tips")
          const fullCategoryName = product.categ_id ? product.categ_id[1] : 'Uncategorized'
          const shortCategoryName = fullCategoryName.includes(' / ') ?
            fullCategoryName.split(' / ').pop() : fullCategoryName

          const transformedProduct = {
            id: product.id,
            name: product.name,
            description: this.stripHtml(product.description_ecommerce) || 'No description available',
            full_description: this.stripHtml(product.description_ecommerce) || 'No description available',
            price: product.list_price || 0,
            image_url: product.image_1920 ? `data:image/png;base64,${product.image_1920}` : '/static/images/product-placeholder.jpg',
            specifications: this.extractSpecifications(product),
            variants: product.variants || [],
            category: shortCategoryName,
            categoryId: product.categ_id ? product.categ_id[0] : null,  // [0] contains the category ID
            x_studio_is_published_b2audio: product.x_studio_is_published_b2audio || false
          }
          console.log(`✨ Transformed product ${product.id}: name='${transformedProduct.name}', category='${transformedProduct.category}'`)
          return transformedProduct
        })

        this.totalProducts = data.total

        // Use categories from API response instead of extracting from products
        this.categories = (data.categories || []).map(category => {
          // Extract short name from full category path (e.g., "Goods / Ear Tips" -> "Ear Tips")
          // This must match the format used for product.category to enable filtering
          const fullCategoryName = category.complete_name || category.name || 'Uncategorized'
          const shortCategoryName = fullCategoryName.includes(' / ') ?
            fullCategoryName.split(' / ').pop() : fullCategoryName
          
          return {
            id: category.id,
            name: shortCategoryName, // Use short name to match product.category format
            completeName: category.complete_name,
            parentId: category.parent_id ? category.parent_id[0] : null
          }
        })

        console.log('✅ Products loaded successfully:', {
          displayedProducts: this.products.length,
          totalProducts: this.totalProducts,
          categories: this.categories.map(c => c.name)
        })

        // Store in cache
        productCache.set(cacheKey, {
          products: this.products,
          totalProducts: this.totalProducts,
          categories: this.categories,
          selectedCategories: this.selectedCategories
        })
        console.log('💾 Stored in cache. Cache now has', productCache.size, 'entries')
      } catch (error) {
        console.error('❌ Error fetching products:', {
          error: error.message,
          stack: error.stack
        })
        this.$emit('show-error', {
          message: error.message || 'Failed to load products',
          type: 'error'
        })
      } finally {
        this.isLoading = false
        console.log('🏁 Product fetch completed, loading:', this.isLoading)
      }
    },

    // Removed mapOdooCategory as we're only showing ear tips

    extractSpecifications(product) {
      // Extract specifications from Odoo product data
      const specs = []

      if (product.default_code) {
        specs.push(`Product Code: ${product.default_code}`)
      }

      // Add more specifications based on available Odoo fields

      return specs
    },

    stripHtml(htmlString) {
      const container = document.createElement('div')
      container.innerHTML = htmlString || ''
      return (container.textContent || container.innerText || '').trim()
    },
    filterProducts() {
      console.log('🔎 Search query changed:', this.searchQuery)
      
      // Clear any existing timeout
      if (this.searchTimeout) {
        console.log('⏱️ Clearing previous search timeout')
        clearTimeout(this.searchTimeout)
      }
      
      // Set new timeout
      console.log('⏳ Setting new search timeout (300ms)')
      this.searchTimeout = setTimeout(() => {
        console.log('⌛ Search timeout triggered, executing search')
        this.currentPage = 1 // Reset to first page when filtering
        this.fetchProducts()
      }, 300) // 300ms delay
    },

    async changePage(page) {
      console.log('📄 Changing page to:', page)
      this.currentPage = page
      await this.fetchProducts()
      console.log('📜 Scrolling to top of product grid')
      this.$refs.productsGrid?.scrollIntoView({ behavior: 'smooth' })
    },

    toggleCategory(category) {
      console.log('📑 Category toggled:', category)
      const index = this.selectedCategories.indexOf(category)
      if (index > -1) {
        // Remove category if already selected
        this.selectedCategories.splice(index, 1)
      } else {
        // Add category if not selected
        this.selectedCategories.push(category)
      }
      this.currentPage = 1 // Reset to first page when changing category selection
    },
    toggleAllCategories() {
      console.log('📑 All categories toggled')
      if (this.selectedCategories.length === 0) {
        // If none are selected, select all categories
        this.selectedCategories = this.categories.map(cat => cat.name)
      } else {
        // If some or all are selected, deselect all
        this.selectedCategories = []
      }
      this.currentPage = 1 // Reset to first page when changing category selection
    },

    showProductDetails(product) {
      this.selectedProduct = product
      // Reset selected variants when showing a new product
      this.selectedVariants = {}

      // Pre-select first value of each variant if available, except Ear Impression Type
      if (product.variants) {
        product.variants.forEach(variant => {
          if (variant.values && variant.values.length > 0 &&
              variant.attribute !== 'Ear Impression Type' &&
              !variant.attribute.toLowerCase().includes('ear impression')) {
            this.selectedVariants[variant.attribute] = variant.values[0]
          }
        })
      }
    },
    
    closeModal() {
      this.selectedProduct = null;
      this.selectedVariants = {};
    },
    
    
    isSelectedVariant(attribute, value) {
      return this.selectedVariants[attribute] === value
    },
    handleVariantSelection({ attribute, value }) {
      if (value === null) {
        delete this.selectedVariants[attribute];
      } else {
        this.selectedVariants[attribute] = value;
      }
    },

    viewOrders() {
      this.$emit('go-to-orders');
      this.closeModal();
    },

    closeModal() {
      this.selectedProduct = null;
      this.selectedVariants = {};
    },


    isTokenExpired(token) {
      try {
        // Decode JWT token (simple decode, not verification)
        const base64Payload = token.split('.')[1];
        const payload = JSON.parse(atob(base64Payload));

        // Check if token is expired
        const currentTime = Date.now() / 1000;
        return payload.exp < currentTime;
      } catch (error) {
        // If we can't decode the token, consider it expired
        return true;
      }
    },
    handleTokenExpired() {
      // Clear stored authentication data
      localStorage.removeItem('decilo_token');
      localStorage.removeItem('decilo_user');

      // Emit event to parent component to handle logout
      this.$emit('token-expired');
    }
  }
}
</script>

<style scoped>
.product-catalog {
  min-height: 100vh;
  padding: 24px;
  position: relative;
}

.catalog-content {
  display: flex;
  gap: 24px;
  max-width: 1400px;
  margin: 0 auto;
  height: calc(100vh - 120px); /* Full height minus header */
}

/* Categories Sidebar */
.categories-sidebar {
  width: 280px;
  flex-shrink: 0;
  position: relative;
  z-index: 1;
  height: 100%;
  background: var(--secondary-color);
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  border: 1px solid #ffffff;
  display: flex;
  flex-direction: column;
}

/* Sidebar Search Section */
.sidebar-search {
  margin-bottom: 24px;
}

.sidebar-search .search-bar {
  position: relative;
}

.sidebar-search .search-bar input {
  padding: 14px 16px 14px 44px;
  background: rgba(51, 65, 85, 0.8);
  border: 2px solid #475569;
  border-radius: 12px;
  color: #ffffff;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.sidebar-search .search-bar input:focus {
  outline: none;
  border-color: var(--primary-color);
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.15);
  background: rgba(51, 65, 85, 1);
}

.sidebar-search .search-bar input::placeholder {
  color: #94a3b8;
  font-weight: 400;
}

.sidebar-search .search-icon {
  position: absolute;
  left: 14px;
  top: 50%;
  transform: translateY(-50%);
  width: 20px;
  height: 20px;
  color: #64748b;
  z-index: 2;
  pointer-events: none;
}

/* Categories Section */
.categories-section {
  flex: 1;
}

.categories-header {
  margin-bottom: 16px;
}

.categories-header h3 {
  font-size: 18px;
  font-weight: 600;
  color: #ffffff;
  margin: 0;
  padding-bottom: 8px;
  border-bottom: 2px solid #ffffff;
}

.categories-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: calc(100vh - 280px); /* Account for header, search, and padding */
  overflow-y: auto;
  padding-right: 4px; /* Space for scrollbar */
}

/* Custom scrollbar for categories list */
.categories-list::-webkit-scrollbar {
  width: 6px;
}

.categories-list::-webkit-scrollbar-track {
  background: rgba(51, 65, 85, 0.3);
  border-radius: 3px;
}

.categories-list::-webkit-scrollbar-thumb {
  background: var(--primary-color);
  border-radius: 3px;
}

.categories-list::-webkit-scrollbar-thumb:hover {
  background: #4f83cc;
}

.category-checkbox-item {
  display: flex;
  width: 100%;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  margin-bottom: 8px;
}

.category-checkbox-item:hover {
  background: #334155;
  border-color: #64748b;
  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.1);
}

.category-checkbox-item input[type="checkbox"] {
  display: none;
}

.category-checkbox-item .checkmark {
  position: relative;
  width: 18px;
  height: 18px;
  border: 2px solid #475569;
  border-radius: 4px;
  margin-right: 12px;
  background: rgba(51, 65, 85, 0.8);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  flex-shrink: 0;
}

.category-checkbox-item input[type="checkbox"]:checked + .checkmark {
  background: #ffffff;
  border-color: #ffffff;
}

.category-checkbox-item input[type="checkbox"]:checked + .checkmark::after {
  content: '';
  position: absolute;
  left: 5px;
  top: 2px;
  width: 6px;
  height: 10px;
  border: solid #000000;
  border-width: 0 2px 2px 0;
  transform: rotate(45deg);
}

.category-checkbox-item:hover .checkmark {
  border-color: #64748b;
  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.1);
}

/* Main Content Area */
.main-content {
  flex: 1;
  min-width: 0; /* Allow content to shrink */
  height: 100%;
  display: flex;
  flex-direction: column;
}

.product-catalog::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  pointer-events: none;
  z-index: 0;
}

.catalog-header {
  text-align: start;
  margin-bottom: 36px;
  position: relative;
  z-index: 1;
}

.catalog-header h1 {
  font-size: 28px;
  font-weight: 700;
  color: #ffffff;
  margin: 0 0 6px 0;
  letter-spacing: -0.025em;
}

.subtitle {
  color: #94a3b8;
  font-size: 14px;
  margin: 0;
  font-weight: 400;
  letter-spacing: 0.025em;
}




.products-grid {
  position: relative;
  z-index: 1;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 20px;
  min-height: 320px; /* Ensure there's always space for the spinner */
  padding-bottom: 20px;
}

.product-card {
  background: var(--secondary-color);
  border: 1px solid #334155;
  border-radius: 16px;
  position: relative;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  display: flex;
  flex-direction: column;
}


.product-card:hover {
  transform: translateY(-8px);
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.4);
  border-color: #475569;
}

.product-image {
  position: relative;
  width: 100%;
  padding-bottom: 100%; /* Creates a square aspect ratio */
  overflow: hidden;
  border-radius: 16px;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.product-image:hover {
  transform: scale(1.05);
}

.product-image img {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  object-fit: contain;
  background: rgba(30, 41, 59, 0.8);
  box-sizing: border-box;
  border-radius: 16px;
  padding: 20px;
  transition: all 0.3s ease;
}

.image-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  border-radius: 16px;
}

.image-overlay span {
  color: #ffffff;
  font-size: 16px;
  font-weight: 600;
  padding: 12px 24px;
  border: 2px solid #ffffff;
  border-radius: 8px;
  background: rgba(0, 0, 0, 0.3);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.product-image:hover .image-overlay {
  opacity: 1;
}

.product-details {
  padding: 20px;
  display: flex;
  flex-direction: column;
  flex: 1;
}

.product-details h3 {
  margin: 0;
  margin-bottom: 10px;
  color: #ffffff;
  font-size: 18px;
  font-weight: 600;
  line-height: 1.3;
}

.product-category {
  margin-bottom: 12px;
}

.category-badge {
  display: inline-block;
  background: rgba(59, 130, 246, 0.1);
  color: #3b82f6;
  padding: 4px 8px;
  border-radius: 6px;
  font-size: 11px;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  border: 1px solid rgba(59, 130, 246, 0.2);
}

.product-description {
  color: #94a3b8;
  font-size: 13px;
  margin-bottom: 16px;
  line-height: 1.5;
}


.product-actions {
  display: flex;
  gap: 12px;
  margin-top: auto;
  flex-shrink: 0;
}

.details-btn {
  flex: 1;
  padding: 12px 20px;
  border-radius: 12px;
  border: 1px solid #ffffff;
  font-weight: 600;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  background: #000000;
  color: #ffffff;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  position: relative;
  overflow: hidden;
}

.details-btn::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  transition: left 0.5s ease;
}

.details-btn:hover::before {
  left: 100%;
}

.details-btn:hover {
  background: #ffffff;
  color: #000000;
  border-color: #ffffff;
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(255, 255, 255, 0.3);
}


.spinner {
  width: 20px;
  height: 20px;
  border: 2px solid #000000;
  border-top: 2px solid transparent;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}


/* Loading styles */
.loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 300px;
  width: 100%;
  backdrop-filter: blur(8px);
  z-index: 10;
  border-radius: 20px;
}


.no-products {
  text-align: center;
  padding: 80px 32px;
  position: relative;
  z-index: 1;
}

.no-products::before {
  content: '';
  position: absolute;
  top: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 80px;
  height: 80px;
  background: var(--secondary-color);
  border-radius: 50%;
  opacity: 0.6;
  margin-bottom: 32px;
}

.no-products p {
  font-size: 18px;
  color: #94a3b8;
  margin: 0;
  font-weight: 500;
}



@media (max-width: 1024px) {
  .product-catalog {
    padding: 20px;
  }

  .catalog-header h1 {
    font-size: 26px;
  }

  .catalog-content {
    gap: 20px;
  }

  .categories-sidebar {
    width: 260px;
    border: 0.5px solid #ffffff;
  }

  .products-grid {
    grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
    gap: 16px;
  }

}

@media (max-width: 768px) {
  .product-catalog {
    padding: 16px;
  }

  .catalog-content {
    flex-direction: column;
    gap: 16px;
    height: auto;
  }

  .categories-sidebar {
    display: none;
  }

  .main-content {
    order: 1;
  }

  .sidebar-search {
    margin-bottom: 20px;
  }

  .catalog-header {
    margin-bottom: 28px;
  }

  .catalog-header h1 {
    font-size: 24px;
  }

  .subtitle {
    font-size: 13px;
  }

  .search-bar input {
    max-width: none;
    padding: 12px 36px 12px 36px;
  }

  .products-grid {
    grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
    gap: 14px;
  }

  .product-card {
    border-radius: 14px;
    display: flex;
    flex-direction: column;
  }

  .product-details {
    padding: 16px;
    display: flex;
    flex-direction: column;
    flex: 1;
  }

  .product-details h3 {
    font-size: 16px;
  }
}

@media (max-width: 480px) {
  .product-catalog {
    padding: 12px;
  }

  .catalog-header h1 {
    font-size: 22px;
  }

  .products-grid {
    grid-template-columns: 1fr;
    gap: 12px;
  }

  .product-card {
    margin-bottom: 0;
    display: flex;
    flex-direction: column;
  }

  .product-details {
    padding: 14px;
    display: flex;
    flex-direction: column;
    flex: 1;
  }

  .product-details h3 {
    font-size: 15px;
  }

}


</style>
