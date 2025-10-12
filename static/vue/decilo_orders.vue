<template>
  <div class="orders-container">
    <div class="orders-header">
      <div class="header-content">
        <h2 class="orders-title">Your Orders</h2>
      </div>
    </div>

    <div class="loading-overlay" v-if="isLoading">
      <div class="loading-container">
      <div class="loading-spinner"></div>
        <p class="loading-text">Loading your orders...</p>
      </div>
    </div>

    <div v-else>
      <div class="orders-summary" v-if="filteredOrders.length">
        <div class="summary-card">
          <span class="summary-label">Total Orders</span>
          <span class="summary-value">{{ filteredOrders.length }}</span>
        </div>
        <div class="summary-card clickable" :class="{ active: summaryFilter === 'ongoing' }" @click="setSummaryFilter('ongoing')">
          <span class="summary-label">Ongoing</span>
          <span class="summary-value">{{ filteredOrders.filter(o => o.manufacturing_state !== 'done').length }}</span>
        </div>
        <div class="summary-card clickable" :class="{ active: summaryFilter === 'completed' }" @click="setSummaryFilter('completed')">
          <span class="summary-label">Completed</span>
          <span class="summary-value">{{ filteredOrders.filter(o => o.manufacturing_state === 'done').length }}</span>
        </div>
      </div>

      <div class="search-section">
        <div class="search-input-container">
          <svg class="search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="11" cy="11" r="8"></circle>
            <path d="m21 21-4.35-4.35"></path>
          </svg>
          <input
            type="text"
            v-model="searchQuery"
            placeholder="Search by order number or product name..."
            @input="filterOrders"
            class="search-input"
          >
          <div class="search-glow"></div>
        </div>
      </div>

      <div class="orders-list" v-if="filteredOrders.length">
        <div
          class="order-item"
          v-for="order in filteredOrders"
          :key="order.id"
          :class="{ 'expanded': expandedOrderId === order.id }"
        >
          <div class="order-header" @click="toggleOrderExpansion(order.id)">
            <div class="order-identity">
              <div class="order-number-badge">
                <span class="order-number">#{{ order.number }}</span>
              </div>
              <div class="order-datetime">
                <div class="order-date">{{ formatDate(order.date) }}</div>
              <div class="order-time">{{ formatTime(order.date) }}</div>
              </div>
            </div>
            <div class="order-status-and-toggle">
              <div class="order-status-indicator">
                <div :class="['status-dot', getStatusClass(order.manufacturing_state)]"></div>
                <span class="status-text">{{ formatStatus(order.manufacturing_state) }}</span>
              </div>
              <div class="expand-toggle">
                <svg
                  class="expand-icon"
                  :class="{ 'rotated': expandedOrderId === order.id }"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                >
                  <polyline points="6,9 12,15 18,9"></polyline>
                </svg>
              </div>
            </div>
          </div>

          <div class="order-details" v-show="expandedOrderId === order.id">
          <div class="order-production">
              <div class="production-header">
                <h4 class="production-title">Production Progress</h4>
                <div class="progress-percentage">{{ Math.round((productionStageIndex(order.manufacturing_state) + 1) / 4 * 100) }}%</div>
              </div>
            <div class="production-timeline-container">
            <div class="production-timeline">
              <div class="timeline-track">
                <div class="timeline-progress" :style="{ width: progressWidth(order.manufacturing_state) }"></div>
                    <div class="timeline-glow"></div>
              </div>
              <div class="timeline-steps">
                <div :class="['t-step', productionStageIndex(order.manufacturing_state) >= 0 ? 'active' : '']">
                  <span class="dot"></span>
                      <span class="label">Review</span>
                      <div class="step-glow"></div>
                </div>
                <div :class="['t-step', productionStageIndex(order.manufacturing_state) >= 1 ? 'active' : '']">
                  <span class="dot"></span>
                      <span class="label">Queue</span>
                      <div class="step-glow"></div>
                </div>
                <div :class="['t-step', productionStageIndex(order.manufacturing_state) >= 2 ? 'active' : '']">
                  <span class="dot"></span>
                      <span class="label">Progress</span>
                      <div class="step-glow"></div>
                </div>
                <div :class="['t-step', productionStageIndex(order.manufacturing_state) >= 3 ? 'active' : '']">
                  <span class="dot"></span>
                      <span class="label">Complete</span>
                      <div class="step-glow"></div>
                </div>
              </div>
              </div>
            </div>
          </div>

          <div class="order-products" v-if="order.products && order.products.length">
              <div class="products-header">
                <h4 class="products-title">Order Items</h4>
                <span class="products-count">{{ order.products.length }} item{{ order.products.length !== 1 ? 's' : '' }}</span>
              </div>
            <div class="products-list">
              <div 
                v-for="p in order.products"
                :key="`${order.id}-${p.id}-${p.name}`"
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
      expandedOrderId: null,
      summaryFilter: 'all', // 'all', 'ongoing', 'completed'
      isLoading: false
    }
  },
  computed: {
    filteredOrders() {
      // Always show newest first
      let filtered = [...this.orders].sort((a, b) => {
        const da = a.date ? new Date(a.date).getTime() : 0
        const db = b.date ? new Date(b.date).getTime() : 0
        return db - da
      })
      
      // Apply status filter
      if (this.selectedStatus !== 'All') {
        filtered = filtered.filter(order => order.status === this.selectedStatus)
      }
      
      // Apply search filter
      if (this.searchQuery) {
        const query = this.searchQuery.toLowerCase()
        filtered = filtered.filter(order =>
          order.number.toLowerCase().includes(query) ||
          order.products.some(product =>
            product.name.toLowerCase().includes(query)
          )
        )
      }

      // Apply summary filter
      if (this.summaryFilter !== 'all') {
        if (this.summaryFilter === 'ongoing') {
          filtered = filtered.filter(order => order.manufacturing_state !== 'done')
        } else if (this.summaryFilter === 'completed') {
          filtered = filtered.filter(order => order.manufacturing_state === 'done')
        }
      }

      return filtered
    }
  },
  created() {
    this.fetchOrders()
  },
  methods: {
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
        this.orders = Array.isArray(data.orders) ? data.orders : []
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
    toggleOrderExpansion(orderId) {
      this.expandedOrderId = this.expandedOrderId === orderId ? null : orderId
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
    }
  }
}
</script>

<style scoped>
.orders-container {
  min-height: 100vh;
  padding: 24px;
  position: relative;
  overflow: hidden;
}

.orders-container::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  pointer-events: none;
  z-index: 0;
}

.orders-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 36px;
  position: relative;
  z-index: 1;
}

.header-content {
  flex: 1;
}

.orders-title {
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

.orders-subtitle {
  color: #94a3b8;
  font-size: 16px;
  margin: 0;
  font-weight: 400;
  letter-spacing: 0.025em;
}

.search-section {
  display: flex;
  justify-content: center;
  margin-bottom: 28px;
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

.search-input:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow:
    0 0 0 4px rgba(59, 130, 246, 0.15),
    0 8px 32px rgba(59, 130, 246, 0.12);
  transform: translateY(-2px);
}

.search-input::placeholder {
  color: #64748b;
  font-weight: 400;
}

.search-glow {
  position: absolute;
  top: -2px;
  left: -2px;
  right: -2px;
  bottom: -2px;
  background: linear-gradient(135deg, #3b82f6, #8b5cf6, #ec4899);
  border-radius: 18px;
  opacity: 0;
  transition: opacity 0.3s ease;
  z-index: -1;
}

.search-input:focus + .search-glow {
  opacity: 0.5;
}

.loading-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(15, 23, 42, 0.8);
  backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  transition: opacity 0.3s ease;
}

.loading-container {
  text-align: center;
  padding: 48px;
  background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
  border-radius: 24px;
  border: 1px solid #334155;
  box-shadow: 0 25px 50px rgba(0, 0, 0, 0.4);
}

.loading-spinner {
  width: 60px;
  height: 60px;
  border: 4px solid rgba(255, 255, 255, 0.1);
  border-radius: 50%;
  border-top-color: #ffffff;
  animation: spin 0.8s cubic-bezier(0.5, 0, 0.5, 1) infinite;
  box-shadow: 0 0 10px rgba(255, 255, 255, 0.2);
  margin: 0 auto 24px;
}

.loading-text {
  color: #e2e8f0;
  font-size: 16px;
  font-weight: 500;
  margin: 0;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

@keyframes rotate {
  to {
    background-position: 400% 0;
  }
}

.orders-summary {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 20px;
  margin-bottom: 36px;
  position: relative;
  z-index: 1;
}

.summary-card {
  background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
  border: 1px solid #334155;
  border-radius: 16px;
  padding: 24px 20px;
  text-align: center;
  position: relative;
  overflow: hidden;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.summary-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: linear-gradient(90deg, #3b82f6, #8b5cf6, #ec4899);
}

.summary-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.4);
}

.summary-card.clickable {
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.summary-card.clickable:hover {
  transform: translateY(-4px);
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.4);
  border-color: #475569;
}

.summary-card.clickable:active {
  transform: translateY(-2px);
}

.summary-card.active {
  border-color: #3b82f6;
  background: linear-gradient(135deg, #1e40af 0%, #1e293b 100%);
  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.3);
}

.summary-card.active::before {
  background: linear-gradient(90deg, #3b82f6, #1e40af);
}

.summary-label {
  display: block;
  color: #94a3b8;
  font-size: 14px;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 12px;
}

.summary-value {
  display: block;
  font-size: 28px;
  font-weight: 700;
  color: #ffffff;
  line-height: 1;
}

.orders-list {
  display: block;
  position: relative;
  z-index: 1;
}

.order-item {
  background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
  border: 1px solid #334155;
  border-radius: 14px;
  margin-bottom: 14px;
  position: relative;
  overflow: hidden;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.order-item.expanded {
  border-color: #475569;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
}

.order-item:last-child {
  margin-bottom: 0;
}

.order-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 20px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.order-header:hover {
  background: rgba(51, 65, 85, 0.3);
}

.order-status-and-toggle {
  display: flex;
  align-items: center;
  gap: 16px;
}

.expand-toggle {
  padding: 8px;
  border-radius: 8px;
  transition: all 0.2s ease;
  color: #64748b;
}

.expand-toggle:hover {
  background: rgba(100, 116, 139, 0.1);
  color: #94a3b8;
}

.expand-icon {
  width: 20px;
  height: 20px;
  transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.expand-icon.rotated {
  transform: rotate(180deg);
}

.order-identity {
  flex: 1;
}

.order-number-badge {
  display: inline-flex;
  align-items: center;
  background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
  color: #ffffff;
  padding: 12px 20px;
  border-radius: 50px;
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 16px;
  box-shadow: 0 8px 16px rgba(59, 130, 246, 0.3);
}

.order-datetime {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.order-date {
  font-size: 16px;
  font-weight: 600;
  color: #ffffff;
  line-height: 1.2;
}

.order-time {
  font-size: 13px;
  color: #94a3b8;
  font-weight: 400;
}

.order-status-indicator {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 20px;
  background: rgba(30, 41, 59, 0.8);
  border-radius: 50px;
  border: 1px solid #334155;
}

.status-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  flex-shrink: 0;
}

.status-dot.status-review {
  background: linear-gradient(135deg, #f59e0b, #d97706);
  box-shadow: 0 0 12px rgba(245, 158, 11, 0.5);
}

.status-dot.status-queue {
  background: linear-gradient(135deg, #3b82f6, #2563eb);
  box-shadow: 0 0 12px rgba(59, 130, 246, 0.5);
}

.status-dot.status-progress {
  background: linear-gradient(135deg, #8b5cf6, #7c3aed);
  box-shadow: 0 0 12px rgba(139, 92, 246, 0.5);
}

.status-dot.status-complete {
  background: linear-gradient(135deg, #10b981, #059669);
  box-shadow: 0 0 12px rgba(16, 185, 129, 0.5);
}

.status-text {
  font-size: 14px;
  font-weight: 600;
  color: #ffffff;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.order-details {
  border-top: 1px solid #334155;
  padding: 0;
  max-height: 0;
  overflow: hidden;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.order-item.expanded .order-details {
  max-height: 1000px;
  padding: 28px;
}

.order-production {
  margin-bottom: 32px;
}

.production-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.production-title {
  font-size: 16px;
  font-weight: 600;
  color: #ffffff;
  margin: 0;
}

.progress-percentage {
  background: linear-gradient(135deg, #3b82f6, #8b5cf6);
  color: #ffffff;
  padding: 8px 16px;
  border-radius: 20px;
  font-size: 14px;
  font-weight: 600;
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
  height: 6px;
  background: linear-gradient(135deg, #334155 0%, #1e293b 100%);
  border-radius: 999px;
  overflow: hidden;
  margin-bottom: 28px;
}

.timeline-progress {
  position: absolute;
  top: 0;
  left: 0;
  height: 100%;
  background: linear-gradient(90deg, #4ade80, #22c55e, #16a34a);
  border-radius: 999px;
  transition: width 0.8s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow:
    0 0 20px rgba(34, 197, 94, 0.4),
    inset 0 1px 0 rgba(255, 255, 255, 0.2);
}

.timeline-glow {
  position: absolute;
  top: -4px;
  left: 0;
  right: 0;
  bottom: -4px;
  background: linear-gradient(90deg, transparent, rgba(34, 197, 94, 0.3), transparent);
  border-radius: 999px;
  opacity: 0;
  transition: opacity 0.3s ease;
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
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.t-step .dot {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: #334155;
  border: 2px solid #475569;
  position: relative;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  z-index: 2;
}

.t-step .label {
  font-size: 13px;
  font-weight: 500;
  text-align: center;
  max-width: 80px;
  line-height: 1.3;
}

.step-glow {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 40px;
  height: 40px;
  background: radial-gradient(circle, rgba(34, 197, 94, 0.2) 0%, transparent 70%);
  border-radius: 50%;
  opacity: 0;
  transition: opacity 0.3s ease;
}

.t-step.active {
  color: #ffffff;
}

.t-step.active .dot {
  background: linear-gradient(135deg, #22c55e, #16a34a);
  border-color: #10b981;
  box-shadow:
    0 0 20px rgba(34, 197, 94, 0.6),
    0 4px 12px rgba(0, 0, 0, 0.3);
  transform: scale(1.2);
}

.t-step.active .step-glow {
  opacity: 1;
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
  color: #3b82f6;
  padding: 6px 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
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
  padding: 16px;
  background: rgba(30, 41, 59, 0.6);
  border: 1px solid #334155;
  border-radius: 12px;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.product-item:hover {
  background: rgba(30, 41, 59, 0.9);
  border-color: #475569;
  transform: translateX(4px);
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
  color: #3b82f6;
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

@media (max-width: 1024px) {
  .orders-container {
    padding: 20px;
  }

  .orders-title {
    font-size: 26px;
  }

  .orders-summary {
    grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
    gap: 14px;
  }
}

@media (max-width: 768px) {
  .orders-header {
    flex-direction: column;
    gap: 28px;
    align-items: stretch;
  }

  .search-input-container {
    max-width: none;
  }

  .orders-title {
    font-size: 22px;
  }

  .orders-summary {
    grid-template-columns: repeat(2, 1fr);
    gap: 14px;
  }

  .summary-card {
    padding: 20px 14px;
  }

  .summary-value {
    font-size: 22px;
  }

  .order-item {
    margin-bottom: 12px;
  }

  .order-header {
    flex-direction: column;
    gap: 16px;
    align-items: stretch;
    padding: 16px;
  }

  .order-status-and-toggle {
    flex-direction: row;
    justify-content: space-between;
    width: 100%;
  }

  .timeline-steps {
    gap: 8px;
  }

  .t-step .label {
    font-size: 11px;
    max-width: 50px;
  }
}

@media (max-width: 480px) {
  .orders-container {
    padding: 16px;
  }

  .orders-summary {
    grid-template-columns: 1fr;
  }

  .summary-card {
    padding: 18px 14px;
  }

  .order-item {
    margin-bottom: 10px;
  }

  .order-header {
    padding: 14px;
  }

  .order-item.expanded .order-details {
    padding: 20px;
  }

  .production-timeline {
    padding: 20px 0;
  }
}
</style>
