<template>
  <!-- Product Details Fullscreen -->
  <div v-if="selectedProduct" class="fullscreen-checkout">
    <button class="back-btn-header" @click="closeModal">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M19 12H5M12 19l-7-7 7-7"/>
      </svg>
      {{ $t('checkout.backToProducts') }}
    </button>
      <!-- Progress Bar: fixed at top of modal -->
      <div class="order-progress">
        <div class="progress-step" :class="{ active: orderStep >= 0, completed: orderStep > 0 }">
          <div class="step-number">1</div>
          <span>{{ $t('checkout.step.product') }}</span>
        </div>
        <div class="progress-line" :class="{ active: orderStep > 0 }"></div>
        <div class="progress-step" :class="{ active: orderStep >= 1, completed: orderStep > 1 }">
          <div class="step-number">2</div>
          <span>{{ $t('checkout.step.patient') }}</span>
        </div>
        <div class="progress-line" :class="{ active: orderStep > 1 }"></div>
        <div class="progress-step" :class="{ active: orderStep >= 2, completed: orderStep > 2 }">
          <div class="step-number">3</div>
          <span>{{ $t('checkout.step.earImpressions') }}</span>
        </div>
        <div class="progress-line" :class="{ active: orderStep > 2 }"></div>
        <div class="progress-step" :class="{ active: orderStep >= 3, completed: orderStep > 3 }">
          <div class="step-number">4</div>
          <span>{{ $t('checkout.step.review') }}</span>
        </div>
        <div class="progress-line" :class="{ active: orderStep > 3 }"></div>
        <div class="progress-step" :class="{ active: orderStep >= 4 }">
          <div class="step-number">5</div>
          <span>{{ $t('checkout.step.confirm') }}</span>
        </div>
      </div>
      <div class="modal-product-details">
        <div class="modal-product-image">
          <div class="image-frame" :class="{ 'is-loading': isImageLoading }">
            <img
              v-show="activeImageUrl"
              :src="activeImageUrl"
              :alt="selectedProduct.name"
              @load="onImageLoaded"
              @error="onImageError"
            >
            <div v-if="isImageLoading" class="image-loading-overlay">
              <div class="loading-spinner-large"></div>
            </div>
          </div>
        </div>
        <div class="modal-product-info">

          <!-- Step 1: Product Selection -->
          <div v-if="orderStep === 0" class="order-step">
            <h2>{{ selectedProduct.name }}</h2>
            <p class="full-description">{{ selectedProduct.full_description }}</p>
            <div v-if="isDetailLoading" class="detail-loading">
              <div class="loading-spinner-small"></div>
              <span>{{ $t('checkout.loadingOptions') }}</span>
            </div>
            <div v-if="selectedProduct.specifications && selectedProduct.specifications.length > 0" class="specifications">
              <h3>{{ $t('checkout.specifications') }}</h3>
              <ul>
                <li v-for="(spec, index) in selectedProduct.specifications" :key="index">
                  {{ spec }}
                </li>
              </ul>
            </div>

            <!-- Product Variants -->
            <div v-if="filteredVariants.length > 0" class="variants-section">
              <h3>{{ $t('checkout.availableOptions') }}</h3>
              <div class="variant-groups">
                <div v-for="variant in filteredVariants" :key="variant.attribute" class="variant-group">
                  <h4>{{ variant.attribute }}</h4>
                  <div class="variant-options">
                    <button
                      v-for="value in variant.values"
                      :key="value"
                      class="variant-btn"
                      :class="{ active: isSelectedVariant(variant.attribute, value), disabled: isServerValueDisabled(variant.attribute, value) }"
                      :disabled="isServerValueDisabled(variant.attribute, value)"
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
            <h2>{{ $t('checkout.patientInformation') }}</h2>

            <!-- Patient Validation Error Message -->
            <div v-if="patientValidationError" class="patient-validation-error">
              {{ patientValidationError }}
            </div>


            <!-- Client Type Selection (if not selected yet) -->
            <div v-if="!isClientTypeSelected" class="client-type-selection">
              <h3>{{ $t('checkout.clientTypePrompt') }}</h3>
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
                    <h4>{{ $t('checkout.newPatient') }}</h4>
                    <p>{{ $t('checkout.newPatientDescription') }}</p>
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
                    <h4>{{ $t('checkout.existingPatient') }}</h4>
                    <p>{{ $t('checkout.existingPatientDescription') }}</p>
                  </div>
                </button>
              </div>
            </div>

            <!-- Existing Client Selection -->
            <div v-else-if="clientType === 'existing'" class="existing-client-section">
              <div class="client-type-header">
                <h3>{{ $t('checkout.existingPatient') }}</h3>
                <button class="change-client-type-btn" @click="changeClientType">
                  {{ $t('checkout.changeToNewPatient') }}
                </button>
              </div>

              <!-- Patient Selection -->
              <div class="form-group">
                <label for="patientSelect">{{ $t('checkout.selectExistingPatient') }}</label>

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
                        <span v-else class="placeholder">{{ $t('checkout.chooseExistingPatient') }}</span>
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
                        <span>{{ $t('checkout.loadingPatients') }}</span>
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
                              <span v-if="patient.email">{{ $t('checkout.email') }}: {{ patient.email }}</span>
                              <span v-if="patient.phone">{{ $t('checkout.phone') }}: {{ patient.phone }}</span>
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
                          <p>{{ $t('checkout.noPatientsFound') }}</p>
                          <small>{{ $t('checkout.addNewPatientInstruction') }}</small>
                        </div>
                      </div>
                    </div>
                  </div>

                  <!-- Patient Search Bar -->
                  <div class="patient-search-container">
                    <input
                      v-model="patientSearchQuery"
                      type="text"
                      :placeholder="$t('checkout.searchPatientsPlaceholder')"
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
                <h3>{{ $t('checkout.newPatient') }}</h3>
                <button class="change-client-type-btn" @click="changeClientType">
                  {{ $t('checkout.changeToExistingPatient') }}
                </button>
              </div>

              <!-- Create New Patient Section -->
              <div class="create-patient-section">
                <div class="form-row">
                  <div class="form-group">
                    <label for="patientFirstName">{{ $t('checkout.firstName') }} *</label>
                    <input
                      id="patientFirstName"
                      v-model="orderForm.patientFirstName"
                      type="text"
                      :placeholder="$t('checkout.firstNamePlaceholder')"
                      @input="clearPatientValidationError"
                    >
                  </div>
                  <div class="form-group">
                    <label for="patientLastName">{{ $t('checkout.lastName') }} *</label>
                    <input
                      id="patientLastName"
                      v-model="orderForm.patientLastName"
                      type="text"
                      :placeholder="$t('checkout.lastNamePlaceholder')"
                      @input="clearPatientValidationError"
                    >
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Step 3: Document Upload -->
          <div v-if="orderStep === 2" class="order-step">
            <h2>{{ $t('checkout.earImpressionsTitle') }}</h2>

            <!-- Impression Method Selection (only for new patients, if not selected yet) -->
            <div v-if="!isImpressionMethodSelected && clientType !== 'existing'" class="impression-method-selection">
              <h3>{{ $t('checkout.impressionQuestion') }}</h3>
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
                    <h4>{{ $t('checkout.impressionScanTitle') }}</h4>
                    <p>{{ $t('checkout.impressionScanSubtitle') }}</p>
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
                    <h4>{{ $t('checkout.impressionShipTitle') }}</h4>
                    <p>{{ $t('checkout.impressionShipSubtitle') }}</p>
                  </div>
                </button>
              </div>
            </div>

            <!-- Content when impression method is selected OR existing patient (auto-scan) -->
            <div v-else-if="isImpressionMethodSelected || clientType === 'existing'">
              <!-- Method header with option to change (only for new patients) -->
              <div v-if="clientType !== 'existing'" class="impression-method-header">
                <h3>{{ impressionMethod === 'scan' ? $t('checkout.impressionScanTitle') : $t('checkout.impressionShipTitle') }}</h3>
                <button class="change-impression-method-btn" @click="changeImpressionMethod">
                  {{ $t('checkout.changeMethod') }}
                </button>
              </div>

              <!-- Shipping method: show message (only for new patients who chose shipping) -->
              <div v-if="impressionMethod === 'ship'" class="form-group">
                <div class="highlight-note">
                  <span class="highlight-icon">📦</span>
                  <span class="highlight-text"><strong>{{ $t('checkout.shipInstruction') }}</strong></span>
                </div>
              </div>

              <!-- Sending impressions method: show message (Paste - Sending ear impressions variant) -->
              <div v-else-if="isSendingImpressions" class="form-group">
                <div class="highlight-note">
                  <span class="highlight-icon">📦</span>
                  <span class="highlight-text"><strong>{{ $t('checkout.shipInstruction') }}</strong></span>
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
                      <span class="info-text"><strong>{{ $t('checkout.docsFound', { name: selectedPatient?.name || '' }) }}</strong> - {{ $t('checkout.docsLoaded') }}</span>
                    </div>
                    <div v-else class="info-note warning">
                      <span class="info-icon">ℹ️</span>
                      <span class="info-text"><strong>{{ $t('checkout.noDocsFound', { name: selectedPatient?.name || '' }) }}</strong> - {{ $t('checkout.docsUploadPrompt') }}</span>
                    </div>
                  </div>

                  <!-- Loading spinner for existing patients -->
                  <div v-if="clientType === 'existing' && earImpressionsLoading" class="form-group">
                    <div class="dropdown-loading">
                      <div class="loading-spinner-small"></div>
                      <span>{{ $t('checkout.loadingDocuments') }}</span>
                    </div>
                  </div>

                <!-- Conditionally render impression uploads for 3D scan or previous order -->
                <upload-ear-impressions
                  v-if="isImpressionScan3D || isWithPreviousOrder"
                  :left-impression-doc="orderForm.leftImpressionDoc"
                  :right-impression-doc="orderForm.rightImpressionDoc"
                  :show-left-upload="showLeftUpload"
                  :show-right-upload="showRightUpload"
                  :require-left-doc="requireLeftDoc"
                  :require-right-doc="requireRightDoc"
                  :disabled="clientType === 'existing' && earImpressionsLoading"
                  @file-upload="handleFileUploadFromComponent"
                ></upload-ear-impressions>
              </div>
            </div>

            <!-- Additional Notes (shown when method is selected or for existing patients) -->
            <div v-if="isImpressionMethodSelected || clientType === 'existing'" class="form-group">
              <label for="notes">{{ $t('checkout.additionalNotes') }}</label>
              <textarea
                id="notes"
                v-model="orderForm.notes"
                :placeholder="$t('checkout.additionalNotesPlaceholder')"
                rows="4"
              ></textarea>
            </div>
          </div>

          <!-- Step 4: Review -->
          <div v-if="orderStep === 3" class="order-step review">
            <h2>{{ $t('checkout.reviewTitle') }}</h2>
            <div class="review-section">
              <h3>{{ $t('checkout.review.product') }}</h3>
              <p><strong>{{ $t('checkout.review.nameLabel') }}</strong> {{ selectedProduct?.name }}</p>
              <p><strong>{{ $t('checkout.review.descriptionLabel') }}</strong> {{ selectedProduct?.full_description }}</p>
            </div>
            <div class="review-section" v-if="Object.keys(selectedVariants).length">
              <h3>{{ $t('checkout.review.selectedOptions') }}</h3>
              <ul>
                <li v-for="(value, attribute) in selectedVariants" :key="attribute">
                  <strong>{{ attribute }}:</strong> {{ value }}
                </li>
              </ul>
            </div>
            <div class="review-section">
              <h3>{{ $t('checkout.review.patientInfo') }}</h3>
              <p><strong>{{ $t('checkout.review.nameLabel') }}</strong> {{ selectedPatient ? selectedPatient.name : ((orderForm.patientFirstName && orderForm.patientLastName) ? (orderForm.patientFirstName + ' ' + orderForm.patientLastName) : (orderForm.patientFirstName || orderForm.patientLastName || '—')) }}</p>
              <p><strong>{{ $t('checkout.review.notesLabel') }}</strong> {{ orderForm.notes || '—' }}</p>
            </div>
            <div class="review-section">
              <h3>{{ $t('checkout.review.documents') }}</h3>
              <template v-if="isSendingImpressions">
                <div class="highlight-note">
                  <span class="highlight-icon">📦</span>
                  <span class="highlight-text"><strong>{{ $t('checkout.shipInstruction') }}</strong></span>
                </div>
              </template>
              <template v-else>
                <p><strong>{{ $t('checkout.review.rightImpression') }}</strong> {{ orderForm.rightImpressionDoc?.name || $t('checkout.review.notUploaded') }}</p>
                <p><strong>{{ $t('checkout.review.leftImpression') }}</strong> {{ orderForm.leftImpressionDoc?.name || $t('checkout.review.notUploaded') }}</p>
              </template>
            </div>
          </div>

          <!-- Step 5: Confirmation -->
          <div v-if="orderStep === 4" class="order-step confirmation">
            <div class="confirmation-content">
              <h2>{{ $t('checkout.confirmationTitle') }}</h2>
              <p>{{ $t('checkout.confirmationMessage') }}</p>
              <button class="confirmation-btn" @click="viewOrders">
                {{ $t('checkout.confirmationSeeOrders') }}
              </button>
              <button class="confirmation-btn" @click="backToProducts">
                {{ $t('checkout.confirmationNewOrder') }}
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
            {{ $t('checkout.back') }}
          </button>
          <button
            v-if="orderStep < 4"
            class="order-btn large"
            :disabled="isSubmittingOrder || (orderStep === 0 && isForbiddenByServer)"
            @click="nextStep"
          >
            <div v-if="orderStep === 3 && isSubmittingOrder" class="button-loader">
              <div class="spinner"></div>
            </div>
            <span v-else>
              {{ orderStep === 3 ? $t('checkout.placeOrder') : $t('checkout.next') }}
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

// Client-side cache for variant images (persists for the session)
const variantImageCache = new Map();

function getVariantCacheKey(productId, variantKey, size) {
  return `${productId}::${variantKey}::${size}`;
}

import UploadEarImpressions from './upload_ear_impressions.vue';

export default {
  name: 'DeciloCheckout',
  components: {
    UploadEarImpressions
  },
  directives: {
    'click-outside': clickOutside
  },
  props: {
    selectedProduct: {
      type: Object,
      default: null
    },
    isDetailLoading: {
      type: Boolean,
      default: false
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
      preloadedLeftDoc: null, // Pre-loaded document from existing patient
      preloadedRightDoc: null, // Pre-loaded document from existing patient
      // Server-side variant exclusions for the selected product
      variantExclusions: [],
      variantExclusionsLoading: false,
      variantExclusionsError: '',
      pendingExclusionsProductId: null,
      activeImageUrl: '',
      isImageLoading: true,
      activeImageRequestId: 0,
      imageRequestId: 0,
      lastImageVariantKey: '',
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

    // Whether the Step 2 options include "Impression Paste - Scan 3D"
    isImpressionScan3D() {
      const values = Object.values(this.selectedVariants || {})
      console.log('values', values)
      return values.includes('Paste - 3D Scan')
    },

    // Whether the Step 2 options include "Paste - Sending ear impressions" (skip documents)
    isSendingImpressions() {
      const values = Object.values(this.selectedVariants || {})
      return values.includes('Paste - Sending ear impressions')
    },

    // Whether the Step 2 options include "With previous order" (force existing client flow)
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
      if (!this.isImpressionScan3D && !this.isWithPreviousOrder) return false
      const s = (this.selectedSides || '').toLowerCase()
      return s === 'stereo' || s === 'mono r'
    },
    showLeftUpload() {
      if (!this.isImpressionScan3D && !this.isWithPreviousOrder) return false
      const s = (this.selectedSides || '').toLowerCase()
      return s === 'stereo' || s === 'mono l'
    },
    requireRightDoc() {
      return this.showRightUpload
    },
    requireLeftDoc() {
      return this.showLeftUpload
    },

    // Filter out Ear Impression Type variants from display since they're auto-selected
    filteredVariants() {
      if (!this.selectedProduct || !this.selectedProduct.variants) return []
      return this.selectedProduct.variants.filter(variant =>
        !(variant.attribute === 'Ear Impression Type' ||
          variant.attribute.toLowerCase().includes('ear impression'))
      )
    },

    // Flatten current selected values to names array
    selectedValueNames() {
      const vals = Object.values(this.selectedVariants || {})
      return vals.filter(v => typeof v === 'string' && v.trim().length > 0)
    },

    // True if the current selected variant combination matches any server-declared exclusion by name
    isForbiddenByServer() {
      try {
        if (!this.selectedProduct || !Array.isArray(this.variantExclusions) || this.variantExclusions.length === 0) return false
        return this.checkForbiddenForValues(this.selectedValueNames)
      } catch (_) {
        return false
      }
    }
  },
  watch: {
    selectedProduct: {
      handler(newProduct, oldProduct) {
        // Only reset the form when the checkout is first opened (null -> product)
        // Don't reset when the same product's properties are updated (e.g., image_url changes)
        const isFirstOpen = !oldProduct && newProduct;

        if (newProduct) {
          this.imageRequestId += 1;
          this.lastImageVariantKey = '';

          if (isFirstOpen) {
            this.activeImageUrl = '';
            this.isImageLoading = true;
            this.resetOrderForm();
            this.variantExclusions = Array.isArray(newProduct?.exclusions) ? newProduct.exclusions : [];
            this.variantExclusionsLoading = false;
            this.variantExclusionsError = '';
            this.pendingExclusionsProductId = Array.isArray(newProduct?.exclusions) ? null : newProduct.id;

            // Fast path: if we have prefetched variant ID, fetch image directly (1 RPC)
            const variantId = newProduct.default_variant_product_id;
            if (variantId) {
              // Capture request ID to detect if user selected a different variant before this resolves
              const prefetchRequestId = this.imageRequestId;
              this.fetchImageByVariantId(variantId, 'medium').then((imageUrl) => {
                // Only apply if no variant selection happened since we started
                if (imageUrl && this.selectedProduct?.id === newProduct.id && prefetchRequestId === this.imageRequestId) {
                  this.activeImageUrl = imageUrl;
                  this.isImageLoading = false;
                  // Fetch full resolution in background
                  this.fetchImageByVariantId(variantId, 'full').then((fullUrl) => {
                    if (fullUrl && this.selectedProduct?.id === newProduct.id && prefetchRequestId === this.imageRequestId) {
                      this.activeImageUrl = fullUrl;
                    }
                  });
                }
              });
            } else {
              // Fallback: no prefetched ID, use traditional variant resolution
              // Wait a tick for selectedVariants to be set by parent, then fetch
              this.$nextTick(() => {
                this.refreshVariantImage();
              });
            }
          } else {
            // For non-first-open updates (e.g., product properties changed), refresh image
            this.refreshVariantImage();
          }

          this.activeImageRequestId = this.imageRequestId;
        } else {
          // Modal closed - reset to spinner state for next open
          this.activeImageUrl = '';
          this.activeImageRequestId = this.imageRequestId;
          this.isImageLoading = true;
          this.lastImageVariantKey = '';
          this.pendingExclusionsProductId = null;
        }
      },
      immediate: true
    }
    ,

    selectedVariants: {
      handler() {
        this.refreshVariantImage();
      },
      deep: true
    },


    orderStep(newVal) {
      // Load patient contacts when entering step 1 (patient info step)
      if (newVal === 1 && this.patientContacts.length === 0) {
        this.fetchPatientContacts();
      }
      // Load documents when entering Documents step with existing patient or with previous order
      // But NOT when sending impressions (Paste - Sending ear impressions variant)
      if (newVal === 2 && this.selectedPatient && (this.clientType === 'existing' || this.isWithPreviousOrder) && !this.isSendingImpressions) {
        this.fetchAndPreloadPatientDocs()
      }
    },
    impressionMethod(newVal) {
      // When user selects 'scan' method and has an existing patient, pre-load their documents
      // But NOT when sending impressions (Paste - Sending ear impressions variant)
      if (newVal === 'scan' && this.selectedPatient && this.clientType === 'existing' && !this.isSendingImpressions) {
        this.fetchAndPreloadPatientDocs()
      }
    }
  },
  methods: {
    // Disable an option if selecting it with current selection would complete a forbidden exclusion group (string matching)
    isServerValueDisabled(attribute, valueName) {
      try {
        if (!this.selectedProduct || !Array.isArray(this.variantExclusions) || this.variantExclusions.length === 0) return false
        const names = this.selectedValueNames.slice()
        // Replace current attribute's selected value (if any) with candidate valueName
        const current = this.selectedVariants && this.selectedVariants[attribute]
        if (current) {
          const idx = names.indexOf(current)
          if (idx >= 0) names.splice(idx, 1)
        }
        names.push(valueName)
        return this.checkForbiddenForValues(names)
      } catch (_) {
        return false
      }
    },
    // Returns true if any exclusion has both its base value and any of its excluded_values present in provided names
    checkForbiddenForValues(names) {
      try {
        if (!Array.isArray(names) || names.length === 0) return false
        for (const ex of this.variantExclusions || []) {
          const base = ex && ex.value
          const excluded = Array.isArray(ex && ex.excluded_values) ? ex.excluded_values : []
          if (!base || excluded.length === 0) continue
          if (names.includes(base) && excluded.some(n => names.includes(n))) {
            return true
          }
        }
        return false
      } catch (_) {
        return false
      }
    },
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
      this.clientType = null
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
        // Block if forbidden combination based on server exclusions
        if (this.isForbiddenByServer) {
          this.$emit('show-error', { message: 'This combination of options is not available for this product.', type: 'error' })
          return
        }
        this.clientType = null
      }

      // Validate patient information only when trying to move from step 1 (Patient Information) to step 2 (Documents)
      if (this.orderStep === 1) {
        if (!this.isClientTypeSelected) {
          this.patientValidationError = 'Please select whether this is a new patient or an existing patient.';
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

    async fetchVariantExclusions() {
      try {
        this.variantExclusionsLoading = true
        this.variantExclusionsError = ''
        this.variantExclusions = []

        // Check if exclusions were already provided in the product response (combined endpoint)
        if (Array.isArray(this.selectedProduct?.exclusions)) {
          this.variantExclusions = this.selectedProduct.exclusions
          return
        }

        // Fall back to fetching separately if not provided
        const token = localStorage.getItem('decilo_token')
        if (!token || !this.selectedProduct?.id) return
        const res = await fetch(`/decilo-api/products/${encodeURIComponent(this.selectedProduct.id)}/variant-exclusions`, {
          headers: { 'Authorization': `Bearer ${token}` }
        })
        const body = await res.json().catch(() => ({}))
        if (!res.ok) {
          this.variantExclusionsError = body?.error || 'Failed to load exclusions'
          return
        }
        this.variantExclusions = Array.isArray(body?.exclusions) ? body.exclusions : []
      } catch (e) {
        this.variantExclusionsError = 'Failed to load exclusions'
      } finally {
        this.variantExclusionsLoading = false
      }
    },

    maybeFetchVariantExclusions() {
      if (!this.pendingExclusionsProductId) return
      if (!this.selectedProduct || this.selectedProduct.id !== this.pendingExclusionsProductId) return
      this.pendingExclusionsProductId = null
      this.fetchVariantExclusions()
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

    handleFileUploadFromComponent({ side, file }) {
      if (side === 'right') {
        this.orderForm.rightImpressionDoc = file;
      } else {
        this.orderForm.leftImpressionDoc = file;
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

      // Pre-select first value for all variants except ear impression type (which is handled in step 1)
      if (this.selectedProduct && this.selectedProduct.variants) {
        this.selectedProduct.variants.forEach(variant => {
          // Skip ear impression type as it's handled separately in step 1
          if (variant.attribute !== 'Ear Impression Type' && !variant.attribute.toLowerCase().includes('ear impression')) {
            if (variant.values && variant.values.length > 0) {
              this.$emit('variant-selected', { attribute: variant.attribute, value: variant.values[0] });
            }
          }
        });
      }
    },

    closeModal() {
      this.$emit('close');
      this.resetOrderForm();
    },

    async fetchVariantImageWithSize(productId, selections, size, token) {
      const res = await fetch(`/decilo-api/products/${encodeURIComponent(productId)}/variant-image`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ selected_variants: selections, size })
      })
      if (!res.ok) {
        throw new Error(`Variant image request failed with status ${res.status}`)
      }
      const data = await res.json()
      return data?.image || null
    },

    async fetchImageByVariantId(variantProductId, size = 'medium') {
      // Fast path: fetch image directly by variant product ID (1 RPC, no resolution needed)
      const token = localStorage.getItem('decilo_token')
      if (!token || !variantProductId) return null

      try {
        const res = await fetch(`/decilo-api/variant-image/${variantProductId}?size=${size}`, {
          headers: { 'Authorization': `Bearer ${token}` }
        })
        if (!res.ok) return null

        // Response is binary image data, convert to data URL
        const blob = await res.blob()
        return new Promise((resolve) => {
          const reader = new FileReader()
          reader.onloadend = () => resolve(reader.result)
          reader.readAsDataURL(blob)
        })
      } catch (err) {
        console.warn('Failed to fetch image by variant ID', err)
        return null
      }
    },

    async fetchFullResolutionInBackground(productId, selections, fullKey) {
      // Silently fetch full resolution image in background (no spinner, non-blocking)
      const token = localStorage.getItem('decilo_token')
      if (!token) return

      const variantKey = JSON.stringify(Object.entries(selections).sort())
      const fullCacheKey = getVariantCacheKey(productId, variantKey, 'full')

      // Skip if already cached
      if (variantImageCache.has(fullCacheKey)) return

      try {
        const fullImage = await this.fetchVariantImageWithSize(productId, selections, 'full', token)
        if (fullImage && this.lastImageVariantKey === fullKey) {
          variantImageCache.set(fullCacheKey, fullImage)
          this.activeImageUrl = fullImage
        }
      } catch (err) {
        // Silent failure - we already have medium resolution
        console.warn('Background full resolution fetch failed', err)
      }
    },

    async refreshVariantImage() {
      if (!this.selectedProduct) return
      const selections = this.selectedVariants || {}
      const hasSelections = Object.keys(selections).length > 0
      const productId = this.selectedProduct?.id
      const fallback = this.selectedProduct?.image_url || ''
      const hasSelectableVariants = (this.selectedProduct?.variants || []).some((variant) => {
        const attribute = (variant?.attribute || '').toLowerCase()
        return attribute && !attribute.includes('ear impression')
      })
      const allowEmptySelections = !hasSelections && !hasSelectableVariants
      const variantKey = JSON.stringify(Object.entries(selections).sort())
      const fullKey = productId ? `${productId}::${variantKey}` : ''

      if (!productId) {
        this.activeImageUrl = fallback
        this.isImageLoading = false
        this.activeImageRequestId = this.imageRequestId
        return
      }

      if (!hasSelections && !allowEmptySelections) {
        // Keep spinner - waiting for product or variant selections
        return
      }

      if (!hasSelections && allowEmptySelections) {
        if (fallback && !this.activeImageUrl) {
          this.activeImageUrl = fallback
          this.activeImageRequestId = this.imageRequestId
          this.lastImageVariantKey = fullKey
          this.isImageLoading = false
        }
        if (this.selectedProduct?.default_variant_product_id) {
          return
        }
        if (fallback) {
          return
        }
        this.maybeFetchVariantExclusions()
        return
      }

      // Avoid duplicate requests for the same selection set
      if (fullKey === this.lastImageVariantKey) {
        // Still increment to cancel any in-flight requests for different variants
        this.imageRequestId += 1
        return
      }

      // Check if selections match the default variant image provided by combined endpoint
      const defaultSelections = this.selectedProduct?.default_selections
      const defaultImage = this.selectedProduct?.default_variant_image
      if (defaultImage && defaultSelections) {
        const defaultKey = JSON.stringify(Object.entries(defaultSelections).sort())
        if (variantKey === defaultKey) {
          // Use the pre-fetched default image, no need to fetch again
          this.activeImageUrl = defaultImage
          this.activeImageRequestId = ++this.imageRequestId
          this.lastImageVariantKey = fullKey
          this.isImageLoading = false
          // Cache it for consistency
          variantImageCache.set(getVariantCacheKey(productId, variantKey, 'medium'), defaultImage)
          // Still fetch full resolution in background
          this.fetchFullResolutionInBackground(productId, selections, fullKey)
          return
        }
      }

      const token = localStorage.getItem('decilo_token')
      if (!token) {
        this.activeImageUrl = fallback
        this.isImageLoading = false
        this.activeImageRequestId = this.imageRequestId
        return
      }

      const requestId = ++this.imageRequestId
      const mediumCacheKey = getVariantCacheKey(productId, variantKey, 'medium')
      const fullCacheKey = getVariantCacheKey(productId, variantKey, 'full')

      // Check if full image is already cached - instant display
      if (variantImageCache.has(fullCacheKey)) {
        this.activeImageUrl = variantImageCache.get(fullCacheKey)
        this.activeImageRequestId = requestId
        this.lastImageVariantKey = fullKey
        this.isImageLoading = false
        return
      }

      // Check if medium image is cached - show it immediately, no spinner needed
      if (variantImageCache.has(mediumCacheKey)) {
        this.activeImageUrl = variantImageCache.get(mediumCacheKey)
        this.activeImageRequestId = requestId
        this.isImageLoading = false
      } else {
        this.isImageLoading = true
      }

      try {
        // Progressive loading: fetch medium first (faster), then full
        let mediumImage = variantImageCache.get(mediumCacheKey)

        if (!mediumImage) {
          mediumImage = await this.fetchVariantImageWithSize(productId, selections, 'medium', token)
          if (requestId !== this.imageRequestId) return
          if (mediumImage) {
            variantImageCache.set(mediumCacheKey, mediumImage)
            this.activeImageUrl = mediumImage
            this.activeImageRequestId = requestId
            this.isImageLoading = false // Hide spinner once medium is displayed
          }
        }

        // Fetch full resolution silently in background (no spinner)
        const fullImage = await this.fetchVariantImageWithSize(productId, selections, 'full', token)
        if (requestId !== this.imageRequestId) return

        if (fullImage) {
          variantImageCache.set(fullCacheKey, fullImage)
          this.activeImageUrl = fullImage
        } else if (mediumImage) {
          this.activeImageUrl = mediumImage
        } else {
          this.activeImageUrl = fallback
        }

        this.activeImageRequestId = requestId
        this.lastImageVariantKey = fullKey
      } catch (error) {
        console.warn('Variant image load failed', error)
        if (requestId !== this.imageRequestId) return
        this.activeImageUrl = fallback
        this.activeImageRequestId = requestId
        this.lastImageVariantKey = fullKey
      } finally {
        if (requestId === this.imageRequestId) {
          this.isImageLoading = false
        }
      }
    },

    onImageLoaded() {
      if (this.activeImageRequestId === this.imageRequestId) {
        this.isImageLoading = false
      }
      this.maybeFetchVariantExclusions()
    },

    onImageError() {
      if (this.activeImageRequestId !== this.imageRequestId) return
      // On error, hide image and stop loading (no placeholder)
      this.activeImageUrl = ''
      this.activeImageRequestId = this.imageRequestId
      this.lastImageVariantKey = ''
      this.isImageLoading = false
      this.maybeFetchVariantExclusions()
    },

    selectVariant(attribute, value) {
      this.$emit('variant-selected', { attribute, value });
    },

    toggleVariant(attribute, value) {
      // Always select the variant (no deselection allowed)
      // If already selected, do nothing
      if (!this.isSelectedVariant(attribute, value)) {
        this.$emit('variant-selected', { attribute, value });
      }
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
        // Remove "From previous order" variant when selecting new patient
        this.$emit('variant-deselected', { attribute: 'Ear Impression Type', value: 'From previous order' });
      } else if (type === 'existing') {
        this.orderForm.patientFirstName = '';
        this.orderForm.patientLastName = '';
        // Automatically select "From previous order" variant when selecting existing patient
        this.$emit('variant-selected', { attribute: 'Ear Impression Type', value: 'From previous order' });
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

      // Automatically select the appropriate variant based on impression method
      if (method === 'scan') {
        this.$emit('variant-selected', { attribute: 'Ear Impression Type', value: 'Paste - 3D Scan' });
        // Remove the sending impressions variant if it was selected
        this.$emit('variant-deselected', { attribute: 'Ear Impression Type', value: 'Paste - Sending ear impressions' });
      } else if (method === 'ship') {
        this.$emit('variant-selected', { attribute: 'Ear Impression Type', value: 'Paste - Sending ear impressions' });
        // Remove the 3D scan variant if it was selected
        this.$emit('variant-deselected', { attribute: 'Ear Impression Type', value: 'Paste - 3D Scan' });
      }
    },

    changeImpressionMethod() {
      this.impressionMethod = null;
      // Reset uploaded documents when changing method
      this.orderForm.rightImpressionDoc = null;
      this.orderForm.leftImpressionDoc = null;
      this.preloadedLeftDoc = null;
      this.preloadedRightDoc = null;
      // Deselect both impression method variants when changing method
      this.$emit('variant-deselected', { attribute: 'Ear Impression Type', value: 'Paste - 3D Scan' });
      this.$emit('variant-deselected', { attribute: 'Ear Impression Type', value: 'Paste - Sending ear impressions' });
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
  background: rgba(30, 41, 59, 0.8);
  padding: 16px;
  box-sizing: border-box;
  border: 1px solid #475569;
  display: flex;
  align-items: center;
  justify-content: center;
}

.image-frame {
  position: relative;
  width: 100%;
}

.image-loading-overlay {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
}

.loading-spinner-large {
  width: 32px;
  height: 32px;
  border: 3px solid #94a3b8;
  border-top: 3px solid #cbd5e1;
  border-radius: 50%;
  animation: spin 1s linear infinite;
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
  font-family: 'Inter', sans-serif;
  font-size: 14px;
  font-weight: 500;
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

.loading-spinner-small {
  width: 16px;
  height: 16px;
  border: 2px solid #64748b;
  border-top: 2px solid transparent;
  border-radius: 50%;
  animation: spin 1s linear infinite;
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

.confirmation-btn {
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

.confirmation-btn:hover {
  background: #ffffff;
  color: #000000;
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(255, 255, 255, 0.3);
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
  border: 2px solid #ffffff;
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

.detail-loading {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 0;
  color: #94a3b8;
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

.variant-btn.disabled,
.variant-btn:disabled {
  background: rgba(255, 255, 255, 0.06);
  border-color: #555555;
  color: #9ca3af; /* muted */
  opacity: 0.7;
  cursor: not-allowed;
  filter: grayscale(0.35);
}

.variant-btn:disabled:hover,
.variant-btn.disabled:hover {
  background: rgba(255, 255, 255, 0.06);
}

/* Orange warning for forbidden combinations */
/* removed orange warning styles */

/* Ear Impression Type Section */
.ear-impression-type-section {
  margin-bottom: 24px;
  padding-bottom: 20px;
}

.ear-impression-type-section h3 {
  color: #ffffff;
  margin-bottom: 16px;
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

.client-type-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  pointer-events: none;
  background: #1e293b;
  border-color: #374151;
}

.client-type-btn:disabled:hover {
  transform: none;
  box-shadow: none;
  border-color: #374151;
  background: #1e293b;
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
