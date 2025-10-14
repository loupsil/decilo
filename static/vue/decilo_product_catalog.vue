<template>
  <div class="product-catalog">
    <div class="catalog-header">
      <h1>Custom Ear Tips</h1>
      <p class="subtitle">Browse our collection of professional ear tips</p>
    </div>

    <div class="catalog-filters">
      <div class="search-bar">
        <svg class="search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="11" cy="11" r="8"></circle>
          <path d="m21 21-4.35-4.35"></path>
        </svg>
        <input
          type="text"
          v-model="searchQuery"
          placeholder="Search ear tips..."
          @input="filterProducts"
        >
      </div>
    </div>

    <div class="products-grid" ref="productsGrid">
      <div v-if="isLoading" class="loading-overlay">
        <div class="loading-spinner"></div>
      </div>
      
      <div v-else-if="products.length === 0" class="no-products">
        <p>No products found</p>
      </div>
      
      <template v-else>
        <div v-for="product in products" :key="product.id" class="product-card">
          <div class="product-image" @click="showProductDetails(product)">
            <img :src="product.image_url" :alt="product.name">
            <div class="image-overlay">
              <span>View Details</span>
            </div>
          </div>
            <div class="product-details">
              <h3>{{ product.name }}</h3>
              <p class="product-description">{{ product.description }}</p>
              <div class="product-actions">
                <button class="details-btn" @click="showProductDetails(product)">View Details</button>
              </div>
            </div>
        </div>
      </template>
    </div>

    <!-- Pagination -->
    <div v-if="totalProducts > itemsPerPage" class="pagination">
      <button 
        :disabled="currentPage === 1"
        @click="changePage(currentPage - 1)"
        class="page-btn"
      >
        Previous
      </button>
      
      <div class="page-numbers">
        <button 
          v-for="page in Math.ceil(totalProducts / itemsPerPage)"
          :key="page"
          :class="['page-number', { active: currentPage === page }]"
          @click="changePage(page)"
        >
          {{ page }}
        </button>
      </div>
      
      <button 
        :disabled="currentPage >= Math.ceil(totalProducts / itemsPerPage)"
        @click="changePage(currentPage + 1)"
        class="page-btn"
      >
        Next
      </button>
    </div>

    <!-- Checkout Modal -->
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
      searchQuery: '',
      selectedProduct: null,
      isLoading: false,
      currentPage: 1,
      itemsPerPage: 12,
      totalProducts: 0,
      searchTimeout: null,
      selectedVariants: {},
    }
  },
  computed: {
    filteredProducts() {
      let filtered = this.products

      // Apply category filter
      if (this.selectedCategory !== 'All') {
        filtered = filtered.filter(product => product.category === this.selectedCategory)
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
        itemsPerPage: this.itemsPerPage || 12,
        selectedCategory: this.selectedCategory || 'All'
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
      if (productCache.has(cacheKey)) {
        console.log('🧠 Using cached products for key:', cacheKey)
        const cached = productCache.get(cacheKey)
        this.products = cached.products
        this.totalProducts = cached.totalProducts
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
        console.log('📦 Received products data:', {
          totalProducts: data.total,
          numberOfProducts: data.products.length,
          firstProduct: data.products[0] // Show sample of first product
        })
        
        // Transform the Odoo data to match our component's structure
        this.products = data.products.map(product => {
          const transformedProduct = {
            id: product.id,
            name: product.name,
            description: this.stripHtml(product.description_ecommerce) || 'No description available',
            full_description: this.stripHtml(product.description_ecommerce) || 'No description available',
            price: product.list_price || 0,
            image_url: product.image_1920 ? `data:image/png;base64,${product.image_1920}` : '/static/images/product-placeholder.jpg',
            specifications: this.extractSpecifications(product),
            variants: product.variants || []
          }
          console.log(`✨ Transformed product ${product.id}:`, transformedProduct)
          return transformedProduct
        })

        this.totalProducts = data.total
        console.log('✅ Products loaded successfully:', {
          displayedProducts: this.products.length,
          totalProducts: this.totalProducts
        })

        // Store in cache
        productCache.set(cacheKey, {
          products: this.products,
          totalProducts: this.totalProducts
        })
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
    selectCategory(category) {
      this.selectedCategory = category
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

    selectCategory(category) {
      console.log('📑 Category selected:', category)
      this.selectedCategory = category
      this.currentPage = 1 // Reset to first page when changing category
      this.fetchProducts()
    },
    showProductDetails(product) {
      this.selectedProduct = product
      // Reset selected variants when showing a new product
      this.selectedVariants = {}

      // Pre-select first value of each variant if available
      if (product.variants) {
        product.variants.forEach(variant => {
          if (variant.values && variant.values.length > 0) {
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
      this.selectedVariants[attribute] = value;
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
  overflow: hidden;
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
  text-align: center;
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

.catalog-filters {
  margin-bottom: 24px;
  position: relative;
  z-index: 1;
}

.search-bar {
  display: flex;
  justify-content: center;
  margin-bottom: 16px;
}

.search-bar input {
  width: 100%;
  max-width: 400px;
  padding: 12px 40px 12px 40px;
  background: var(--secondary-color);
  border: 2px solid #334155;
  border-radius: 12px;
  color: #ffffff;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  backdrop-filter: blur(12px);
  position: relative;
  z-index: 1;
}

.search-bar input:focus {
  outline: none;
  border-color: var(--primary-color);
  box-shadow:
    0 0 0 4px rgba(59, 130, 246, 0.15),
    0 8px 32px rgba(59, 130, 246, 0.12);
  transform: translateY(-2px);
}

.search-bar input::placeholder {
  color: #64748b;
  font-weight: 400;
}

.search-icon {
  position: absolute;
  left: 16px;
  top: 50%;
  transform: translateY(-50%);
  width: 20px;
  height: 20px;
  color: #64748b;
  z-index: 2;
  pointer-events: none;
}



.products-grid {
  position: relative;
  z-index: 1;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 20px;
  min-height: 320px; /* Ensure there's always space for the spinner */
}

.product-card {
  background: var(--secondary-color);
  border: 1px solid #334155;
  border-radius: 16px;
  overflow: hidden;
  position: relative;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  min-height: 320px;
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
  border: none;
  font-weight: 600;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  background: var(--primary-color);
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
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(59, 130, 246, 0.4);
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

  .products-grid {
    grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
    gap: 16px;
  }

}

@media (max-width: 768px) {
  .product-catalog {
    padding: 16px;
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
