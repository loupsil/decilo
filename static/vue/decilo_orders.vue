<template>
  <div class="orders-container">
    <div class="orders-header">
      <h2 class="orders-title">Your Orders</h2>
    </div>

    <div v-if="isLoading" class="loading-state">
      <div class="loading-spinner"></div>
    </div>

    <div v-else>

      <div class="search-and-filters-section">
        <div class="search-section">
          <div class="search-input-container">
            <svg class="search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="11" cy="11" r="8"></circle>
              <path d="m21 21-4.35-4.35"></path>
            </svg>
            <input
              type="text"
              v-model="searchQuery"
              placeholder="Search orders..."
              @input="filterOrders"
              class="search-input"
            >
          </div>
        </div>

        <div v-if="orders.length" class="orders-summary-inline">
          <div class="summary-card clickable" :class="{ active: summaryFilter === 'all' }" @click="setSummaryFilter('all')">
            <span class="summary-label">Total Orders</span>
            <span class="summary-value">{{ orders.length }}</span>
          </div>
          <div class="summary-card clickable" :class="{ active: summaryFilter === 'review' }" @click="setSummaryFilter('review')">
            <span class="summary-label">In Review</span>
            <span class="summary-value">{{ orders.filter(o => o && (o.manufacturing_state === null || o.manufacturing_state === undefined || o.manufacturing_state === '')).length }}</span>
          </div>
          <div class="summary-card clickable" :class="{ active: summaryFilter === 'queue' }" @click="setSummaryFilter('queue')">
            <span class="summary-label">In Queue</span>
            <span class="summary-value">{{ orders.filter(o => o && o.manufacturing_state === 'draft').length }}</span>
          </div>
          <div class="summary-card clickable" :class="{ active: summaryFilter === 'progress' }" @click="setSummaryFilter('progress')">
            <span class="summary-label">In Progress</span>
            <span class="summary-value">{{ orders.filter(o => o && (o.manufacturing_state === 'confirmed' || o.manufacturing_state === 'progress' || o.manufacturing_state === 'planned')).length }}</span>
          </div>
          <div class="summary-card clickable" :class="{ active: summaryFilter === 'completed' }" @click="setSummaryFilter('completed')">
            <span class="summary-label">Completed</span>
            <span class="summary-value">{{ orders.filter(o => o && o.manufacturing_state === 'done').length }}</span>
          </div>
        </div>
      </div>

      <div v-if="filteredOrders.length" class="orders-layout">
        <div class="orders-list">
          <div
            class="order-item"
            v-for="order in filteredOrders"
            :key="order.id"
            :class="{ 'selected': selectedOrder && selectedOrder.id === order.id }"
            @click="selectOrder(order)"
          >
            <div class="order-header">
              <div class="order-identity">
                <div class="order-number-badge">
                  <span class="order-number">#{{ order.number || 'Unknown' }}</span>
                </div>
                <div class="order-datetime">
                  <div class="order-date">{{ order.date ? formatDate(order.date) : 'Unknown date' }}</div>
                  <div class="order-time">
                    {{ order.date ? formatTime(order.date) : '' }}
                    <span v-if="order.patient?.name" class="doc-filename" style="margin-left:8px;">{{ '• ' + order.patient.name }}</span>
                  </div>
                </div>
              </div>
              <div class="order-status">
                <div class="order-status-indicator">
                  <div :class="['status-dot', getStatusClass(order.manufacturing_state)]"></div>
                  <span class="status-text">{{ formatStatus(order.manufacturing_state) }}</span>
                </div>
              </div>
            </div>
            
          </div>
        </div>

        <div class="order-preview" v-if="selectedOrder">
          <div class="preview-header">
            <div class="preview-header-content">
              <h3 class="preview-title">Order #{{ selectedOrder.number || 'Unknown' }}</h3>
              <div class="preview-date">{{ selectedOrder.date ? formatDate(selectedOrder.date) + ' at ' + formatTime(selectedOrder.date) : 'Unknown date' }}</div>
            </div>
            <div class="preview-progress">
              <div class="mini-timeline-container">
                <div class="mini-timeline">
                  <div class="mini-timeline-track">
                    <div class="mini-timeline-progress" :style="{ width: progressWidth(selectedOrder.manufacturing_state) }"></div>
                    <div class="mini-timeline-glow"></div>
                  </div>
                  <div class="mini-timeline-steps">
                    <div :class="['mini-t-step', productionStageIndex(selectedOrder.manufacturing_state) >= 0 ? 'active' : '']">
                      <span class="mini-dot"></span>
                      <span class="mini-label">Review</span>
                    </div>
                    <div :class="['mini-t-step', productionStageIndex(selectedOrder.manufacturing_state) >= 1 ? 'active' : '']">
                      <span class="mini-dot"></span>
                      <span class="mini-label">Queue</span>
                    </div>
                    <div :class="['mini-t-step', productionStageIndex(selectedOrder.manufacturing_state) >= 2 ? 'active' : '']">
                      <span class="mini-dot"></span>
                      <span class="mini-label">Progress</span>
                    </div>
                    <div :class="['mini-t-step', productionStageIndex(selectedOrder.manufacturing_state) >= 3 ? 'active' : '']">
                      <span class="mini-dot"></span>
                      <span class="mini-label">Complete</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div class="order-details">

            <div class="preview-section" v-if="selectedOrder.products && selectedOrder.products.length">
              <div class="section-header" style="display:flex;align-items:center;justify-content:space-between;">
                <h4 class="section-title">Order Items</h4>
                <span class="products-count">{{ selectedOrder.products.length }} item{{ selectedOrder.products.length !== 1 ? 's' : '' }}</span>
              </div>
              <div class="section-body">
                <div class="products-list">
                  <div
                    v-for="p in selectedOrder.products"
                    :key="`${selectedOrder.id}-${p.id}-${p.name}`"
                    class="product-item"
                  >
                    <div class="product-info">
                      <span class="product-name">{{ p.name }}</span>
                      <div class="product-meta">
                        <span class="product-qty" v-if="p.quantity">Quantity: {{ p.quantity }}</span>
                        <span class="product-separator" v-if="p.quantity">•</span>
                        <span class="product-id">#{{ p.id }}</span>
                      </div>
                    </div>
                    <div class="product-arrow">
                      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <polyline points="9,18 15,12 9,6"></polyline>
                      </svg>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            <!-- Preview sections: Documents, Patient information, Notes -->
            <div class="preview-sections" v-if="selectedOrder">
              <!-- Documents -->
              <div class="preview-section">
                <div class="section-header">
                  <h4 class="section-title">Documents</h4>
                </div>
                <div class="section-body">
                  <div v-if="selectedOrderPatient?.id">
                    <div v-if="docsLoading" class="dropdown-loading">
                      <div class="loading-spinner-small"></div>
                      <span>Loading documents...</span>
                    </div>
                    <div v-else>
                      <div v-if="docsError" class="patient-validation-error">{{ docsError }}</div>
                      <ul v-else class="existing-docs-list">
                        <li>
                          <strong>Right:</strong>
                          <template v-if="docs.right?.exists">
                            <a class="doc-link" href="#" @click.prevent="downloadDoc('right')">
                              <span class="doc-icon" aria-hidden="true">
                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                  <path d="M12 5v10"/>
                                  <path d="m7 10 5 5 5-5"/>
                                  <path d="M5 19h14"/>
                                </svg>
                              </span>
                              <span class="doc-filename">{{ docs.right.filename }}</span>
                            </a>
                          </template>
                          <template v-else>
                            <span>Not found</span>
                          </template>
                        </li>
                        <li>
                          <strong>Left:</strong>
                          <template v-if="docs.left?.exists">
                            <a class="doc-link" href="#" @click.prevent="downloadDoc('left')">
                              <span class="doc-icon" aria-hidden="true">
                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                  <path d="M12 5v10"/>
                                  <path d="m7 10 5 5 5-5"/>
                                  <path d="M5 19h14"/>
                                </svg>
                              </span>
                              <span class="doc-filename">{{ docs.left.filename }}</span>
                            </a>
                          </template>
                          <template v-else>
                            <span>Not found</span>
                          </template>
                        </li>
                      </ul>
                    </div>
                  </div>
                  <div v-else class="section-empty">No documents available</div>
                </div>
              </div>

              <!-- Patient information -->
              <div class="preview-section">
                <div class="section-header">
                  <h4 class="section-title">Patient information</h4>
                </div>
                <div class="section-body">
                  <div class="products-list">
                    <div class="product-item">
                      <div class="product-info">
                        <span class="product-name">Name</span>
                        <div class="product-meta">
                          <span class="product-id">{{ selectedOrderPatient?.name || '—' }}</span>
                        </div>
                      </div>
                      <div class="product-arrow">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                          <polyline points="9,18 15,12 9,6"></polyline>
                        </svg>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Notes -->
              <div class="preview-section">
                <div class="section-header">
                  <h4 class="section-title">Notes</h4>
                </div>
                <div class="section-body">
                  <div v-if="selectedOrder.patient_comment" class="patient-notes-box">
                    <div class="patient-notes-text" v-html="selectedOrder.patient_comment"></div>
                  </div>
                  <div v-else class="section-empty">No notes</div>
                </div>
              </div>
            </div>
          </div>
        </div>

      <div v-else class="empty-state">
        <div class="empty-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <path d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
          </svg>
        </div>
        <h3 class="empty-title">No orders found</h3>
        <p class="empty-description">Your orders will appear here once you place them.</p>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'DeciloOrders',
  props: {
    customerInfo: {
      type: Object,
      required: true
    }
  },
  data() {
    return {
      orders: [],
      searchQuery: '',
      selectedStatus: 'All',
      orderStatuses: ['All', 'Processing', 'Shipped', 'Delivered', 'Cancelled'],
      selectedOrder: null,
      summaryFilter: 'all', // 'all', 'ongoing', 'completed'
      isLoading: false,
      selectedOrderPartner: null,
      selectedOrderPatient: null,
      docs: { left: { exists: false, filename: '' }, right: { exists: false, filename: '' } },
      docsLoading: false,
      docsError: '',
      lastDetailsOrderId: null,
    }
  },
  computed: {
    filteredOrders() {
      // Always show newest first
      let filtered = (this.orders || []).filter(order => order).sort((a, b) => {
        const da = a && a.date ? new Date(a.date).getTime() : 0
        const db = b && b.date ? new Date(b.date).getTime() : 0
        return db - da
      })

      // Apply status filter
      if (this.selectedStatus !== 'All') {
        filtered = filtered.filter(order => order && order.status === this.selectedStatus)
      }

      // Apply search filter
      if (this.searchQuery) {
        const query = this.searchQuery.toLowerCase()
        filtered = filtered.filter(order =>
          order && order.number && order.number.toLowerCase().includes(query) ||
          (order && order.products && order.products.some(product =>
            product && product.name && product.name.toLowerCase().includes(query)
          ))
        )
      }

      // Apply summary filter
      if (this.summaryFilter !== 'all') {
        if (this.summaryFilter === 'review') {
          filtered = filtered.filter(order => order && (order.manufacturing_state === null || order.manufacturing_state === undefined || order.manufacturing_state === ''))
        } else if (this.summaryFilter === 'queue') {
          filtered = filtered.filter(order => order && order.manufacturing_state === 'draft')
        } else if (this.summaryFilter === 'progress') {
          filtered = filtered.filter(order => order && (order.manufacturing_state === 'confirmed' || order.manufacturing_state === 'progress' || order.manufacturing_state === 'planned'))
        } else if (this.summaryFilter === 'completed') {
          filtered = filtered.filter(order => order && order.manufacturing_state === 'done')
        }
      }

      return filtered
    }
  },
  created() {
    this.fetchOrders()
  },
  watch: {
    selectedStatus() {
      this.autoSelectFirstOrder()
    },
    searchQuery() {
      this.autoSelectFirstOrder()
    },
    summaryFilter() {
      this.autoSelectFirstOrder()
    },
    selectedOrder: {
      handler(newOrder) {
        // Fetch patient/docs only when order selection actually changes
        if (newOrder && newOrder.id && newOrder.id !== this.lastDetailsOrderId) {
          this.loadSelectedOrderPartner(newOrder.id)
        } else if (!newOrder) {
          this.docs = { left: { exists: false, filename: '' }, right: { exists: false, filename: '' } }
          this.docsError = ''
          this.selectedOrderPartner = null
          this.selectedOrderPatient = null
          this.lastDetailsOrderId = null
        }
      },
      immediate: true
    }
  },
  methods: {
    async loadSelectedOrderPartner(orderId) {
      try {
        const token = localStorage.getItem('decilo_token')
        if (!token) throw new Error('Authentication required')
        const res = await fetch(`/decilo-api/orders/${orderId}`, { headers: { 'Authorization': `Bearer ${token}` } })
        const body = await res.json().catch(() => ({}))
        if (!res.ok) throw new Error(body?.error || 'Failed to load order details')
        this.selectedOrderPartner = body?.partner || null
        this.selectedOrderPatient = body?.patient || null
        // Merge patient_comment without changing object reference to avoid retriggering watcher
        if (this.selectedOrder && this.selectedOrder.id === orderId) {
          const comment = body?.patient_comment || ''
          if (this.$set) {
            this.$set(this.selectedOrder, 'patient_comment', comment)
          } else {
            this.selectedOrder.patient_comment = comment
          }
        }
        this.lastDetailsOrderId = orderId
        if (this.selectedOrderPatient?.id) {
          this.fetchOrderPatientDocs(this.selectedOrderPatient.id, this.selectedOrderPatient.name)
        } else {
          this.docs = { left: { exists: false, filename: '' }, right: { exists: false, filename: '' } }
          this.docsError = ''
        }
      } catch (_) {
        this.selectedOrderPartner = null
        this.selectedOrderPatient = null
        this.lastDetailsOrderId = null
      }
    },
    productionStageIndex(state) {
      const s = (state || '').toLowerCase()
      // New 4-step model:
      // 0: In Review (no manufacturing order yet)
      // 1: In Queue (draft)
      // 2: Started (confirmed/progress/planned)
      // 3: Ready (done)
      if (!s) return 0
      if (s === 'done') return 3
      if (s === 'confirmed' || s === 'progress' || s === 'planned') return 2
      if (s === 'draft') return 1
      return 0
    },
    progressWidth(state) {
      const idx = this.productionStageIndex(state)
      if (idx < 0) return '0%'
      if (idx === 0) return '16%'
      if (idx === 1) return '40%'
      if (idx === 2) return '70%'
      return '100%'
    },
    getDetailedProgressInfo(state) {
      const stageIndex = this.productionStageIndex(state)
      const stages = [
        { name: 'Review', width: '16%', color: '#f59e0b' },
        { name: 'Queue', width: '40%', color: 'var(--primary-color)' },
        { name: 'Progress', width: '70%', color: '#8b5cf6' },
        { name: 'Complete', width: '100%', color: '#10b981' }
      ]
      return stages[stageIndex] || stages[0]
    },
    getStatusClass(state) {
      const s = (state || '').toLowerCase()
      if (s === 'done') return 'status-complete'
      if (s === 'confirmed' || s === 'progress' || s === 'planned') return 'status-progress'
      if (s === 'draft') return 'status-queue'
      return 'status-review'
    },
    formatStatus(state) {
      const s = (state || '').toLowerCase()
      if (s === 'done') return 'Completed'
      if (s === 'confirmed' || s === 'progress' || s === 'planned') return 'In Progress'
      if (s === 'draft') return 'In Queue'
      return 'In Review'
    },
    async fetchOrders() {
      this.isLoading = true
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

        const params = new URLSearchParams()
        if (this.searchQuery) params.append('search', this.searchQuery)
        if (this.selectedStatus && this.selectedStatus !== 'All') params.append('status', this.selectedStatus)

        const url = `/decilo-api/orders${params.toString() ? `?${params.toString()}` : ''}`
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
          const error = await response.json().catch(() => ({}))
          throw new Error(error.error || 'Failed to fetch orders')
        }

        const data = await response.json()
        this.orders = Array.isArray(data.orders) ? data.orders.filter(order => order) : []

        // Auto-select first order
        this.autoSelectFirstOrder()
      } catch (error) {
        if (error.message !== 'Token expired') {
          console.error('Error fetching orders:', error)
        }
      } finally {
        this.isLoading = false
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
    formatDate(dateString) {
      const date = new Date(dateString)
      return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
      })
    },
    formatTime(dateString) {
      // Add 2 hours to align with Belgian time since dates from API are in UTC
      const date = new Date(dateString)
      date.setHours(date.getHours() + 2)
      return date.toLocaleTimeString('nl-BE', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
      })
    },
    selectStatus(status) {
      this.selectedStatus = status
    },
    filterOrders() {
      // Debounced search implementation could be added here
    },
    selectOrder(order) {
      this.selectedOrder = order
    },
    autoSelectFirstOrder() {
      // Auto-select first order if no order is currently selected or current selection is not in filtered results
      if (this.filteredOrders.length > 0) {
        const currentSelectedInFiltered = this.selectedOrder && this.filteredOrders.some(order => order.id === this.selectedOrder.id)
        if (!currentSelectedInFiltered) {
          this.selectedOrder = this.filteredOrders[0]
        }
      } else {
        this.selectedOrder = null
      }
    },
    setSummaryFilter(filter) {
      this.summaryFilter = this.summaryFilter === filter ? 'all' : filter
    },
    closeModal() {
      this.selectedOrder = null
    },
    async cancelOrder(order) {
      try {
        // TODO: Implement order cancellation
        console.log('Cancelling order:', order)
      } catch (error) {
        console.error('Error cancelling order:', error)
      }
    },
    async fetchOrderPatientDocs(partnerId, partnerName) {
      try {
        this.docsLoading = true
        this.docsError = ''
        const token = localStorage.getItem('decilo_token')
        if (!token) throw new Error('Authentication required')
        // Prefer order-based API which follows x_studio_patient on the order
        const url = `/decilo-api/orders/${this.selectedOrder.id}/ear-impressions`
        const res = await fetch(url, { headers: { 'Authorization': `Bearer ${token}` } })
        const body = await res.json().catch(() => ({}))
        if (!res.ok) {
          this.docsError = body?.error || `The ear document associated with the following patient: ${partnerName || ''} could not be found`
          this.docs = { left: { exists: false, filename: '' }, right: { exists: false, filename: '' } }
          return
        }
        this.docs = body
      } catch (e) {
        this.docsError = `The ear document associated with the following patient: ${partnerName || ''} could not be found`
        this.docs = { left: { exists: false, filename: '' }, right: { exists: false, filename: '' } }
      } finally {
        this.docsLoading = false
      }
    },
    async downloadDoc(side) {
      if (!this.selectedOrderPatient?.id) return
      try {
        const token = localStorage.getItem('decilo_token')
        if (!token) throw new Error('Authentication required')
        const params = new URLSearchParams({ side })
        const url = `/decilo-api/orders/${this.selectedOrder.id}/ear-impressions/download?${params.toString()}`
        const res = await fetch(url, { headers: { 'Authorization': `Bearer ${token}` } })
        if (!res.ok) return
        const blob = await res.blob()
        const a = document.createElement('a')
        a.href = URL.createObjectURL(blob)
        a.download = side === 'left' ? (this.docs.left?.filename || 'left_ear_impression') : (this.docs.right?.filename || 'right_ear_impression')
        document.body.appendChild(a)
        a.click()
        a.remove()
      } catch (_) {
        // ignore
      }
    }
  }
}
</script>

<style scoped>
.patient-notes-box {
  margin-top: 6px;
  padding: 12px 14px;
  border: 1px solid #334155;
  border-radius: 10px;
  background: rgba(30, 41, 59, 0.6);
}

.patient-notes-text {
  margin: 0;
  color: #e2e8f0;
  font-size: 13px;
  white-space: pre-wrap;
}
.orders-container {
  padding: 32px;
  color: #e2e8f0;
}


.orders-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
  position: relative;
  z-index: 1;
}

/* Preview sections */
.preview-sections {
  display: grid;
  gap: 16px;
  margin-top: 8px;
}

.preview-section {
  border: 1px solid #334155;
  border-radius: 12px;
  background: rgba(30, 41, 59, 0.6);
}

.section-header {
  padding: 10px 14px;
  border-bottom: 1px solid #334155;
}

.section-title {
  margin: 0;
  font-size: 14px;
  font-weight: 700;
  color: #e2e8f0;
}

.section-body {
  padding: 12px 14px;
}

.section-empty {
  color: #94a3b8;
  font-size: 13px;
}

.patient-info-row {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: 8px;
}

.info-label {
  color: #94a3b8;
  font-size: 13px;
}

.info-value {
  color: #94a3b8;
  font-weight: 500;
  font-size: 13px;
}

.header-content {
  flex: 1;
}

.orders-title {
  font-weight: 700;
  color: #ffffff;
  margin: 0 0 8px 0;
  letter-spacing: -0.025em;
}



.search-and-filters-section {
  display: flex;
  gap: 24px;
  align-items: center;
  margin-bottom: 32px;
}

.search-section {
  flex: 1;
  display: flex;
  justify-content: start;
}

.orders-summary-inline {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
}

.search-input-container {
  position: relative;
  width: 100%;
  max-width: 400px;
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

.search-input {
  width: 100%;
  padding: 12px 16px 12px 44px;
  background: var(--secondary-color);
  border: 1px solid #334155;
  border-radius: 8px;
  color: #ffffff;
  font-size: 14px;
  font-weight: 400;
  transition: all 0.2s ease;
}

.search-input:focus {
  outline: none;
  border-color: var(--primary-color);
  background: rgba(59, 130, 246, 0.05);
}

.search-input::placeholder {
  color: #64748b;
  font-weight: 400;
}

.loading-state {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 300px;
  padding: 40px 20px;
}


@keyframes rotate {
  to {
    background-position: 400% 0;
  }
}

.orders-summary {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 24px;
  margin-bottom: 40px;
}

.summary-card {
  background: var(--secondary-color);
  border-radius: 8px;
  padding: 8px 12px;
  text-align: center;
  position: relative;
  transition: all 0.2s ease;
  min-width: 60px;
}

.summary-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
  border-color: #475569;
}

.summary-card.clickable {
  cursor: pointer;
}

.summary-card.clickable:hover {
  border-color: var(--primary-color);
}

.summary-card.active {
  border-color: var(--primary-color);
  background: var(--primary-color);
}

.summary-card.active .summary-label {
  color: #93c5fd;
}

.summary-label {
  display: block;
  color: #94a3b8;
  font-size: 10px;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 2px;
  line-height: 1;
}

.summary-value {
  display: block;
  font-size: 16px;
  font-weight: 700;
  color: #ffffff;
  line-height: 1;
}

.orders-layout {
  display: flex;
  gap: 32px;
  height: calc(100vh - 300px);
  margin-top: 32px;
}

.orders-list {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 100%;
  overflow-y: auto;
  padding-right: 8px;
}

.order-preview {
  flex: 1;
  background: var(--secondary-color);
  border-radius: 12px;
  padding: 24px;
  overflow-y: auto;
}

/* Custom scrollbar styling */
.orders-list::-webkit-scrollbar,
.order-preview::-webkit-scrollbar {
  width: 8px;
}

.orders-list::-webkit-scrollbar-track,
.order-preview::-webkit-scrollbar-track {
  background: rgba(51, 65, 85, 0.3);
  border-radius: 4px;
}

.orders-list::-webkit-scrollbar-thumb,
.order-preview::-webkit-scrollbar-thumb {
  background: #475569;
  border-radius: 4px;
  transition: background 0.2s ease;
}

.orders-list::-webkit-scrollbar-thumb:hover,
.order-preview::-webkit-scrollbar-thumb:hover {
  background: #64748b;
}

.orders-list::-webkit-scrollbar-thumb:active,
.order-preview::-webkit-scrollbar-thumb:active {
  background: #94a3b8;
}

.order-item {
  background: var(--secondary-color);
  border-radius: 12px;
  border: 1px solid #33415500;
  padding: 16px;
  transition: all 0.2s ease;
  flex-shrink: 0;
  cursor: pointer;
}

.order-item:hover {
  border-color: #475569;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
}

.order-item.selected {
  border-color: var(--primary-color);
  box-shadow: 0 8px 32px rgba(59, 130, 246, 0.1);
}

.order-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
}

.order-identity {
  display: flex;
  align-items: center;
  gap: 16px;
}

.order-status {
  display: flex;
  justify-content: flex-end;
}

.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 10px;
  padding-bottom: 10px;
  gap: 16px;
}

.preview-title {
  font-size: 24px;
  font-weight: 600;
  color: #ffffff;
  margin: 0 0 8px 0;
}

.preview-date {
  font-size: 14px;
  color: #94a3b8;
}

.preview-header-content {
  flex: 1;
}

.preview-progress {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 8px;
  min-width: 120px;
}

.progress-track {
  width: 100px;
  height: 6px;
  background: #334155;
  border-radius: 3px;
  overflow: hidden;
  position: relative;
}

.progress-fill {
  height: 100%;
  background: #22c55e;
  border-radius: 3px;
  transition: width 0.8s cubic-bezier(0.4, 0, 0.2, 1);
}

.progress-status {
  display: flex;
  align-items: center;
  gap: 6px;
}

.status-dot-small {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  flex-shrink: 0;
}

.status-text-small {
  font-size: 11px;
  font-weight: 600;
  color: #ffffff;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

/* Status dot colors for small version */
.status-dot-small.status-review {
  background: #f59e0b;
}

.status-dot-small.status-queue {
  background: var(--primary-color);
}

.status-dot-small.status-progress {
  background: #8b5cf6;
}

.status-dot-small.status-complete {
  background: #10b981;
}

.mini-timeline-container {
  display: flex;
  justify-content: center;
}

.mini-timeline {
  width: 100%;
  max-width: 300px;
}

.mini-timeline-track {
  position: relative;
  width: 100%;
  height: 6px;
  background: #334155;
  border-radius: 999px;
  overflow: hidden;
  margin-bottom: 16px;
}

.mini-timeline-progress {
  position: absolute;
  top: 0;
  left: 0;
  height: 100%;
  background: #22c55e;
  border-radius: 999px;
  transition: width 0.8s cubic-bezier(0.4, 0, 0.2, 1);
}

.mini-timeline-glow {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(34, 197, 94, 0.3), transparent);
  border-radius: 999px;
  animation: pulse 2s ease-in-out infinite;
}

.mini-timeline-steps {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
  align-items: center;
}

.mini-t-step {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  color: #64748b;
  position: relative;
  transition: all 0.2s ease;
}

.mini-t-step .mini-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #334155;
  border: 2px solid #475569;
  position: relative;
  transition: all 0.2s ease;
  z-index: 2;
}

.mini-t-step .mini-label {
  font-size: 10px;
  font-weight: 500;
  text-align: center;
  max-width: 50px;
  line-height: 1.2;
}

.mini-t-step.active {
  color: #ffffff;
}

.mini-t-step.active .mini-dot {
  background: #22c55e;
  border-color: #10b981;
  transform: scale(1.2);
  box-shadow: 0 0 8px rgba(34, 197, 94, 0.4);
}

@keyframes pulse {
  0%, 100% {
    opacity: 0.4;
  }
  50% {
    opacity: 0.8;
  }
}

.order-number-badge {
  display: inline-flex;
  align-items: center;
  background: var(--primary-color);
  color: #ffffff;
  padding: 6px 12px;
  border-radius: 16px;
  font-size: 12px;
  font-weight: 600;
  flex-shrink: 0;
}

.order-datetime {
  display: flex;
  align-items: center;
  gap: 12px;
}

.order-date {
  font-size: 14px;
  font-weight: 500;
  color: #ffffff;
  line-height: 1.2;
}

.order-time {
  font-size: 12px;
  color: #94a3b8;
  font-weight: 400;
}

.order-status-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  background: rgba(30, 41, 59, 0.8);
  border-radius: 12px;
  border: 1px solid #334155;
  flex-shrink: 0;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.status-dot.status-review {
  background: #f59e0b;
}

.status-dot.status-queue {
  background: var(--primary-color);
}

.status-dot.status-progress {
  background: #8b5cf6;
}

.status-dot.status-complete {
  background: #10b981;
}

.status-text {
  font-size: 14px;
  font-weight: 600;
  color: #ffffff;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.order-patient-inline {
  margin-top: 6px;
  margin-left: 8px;
}

.order-details {
  padding: 0;
}

.order-production {
  margin-bottom: 32px;
}

.production-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.production-title {
  font-size: 18px;
  font-weight: 600;
  color: #ffffff;
  margin: 0;
}

.production-timeline-container {
  display: flex;
  justify-content: center;
}

.production-timeline {
  width: 100%;
  max-width: 500px;
  padding: 32px 0;
}

.timeline-track {
  position: relative;
  width: 100%;
  height: 8px;
  background: #334155;
  border-radius: 999px;
  overflow: hidden;
  margin-bottom: 32px;
}

.timeline-progress {
  position: absolute;
  top: 0;
  left: 0;
  height: 100%;
  background: #22c55e;
  border-radius: 999px;
  transition: width 0.8s cubic-bezier(0.4, 0, 0.2, 1);
}

.timeline-steps {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 14px;
  align-items: center;
}

.t-step {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  color: #64748b;
  position: relative;
  transition: all 0.2s ease;
}

.t-step .dot {
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: #334155;
  border: 2px solid #475569;
  position: relative;
  transition: all 0.2s ease;
  z-index: 2;
}

.t-step .label {
  font-size: 12px;
  font-weight: 500;
  text-align: center;
  max-width: 70px;
  line-height: 1.3;
}

.t-step.active {
  color: #ffffff;
}

.t-step.active .dot {
  background: #22c55e;
  border-color: #10b981;
  transform: scale(1.1);
}

.order-products {
  border-top: 1px solid #334155;
  padding-top: 32px;
}

.products-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.products-title {
  font-size: 16px;
  font-weight: 600;
  color: #ffffff;
  margin: 0;
}

.products-count {
  background: rgba(59, 130, 246, 0.1);
  color: var(--primary-color);
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.products-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.product-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  background: rgba(30, 41, 59, 0.6);
  border: 1px solid #334155;
  border-radius: 8px;
  transition: all 0.2s ease;
}

.product-item:hover {
  background: rgba(30, 41, 59, 0.9);
  border-color: #475569;
}

.product-info {
  flex: 1;
}

.product-name {
  display: block;
  font-size: 15px;
  font-weight: 600;
  color: #ffffff;
  margin-bottom: 6px;
  line-height: 1.3;
}

.product-meta {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 13px;
}

.product-qty {
  color: #94a3b8;
  font-weight: 500;
}

.product-separator {
  color: #475569;
}

.product-id {
  color: #64748b;
  font-weight: 400;
  font-family: 'SF Mono', 'Monaco', 'Inconsolata', 'Roboto Mono', monospace;
}

.product-arrow {
  color: #64748b;
  transition: all 0.2s ease;
}

.product-item:hover .product-arrow {
  color: var(--primary-color);
  transform: translateX(4px);
}

.empty-state {
  text-align: center;
  padding: 80px 32px;
  position: relative;
  z-index: 1;
}

.empty-icon {
  width: 80px;
  height: 80px;
  margin: 0 auto 32px;
  color: #475569;
  opacity: 0.6;
}

.empty-icon svg {
  width: 100%;
  height: 100%;
}

.empty-title {
  font-size: 24px;
  font-weight: 600;
  color: #ffffff;
  margin: 0 0 16px 0;
}

.empty-description {
  font-size: 16px;
  color: #94a3b8;
  margin: 0;
  max-width: 400px;
  margin-left: auto;
  margin-right: auto;
}

.patient-docs {
  margin-top: 32px;
  padding-top: 32px;
  border-top: 1px solid #334155;
}

.patient-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.patient-name {
  font-size: 16px;
  font-weight: 600;
  color: #ffffff;
  background: rgba(59, 130, 246, 0.1);
  padding: 6px 12px;
  border-radius: 12px;
  flex-shrink: 0;
}

.existing-docs {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.existing-docs-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 0;
  margin: 0;
}

.existing-docs-list li {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: rgba(30, 41, 59, 0.6);
  border: 1px solid #334155;
  border-radius: 8px;
  transition: all 0.2s ease;
}

.existing-docs-list li:hover {
  background: rgba(30, 41, 59, 0.9);
  border-color: #475569;
}

.doc-link {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #94a3b8;
  text-decoration: none;
  transition: all 0.2s ease;
}

.doc-link:hover {
  color: var(--primary-color);
  transform: translateX(4px);
}

.doc-icon {
  width: 20px;
  height: 20px;
  color: #64748b;
}

.doc-filename {
  font-size: 14px;
  font-weight: 500;
  color: #94a3b8;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex-grow: 1;
}

.dropdown-loading {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #94a3b8;
  font-size: 14px;
  padding: 12px 16px;
  background: rgba(30, 41, 59, 0.6);
  border: 1px solid #334155;
  border-radius: 8px;
}

.loading-spinner-small {
  width: 16px;
  height: 16px;
  border: 2px solid #64748b;
  border-top-color: #94a3b8;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.patient-validation-error {
  color: #f56565;
  font-size: 14px;
  margin-top: 12px;
  text-align: center;
}

@media (max-width: 1024px) {
  .orders-container {
    padding: 24px;
  }
  .orders-summary {
    grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
    gap: 20px;
  }

  .search-input{
    max-width: 50%;
  }

  .order-datetime{
    display: none;
  }

.order-time{
  display: none;
  }
}

@media (max-width: 768px) {
  .orders-container {
    padding: 20px;
  }

  .orders-header {
    text-align: center;
  }

  .search-input{
    max-width: 50%;
  }

  .search-and-filters-section {
    flex-direction: column;
    align-items: stretch;
    gap: 16px;
  }

  .orders-summary-inline {
    justify-content: center;
    gap: 12px;
  }
  .orders-summary {
    grid-template-columns: repeat(2, 1fr);
    gap: 16px;
  }

  .summary-card {
    padding: 6px 10px;
    min-width: 50px;
  }

  .summary-value {
    font-size: 14px;
  }

  .summary-label {
    font-size: 9px;
  }

  .orders-layout {
    flex-direction: column;
    height: auto;
    gap: 24px;
  }

  .orders-summary-inline {
    gap: 8px;
  }

  .orders-list {
    flex: none;
    max-height: 400px;
  }

  .order-preview {
    padding: 20px;
  }

  .preview-header {
    flex-direction: column;
    gap: 12px;
  }

  .preview-progress {
    align-items: flex-start;
    min-width: auto;
  }

  .mini-timeline {
    max-width: 250px;
  }

  .mini-timeline-steps {
    gap: 6px;
  }

  .mini-t-step .mini-label {
    font-size: 9px;
    max-width: 45px;
  }

  .order-header {
    gap: 12px;
  }

  .order-datetime {
    gap: 8px;
  }

  .timeline-steps {
    gap: 12px;
  }

  .t-step .label {
    font-size: 11px;
    max-width: 60px;
  }
}

@media (max-width: 480px) {
  .orders-container {
    padding: 16px;
  }

  .orders-summary {
    grid-template-columns: 1fr;
    gap: 16px;
  }

  .summary-card {
    padding: 6px 8px;
    min-width: 45px;
  }

  .summary-value {
    font-size: 12px;
  }

  .summary-label {
    font-size: 8px;
  }

  .orders-layout {
    flex-direction: column;
    height: auto;
    gap: 20px;
  }

  .orders-list {
    flex: none;
    max-height: 300px;
  }

  .order-preview {
    padding: 16px;
  }

  .preview-header {
    gap: 10px;
  }

  .progress-track {
    width: 80px;
  }

  .mini-timeline {
    max-width: 200px;
  }

  .mini-timeline-steps {
    gap: 4px;
  }

  .mini-t-step .mini-label {
    font-size: 8px;
    max-width: 40px;
  }

  .mini-t-step .mini-dot {
    width: 6px;
    height: 6px;
  }

  .order-header {
    gap: 8px;
  }

  .order-number-badge {
    font-size: 11px;
    padding: 4px 10px;
  }

  .order-date {
    font-size: 13px;
  }

  .order-time {
    font-size: 11px;
  }

  .search-input{
    max-width: 50%;
  }
}

@media (max-width: 360px) {
  .order-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 6px;
  }

  .order-datetime {
    flex-direction: column;
    align-items: flex-start;
    gap: 4px;
  }

  .order-number-badge {
    margin-bottom: 0;
  }

  .orders-summary-inline {
    flex-direction: column;
    gap: 8px;
  }

  .search-input{
    max-width: 50%;
  }
}
</style>
