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

    <!-- Product Details Modal -->
    <div v-if="selectedProduct" class="modal-overlay" @click="closeModal">
      <div class="modal-content" @click.stop>
        <button class="close-btn" @click="closeModal">&times;</button>
        <!-- Progress Bar: fixed at top of modal -->
        <div class="order-progress">
          <div class="progress-step" :class="{ active: orderStep >= 0, completed: orderStep > 0 }">
            <div class="step-number">1</div>
            <span>Product</span>
          </div>
          <div class="progress-line" :class="{ active: orderStep > 0 }"></div>
          <div class="progress-step" :class="{ active: orderStep >= 1, completed: orderStep > 1 }">
            <div class="step-number">2</div>
            <span>Details</span>
          </div>
          <div class="progress-line" :class="{ active: orderStep > 1 }"></div>
          <div class="progress-step" :class="{ active: orderStep >= 2, completed: orderStep > 2 }">
            <div class="step-number">3</div>
            <span>Documents</span>
          </div>
          <div class="progress-line" :class="{ active: orderStep > 2 }"></div>
          <div class="progress-step" :class="{ active: orderStep >= 3, completed: orderStep > 3 }">
            <div class="step-number">4</div>
            <span>Review</span>
          </div>
          <div class="progress-line" :class="{ active: orderStep > 3 }"></div>
          <div class="progress-step" :class="{ active: orderStep >= 4 }">
            <div class="step-number">5</div>
            <span>Confirm</span>
          </div>
        </div>
        <div class="modal-product-details">
          <div class="modal-product-image">
            <img :src="selectedProduct.image_url" :alt="selectedProduct.name">
          </div>
          <div class="modal-product-info">

            <!-- Step 1: Product Selection -->
            <div v-if="orderStep === 0" class="order-step">
              <h2>{{ selectedProduct.name }}</h2>
              <p class="full-description">{{ selectedProduct.full_description }}</p>
              <div class="specifications">
                <h3>Specifications</h3>
                <ul>
                  <li v-for="(spec, index) in selectedProduct.specifications" :key="index">
                    {{ spec }}
                  </li>
                </ul>
              </div>
              
              <!-- Product Variants -->
              <div v-if="selectedProduct.variants && selectedProduct.variants.length > 0" class="variants-section">
                <h3>Available Options</h3>
                <div class="variant-groups">
                  <div v-for="variant in selectedProduct.variants" :key="variant.attribute" class="variant-group">
                    <h4>{{ variant.attribute }}</h4>
                    <div class="variant-options">
                      <button 
                        v-for="value in variant.values" 
                        :key="value"
                        class="variant-btn"
                        :class="{ active: isSelectedVariant(variant.attribute, value) }"
                        @click="selectVariant(variant.attribute, value)"
                      >
                        {{ value }}
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Step 2: Additional Info -->
            <div v-if="orderStep === 1" class="order-step">
              <h2>Patient Information</h2>

              <!-- Patient Validation Error Message -->
              <div v-if="patientValidationError" class="patient-validation-error">
                {{ patientValidationError }}
              </div>

              <!-- Patient Selection -->
              <div class="form-group">
                <label for="patientSelect">Select Existing Patient</label>

                <!-- Patient Search Bar -->
                <div class="patient-search-container">
                  <input
                    v-model="patientSearchQuery"
                    type="text"
                    placeholder="Search patients by name, first name, last name, or email..."
                    class="patient-search-input"
                    @input="filterPatients"
                  >
                  <svg class="patient-search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="11" cy="11" r="8"></circle>
                    <path d="m21 21-4.35-4.35"></path>
                  </svg>
                </div>

                <!-- Custom Dropdown -->
                <div class="custom-dropdown" :class="{ 'is-open': isDropdownOpen }">
                  <div class="dropdown-trigger" @click="toggleDropdown" :class="{ 'has-selection': selectedPatient }">
                    <div class="dropdown-icon">
                      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
                        <circle cx="12" cy="7" r="4"></circle>
                      </svg>
                    </div>
                    <div class="dropdown-text">
                      <span v-if="selectedPatient">{{ selectedPatient.name }}</span>
                      <span v-else class="placeholder">Choose existing patient</span>
                    </div>
                    <div class="dropdown-arrow" :class="{ 'rotated': isDropdownOpen }">
                      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <polyline points="6,9 12,15 18,9"></polyline>
                      </svg>
                    </div>
                    <div v-if="selectedPatient" class="dropdown-clear-btn" @click.stop="clearPatientSelection">
                      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <line x1="18" y1="6" x2="6" y2="18"></line>
                        <line x1="6" y1="6" x2="18" y2="18"></line>
                      </svg>
                    </div>
                  </div>

                  <!-- Dropdown Options Panel -->
                  <div v-if="isDropdownOpen" class="dropdown-options" v-click-outside="closeDropdown">
                    <!-- Loading State -->
                    <div v-if="isLoadingPatients" class="dropdown-loading">
                      <div class="loading-spinner-small"></div>
                      <span>Loading patients...</span>
                    </div>

                    <!-- Options List -->
                    <div v-else-if="filterPatients().length > 0" class="dropdown-options-list">
                      <div
                        v-for="patient in filterPatients()"
                        :key="patient.id"
                        class="dropdown-option"
                        :class="{ 'is-selected': selectedPatient && selectedPatient.id === patient.id }"
                        @click="selectPatient(patient)"
                      >
                        <div class="option-icon">
                          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
                            <circle cx="12" cy="7" r="4"></circle>
                          </svg>
                        </div>
                        <div class="option-content">
                          <div class="option-name">{{ patient.name }}</div>
                          <div class="option-details">
                            <span v-if="patient.email">{{ patient.email }}</span>
                            <span v-if="patient.phone">{{ patient.phone }}</span>
                          </div>
                        </div>
                        <div v-if="selectedPatient && selectedPatient.id === patient.id" class="option-check">
                          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <polyline points="20,6 9,17 4,12"></polyline>
                          </svg>
                        </div>
                      </div>
                    </div>

                    <!-- Empty State -->
                    <div v-else class="dropdown-empty">
                      <div class="empty-icon">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                          <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
                          <circle cx="12" cy="7" r="4"></circle>
                        </svg>
                      </div>
                      <div class="empty-content">
                        <p>No patients found</p>
                        <small>Create a new patient below or start typing to add one manually</small>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <!-- OR Divider -->
              <div class="patient-or-divider">
                <span>OR</span>
              </div>

    <!-- Create New Patient Section -->
    <h4>Create New Patient</h4>
    <div class="create-patient-section">
      <div class="form-row">
        <div class="form-group">
          <label for="patientFirstName">First Name *</label>
          <input
            id="patientFirstName"
            v-model="orderForm.patientFirstName"
            type="text"
            placeholder="Enter patient's first name"
            :disabled="!!orderForm.patientId"
            @input="clearPatientValidationError"
          >
        </div>
        <div class="form-group">
          <label for="patientLastName">Last Name *</label>
          <input
            id="patientLastName"
            v-model="orderForm.patientLastName"
            type="text"
            placeholder="Enter patient's last name"
            :disabled="!!orderForm.patientId"
            @input="clearPatientValidationError"
          >
        </div>
      </div>
    </div>

            </div>

            <!-- Step 3: Document Upload -->
            <div v-if="orderStep === 2" class="order-step">
              <h2>Document Upload</h2>
              <div class="form-group">
                <label for="rightImpressionDoc">Right Ear Impression</label>
                <div class="file-upload">
                  <input 
                    id="rightImpressionDoc"
                    type="file"
                    @change="handleFileUpload('right', $event)"
                    accept=".pdf,.doc,.docx,.jpg,.jpeg,.png"
                  >
                  <div class="upload-status" v-if="orderForm.rightImpressionDoc">
                    {{ orderForm.rightImpressionDoc.name }}
                  </div>
                </div>
              </div>
              <div class="form-group">
                <label for="leftImpressionDoc">Left Ear Impression</label>
                <div class="file-upload">
                  <input
                    id="leftImpressionDoc"
                    type="file"
                    @change="handleFileUpload('left', $event)"
                    accept=".pdf,.doc,.docx,.jpg,.jpeg,.png"
                  >
                  <div class="upload-status" v-if="orderForm.leftImpressionDoc">
                    {{ orderForm.leftImpressionDoc.name }}
                  </div>
                </div>
              </div>

              <!-- Additional Notes -->
              <div class="form-group">
                <label for="notes">Additional Notes</label>
                <textarea
                  id="notes"
                  v-model="orderForm.notes"
                  placeholder="Enter any additional notes or requirements"
                  rows="4"
                ></textarea>
              </div>
            </div>

            <!-- Step 4: Review -->
            <div v-if="orderStep === 3" class="order-step review">
              <h2>Review Your Order</h2>
              <div class="review-section">
                <h3>Product</h3>
                <p><strong>Name:</strong> {{ selectedProduct?.name }}</p>
                <p><strong>Description:</strong> {{ selectedProduct?.full_description }}</p>
              </div>
              <div class="review-section" v-if="Object.keys(selectedVariants).length">
                <h3>Selected Options</h3>
                <ul>
                  <li v-for="(value, attribute) in selectedVariants" :key="attribute">
                    <strong>{{ attribute }}:</strong> {{ value }}
                  </li>
                </ul>
              </div>
              <div class="review-section">
                <h3>Patient Information</h3>
                <p><strong>Name:</strong> {{ selectedPatient ? selectedPatient.name : ((orderForm.patientFirstName && orderForm.patientLastName) ? (orderForm.patientFirstName + ' ' + orderForm.patientLastName) : (orderForm.patientFirstName || orderForm.patientLastName || '—')) }}</p>
                <p><strong>Notes:</strong> {{ orderForm.notes || '—' }}</p>
              </div>
              <div class="review-section">
                <h3>Documents</h3>
                <p><strong>Right Impression:</strong> {{ orderForm.rightImpressionDoc?.name || 'Not uploaded' }}</p>
                <p><strong>Left Impression:</strong> {{ orderForm.leftImpressionDoc?.name || 'Not uploaded' }}</p>
              </div>
            </div>

            <!-- Step 5: Confirmation -->
            <div v-if="orderStep === 4" class="order-step confirmation">
              <div class="confirmation-content">
                <h2>Order Confirmation</h2>
                <p>Your order has been successfully placed!</p>
                <button class="view-orders-btn" @click="viewOrders">
                  See My Orders
                </button>
              </div>
            </div>
          </div>
          <div>
            <!-- empty div for grid management-->
          </div>
          <!-- Navigation Buttons -->
          <div class="modal-order-button-container">
            <button
              v-if="orderStep >= 0 && orderStep < 4"
              class="back-btn"
              :disabled="isSubmittingOrder"
              @click="handleBack"
            >
              Back
            </button>
            <button
              v-if="orderStep < 4"
              class="order-btn large"
              :disabled="isSubmittingOrder"
              @click="nextStep"
            >
              <div v-if="orderStep === 3 && isSubmittingOrder" class="button-loader">
                <div class="spinner"></div>
              </div>
              <span v-else>
                {{ orderStep === 3 ? 'Place Order' : 'Next' }}
              </span>
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
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
  directives: {
    'click-outside': clickOutside
  },
  data() {
    return {
      products: [],
      searchQuery: '',
      selectedProduct: null,
      isLoading: false,
      isSubmittingOrder: false,
      currentPage: 1,
      itemsPerPage: 12,
      totalProducts: 0,
      searchTimeout: null,
      selectedVariants: {},
      orderStep: 0, // 0: product, 1: additional info, 2: documents, 3: review, 4: confirmation
      orderForm: {
        notes: '',
        patientFirstName: '',
        patientLastName: '',
        patientId: null, // Selected existing patient ID
        rightImpressionDoc: null,
        leftImpressionDoc: null
      },
      patientContacts: [], // List of existing patient contacts
      patientSearchQuery: '', // Search query for filtering patients
      isLoadingPatients: false,
      isDropdownOpen: false, // Custom dropdown state
      patientValidationError: '', // Error message for patient validation
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
    },

    selectedPatient() {
      return this.patientContacts.find(p => p.id === this.orderForm.patientId) || null;
    },

    isPatientInfoValid() {
      // Either an existing patient is selected, OR both first and last names are provided for creating a new patient
      return !!(this.orderForm.patientId || (this.orderForm.patientFirstName && this.orderForm.patientLastName));
    }
  },
  created() {
    this.fetchProducts()
  },
  methods: {
    handleBack() {
      if (this.orderStep === 0) {
        this.closeModal();
      } else {
        this.orderStep--;
      }
    },
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

      // Fetch patient contacts for this user
      this.fetchPatientContacts()
    },
    
    closeModal() {
      this.selectedProduct = null
      this.selectedVariants = {}
      this.resetOrderForm();
    },
    
    selectVariant(attribute, value) {
      this.selectedVariants[attribute] = value
    },
    
    isSelectedVariant(attribute, value) {
      return this.selectedVariants[attribute] === value
    },
    nextStep() {
      // Validate patient information only when trying to move from step 1 (Patient Information) to step 2 (Documents)
      if (this.orderStep === 1 && !this.isPatientInfoValid) {
        this.patientValidationError = 'Please select an existing patient or provide both first and last name to create a new patient.';
        this.$emit('show-error', {
          message: this.patientValidationError,
          type: 'error'
        });
        return;
      }

      // Clear any existing validation error when proceeding successfully
      this.patientValidationError = '';

      if (this.orderStep === 3) {
        this.submitOrder();
      } else {
        this.orderStep++;
      }
    },

    async submitOrder() {
      this.isSubmittingOrder = true
      try {
        const token = localStorage.getItem('decilo_token')
        if (!token) {
          throw new Error('Authentication required - Please log in first')
        }

        // Check if token is expired before making the request
        if (this.isTokenExpired(token)) {
          this.handleTokenExpired()
          return
        }

        if (!this.selectedProduct?.id) {
          throw new Error('No product selected')
        }

        const formData = new FormData()
        formData.append('product_template_id', String(this.selectedProduct.id))
        formData.append('selected_variants', JSON.stringify(this.selectedVariants || {}))
        formData.append('notes', this.orderForm.notes || '')

        // Add patient information - either existing patient ID or manual entry
        if (this.orderForm.patientId) {
          formData.append('patientId', String(this.orderForm.patientId))
        } else {
          formData.append('patientFirstName', this.orderForm.patientFirstName || '')
          formData.append('patientLastName', this.orderForm.patientLastName || '')
        }

        if (this.orderForm.rightImpressionDoc) {
          formData.append('rightImpressionDoc', this.orderForm.rightImpressionDoc)
        }
        if (this.orderForm.leftImpressionDoc) {
          formData.append('leftImpressionDoc', this.orderForm.leftImpressionDoc)
        }

        const response = await fetch('/decilo-api/orders', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`
          },
          body: formData
        })

        if (!response.ok) {
          if (response.status === 401) {
            // Token expired or invalid, handle it
            this.handleTokenExpired()
            return
          }
          const err = await response.json().catch(() => ({ error: 'Failed to place order' }))
          throw new Error(err.error || 'Failed to place order')
        }

        const data = await response.json()
        console.log('✅ Order created:', data)
        this.orderStep++
      } catch (error) {
        console.error('Error submitting order:', error)
        this.$emit('show-error', { message: error.message || 'Order submission failed', type: 'error' })
      } finally {
        this.isSubmittingOrder = false
      }
    },

    handleFileUpload(side, event) {
      const file = event.target.files[0];
      if (file) {
        if (side === 'right') {
          this.orderForm.rightImpressionDoc = file;
        } else {
          this.orderForm.leftImpressionDoc = file;
        }
      }
    },

    viewOrders() {
      this.$emit('go-to-orders');
      this.closeModal();
    },

    resetOrderForm() {
      this.orderStep = 0;
      this.orderForm = {
        notes: '',
        patientFirstName: '',
        patientLastName: '',
        patientId: null,
        rightImpressionDoc: null,
        leftImpressionDoc: null
      };
    },

    closeModal() {
      this.selectedProduct = null;
      this.resetOrderForm();
    },

    async fetchPatientContacts() {
      this.isLoadingPatients = true;
      try {
        const token = localStorage.getItem('decilo_token');
        if (!token) {
          throw new Error('Authentication required');
        }

        const response = await fetch('/decilo-api/patient-contacts', {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        });

        if (!response.ok) {
          if (response.status === 401) {
            this.handleTokenExpired();
            return;
          }
          throw new Error('Failed to fetch patient contacts');
        }

        const data = await response.json();
        this.patientContacts = data.patients || [];
      } catch (error) {
        console.error('Error fetching patient contacts:', error);
        this.$emit('show-error', {
          message: error.message || 'Failed to load patient contacts',
          type: 'error'
        });
      } finally {
        this.isLoadingPatients = false;
      }
    },

    onPatientSelectionChange() {
      // Clear validation error when patient selection changes
      this.patientValidationError = '';

      if (this.orderForm.patientId) {
        // Patient selected - keep new contact fields empty
        // (Removed auto-population of first/last name fields)
      } else {
        // Clear manual entry when no patient is selected
        this.orderForm.patientFirstName = '';
        this.orderForm.patientLastName = '';
      }
    },

    clearPatientSelection() {
      this.orderForm.patientId = '';
      this.onPatientSelectionChange();
    },

    toggleDropdown() {
      this.isDropdownOpen = !this.isDropdownOpen;
    },

    closeDropdown() {
      this.isDropdownOpen = false;
    },

    selectPatient(patient) {
      this.orderForm.patientId = patient.id;
      this.onPatientSelectionChange();
      this.closeDropdown();
    },

    filterPatients() {
      // Filter patientContacts based on patientSearchQuery
      if (!this.patientSearchQuery.trim()) {
        // If no search query, show all patients
        return this.patientContacts;
      }

      const query = this.patientSearchQuery.toLowerCase().trim();
      return this.patientContacts.filter(patient => {
        const name = patient.name ? patient.name.toLowerCase() : '';
        const firstName = patient.firstName ? patient.firstName.toLowerCase() : '';
        const lastName = patient.lastName ? patient.lastName.toLowerCase() : '';
        const email = patient.email ? patient.email.toLowerCase() : '';
        const phone = patient.phone ? patient.phone.toLowerCase() : '';

        return name.includes(query) ||
               firstName.includes(query) ||
               lastName.includes(query) ||
               email.includes(query) ||
               phone.includes(query);
      });
    },

    clearPatientValidationError() {
      // Clear validation error when user starts typing in form fields
      if (this.patientValidationError) {
        this.patientValidationError = '';
      }
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
  background: linear-gradient(135deg, #ffffff 0%, #e2e8f0 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
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
  background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
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


.filter-buttons {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.filter-btn {
  padding: 8px 16px;
  border: 1px solid #333333;
  border-radius: 20px;
  background: none;
  color: #ffffff;
  cursor: pointer;
  transition: all 0.2s;
}

.filter-btn.active {
  background: #ffffff;
  color: #000000;
  border-color: #ffffff;
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
  background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
  border: 1px solid #334155;
  border-radius: 16px;
  overflow: hidden;
  position: relative;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  min-height: 320px;
  display: flex;
  flex-direction: column;
}

.product-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: linear-gradient(90deg, var(--primary-color), #8b5cf6, #ec4899);
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
  top: 10px;
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

.product-price {
  font-size: 24px;
  color: #ffffff;
  margin-bottom: 16px;
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
  background: linear-gradient(135deg, var(--primary-color) 0%, #8b5cf6 100%);
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
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
  transition: left 0.5s ease;
}

.details-btn:hover::before {
  left: 100%;
}

.details-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(59, 130, 246, 0.4);
}

.order-btn.large {
  padding: 18px 40px;
  font-size: 16px;
  font-weight: 600;
  min-width: 160px;
  border-radius: 16px;
  background: linear-gradient(135deg, var(--primary-color) 0%, #8b5cf6 100%);
  color: #ffffff;
  border: none;
  box-shadow: 0 8px 24px rgba(59, 130, 246, 0.3);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  position: relative;
  overflow: hidden;
}

.order-btn.large::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
  transition: left 0.5s ease;
}

.order-btn.large:hover::before {
  left: 100%;
}

.order-btn.large:hover {
  background: linear-gradient(135deg, #2563eb 0%, #7c3aed 100%);
  transform: translateY(-3px);
  box-shadow: 0 12px 32px rgba(59, 130, 246, 0.4);
}

.order-btn.large:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

.button-loader {
  display: flex;
  align-items: center;
  justify-content: center;
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

/* Modal styles */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(15, 23, 42, 0.9);
  backdrop-filter: blur(8px);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
  padding: 20px;
}

.modal-content {
  background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
  border: 1px solid #334155;
  border-radius: 16px;
  width: 100%;
  max-width: 90%;
  max-height: 95vh;
  position: relative;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.4);
}

.close-btn {
  position: absolute;
  top: 20px;
  right: 20px;
  background: rgba(30, 41, 59, 0.8);
  border: 1px solid #475569;
  border-radius: 10px;
  color: #ffffff;
  font-size: 18px;
  width: 36px;
  height: 36px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  backdrop-filter: blur(8px);
  z-index: 10;
}

.close-btn:hover {
  background: rgba(239, 68, 68, 0.8);
  border-color: #ef4444;
  transform: scale(1.1);
}

.modal-product-details {
  display: grid;
  grid-template-columns: minmax(0, 30%) minmax(0, 1fr);
  gap: 32px;
  min-height: calc(100vh - 200px);
  padding: 32px;
  padding-top: 112px;
  box-sizing: border-box;
}

.modal-product-image {
  position: sticky;
  top: 32px;
  width: 100%;
  height: auto;
  min-height: 200px;
  border-radius: 14px;
  overflow: hidden;
  background: linear-gradient(135deg, #334155 0%, #1e293b 100%);
  padding: 16px;
  box-sizing: border-box;
  border: 1px solid #475569;
  display: flex;
  align-items: center;
  justify-content: center;
}

.modal-product-image img {
  width: 100%;
  object-fit: contain;
  box-sizing: border-box;
  border-radius: 16px;
  transition: transform 0.3s ease;
}

.modal-product-image:hover img {
  transform: scale(1.05);
}

.modal-product-info {
  overflow-y: auto;
  height: calc(100vh - 300px);
  scrollbar-width: thin;
  scrollbar-color: #475569 #1e293b;
  padding-right: 14px;
  position: relative;
  box-sizing: border-box;
}

/* Progress Bar Styles */
.order-progress {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin: 0;
  padding: 20px 20px;
  padding-right: 100px;
  background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
  border-bottom: 1px solid #334155;
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  z-index: 3;
  min-height: 80px;
  box-sizing: border-box;
}

.progress-step {
  display: flex;
  flex-direction: column;
  align-items: center;
  position: relative;
  color: #64748b;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  font-size: 10px;
}

.progress-step.active {
  color: #ffffff;
}

.progress-step.completed .step-number {
  background: linear-gradient(135deg, #10b981, #059669);
  border-color: #10b981;
  box-shadow: 0 0 20px rgba(16, 185, 129, 0.5);
}

.step-number {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  border: 2px solid #475569;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
  margin-bottom: 8px;
  font-weight: 600;
  font-size: 14px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.progress-step.active .step-number {
  border-color: var(--primary-color);
  background: linear-gradient(135deg, var(--primary-color), #8b5cf6);
  box-shadow: 0 0 20px rgba(59, 130, 246, 0.5);
  transform: scale(1.1);
}

.progress-line {
  flex: 1;
  height: 3px;
  background: linear-gradient(135deg, #334155 0%, #475569 100%);
  margin: 0 12px;
  margin-bottom: 36px;
  border-radius: 2px;
  position: relative;
  overflow: hidden;
}

.progress-line::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  height: 100%;
  width: 0%;
  background: linear-gradient(90deg, var(--primary-color), #8b5cf6, #ec4899);
  transition: width 0.5s ease;
  border-radius: 2px;
}

.progress-line.active::before {
  width: 100%;
}

/* Form Styles */
.form-group {
  margin-bottom: 24px;
}

/* Patient Validation Error */
.patient-validation-error {
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid #ef4444;
  border-radius: 8px;
  padding: 12px 16px;
  margin-bottom: 20px;
  color: #ef4444;
  font-size: 14px;
  font-weight: 500;
  text-align: center;
}

.form-group label {
  display: block;
  color: #ffffff;
  margin-bottom: 8px;
  font-weight: 600;
  font-size: 13px;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.form-group input,
.form-group textarea {
  width: 80%;
  padding: 12px 16px;
  background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
  border: 2px solid #334155;
  border-radius: 10px;
  color: #ffffff;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  backdrop-filter: blur(8px);
}

.form-group textarea {
  resize: vertical;
  min-height: 120px;
}

.form-group input:focus,
.form-group textarea:focus {
  outline: none;
  border-color: var(--primary-color);
  box-shadow:
    0 0 0 4px rgba(59, 130, 246, 0.15),
    0 8px 32px rgba(59, 130, 246, 0.12);
  transform: translateY(-2px);
}

.form-group input::placeholder,
.form-group textarea::placeholder {
  color: #64748b;
  font-weight: 400;
}

/* Custom Dropdown Styles */
.custom-dropdown {
  position: relative;
  width: 100%;
}

.dropdown-trigger {
  position: relative;
  display: flex;
  align-items: center;
  padding: 16px 20px;
  background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
  border: 2px solid #334155;
  border-radius: 12px;
  color: #ffffff;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  min-height: 56px;
}

.dropdown-trigger:hover {
  border-color: #475569;
  background: linear-gradient(135deg, #334155 0%, #1e293b 100%);
}

.dropdown-trigger.has-selection {
  border-color: #10b981;
  background: linear-gradient(135deg, #064e3b 0%, #065f46 100%);
}

.dropdown-icon {
  width: 20px;
  height: 20px;
  color: #64748b;
  margin-right: 12px;
  flex-shrink: 0;
}

.dropdown-text {
  flex: 1;
  text-align: left;
  min-width: 0;
}

.placeholder {
  color: #64748b;
}

.dropdown-arrow {
  width: 20px;
  height: 20px;
  color: #64748b;
  margin-left: 12px;
  transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  flex-shrink: 0;
}

.dropdown-arrow.rotated {
  transform: rotate(180deg);
}

.dropdown-clear-btn {
  position: absolute;
  right: 16px;
  top: 50%;
  transform: translateY(-50%);
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: rgba(239, 68, 68, 0.2);
  border: 1px solid #ef4444;
  color: #ef4444;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  z-index: 3;
}

.dropdown-clear-btn:hover {
  background: rgba(239, 68, 68, 0.3);
  transform: translateY(-50%) scale(1.1);
}

.dropdown-clear-btn svg {
  width: 14px;
  height: 14px;
}

.dropdown-options {
  position: absolute;
  top: calc(100% + 8px);
  left: 0;
  right: 0;
  background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
  border: 1px solid #334155;
  border-radius: 12px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.4);
  z-index: 1000;
  max-height: 300px;
  overflow-y: auto;
  animation: dropdownFadeIn 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

@keyframes dropdownFadeIn {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.dropdown-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 20px;
  color: #64748b;
  font-size: 14px;
}

.dropdown-options-list {
  padding: 8px 0;
}

.dropdown-option {
  display: flex;
  align-items: center;
  padding: 16px 20px;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  border-bottom: 1px solid rgba(51, 65, 85, 0.3);
}

.dropdown-option:last-child {
  border-bottom: none;
}

.dropdown-option:hover {
  background: linear-gradient(135deg, #334155 0%, #475569 100%);
}

.dropdown-option.is-selected {
  background: linear-gradient(135deg, #064e3b 0%, #065f46 100%);
  border-left: 4px solid #10b981;
}

.option-icon {
  width: 24px;
  height: 24px;
  color: #64748b;
  margin-right: 16px;
  flex-shrink: 0;
}

.option-content {
  flex: 1;
  min-width: 0;
}

.option-name {
  color: #ffffff;
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 4px;
}

.option-details {
  display: flex;
  gap: 16px;
  font-size: 12px;
  color: #64748b;
}

.option-check {
  width: 20px;
  height: 20px;
  color: #10b981;
  margin-left: 12px;
  flex-shrink: 0;
}

.dropdown-empty {
  padding: 32px 20px;
  text-align: center;
}

.empty-icon {
  width: 48px;
  height: 48px;
  margin: 0 auto 16px;
  color: #64748b;
  opacity: 0.6;
}

.empty-content p {
  color: #ffffff;
  font-size: 16px;
  font-weight: 600;
  margin: 0 0 8px 0;
}

.empty-content small {
  color: #64748b;
  font-size: 12px;
  line-height: 1.4;
  display: block;
}

.form-divider {
  text-align: center;
  margin: 24px 0;
  position: relative;
  color: #64748b;
  font-size: 14px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.1em;
}

.form-divider::before {
  content: '';
  position: absolute;
  top: 50%;
  left: 0;
  right: 0;
  height: 1px;
  background: linear-gradient(90deg, transparent, #334155, transparent);
}

.form-divider span {
  background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
  padding: 0 16px;
  position: relative;
  z-index: 1;
}

.patient-or-divider {
  text-align: center;
  margin: 32px 0;
  position: relative;
  color: #ffffff;
  font-size: 18px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.15em;
}

.patient-or-divider::before {
  content: '';
  position: absolute;
  top: 50%;
  left: 0;
  right: 0;
  height: 2px;
  background: linear-gradient(90deg, transparent, var(--primary-color), transparent);
}

.patient-or-divider span {
  background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
  padding: 0 24px;
  position: relative;
  z-index: 1;
  border: 2px solid var(--primary-color);
  border-radius: 8px;
}

/* Create Patient Section */
.create-patient-section {
  background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
  border: 1px solid #334155;
  border-radius: 12px;
  padding: 24px;
  margin-top: 16px;
  margin-bottom: 16px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}


.create-patient-section h3 {
  color: #ffffff;
  margin: 0 0 20px 0;
  font-size: 16px;
  font-weight: 600;
  transition: color 0.3s ease;
}


/* File Upload Styles */
.file-upload {
  position: relative;
}

.file-upload input[type="file"] {
  width: 80%;
  padding: 16px 20px;
  background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
  border: 2px solid #334155;
  border-radius: 12px;
  color: #ffffff;
  cursor: pointer;
  font-size: 15px;
  font-weight: 500;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.file-upload input[type="file"]:hover {
  border-color: #475569;
  background: linear-gradient(135deg, #334155 0%, #1e293b 100%);
}

.upload-status {
  margin-top: 12px;
  color: #10b981;
  font-size: 14px;
  font-weight: 500;
  padding: 8px 16px;
  background: rgba(16, 185, 129, 0.1);
  border-radius: 8px;
  border: 1px solid rgba(16, 185, 129, 0.3);
}

/* Confirmation Styles */
.confirmation {
  text-align: center;
  padding: 60px 40px;
}

.confirmation h2 {
  margin-bottom: 20px;
  color: #ffffff;
  font-size: 28px;
  font-weight: 700;
}

.confirmation p {
  color: #10b981;
  margin-bottom: 32px;
  font-size: 16px;
  font-weight: 500;
}

/* Review Styles */
.review .review-section {
  margin-bottom: 20px;
}

.review .review-section h3 {
  color: #ffffff;
  margin-bottom: 8px;
}

.review .review-section p,
.review .review-section li {
  color: #cccccc;
}

.view-orders-btn {
  padding: 12px 24px;
  background: #333333;
  color: #ffffff;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
  transition: background-color 0.2s;
}

.view-orders-btn:hover {
  background: #444444;
}

/* Navigation Buttons */
.modal-order-button-container {
  display: flex;
  gap: 20px;
  justify-content: space-between;
  align-items: center;
}

.back-btn {
  padding: 16px 32px;
  background: linear-gradient(135deg, #475569 0%, #334155 100%);
  color: #ffffff;
  border: 2px solid #64748b;
  border-radius: 16px;
  cursor: pointer;
  font-weight: 600;
  font-size: 14px;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  min-width: 140px;
}

.back-btn:hover:not(:disabled) {
  background: linear-gradient(135deg, #64748b 0%, #475569 100%);
  border-color: #94a3b8;
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(100, 116, 139, 0.3);
}

.back-btn:disabled {
  background: #e2e8f0;
  border-color: #cbd5e1;
  color: #94a3b8;
  cursor: not-allowed;
  opacity: 0.6;
  transform: none;
  box-shadow: none;
}

.modal-order-button-container {
  position: sticky;
  bottom: 0;
  left: 32px;
  right: 32px;
  padding: 24px 0;
  display: flex;
  justify-content: space-between;
  align-items: center;
  z-index: 3;
}

/* Webkit scrollbar styles */
.modal-product-info::-webkit-scrollbar {
  width: 8px;
}

.modal-product-info::-webkit-scrollbar-track {
  background: #111111;
  border-radius: 4px;
}

.modal-product-info::-webkit-scrollbar-thumb {
  background: #333333;
  border-radius: 4px;
}

.modal-product-info::-webkit-scrollbar-thumb:hover {
  background: #444444;
}

.modal-product-info h2 {
  margin: 0;
  margin-bottom: 12px;
  font-size: 20px;
  color: #ffffff;
}

.full-description {
  color: #888888;
  line-height: 1.6;
  margin-bottom: 20px;
}

.specifications {
  margin-bottom: 24px;
}

.specifications h3 {
  color: #ffffff;
  margin-bottom: 12px;
}

.specifications ul {
  list-style: none;
  padding: 0;
  margin: 0;
  color: #888888;
}

.specifications li {
  margin-bottom: 8px;
  padding-left: 20px;
  position: relative;
}

.specifications li::before {
  content: "•";
  position: absolute;
  left: 0;
  color: #ffffff;
}

/* Variant styles */
.variants-section {
  margin-bottom: 24px;
  padding-bottom: 20px;
}

.variants-section h3 {
  color: #ffffff;
  margin-bottom: 16px;
}

.variant-groups {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.variant-group h4 {
  color: #ffffff;
  margin: 0 0 8px 0;
  font-size: 14px;
}

.variant-options {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.variant-btn {
  padding: 8px 16px;
  border: 1px solid #333333;
  border-radius: 20px;
  background: none;
  color: #ffffff;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 14px;
}

.variant-btn:hover {
  background: #333333;
}

.variant-btn.active {
  background: #333333;
  color: #ffffff;
  border-color: #444444;
}

.modal-price {
  font-size: 32px;
  color: #ffffff;
  margin-bottom: 24px;
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

.loading-spinner {
  width: 60px;
  height: 60px;
  border: 4px solid rgba(255, 255, 255, 0.1);
  border-radius: 50%;
  border-top-color: #ffffff;
  animation: spin 0.8s cubic-bezier(0.5, 0, 0.5, 1) infinite;
  box-shadow: 0 0 20px rgba(255, 255, 255, 0.2);
}

@keyframes spin {
  100% {
    transform: rotate(360deg);
  }
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
  background: linear-gradient(135deg, #334155 0%, #475569 100%);
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

/* Pagination styles */
.pagination {
  margin-top: 36px;
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 20px;
  position: relative;
  z-index: 1;
}

.page-btn {
  padding: 12px 24px;
  border: 2px solid #475569;
  border-radius: 12px;
  background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
  color: #ffffff;
  cursor: pointer;
  font-weight: 600;
  font-size: 14px;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  backdrop-filter: blur(8px);
}

.page-btn:hover:not(:disabled) {
  background: linear-gradient(135deg, #334155 0%, #1e293b 100%);
  border-color: #64748b;
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(71, 85, 105, 0.3);
}

.page-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
}

.page-numbers {
  display: flex;
  gap: 12px;
}

.page-number {
  width: 44px;
  height: 44px;
  border: 2px solid #475569;
  border-radius: 50%;
  background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
  color: #ffffff;
  cursor: pointer;
  font-weight: 600;
  font-size: 14px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  display: flex;
  align-items: center;
  justify-content: center;
  backdrop-filter: blur(8px);
}

.page-number:hover {
  background: linear-gradient(135deg, #334155 0%, #1e293b 100%);
  border-color: #64748b;
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(71, 85, 105, 0.3);
}

.page-number.active {
  background: linear-gradient(135deg, var(--primary-color) 0%, #8b5cf6 100%);
  color: #ffffff;
  border-color: var(--primary-color);
  box-shadow: 0 0 20px rgba(59, 130, 246, 0.5);
  transform: scale(1.1);
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

  .modal-content {
    max-width: 90%;
    overflow-y: auto;
    overflow-x: hidden;
  }

  .modal-product-details {
    gap: 24px;
    padding: 24px;
    padding-top: 75px;
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

  .modal-overlay {
    padding: 12px;
  }

  .modal-content {
    max-width: 95%;
    border-radius: 14px;
    overflow-y: auto;
    overflow-x: hidden;
  }

  .close-btn {
    top: 15px;
    right: 15px;
  }

  .modal-product-details {
    grid-template-columns: 1fr;
    gap: 18px;
    min-height: calc(100vh - 180px);
    padding: 18px;
    padding-top: 98px;
    box-sizing: border-box;
  }

  .order-progress {
    padding: 16px 12px;
    padding-right: 80px;
    flex-wrap: wrap;
    gap: 6px;
    justify-content: center;
    min-height: 60px;
  }

  .progress-step {
    flex: 0 0 auto;
    font-size: 9px;
  }

  .step-number {
    width: 28px;
    height: 28px;
    font-size: 11px;
  }

  .progress-line {
    height: 2px;
    margin: 0 4px;
    flex: 1;
    min-width: 20px;
  }

  .modal-product-image {
    position: relative;
    height: 300px;
    padding: 24px;
    top: 0;
    border-radius: 16px;
  }

  .modal-product-info {
    height: calc(100vh - 240px);
    padding-right: 0;
    padding-bottom: 120px;
    overflow-y: auto;
  }

  .modal-order-button-container {
    position: sticky;
    bottom: 0;
    left: 18px;
    right: 18px;
    padding: 20px 0;
    background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
    border-top: 1px solid #334155;
    flex-direction: column;
    gap: 14px;
    align-items: stretch;
    z-index: 3;
  }

  .back-btn,
  .order-btn.large {
    width: 100%;
    min-width: none;
  }

  .form-group input,
  .form-group textarea {
    max-width: none;
  }

  .dropdown-trigger {
    padding: 14px 18px;
    min-height: 48px;
    font-size: 13px;
  }

  .dropdown-icon {
    width: 18px;
    height: 18px;
    margin-right: 10px;
  }

  .dropdown-arrow {
    width: 18px;
    height: 18px;
    margin-left: 10px;
  }

  .dropdown-clear-btn {
    right: 14px;
    width: 20px;
    height: 20px;
  }

  .dropdown-options {
    max-height: 250px;
  }

  .dropdown-option {
    padding: 14px 16px;
  }

  .option-icon {
    width: 20px;
    height: 20px;
    margin-right: 12px;
  }

  .option-name {
    font-size: 13px;
  }

  .option-details {
    font-size: 11px;
  }

  .form-row {
    grid-template-columns: 1fr;
    gap: 12px;
  }

  .new-patient-form {
    padding: 16px;
  }

  .create-patient-btn {
    font-size: 13px;
    padding: 10px 16px;
  }

  .patient-empty-state {
    padding: 24px 12px;
  }

  .empty-icon {
    width: 40px;
    height: 40px;
  }

  .pagination {
    gap: 16px;
    flex-wrap: wrap;
  }

  .page-btn {
    padding: 10px 20px;
    font-size: 13px;
  }

  .page-number {
    width: 40px;
    height: 40px;
    font-size: 13px;
  }
}

@media (max-width: 480px) {
  .product-catalog {
    padding: 12px;
  }

  .catalog-header h1 {
    font-size: 22px;
  }

  .close-btn {
    top: 10px;
    right: 10px;
    width: 32px;
    height: 32px;
    font-size: 16px;
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

  .modal-overlay {
    padding: 8px;
  }

  .modal-content {
    max-width: 98%;
    max-height: 95%;
    overflow-y: auto;
    overflow-x: hidden;
  }

  .modal-product-details {
    padding: 14px;
    padding-top: 75px;
    min-height: calc(100vh - 140px);
    box-sizing: border-box;
  }

  .order-progress {
    padding: 10px 6px;
    padding-right: 60px;
    gap: 3px;
    min-height: 50px;
    padding-right : 60px;
  }

  .progress-step {
    font-size: 8px;
  }

  .step-number {
    width: 22px;
    height: 22px;
    font-size: 9px;
  }

  .progress-line {
    height: 1px;
    margin: 0 2px;
    min-width: 15px;
  }

  .modal-product-image {
    height: auto;
    min-height: 150px;
    max-height: 250px;
    padding: 12px;
  }

  .modal-order-button-container {
    position: sticky;
    bottom: 0;
    left: 14px;
    right: 14px;
    padding: 14px 0;
    background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
    border-top: 1px solid #334155;
    z-index: 3;
  }

  .back-btn,
  .order-btn.large {
    padding: 10px 16px;
    font-size: 12px;
  }

  .form-divider {
    margin: 16px 0;
    font-size: 12px;
  }

  .new-patient-form h3 {
    font-size: 14px;
  }

  .save-patient-btn {
    padding: 12px 20px;
    font-size: 12px;
  }

  .dropdown-trigger {
    padding: 12px 14px;
    min-height: 44px;
    font-size: 12px;
  }

  .dropdown-icon {
    width: 16px;
    height: 16px;
    margin-right: 8px;
  }

  .dropdown-arrow {
    width: 16px;
    height: 16px;
    margin-left: 8px;
  }

  .dropdown-clear-btn {
    right: 10px;
    width: 18px;
    height: 18px;
  }

  .dropdown-options {
    max-height: 200px;
  }

  .dropdown-option {
    padding: 12px 14px;
  }

  .option-icon {
    width: 18px;
    height: 18px;
    margin-right: 10px;
  }

  .option-name {
    font-size: 12px;
  }

  .option-details {
    font-size: 10px;
  }

  .option-check {
    width: 16px;
    height: 16px;
  }

  .patient-loading-state {
    padding: 12px;
    font-size: 12px;
  }

  .loading-spinner-small {
    width: 14px;
    height: 14px;
  }

  .patient-empty-state {
    padding: 20px 10px;
  }

  .empty-icon {
    width: 36px;
    height: 36px;
  }

  .patient-empty-state p {
    font-size: 14px;
  }

  .patient-empty-state small {
    font-size: 11px;
  }
}

/* Patient Search Styles */
.patient-search-container {
  position: relative;
  margin-bottom: 16px;
}

.patient-search-input {
  width: 100%;
  padding: 12px 40px 12px 16px;
  border: 1px solid #e1e5e9;
  border-radius: 8px;
  font-size: 14px;
  background-color: #ffffff;
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}

.patient-search-input:focus {
  outline: none;
  border-color: var(--primary-color);
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.patient-search-input::placeholder {
  color: #9ca3af;
}

.patient-search-icon {
  position: absolute;
  right: 12px;
  top: 50%;
  transform: translateY(-50%);
  width: 20px;
  height: 20px;
  color: #6b7280;
  pointer-events: none;
}
</style>
