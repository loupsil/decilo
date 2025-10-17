<template>
  <!-- Product Details Fullscreen -->
  <div v-if="selectedProduct" class="fullscreen-checkout">
    <button class="back-btn-header" @click="closeModal">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M19 12H5M12 19l-7-7 7-7"/>
      </svg>
      Back to Products
    </button>
      <!-- Progress Bar: fixed at top of modal -->
      <div class="order-progress">
        <div class="progress-step" :class="{ active: orderStep >= 0, completed: orderStep > 0 }">
          <div class="step-number">1</div>
          <span>Product</span>
        </div>
        <div class="progress-line" :class="{ active: orderStep > 0 }"></div>
        <div class="progress-step" :class="{ active: orderStep >= 1, completed: orderStep > 1 }">
          <div class="step-number">2</div>
          <span>Patient</span>
        </div>
        <div class="progress-line" :class="{ active: orderStep > 1 }"></div>
        <div class="progress-step" :class="{ active: orderStep >= 2, completed: orderStep > 2 }">
          <div class="step-number">3</div>
          <span>Ear Impressions</span>
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
            <div v-if="selectedProduct.specifications && selectedProduct.specifications.length > 0" class="specifications">
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

          <!-- Step 2: Patient Information -->
          <div v-if="orderStep === 1" class="order-step">
            <h2>Patient Information</h2>

            <!-- Patient Validation Error Message -->
            <div v-if="patientValidationError" class="patient-validation-error">
              {{ patientValidationError }}
            </div>

            <!-- Client Type Selection (if not selected yet) -->
            <div v-if="!isClientTypeSelected" class="client-type-selection">
              <h3>Is this a new client or an existing client?</h3>
              <div class="client-type-buttons">
                <button
                  class="client-type-btn"
                  :class="{ active: clientType === 'new' }"
                  @click="selectClientType('new')"
                >
                  <div class="client-type-icon">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
                      <circle cx="12" cy="7" r="4"></circle>
                    </svg>
                  </div>
                  <div class="client-type-content">
                    <h4>New Patient</h4>
                    <p>Create a new patient profile</p>
                  </div>
                </button>

                <button
                  class="client-type-btn"
                  :class="{ active: clientType === 'existing' }"
                  @click="selectClientType('existing')"
                >
                  <div class="client-type-icon">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
                      <circle cx="9" cy="7" r="4"></circle>
                      <path d="M23 21v-2a4 4 0 0 0-3-3.87"></path>
                      <path d="M16 3.13a4 4 0 0 1 0 7.75"></path>
                    </svg>
                  </div>
                  <div class="client-type-content">
                    <h4>Existing Patient</h4>
                    <p>Select from existing patients</p>
                  </div>
                </button>
              </div>
            </div>

            <!-- Existing Client Selection -->
            <div v-else-if="clientType === 'existing'" class="existing-client-section">
              <div class="client-type-header">
                <h3>Existing Client</h3>
                <button v-if="!isWithPreviousOrder" class="change-client-type-btn" @click="changeClientType">
                  Change to New Client
                </button>
              </div>

              <!-- Patient Selection -->
              <div class="form-group">
                <label for="patientSelect">Select Existing Patient</label>

                <!-- Patient Selection Container -->
                <div class="patient-selection-container">
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

                  <!-- Patient Search Bar -->
                  <div class="patient-search-container">
                    <input
                      v-model="patientSearchQuery"
                      type="text"
                      placeholder="Search patients..."
                      class="patient-search-input"
                      @input="filterPatients"
                    >
                    <svg class="patient-search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <circle cx="11" cy="11" r="8"></circle>
                      <path d="m21 21-4.35-4.35"></path>
                    </svg>
                  </div>
                </div>
              </div>
            </div>

            <!-- New Client Form -->
            <div v-else-if="clientType === 'new'" class="new-client-section">
              <div class="client-type-header">
                <h3>New Client</h3>
                <button class="change-client-type-btn" @click="changeClientType">
                  Change to Existing Client
                </button>
              </div>

              <!-- Create New Patient Section -->
              <div class="create-patient-section">
                <div class="form-row">
                  <div class="form-group">
                    <label for="patientFirstName">First Name *</label>
                    <input
                      id="patientFirstName"
                      v-model="orderForm.patientFirstName"
                      type="text"
                      placeholder="Enter patient's first name"
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
                      @input="clearPatientValidationError"
                    >
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Step 3: Document Upload -->
          <div v-if="orderStep === 2" class="order-step">
            <h2>Ear Impressions</h2>

            <!-- Impression Method Selection (only for new patients, if not selected yet) -->
            <div v-if="!isImpressionMethodSelected && clientType !== 'existing'" class="impression-method-selection">
              <h3>How would you like to provide the ear impressions?</h3>
              <div class="impression-method-buttons">
                <button
                  class="impression-method-btn"
                  :class="{ active: impressionMethod === 'scan' }"
                  @click="selectImpressionMethod('scan')"
                >
                  <div class="impression-method-icon">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <path d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
                    </svg>
                  </div>
                  <div class="impression-method-content">
                    <h4>Scan of ear impressions</h4>
                    <p>Upload scan of impressions</p>
                  </div>
                </button>

                <button
                  class="impression-method-btn"
                  :class="{ active: impressionMethod === 'ship' }"
                  @click="selectImpressionMethod('ship')"
                >
                  <div class="impression-method-icon">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <path d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4"></path>
                    </svg>
                  </div>
                  <div class="impression-method-content">
                    <h4>Shipping of ear impressions</h4>
                    <p>Ship your ear impressions</p>
                  </div>
                </button>
              </div>
            </div>

            <!-- Content when impression method is selected OR existing patient (auto-scan) -->
            <div v-else-if="isImpressionMethodSelected || clientType === 'existing'">
              <!-- Method header with option to change (only for new patients) -->
              <div v-if="clientType !== 'existing'" class="impression-method-header">
                <h3>{{ impressionMethod === 'scan' ? 'Scan of ear impressions' : 'Shipping of ear impressions' }}</h3>
                <button class="change-impression-method-btn" @click="changeImpressionMethod">
                  Change Method
                </button>
              </div>

              <!-- Shipping method: show message (only for new patients who chose shipping) -->
              <div v-if="impressionMethod === 'ship'" class="form-group">
                <div class="highlight-note">
                  <span class="highlight-icon">📦</span>
                  <span class="highlight-text"><strong>Merci d'envoyer les empreintes en indiquant le numéro ID MO</strong></span>
                </div>
              </div>

              <!-- Scan method: show upload options (default for existing patients, or when scan is selected for new patients) -->
              <div v-else-if="impressionMethod === 'scan' || clientType === 'existing'">
                
                <!-- Document status message for existing patients -->
                <div v-if="clientType === 'existing' && !earImpressionsLoading" class="form-group">
                  <div v-if="earImpressionsError" class="info-note error">
                    <span class="info-icon">⚠️</span>
                    <span class="info-text">{{ earImpressionsError }}</span>
                  </div>
                  <div v-else-if="earImpressions.left?.exists || earImpressions.right?.exists" class="info-note success">
                    <span class="info-icon">✓</span>
                    <span class="info-text"><strong>Documents found for {{ selectedPatient?.name }}</strong> - They have been automatically loaded. You can replace them if needed.</span>
                  </div>
                  <div v-else class="info-note warning">
                    <span class="info-icon">ℹ️</span>
                    <span class="info-text"><strong>No existing documents found for {{ selectedPatient?.name }}</strong> - Please upload new ear impression documents.</span>
                  </div>
                </div>

                <!-- With previous order: show previously stored documents (downloadable) -->
                <div v-if="isWithPreviousOrder" class="form-group">
              <h3 style="margin-top: 16px;">Existing Ear Impression Documents</h3>
              <div v-if="earImpressionsLoading" class="dropdown-loading">
                <div class="loading-spinner-small"></div>
                <span>Loading documents...</span>
              </div>
              <div v-else>
                <div v-if="earImpressionsError" class="patient-validation-error">{{ earImpressionsError }}</div>
                <ul v-else class="existing-docs-list">
                  <li>
                    <strong>Right:</strong>
                    <template v-if="earImpressions.right?.exists">
                      <a class="doc-link" :href="downloadEarUrl('right')" @click.prevent="downloadEar('right')">
                        <span class="doc-icon" aria-hidden="true">
                          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M12 5v10"/>
                            <path d="m7 10 5 5 5-5"/>
                            <path d="M5 19h14"/>
                          </svg>
                        </span>
                        <span class="doc-filename">{{ earImpressions.right.filename }}</span>
                      </a>
                    </template>
                    <template v-else>
                      <span>Not found</span>
                    </template>
                  </li>
                  <li>
                    <strong>Left:</strong>
                    <template v-if="earImpressions.left?.exists">
                      <a class="doc-link" :href="downloadEarUrl('left')" @click.prevent="downloadEar('left')">
                        <span class="doc-icon" aria-hidden="true">
                          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M12 5v10"/>
                            <path d="m7 10 5 5 5-5"/>
                            <path d="M5 19h14"/>
                          </svg>
                        </span>
                        <span class="doc-filename">{{ earImpressions.left.filename }}</span>
                      </a>
                    </template>
                    <template v-else>
                      <span>Not found</span>
                    </template>
                  </li>
                </ul>
              </div>
            </div>

                <!-- Conditionally render impression uploads only when 3D scan is selected -->
                <div v-if="isImpressionScan3D" class="ear-upload-container">
              <div 
                v-if="showLeftUpload" 
                class="ear-upload-box left-ear" 
                :class="{ 'has-file': !!orderForm.leftImpressionDoc, 'dragging': isDraggingLeft }"
                @click="triggerFileInput('left')"
                @dragover.prevent="isDraggingLeft = true"
                @dragleave.prevent="isDraggingLeft = false"
                @drop.prevent="handleDrop('left', $event)"
              >
                <div class="ear-illustration left">
                  <svg viewBox="0 0 100 150" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M70 30C70 20 65 10 50 10C35 10 30 20 30 30C30 35 28 40 28 45C28 50 30 55 32 60C34 65 36 70 36 75C36 85 34 95 40 100C46 105 55 105 60 100C65 95 68 85 68 75C68 70 70 65 72 60C74 55 76 50 76 45C76 40 74 35 70 30Z" stroke="currentColor" stroke-width="3" fill="none"/>
                    <ellipse cx="45" cy="50" rx="8" ry="12" stroke="currentColor" stroke-width="2" fill="none"/>
                  </svg>
                </div>
                <div class="ear-upload-content">
                  <h4>Left Ear<span v-if="requireLeftDoc" class="required-mark"> *</span></h4>
                  <div class="upload-info">
                    <span v-if="!orderForm.leftImpressionDoc" class="upload-prompt">Click or drag file here</span>
                    <span v-else class="uploaded-filename">{{ orderForm.leftImpressionDoc.name }}</span>
                  </div>
                  <input
                    ref="leftFileInput"
                    id="leftImpressionDoc"
                    type="file"
                    @change="handleFileUpload('left', $event)"
                    accept=".pdf,.doc,.docx,.jpg,.jpeg,.png"
                    class="hidden-file-input"
                  >
                </div>
              </div>

              <div 
                v-if="showRightUpload" 
                class="ear-upload-box right-ear" 
                :class="{ 'has-file': !!orderForm.rightImpressionDoc, 'dragging': isDraggingRight }"
                @click="triggerFileInput('right')"
                @dragover.prevent="isDraggingRight = true"
                @dragleave.prevent="isDraggingRight = false"
                @drop.prevent="handleDrop('right', $event)"
              >
                <div class="ear-illustration right">
                  <svg viewBox="0 0 100 150" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M30 30C30 20 35 10 50 10C65 10 70 20 70 30C70 35 72 40 72 45C72 50 70 55 68 60C66 65 64 70 64 75C64 85 66 95 60 100C54 105 45 105 40 100C35 95 32 85 32 75C32 70 30 65 28 60C26 55 24 50 24 45C24 40 26 35 30 30Z" stroke="currentColor" stroke-width="3" fill="none"/>
                    <ellipse cx="55" cy="50" rx="8" ry="12" stroke="currentColor" stroke-width="2" fill="none"/>
                  </svg>
                </div>
                <div class="ear-upload-content">
                  <h4>Right Ear<span v-if="requireRightDoc" class="required-mark"> *</span></h4>
                  <div class="upload-info">
                    <span v-if="!orderForm.rightImpressionDoc" class="upload-prompt">Click or drag file here</span>
                    <span v-else class="uploaded-filename">{{ orderForm.rightImpressionDoc.name }}</span>
                  </div>
                  <input
                    ref="rightFileInput"
                    id="rightImpressionDoc"
                    type="file"
                    @change="handleFileUpload('right', $event)"
                    accept=".pdf,.doc,.docx,.jpg,.jpeg,.png"
                    class="hidden-file-input"
                  >
                </div>
              </div>
                </div>
              </div>
            </div>

            <!-- Additional Notes (shown when method is selected or for existing patients) -->
            <div v-if="isImpressionMethodSelected || clientType === 'existing'" class="form-group">
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
              <template v-if="isSendingImpressions">
                <div class="highlight-note">
                  <span class="highlight-icon">📦</span>
                  <span class="highlight-text"><strong>Merci d’envoyer les empreintes en indiquant le numéro ID MO</strong></span>
                </div>
              </template>
              <template v-else>
                <p><strong>Right Impression:</strong> {{ orderForm.rightImpressionDoc?.name || 'Not uploaded' }}</p>
                <p><strong>Left Impression:</strong> {{ orderForm.leftImpressionDoc?.name || 'Not uploaded' }}</p>
              </template>
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
              <button class="back-to-products-btn" @click="backToProducts">
                Place a new order
              </button>
            </div>
          </div>
        </div>
        <div>
          <!-- empty div for grid management-->
        </div>
        <!-- Navigation Buttons -->
        <div class="checkout-button-container">
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
</template>

<script>
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
  name: 'DeciloCheckout',
  directives: {
    'click-outside': clickOutside
  },
  props: {
    selectedProduct: {
      type: Object,
      default: null
    },
    selectedVariants: {
      type: Object,
      default: () => ({})
    }
  },
  data() {
    return {
      orderStep: 0, // 0: product, 1: additional info, 2: documents, 3: review, 4: confirmation
      clientType: null, // 'new' or 'existing' - null means not selected yet
      impressionMethod: null, // 'scan' or 'ship' - null means not selected yet
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
      isSubmittingOrder: false,
      earImpressions: { left: { exists: false, filename: '' }, right: { exists: false, filename: '' } },
      earImpressionsLoading: false,
      earImpressionsError: '',
      isDraggingLeft: false,
      isDraggingRight: false,
      preloadedLeftDoc: null, // Pre-loaded document from existing patient
      preloadedRightDoc: null, // Pre-loaded document from existing patient
    }
  },
  computed: {
    selectedPatient() {
      return this.patientContacts.find(p => p.id === this.orderForm.patientId) || null;
    },

    isClientTypeSelected() {
      return this.clientType !== null;
    },

    isImpressionMethodSelected() {
      return this.impressionMethod !== null;
    },

    isPatientInfoValid() {
      if (this.clientType === 'existing') {
        return !!this.orderForm.patientId;
      } else if (this.clientType === 'new') {
        return !!(this.orderForm.patientFirstName && this.orderForm.patientLastName);
      }
      return false;
    },

    // Whether the Step 1 options include "Impression Paste - Scan 3D"
    isImpressionScan3D() {
      const values = Object.values(this.selectedVariants || {})
      console.log('values', values)
      return values.includes('Paste - 3D Scan')
    },

    // Whether the Step 1 options include "Paste - Sending ear impressions" (skip documents)
    isSendingImpressions() {
      const values = Object.values(this.selectedVariants || {})
      return values.includes('Paste - Sending ear impressions')
    },

    // Whether the Step 1 options include "With previous order" (force existing client flow)
    isWithPreviousOrder() {
      const values = Object.values(this.selectedVariants || {})
      return values.includes('From previous order')
    },

    // Resolve the selected Sides value from variants. Prefer attribute key 'Sides',
    // otherwise fall back to the first key whose name contains 'side'.
    selectedSides() {
      if (!this.selectedVariants) return null
      if (this.selectedVariants['Sides']) return this.selectedVariants['Sides']
      const sidesKey = Object.keys(this.selectedVariants).find(k => k && k.toLowerCase().includes('side'))
      return sidesKey ? this.selectedVariants[sidesKey] : null
    },

    // UI flags for which uploads to show and require
    showRightUpload() {
      if (!this.isImpressionScan3D) return false
      const s = (this.selectedSides || '').toLowerCase()
      return s === 'stereo' || s === 'mono r'
    },
    showLeftUpload() {
      if (!this.isImpressionScan3D) return false
      const s = (this.selectedSides || '').toLowerCase()
      return s === 'stereo' || s === 'mono l'
    },
    requireRightDoc() {
      return this.showRightUpload
    },
    requireLeftDoc() {
      return this.showLeftUpload
    }
  },
  watch: {
    selectedProduct: {
      handler(newProduct) {
        if (newProduct) {
          this.resetOrderForm();
          this.fetchPatientContacts();
        }
      },
      immediate: true
    }
    ,
    // React to variant changes to force Existing Client selection when "With previous order" is chosen
    selectedVariants: {
      handler() {
        if (this.isWithPreviousOrder) {
          this.clientType = 'existing'
        }
      },
      deep: true
    },
    orderStep(newVal) {
      // Load previous-order documents when entering Documents step with existing patient
      if (newVal === 2 && this.selectedPatient && this.clientType === 'existing') {
        this.fetchAndPreloadPatientDocs()
      }
    },
    impressionMethod(newVal) {
      // When user selects 'scan' method and has an existing patient, pre-load their documents
      if (newVal === 'scan' && this.selectedPatient && this.clientType === 'existing') {
        this.fetchAndPreloadPatientDocs()
      }
    }
  },
  methods: {
    handleBack() {
      if (this.orderStep === 0) {
        this.closeModal();
      } else {
        // If we skipped the documents step due to "Sending ear impressions", jump back two steps from review
        if (this.orderStep === 3 && this.isSendingImpressions) {
          this.orderStep -= 2;
        } else {
          this.orderStep--;
        }

        // If we returned to Product step, clear client type selection and patient data
        if (this.orderStep === 0) {
          if (this.isWithPreviousOrder) {
            // Force existing flow when "With previous order" is chosen
            this.clientType = 'existing'
          } else {
            this.clientType = null
          }
          // Always clear manual/selected patient when going back to product
          this.orderForm.patientId = null
          this.orderForm.patientFirstName = ''
          this.orderForm.patientLastName = ''
          this.patientValidationError = ''
        }

        // If we returned to Patient step, clear impression method and preloaded docs
        if (this.orderStep === 1) {
          this.impressionMethod = null
          this.orderForm.rightImpressionDoc = null
          this.orderForm.leftImpressionDoc = null
          this.preloadedLeftDoc = null
          this.preloadedRightDoc = null
        }
      }
    },

    nextStep() {
      // Initialize clientType when moving from Product -> Patient Information
      if (this.orderStep === 0) {
        if (this.isWithPreviousOrder) {
          this.clientType = 'existing'
        } else {
          this.clientType = null
        }
      }

      // Validate patient information only when trying to move from step 1 (Patient Information) to step 2 (Documents)
      if (this.orderStep === 1) {
        if (!this.isClientTypeSelected) {
          this.patientValidationError = 'Please select whether this is a new client or an existing client.';
          this.$emit('show-error', {
            message: this.patientValidationError,
            type: 'error'
          });
          return;
        }

        if (!this.isPatientInfoValid) {
          if (this.clientType === 'existing') {
            this.patientValidationError = 'Please select an existing patient.';
          } else {
            this.patientValidationError = 'Please provide both first and last name to create a new patient.';
          }
          this.$emit('show-error', {
            message: this.patientValidationError,
            type: 'error'
          });
          return;
        }

        // Do not skip the Documents step anymore when sending impressions; show a note in Step 3 instead
      }

      // Validate impression method selection when moving from Step 2 (Documents) to Step 3 (Review)
      if (this.orderStep === 2) {
        // For new patients, validate that they selected a method
        if (this.clientType !== 'existing' && !this.isImpressionMethodSelected) {
          this.$emit('show-error', { message: 'Please select how you would like to provide the ear impressions.', type: 'error' })
          return
        }

        // Validate documents if scan method is selected OR if it's an existing patient (auto-scan)
        if (this.impressionMethod === 'scan' || this.clientType === 'existing') {
          const docError = this.validateDocuments()
          if (docError) {
            this.$emit('show-error', { message: docError, type: 'error' })
            return
          }
        }
      }

      // Clear any existing validation error when proceeding successfully
      this.patientValidationError = '';

      if (this.orderStep === 3) {
        this.submitOrder();
      } else {
        this.orderStep++;
      }
    },
    validateDocuments() {
      // Only enforce when the 3D impression option is selected
      if (!this.isImpressionScan3D) {
        return ''
      }
      const s = (this.selectedSides || '').toLowerCase()
      if (s === 'stereo') {
        if (!this.orderForm.rightImpressionDoc || !this.orderForm.leftImpressionDoc) {
          return 'Please upload both right and left ear impression documents.'
        }
      } else if (s === 'mono r') {
        if (!this.orderForm.rightImpressionDoc) {
          return 'Please upload the right ear impression document.'
        }
      } else if (s === 'mono l') {
        if (!this.orderForm.leftImpressionDoc) {
          return 'Please upload the left ear impression document.'
        }
      }
      return ''
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

    triggerFileInput(side) {
      if (side === 'left') {
        this.$refs.leftFileInput.click();
      } else {
        this.$refs.rightFileInput.click();
      }
    },

    handleDrop(side, event) {
      if (side === 'left') {
        this.isDraggingLeft = false;
      } else {
        this.isDraggingRight = false;
      }
      
      const files = event.dataTransfer.files;
      if (files.length > 0) {
        const file = files[0];
        // Check file type
        const allowedTypes = ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'image/jpeg', 'image/png'];
        if (allowedTypes.includes(file.type) || file.name.match(/\.(pdf|doc|docx|jpg|jpeg|png)$/i)) {
          if (side === 'right') {
            this.orderForm.rightImpressionDoc = file;
          } else {
            this.orderForm.leftImpressionDoc = file;
          }
        }
      }
    },

    viewOrders() {
      this.$emit('go-to-orders');
      this.closeModal();
    },

    backToProducts() {
      this.closeModal();
    },

    resetOrderForm() {
      this.orderStep = 0;
      this.clientType = null;
      this.impressionMethod = null;
      this.orderForm = {
        notes: '',
        patientFirstName: '',
        patientLastName: '',
        patientId: null,
        rightImpressionDoc: null,
        leftImpressionDoc: null
      };
      this.preloadedLeftDoc = null;
      this.preloadedRightDoc = null;
    },

    closeModal() {
      this.$emit('close');
      this.resetOrderForm();
    },

    selectVariant(attribute, value) {
      this.$emit('variant-selected', { attribute, value });
    },

    isSelectedVariant(attribute, value) {
      return this.selectedVariants[attribute] === value
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

    selectClientType(type) {
      this.clientType = type;
      this.patientValidationError = '';

      // Reset form data when switching client types
      if (type === 'new') {
        this.orderForm.patientId = null;
        this.selectedPatient = null;
      } else if (type === 'existing') {
        this.orderForm.patientFirstName = '';
        this.orderForm.patientLastName = '';
      }
    },

    changeClientType() {
      this.clientType = null;
      this.patientValidationError = '';

      // Reset all form data when changing client type
      this.orderForm.patientId = null;
      this.orderForm.patientFirstName = '';
      this.orderForm.patientLastName = '';
      this.selectedPatient = null;
    },

    selectImpressionMethod(method) {
      this.impressionMethod = method;
    },

    changeImpressionMethod() {
      this.impressionMethod = null;
      // Reset uploaded documents when changing method
      this.orderForm.rightImpressionDoc = null;
      this.orderForm.leftImpressionDoc = null;
      this.preloadedLeftDoc = null;
      this.preloadedRightDoc = null;
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
    },

    async fetchEarImpressions() {
      try {
        this.earImpressionsLoading = true
        this.earImpressionsError = ''
        const token = localStorage.getItem('decilo_token')
        if (!token) throw new Error('Authentication required')
        const url = `/decilo-api/patient-ear-impressions?patient_id=${encodeURIComponent(this.selectedPatient.id)}`
        const res = await fetch(url, { headers: { 'Authorization': `Bearer ${token}` } })
        const body = await res.json().catch(() => ({}))
        if (!res.ok) {
          const patientName = this.selectedPatient?.name || ''
          this.earImpressionsError = body?.error || `The ear document associated with the following patient: ${patientName} could not be found`
          this.earImpressions = { left: { exists: false, filename: '' }, right: { exists: false, filename: '' } }
          return
        }
        this.earImpressions = body
      } catch (e) {
        const patientName = this.selectedPatient?.name || ''
        this.earImpressionsError = `The ear document associated with the following patient: ${patientName} could not be found`
        this.earImpressions = { left: { exists: false, filename: '' }, right: { exists: false, filename: '' } }
      } finally {
        this.earImpressionsLoading = false
      }
    },
    downloadEarUrl(side) {
      if (!this.selectedPatient) return '#'
      const params = new URLSearchParams({ patient_id: String(this.selectedPatient.id), side })
      return `/decilo-api/patient-ear-impressions/download?${params.toString()}`
    },
    async downloadEar(side) {
      try {
        const token = localStorage.getItem('decilo_token')
        if (!token) throw new Error('Authentication required')
        const url = this.downloadEarUrl(side)
        const res = await fetch(url, { headers: { 'Authorization': `Bearer ${token}` } })
        if (!res.ok) return
        const blob = await res.blob()
        const a = document.createElement('a')
        a.href = URL.createObjectURL(blob)
        a.download = side === 'left' ? (this.earImpressions.left?.filename || 'left_ear_impression') : (this.earImpressions.right?.filename || 'right_ear_impression')
        document.body.appendChild(a)
        a.click()
        a.remove()
      } catch (_) {
        // swallow
      }
    },

    async fetchAndPreloadPatientDocs() {
      try {
        this.earImpressionsLoading = true
        this.earImpressionsError = ''
        const token = localStorage.getItem('decilo_token')
        if (!token) throw new Error('Authentication required')
        
        const url = `/decilo-api/patient-ear-impressions?patient_id=${encodeURIComponent(this.selectedPatient.id)}`
        const res = await fetch(url, { headers: { 'Authorization': `Bearer ${token}` } })
        const body = await res.json().catch(() => ({}))
        
        if (!res.ok) {
          this.earImpressionsError = body?.error || 'Could not load patient documents'
          this.earImpressions = { left: { exists: false, filename: '' }, right: { exists: false, filename: '' } }
          return
        }
        
        this.earImpressions = body
        
        // Pre-load the documents into the upload fields
        if (body.left?.exists && body.left?.filename) {
          await this.preloadDocument('left', body.left.filename)
        }
        if (body.right?.exists && body.right?.filename) {
          await this.preloadDocument('right', body.right.filename)
        }
      } catch (e) {
        this.earImpressionsError = 'Could not load patient documents'
        this.earImpressions = { left: { exists: false, filename: '' }, right: { exists: false, filename: '' } }
      } finally {
        this.earImpressionsLoading = false
      }
    },

    async preloadDocument(side, filename) {
      try {
        const token = localStorage.getItem('decilo_token')
        if (!token) return
        
        const params = new URLSearchParams({ patient_id: String(this.selectedPatient.id), side })
        const url = `/decilo-api/patient-ear-impressions/download?${params.toString()}`
        const res = await fetch(url, { headers: { 'Authorization': `Bearer ${token}` } })
        
        if (!res.ok) return
        
        const blob = await res.blob()
        // Create a File object from the blob with the original filename
        const file = new File([blob], filename, { type: blob.type })
        
        // Assign to the appropriate form field and preloaded property
        if (side === 'left') {
          this.preloadedLeftDoc = file
          this.orderForm.leftImpressionDoc = file
        } else {
          this.preloadedRightDoc = file
          this.orderForm.rightImpressionDoc = file
        }
      } catch (e) {
        console.error(`Failed to preload ${side} document:`, e)
      }
    },
  }
}
</script>

<style scoped>
/* Fullscreen styles */
.fullscreen-checkout {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: var(--secondary-color);
  z-index: 1000;
  overflow-y: auto;
  padding: 20px;
}

.back-btn-header {
  position: absolute;
  top: 20px;
  left: 20px;
  background: var(--secondary-color);
  border: 1px solid #475569;
  border-radius: 10px;
  color: #ffffff;
  font-size: 14px;
  padding: 12px 16px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  backdrop-filter: blur(8px);
  z-index: 10;
}

.back-btn-header:hover {
  background: rgba(239, 68, 68, 0.8);
  border-color: #ef4444;
  transform: translateY(-2px);
}

.back-btn-header svg {
  width: 16px;
  height: 16px;
}

.modal-product-details {
  overflow: hidden;
  max-height: 100%;
  display: grid;
  grid-template-columns: minmax(0, 30%) minmax(0, 1fr);
  gap: 32px;
  min-height: calc(100vh - 200px);
  padding: 32px;
  padding-top: 120px;
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
  background: var(--secondary-color);
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
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin: 0;
  padding: 20px 250px;
  padding-right: 100px;
  background: var(--secondary-color);
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
  background: #10b981;
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
  background: var(--secondary-color);
  margin-bottom: 8px;
  font-weight: 600;
  font-size: 14px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.progress-step.active .step-number {
  border-color: #ffffff;
  background: #ffffff;
  color: #000000;
  box-shadow: 0 0 20px rgba(255, 255, 255, 0.5);
  transform: scale(1.1);
}

.progress-line {
  flex: 1;
  height: 3px;
  background: rgba(255, 255, 255, 0.1);
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
  background: #ffffff;
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
  background: var(--secondary-color);
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

/* Highlight note for sending impressions */
.highlight-note {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  background: rgba(16, 185, 129, 0.12);
  border: 1px solid rgba(16, 185, 129, 0.5);
  border-radius: 10px;
  color: #d1fae5;
  font-size: 14px;
  font-weight: 600;
  box-shadow:
    0 0 0 3px rgba(16, 185, 129, 0.08),
    inset 0 1px 0 rgba(255, 255, 255, 0.05);
}

.highlight-icon {
  font-size: 18px;
}

.highlight-text {
  line-height: 1.4;
}

/* Info notes for document status */
.info-note {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 18px;
  border-radius: 10px;
  font-size: 14px;
  font-weight: 500;
  box-shadow:
    0 0 0 3px rgba(255, 255, 255, 0.05),
    inset 0 1px 0 rgba(255, 255, 255, 0.05);
}

.info-note.success {
  background: rgba(16, 185, 129, 0.12);
  border: 1px solid rgba(16, 185, 129, 0.5);
  color: #d1fae5;
}

.info-note.warning {
  background: rgba(245, 158, 11, 0.12);
  border: 1px solid rgba(245, 158, 11, 0.5);
  color: #fde68a;
}

.info-note.error {
  background: rgba(239, 68, 68, 0.12);
  border: 1px solid rgba(239, 68, 68, 0.5);
  color: #fecaca;
}

.info-icon {
  font-size: 20px;
  flex-shrink: 0;
}

.info-text {
  line-height: 1.5;
  flex: 1;
}

/* Existing documents minimalist links */
.existing-docs-list {
  list-style: none;
  padding-left: 0;
  display: grid;
  gap: 10px;
}

.existing-docs-list li {
  display: flex;
  align-items: center;
  gap: 10px;
  color: #e2e8f0;
}

.doc-link {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border: 1px solid #334155;
  border-radius: 10px;
  background: rgba(30, 41, 59, 0.6);
  color: #ffffff;
  text-decoration: none;
  transition: all 0.2s ease;
}

.doc-link:hover {
  border-color: #475569;
  background: rgba(30, 41, 59, 0.8);
  transform: translateY(-1px);
}

.doc-icon svg {
  width: 18px;
  height: 18px;
}

.doc-filename {
  font-weight: 600;
  font-size: 13px;
}

/* Ear Upload Container */
.ear-upload-container {
  display: flex;
  justify-content: center;
  gap: 32px;
  margin-top: 24px;
  margin-bottom: 24px;
}

.ear-upload-box {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 24px 20px;
  border: 3px solid;
  border-radius: 16px;
  background: var(--secondary-color);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  cursor: pointer;
  min-height: 280px;
  width: 220px;
  max-width: 220px;
  justify-content: center;
}

.ear-upload-box.left-ear {
  border-color: rgba(59, 130, 246, 0.5);
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.05), rgba(59, 130, 246, 0.02));
}

.ear-upload-box.right-ear {
  border-color: rgba(239, 68, 68, 0.5);
  background: linear-gradient(135deg, rgba(239, 68, 68, 0.05), rgba(239, 68, 68, 0.02));
}

.ear-upload-box.left-ear:hover {
  border-color: rgba(59, 130, 246, 0.8);
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.08), rgba(59, 130, 246, 0.04));
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(59, 130, 246, 0.2);
}

.ear-upload-box.right-ear:hover {
  border-color: rgba(239, 68, 68, 0.8);
  background: linear-gradient(135deg, rgba(239, 68, 68, 0.08), rgba(239, 68, 68, 0.04));
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(239, 68, 68, 0.2);
}

.ear-upload-box.has-file.left-ear {
  border-color: rgba(59, 130, 246, 1);
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.12), rgba(59, 130, 246, 0.06));
}

.ear-upload-box.has-file.right-ear {
  border-color: rgba(239, 68, 68, 1);
  background: linear-gradient(135deg, rgba(239, 68, 68, 0.12), rgba(239, 68, 68, 0.06));
}

.ear-upload-box.dragging.left-ear {
  border-color: rgba(59, 130, 246, 1);
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.15), rgba(59, 130, 246, 0.08));
  transform: scale(1.02);
}

.ear-upload-box.dragging.right-ear {
  border-color: rgba(239, 68, 68, 1);
  background: linear-gradient(135deg, rgba(239, 68, 68, 0.15), rgba(239, 68, 68, 0.08));
  transform: scale(1.02);
}

.ear-illustration {
  width: 100px;
  height: 150px;
  margin-bottom: 24px;
  transform: scaleX(-1);
}

.ear-illustration.left {
  color: rgba(59, 130, 246, 0.8);
}

.ear-illustration.right {
  color: rgba(239, 68, 68, 0.8);
}

.ear-illustration svg {
  width: 100%;
  height: 100%;
}

.ear-upload-content {
  text-align: center;
  width: 100%;
}

.ear-upload-content h4 {
  color: #ffffff;
  margin: 0 0 16px 0;
  font-size: 18px;
  font-weight: 600;
}

.required-mark {
  color: #ef4444;
  margin-left: 4px;
}

.upload-info {
  margin-top: 16px;
  text-align: center;
}

.upload-prompt {
  color: #94a3b8;
  font-size: 14px;
  font-weight: 500;
  display: block;
}

.uploaded-filename {
  color: #10b981;
  font-size: 13px;
  font-weight: 600;
  word-break: break-word;
}

.hidden-file-input {
  display: none;
}


/* Patient Selection Container */
.patient-selection-container {
  display: flex;
  gap: 16px;
  align-items: stretch;
}

/* Custom Dropdown Styles */
.custom-dropdown {
  position: relative;
  flex: 1;
  min-width: 0;
}

.dropdown-trigger {
  width: 80%;
  position: relative;
  display: flex;
  align-items: center;
  padding: 12px 16px;
  background: var(--secondary-color);
  border: 2px solid #334155;
  border-radius: 12px;
  color: #ffffff;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.dropdown-trigger:hover {
  border-color: #475569;
  background: var(--secondary-color);
}

.dropdown-trigger.has-selection {
  border: 1px solid white;
  color: white;
  background: var(--secondary-color);
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
  width: 100%;
  position: absolute;
  top: calc(100% + 8px);
  left: 0;
  right: 0;
  background: var(--secondary-color);
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
  background: var(--secondary-color);
}

.dropdown-option.is-selected {
  background: var(--primary-color);
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
  background: #334155;
}

.form-divider span {
  background: var(--secondary-color);
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
  background: var(--primary-color);
}

.patient-or-divider span {
  background: var(--secondary-color);
  padding: 0 24px;
  position: relative;
  z-index: 1;
  border: 2px solid var(--primary-color);
  border-radius: 8px;
}

/* Create Patient Section */
.create-patient-section {
  background: var(--secondary-color);
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
  width: 80%;
}

.file-upload input[type="file"] {
  width: 100%;
  box-sizing: border-box;
  padding: 16px 20px;
  background: var(--secondary-color);
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
  background: var(--secondary-color);
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
  width: fit-content;
}

/* Confirmation Styles */
.confirmation {
  text-align: center;
  padding: 60px 40px;
}

.confirmation-content {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.confirmation h2 {
  margin-bottom: 20px;
  color: #ffffff;
  font-size: 28px;
  font-weight: 700;
}

.confirmation p {
  color: #10b981;
  margin-bottom: 48px;
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
  background: #000000;
  color: #ffffff;
  border: 2px solid #ffffff;
  border-radius: 12px;
  cursor: pointer;
  font-weight: 600;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  margin-bottom: 24px;
}

.view-orders-btn:hover {
  background: #ffffff;
  color: #000000;
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(255, 255, 255, 0.3);
}

.back-to-products-btn {
  padding: 12px 24px;
  background: transparent;
  color: #ffffff;
  border: 2px solid #64748b;
  border-radius: 12px;
  cursor: pointer;
  font-weight: 600;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.back-to-products-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  border-color: #ffffff;
  transform: translateY(-2px);
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
  background: #000000;
  color: #ffffff;
  border: 2px solid #ffffff;
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
  background: #ffffff;
  color: #000000;
  border-color: #ffffff;
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(255, 255, 255, 0.3);
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

.checkout-button-container {
  position: sticky;
  bottom: 0;
  left: 32px;
  right: 32px;
  padding: 24px 0;
  display: flex;
  justify-content: space-between;
  align-items: center;
  z-index: 3;
  padding: 0 20px;
}

.order-btn.large {
  padding: 18px 40px;
  font-size: 16px;
  font-weight: 600;
  min-width: 160px;
  border-radius: 16px;
  background: #000000;
  color: #ffffff;
  border: 2px solid #ffffff;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  position: relative;
  overflow: hidden;
  backdrop-filter: blur(8px);
}

.order-btn.large::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  transition: left 0.5s ease;
}

.order-btn.large:hover::before {
  left: 100%;
}

.order-btn.large:hover {
  background: #ffffff;
  color: #000000;
  border-color: #ffffff;
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(255, 255, 255, 0.3);
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

/* Responsive Design */
@media (max-width: 1024px) {
  .modal-content {
    max-width: 90%;
    overflow-y: auto;
    overflow-x: hidden;
  }

  .modal-product-details {
    max-height: 100%;
    gap: 24px;
    padding: 24px;
    padding-top: 75px;
  }
}

@media (max-width: 768px) {
  .fullscreen-checkout {
    padding: 12px;
  }

  .back-btn-header {
    top: 15px;
    left: 15px;
  }

  .patient-selection-container {
    flex-direction: column;
    gap: 12px;
  }

  .modal-product-details {
    max-height: 100%;
    grid-template-columns: 1fr;
    gap: 18px;
    min-height: calc(100vh - 180px);
    padding: 18px;
    padding-top: 80px;
    box-sizing: border-box;
  }

  .order-progress {
    display: none;
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
    background: rgba(255, 255, 255, 0.1);
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

  .checkout-button-container {
    position: sticky;
    bottom: 0;
    left: 18px;
    right: 18px;
    padding: 20px 0;
    background: var(--secondary-color);
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
}

@media (max-width: 480px) {
  .fullscreen-checkout {
    padding: 8px;
  }

  .modal-product-details {
    max-height: 100%;
    padding: 14px;
    padding-top: 75px;
    min-height: calc(100vh - 140px);
    box-sizing: border-box;
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
    background: rgba(255, 255, 255, 0.1);
  }

  .modal-product-image {
    height: auto;
    min-height: 150px;
    max-height: 250px;
    padding: 12px;
  }

  .checkout-button-container {
    position: sticky;
    bottom: 0;
    left: 14px;
    right: 14px;
    padding: 14px 0;
    background: var(--secondary-color);
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
}

/* Client Type Selection Styles */
.client-type-selection {
  text-align: center;
  padding: 40px 20px;
}

.client-type-selection h3 {
  color: #ffffff;
  margin-bottom: 32px;
  font-size: 18px;
  font-weight: 600;
}

.client-type-buttons {
  display: flex;
  gap: 24px;
  justify-content: center;
  max-width: 600px;
  margin: 0 auto;
}

.client-type-btn {
  flex: 1;
  max-width: 280px;
  padding: 32px 24px;
  background: var(--secondary-color);
  border: 2px solid #334155;
  border-radius: 16px;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  text-align: center;
  position: relative;
  overflow: hidden;
}

.client-type-btn:hover {
  border-color: #475569;
  background: var(--secondary-color);
  transform: translateY(-4px);
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.3);
}

.client-type-btn.active {
  border-color: var(--primary-color);
  background: var(--primary-color);
  box-shadow: 0 0 20px rgba(59, 130, 246, 0.3);
}

.client-type-icon {
  width: 48px;
  height: 48px;
  margin: 0 auto 16px;
  color: #64748b;
  transition: color 0.3s ease;
}

.client-type-btn.active .client-type-icon {
  color: #ffffff;
}

.client-type-content h4 {
  color: #ffffff;
  margin: 0 0 8px 0;
  font-size: 16px;
  font-weight: 600;
}

.client-type-content p {
  color: #94a3b8;
  margin: 0;
  font-size: 14px;
  line-height: 1.4;
}

.client-type-btn.active .client-type-content h4,
.client-type-btn.active .client-type-content p {
  color: #ffffff;
}

/* Client Type Header */
.client-type-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.client-type-header h3 {
  color: #ffffff;
  margin: 0;
  font-size: 16px;
  font-weight: 600;
}

.change-client-type-btn {
  padding: 8px 16px;
  background: transparent;
  border: 1px solid #64748b;
  border-radius: 8px;
  color: #94a3b8;
  cursor: pointer;
  font-size: 12px;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.change-client-type-btn:hover {
  border-color: #ffffff;
  color: #ffffff;
  background: rgba(255, 255, 255, 0.1);
}

/* Impression Method Selection Styles */
.impression-method-selection {
  text-align: center;
  padding: 40px 20px;
}

.impression-method-selection h3 {
  color: #ffffff;
  margin-bottom: 32px;
  font-size: 18px;
  font-weight: 600;
}

.impression-method-buttons {
  display: flex;
  gap: 24px;
  justify-content: center;
  max-width: 600px;
  margin: 0 auto;
}

.impression-method-btn {
  flex: 1;
  max-width: 280px;
  padding: 32px 24px;
  background: var(--secondary-color);
  border: 2px solid #334155;
  border-radius: 16px;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  text-align: center;
  position: relative;
  overflow: hidden;
}

.impression-method-btn:hover {
  border-color: #475569;
  background: var(--secondary-color);
  transform: translateY(-4px);
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.3);
}

.impression-method-btn.active {
  border-color: var(--primary-color);
  background: var(--primary-color);
  box-shadow: 0 0 20px rgba(59, 130, 246, 0.3);
}

.impression-method-icon {
  width: 48px;
  height: 48px;
  margin: 0 auto 16px;
  color: #64748b;
  transition: color 0.3s ease;
}

.impression-method-btn.active .impression-method-icon {
  color: #ffffff;
}

.impression-method-content h4 {
  color: #ffffff;
  margin: 0 0 8px 0;
  font-size: 16px;
  font-weight: 600;
}

.impression-method-content p {
  color: #94a3b8;
  margin: 0;
  font-size: 14px;
  line-height: 1.4;
}

.impression-method-btn.active .impression-method-content h4,
.impression-method-btn.active .impression-method-content p {
  color: #ffffff;
}

/* Impression Method Header */
.impression-method-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.impression-method-header h3 {
  color: #ffffff;
  margin: 0;
  font-size: 16px;
  font-weight: 600;
}

.change-impression-method-btn {
  padding: 8px 16px;
  background: transparent;
  border: 1px solid #64748b;
  border-radius: 8px;
  color: #94a3b8;
  cursor: pointer;
  font-size: 12px;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.change-impression-method-btn:hover {
  border-color: #ffffff;
  color: #ffffff;
  background: rgba(255, 255, 255, 0.1);
}

/* Patient Search Styles */
  .patient-search-container {
    position: relative;
    flex: 1;
    min-width: unset;
  }

.patient-search-input {
  width: 100%;
  padding: 12px 40px 12px 16px;
  border: 2px solid #334155;
  border-radius: 12px;
  font-size: 14px;
  background-color: var(--secondary-color);
  color: #ffffff;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.patient-search-input:focus {
  outline: none;
  border-color: var(--primary-color);
  box-shadow:
    0 0 0 4px rgba(59, 130, 246, 0.15),
    0 8px 32px rgba(59, 130, 246, 0.12);
  transform: translateY(-2px);
}

.patient-search-input::placeholder {
  color: #64748b;
  font-weight: 400;
}

.patient-search-icon {
  position: absolute;
  right: 12px;
  top: 50%;
  transform: translateY(-50%);
  width: 20px;
  height: 20px;
  color: #64748b;
  pointer-events: none;
}
</style>
