<template>
  <div class="ear-impressions-container">
    <!-- Login Section -->
    <div v-if="!isLoggedIn" class="login-section">
      <div class="login-card">
        <div class="login-header">
          <img 
            src="/static/images/decilo_logo_white.png" 
            alt="Decilo Logo" 
            class="login-logo"
          >
          <h2>Ear Impressions Portal</h2>
          <p class="login-subtitle">Sign in to download ear impression files</p>
        </div>
        <form @submit.prevent="login" class="login-form">
          <div class="form-group">
            <div class="input-wrapper">
              <input
                id="email"
                type="email"
                v-model="email"
                placeholder="Email address"
                required
                autocomplete="email"
              >
            </div>
          </div>
          <div class="form-group">
            <div class="input-wrapper">
              <input
                id="password"
                type="password"
                v-model="password"
                placeholder="Password"
                required
                autocomplete="current-password"
              >
            </div>
          </div>
          <button type="submit" class="login-button" :disabled="isLoading">
            <span v-if="isLoading" class="btn-spinner"></span>
            <span v-else>Sign In</span>
          </button>
          <p v-if="error" class="error-message">{{ error }}</p>
        </form>
      </div>
    </div>

    <!-- Dashboard Section -->
    <div v-else class="dashboard">
      <header class="dashboard-header">
        <div class="header-content">
          <div class="header-left">
            <img 
              src="/static/images/decilo_logo_white.png" 
              alt="Decilo Logo" 
              class="dashboard-logo"
            >
            <div class="header-title">
              <h1>Ear Impressions</h1>
              <span class="header-badge">Download Portal</span>
            </div>
          </div>
          <div class="header-right">
            <div class="user-info">
              <span class="user-name">{{ customerInfo.name }}</span>
              <button @click="logout" class="logout-btn">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path>
                  <polyline points="16 17 21 12 16 7"></polyline>
                  <line x1="21" y1="12" x2="9" y2="12"></line>
                </svg>
                Sign Out
              </button>
            </div>
          </div>
        </div>
      </header>

      <main class="dashboard-content">
        <!-- Filters Section -->
        <div class="filters-section">
          <div class="filters-row">
            <div class="filter-group">
              <label>Designer</label>
              <select v-model="selectedDesigner" @change="fetchOrders" class="filter-select">
                <option value="">All Designers</option>
                <option v-for="designer in designers" :key="designer" :value="designer">
                  {{ designer }}
                </option>
              </select>
            </div>
            <div class="filter-group">
              <label>Files</label>
              <label class="toggle-filter">
                <input 
                  type="checkbox" 
                  v-model="onlyWithFiles" 
                  @change="fetchOrders"
                  class="toggle-checkbox"
                >
                <span class="toggle-slider"></span>
                <span class="toggle-label">Only with files</span>
              </label>
            </div>
            <div class="filter-group search-group">
              <label>Search MO</label>
              <div class="search-input-wrapper">
                <svg class="search-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <circle cx="11" cy="11" r="8"></circle>
                  <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
                </svg>
                <input 
                  type="text" 
                  v-model="searchQuery" 
                  @input="debouncedSearch"
                  placeholder="Search by MO name..."
                  class="search-input"
                >
              </div>
            </div>
            <div class="filter-actions">
              <button @click="refreshOrders" class="refresh-btn" :disabled="isLoadingOrders">
                <svg :class="{ spinning: isLoadingOrders }" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M23 4v6h-6"></path>
                  <path d="M1 20v-6h6"></path>
                  <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"></path>
                </svg>
                Refresh
              </button>
            </div>
          </div>
        </div>

        <!-- Selection Summary -->
        <div v-if="selectedOrders.length > 0" class="selection-summary">
          <div class="selection-info">
            <span class="selection-count">{{ selectedOrders.length }}</span>
            <span class="selection-label">orders selected</span>
            <span class="file-count">({{ totalFilesSelected }} files)</span>
          </div>
          <div class="selection-actions">
            <button @click="clearSelection" class="clear-btn">Clear Selection</button>
            <button @click="downloadSelected" class="download-btn" :disabled="isDownloading">
              <svg v-if="!isDownloading" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                <polyline points="7 10 12 15 17 10"></polyline>
                <line x1="12" y1="15" x2="12" y2="3"></line>
              </svg>
              <span v-if="isDownloading" class="btn-spinner"></span>
              <span v-else>Download ZIP</span>
            </button>
            <button @click="markSelectedAsDone" class="mark-done-btn" :disabled="isMarkingDone">
              <svg v-if="!isMarkingDone" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="20 6 9 17 4 12"></polyline>
              </svg>
              <span v-if="isMarkingDone" class="btn-spinner"></span>
              <span v-else>Mark as Done</span>
            </button>
          </div>
        </div>

        <!-- Orders Table -->
        <div class="orders-table-container">
          <div v-if="isLoadingOrders" class="loading-overlay">
            <div class="loading-spinner"></div>
            <span>Loading orders...</span>
          </div>

          <table v-else-if="orders.length > 0" class="orders-table">
            <thead>
              <tr>
                <th class="checkbox-col">
                  <input 
                    type="checkbox" 
                    :checked="allSelected" 
                    @change="toggleSelectAll"
                    class="checkbox"
                  >
                </th>
                <th>MO Reference</th>
                <th>Product</th>
                <th>Designer</th>
                <th>Operation</th>
                <th>Origin</th>
                <th class="files-col">Files</th>
                <th class="actions-col">Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr 
                v-for="order in orders" 
                :key="order.id"
                :class="{ selected: isOrderSelected(order.id) }"
              >
                <td class="checkbox-col">
                  <input 
                    type="checkbox" 
                    :checked="isOrderSelected(order.id)"
                    @change="toggleOrderSelection(order)"
                    class="checkbox"
                    :disabled="!order.has_left_ear && !order.has_right_ear"
                  >
                </td>
                <td class="mo-name">{{ order.name }}</td>
                <td class="product-name">{{ order.product || '-' }}</td>
                <td>{{ order.designer || '-' }}</td>
                <td>
                  <span class="operation-badge" :class="getOperationClass(order.operation)">
                    {{ order.operation || '-' }}
                  </span>
                </td>
                <td>{{ order.origin || '-' }}</td>
                <td class="files-col">
                  <div class="file-indicators">
                    <span 
                      class="file-indicator" 
                      :class="{ available: order.has_left_ear, unavailable: !order.has_left_ear }"
                      title="Left Ear"
                    >
                      L
                    </span>
                    <span 
                      class="file-indicator" 
                      :class="{ available: order.has_right_ear, unavailable: !order.has_right_ear }"
                      title="Right Ear"
                    >
                      R
                    </span>
                  </div>
                </td>
                <td class="actions-col">
                  <div class="action-buttons">
                    <div class="download-actions">
                      <button 
                        v-if="order.has_left_ear"
                        @click="downloadSingle(order.id, 'left')"
                        class="action-btn"
                        title="Download Left Ear"
                      >
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                          <polyline points="7 10 12 15 17 10"></polyline>
                          <line x1="12" y1="15" x2="12" y2="3"></line>
                        </svg>
                        L
                      </button>
                      <button 
                        v-if="order.has_right_ear"
                        @click="downloadSingle(order.id, 'right')"
                        class="action-btn"
                        title="Download Right Ear"
                      >
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                          <polyline points="7 10 12 15 17 10"></polyline>
                          <line x1="12" y1="15" x2="12" y2="3"></line>
                        </svg>
                        R
                      </button>
                    </div>
                    <button 
                      @click="markSingleAsDone(order)"
                      class="action-btn action-btn-done"
                      title="Mark as Done (Set to 3D Printing)"
                      :disabled="order.isMarking"
                    >
                      <svg v-if="!order.isMarking" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <polyline points="20 6 9 17 4 12"></polyline>
                      </svg>
                      <span v-if="order.isMarking" class="btn-spinner-small"></span>
                      <span v-else>Mark As Done</span>
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>

          <div v-else class="empty-state">
            <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1">
              <path d="M12 2L2 7l10 5 10-5-10-5z"></path>
              <path d="M2 17l10 5 10-5"></path>
              <path d="M2 12l10 5 10-5"></path>
            </svg>
            <h3>No Manufacturing Orders Found</h3>
            <p>No orders match your current filters.</p>
          </div>
        </div>

        <!-- Pagination -->
        <div v-if="totalOrders > limit" class="pagination">
          <button 
            @click="previousPage" 
            :disabled="offset === 0"
            class="pagination-btn"
          >
            Previous
          </button>
          <span class="pagination-info">
            Showing {{ offset + 1 }} - {{ Math.min(offset + limit, totalOrders) }} of {{ totalOrders }}
          </span>
          <button 
            @click="nextPage" 
            :disabled="offset + limit >= totalOrders"
            class="pagination-btn"
          >
            Next
          </button>
        </div>
      </main>
    </div>
  </div>
</template>

<script>
export default {
  name: 'EarImpressionsPortal',
  data() {
    return {
      // Auth state
      isLoggedIn: false,
      isLoading: false,
      email: '',
      password: '',
      error: '',
      customerInfo: {
        name: '',
        email: '',
        id: null
      },

      // Data state
      orders: [],
      designers: [],
      userMatchedDesigners: [],
      selectedDesigner: '',
      searchQuery: '',
      onlyWithFiles: false,
      selectedOrders: [],
      isLoadingOrders: false,
      isDownloading: false,
      isMarkingDone: false,

      // Pagination
      offset: 0,
      limit: 50,
      totalOrders: 0,

      // Debounce
      searchTimeout: null
    }
  },
  computed: {
    allSelected() {
      const selectableOrders = this.orders.filter(o => o.has_left_ear || o.has_right_ear)
      return selectableOrders.length > 0 && selectableOrders.every(o => this.isOrderSelected(o.id))
    },
    totalFilesSelected() {
      let count = 0
      for (const orderId of this.selectedOrders) {
        const order = this.orders.find(o => o.id === orderId)
        if (order) {
          if (order.has_left_ear) count++
          if (order.has_right_ear) count++
        }
      }
      return count
    }
  },
  mounted() {
    // Check for stored token
    const storedToken = localStorage.getItem('decilo_token')
    const storedUser = localStorage.getItem('decilo_user')
    if (storedToken && storedUser) {
      if (this.isTokenExpired(storedToken)) {
        this.logout()
      } else {
        this.customerInfo = JSON.parse(storedUser)
        this.isLoggedIn = true
        this.initializeData()
      }
    }
  },
  methods: {
    async login() {
      if (!this.email || !this.password) {
        this.error = 'Please enter email and password'
        return
      }

      this.isLoading = true
      this.error = ''

      try {
        const response = await fetch('/decilo-api/customer-login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email: this.email, password: this.password })
        })

        const data = await response.json()

        if (!response.ok) {
          this.error = data.error || 'Login failed'
          return
        }

        localStorage.setItem('decilo_token', data.token)
        localStorage.setItem('decilo_user', JSON.stringify(data.user))

        this.customerInfo = data.user
        this.isLoggedIn = true
        this.initializeData()

      } catch (err) {
        this.error = 'Login failed. Please try again.'
      } finally {
        this.isLoading = false
      }
    },

    logout() {
      localStorage.removeItem('decilo_token')
      localStorage.removeItem('decilo_user')
      this.isLoggedIn = false
      this.customerInfo = { name: '', email: '', id: null }
      this.email = ''
      this.password = ''
      this.error = ''
      this.orders = []
      this.selectedOrders = []
    },

    isTokenExpired(token) {
      try {
        const base64Payload = token.split('.')[1]
        const payload = JSON.parse(atob(base64Payload))
        return payload.exp < Date.now() / 1000
      } catch {
        return true
      }
    },

    getAuthHeaders() {
      const token = localStorage.getItem('decilo_token')
      return {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    },

    async initializeData() {
      await Promise.all([this.fetchDesigners(), this.fetchOrders()])
    },

    async fetchDesigners() {
      try {
        const response = await fetch('/ear-impressions-api/designers', {
          headers: this.getAuthHeaders()
        })

        if (response.status === 401) {
          this.logout()
          return
        }

        const data = await response.json()
        this.designers = data.designers || []
        this.userMatchedDesigners = data.user_matched_designers || []

        // Auto-select user's matched designer if available
        if (this.userMatchedDesigners.length > 0) {
          this.selectedDesigner = this.userMatchedDesigners[0]
        }
      } catch (err) {
        console.error('Failed to fetch designers:', err)
      }
    },

    async fetchOrders() {
      this.isLoadingOrders = true
      try {
        const params = new URLSearchParams()
        if (this.selectedDesigner) params.append('designer', this.selectedDesigner)
        if (this.searchQuery) params.append('search', this.searchQuery)
        if (this.onlyWithFiles) params.append('has_files', 'true')
        params.append('limit', this.limit)
        params.append('offset', this.offset)

        const response = await fetch(`/ear-impressions-api/manufacturing-orders?${params}`, {
          headers: this.getAuthHeaders()
        })

        if (response.status === 401) {
          this.logout()
          return
        }

        const data = await response.json()
        this.orders = data.orders || []
        this.totalOrders = data.total || 0

      } catch (err) {
        console.error('Failed to fetch orders:', err)
      } finally {
        this.isLoadingOrders = false
      }
    },

    refreshOrders() {
      this.offset = 0
      this.fetchOrders()
    },

    debouncedSearch() {
      if (this.searchTimeout) clearTimeout(this.searchTimeout)
      this.searchTimeout = setTimeout(() => {
        this.offset = 0
        this.fetchOrders()
      }, 300)
    },

    isOrderSelected(orderId) {
      return this.selectedOrders.includes(orderId)
    },

    toggleOrderSelection(order) {
      if (!order.has_left_ear && !order.has_right_ear) return

      const idx = this.selectedOrders.indexOf(order.id)
      if (idx === -1) {
        this.selectedOrders.push(order.id)
      } else {
        this.selectedOrders.splice(idx, 1)
      }
    },

    toggleSelectAll() {
      const selectableOrders = this.orders.filter(o => o.has_left_ear || o.has_right_ear)
      if (this.allSelected) {
        // Deselect all on current page
        for (const order of selectableOrders) {
          const idx = this.selectedOrders.indexOf(order.id)
          if (idx !== -1) this.selectedOrders.splice(idx, 1)
        }
      } else {
        // Select all on current page
        for (const order of selectableOrders) {
          if (!this.selectedOrders.includes(order.id)) {
            this.selectedOrders.push(order.id)
          }
        }
      }
    },

    clearSelection() {
      this.selectedOrders = []
    },

    async downloadSelected() {
      if (this.selectedOrders.length === 0) return

      this.isDownloading = true
      try {
        const response = await fetch('/ear-impressions-api/download', {
          method: 'POST',
          headers: this.getAuthHeaders(),
          body: JSON.stringify({
            mo_ids: this.selectedOrders,
            sides: ['left', 'right']
          })
        })

        if (response.status === 401) {
          this.logout()
          return
        }

        if (!response.ok) {
          const err = await response.json()
          alert(err.error || 'Download failed')
          return
        }

        // Trigger file download
        const blob = await response.blob()
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        const disposition = response.headers.get('Content-Disposition')
        const filename = disposition?.match(/filename="(.+)"/)?.[1] || 'ear_impressions.zip'
        a.download = filename
        document.body.appendChild(a)
        a.click()
        a.remove()
        window.URL.revokeObjectURL(url)

        // Clear selection after successful download
        this.selectedOrders = []

      } catch (err) {
        console.error('Download failed:', err)
        alert('Download failed. Please try again.')
      } finally {
        this.isDownloading = false
      }
    },

    async downloadSingle(moId, side) {
      try {
        const response = await fetch(`/ear-impressions-api/download-single?mo_id=${moId}&side=${side}`, {
          headers: this.getAuthHeaders()
        })

        if (response.status === 401) {
          this.logout()
          return
        }

        if (!response.ok) {
          const err = await response.json()
          alert(err.error || 'Download failed')
          return
        }

        const blob = await response.blob()
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        const disposition = response.headers.get('Content-Disposition')
        const filename = disposition?.match(/filename="(.+)"/)?.[1] || `${side}_ear.stl`
        a.download = filename
        document.body.appendChild(a)
        a.click()
        a.remove()
        window.URL.revokeObjectURL(url)

      } catch (err) {
        console.error('Download failed:', err)
        alert('Download failed. Please try again.')
      }
    },

    getOperationClass(operation) {
      if (!operation) return ''
      const op = operation.toLowerCase()
      if (op.includes('to do')) return 'operation-todo'
      if (op.includes('design 3d')) return 'operation-design'
      return ''
    },

    previousPage() {
      if (this.offset >= this.limit) {
        this.offset -= this.limit
        this.fetchOrders()
      }
    },

    nextPage() {
      if (this.offset + this.limit < this.totalOrders) {
        this.offset += this.limit
        this.fetchOrders()
      }
    },

    async markSelectedAsDone() {
      if (this.selectedOrders.length === 0) return

      if (!confirm(`Are you sure you want to mark ${this.selectedOrders.length} order(s) as done?\n\nThis will set the operation to "3D Printing".`)) {
        return
      }

      this.isMarkingDone = true
      try {
        const response = await fetch('/ear-impressions-api/mark-done', {
          method: 'POST',
          headers: this.getAuthHeaders(),
          body: JSON.stringify({ mo_ids: this.selectedOrders })
        })

        if (response.status === 401) {
          this.logout()
          return
        }

        const data = await response.json()

        if (!response.ok) {
          alert(data.error || 'Failed to mark orders as done')
          return
        }

        // Success - refresh the list and clear selection
        alert(data.message || 'Orders marked as done successfully')
        this.selectedOrders = []
        this.fetchOrders()

      } catch (err) {
        console.error('Mark as done failed:', err)
        alert('Failed to mark orders as done. Please try again.')
      } finally {
        this.isMarkingDone = false
      }
    },

    async markSingleAsDone(order) {
      if (!confirm(`Mark "${order.name}" as done?\n\nThis will set the operation to "3D Printing".`)) {
        return
      }

      // Set loading state on the order
      order.isMarking = true

      try {
        const response = await fetch(`/ear-impressions-api/mark-done/${order.id}`, {
          method: 'POST',
          headers: this.getAuthHeaders()
        })

        if (response.status === 401) {
          this.logout()
          return
        }

        const data = await response.json()

        if (!response.ok) {
          alert(data.error || 'Failed to mark order as done')
          return
        }

        // Success - refresh the list
        this.fetchOrders()

      } catch (err) {
        console.error('Mark as done failed:', err)
        alert('Failed to mark order as done. Please try again.')
      } finally {
        order.isMarking = false
      }
    }
  }
}
</script>

<style>
.ear-impressions-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #0a0a0f 0%, #1a1a2e 50%, #16213e 100%);
  color: #e8e8e8;
  font-family: 'DM Sans', -apple-system, BlinkMacSystemFont, sans-serif;
}

/* Login Section */
.login-section {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  padding: 20px;
}

.login-card {
  background: rgba(20, 20, 35, 0.9);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 20px;
  box-shadow: 0 25px 50px rgba(0, 0, 0, 0.5);
  padding: 48px 40px;
  width: 100%;
  max-width: 420px;
  text-align: center;
}

.login-logo {
  width: 140px;
  height: auto;
  margin-bottom: 24px;
  filter: drop-shadow(0 4px 8px rgba(0, 0, 0, 0.3));
}

.login-header h2 {
  font-family: 'Space Mono', monospace;
  font-size: 24px;
  font-weight: 700;
  margin: 0 0 8px 0;
  color: #fff;
  letter-spacing: -0.5px;
}

.login-subtitle {
  color: #8888a0;
  font-size: 14px;
  margin: 0 0 32px 0;
}

.login-form .form-group {
  margin-bottom: 20px;
}

.input-wrapper {
  display: flex;
  justify-content: center;
}

.login-form input {
  width: 100%;
  padding: 14px 18px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  color: #fff;
  font-size: 15px;
  font-family: inherit;
  transition: all 0.2s ease;
}

.login-form input:focus {
  outline: none;
  border-color: #6366f1;
  background: rgba(99, 102, 241, 0.08);
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.15);
}

.login-form input::placeholder {
  color: #6b6b80;
}

.login-button {
  width: 100%;
  padding: 14px;
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  color: #fff;
  border: none;
  border-radius: 12px;
  font-size: 15px;
  font-weight: 600;
  font-family: inherit;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.login-button:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(99, 102, 241, 0.4);
}

.login-button:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.error-message {
  color: #f87171;
  font-size: 13px;
  margin-top: 16px;
  padding: 10px;
  background: rgba(248, 113, 113, 0.1);
  border-radius: 8px;
}

/* Dashboard */
.dashboard {
  min-height: 100vh;
}

.dashboard-header {
  background: rgba(15, 15, 25, 0.95);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  padding: 16px 32px;
  position: sticky;
  top: 0;
  z-index: 100;
}

.header-content {
  max-width: 1600px;
  margin: 0 auto;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 20px;
}

.dashboard-logo {
  height: 44px;
  width: auto;
}

.header-title h1 {
  font-family: 'Space Mono', monospace;
  font-size: 20px;
  font-weight: 700;
  margin: 0;
  color: #fff;
}

.header-badge {
  display: inline-block;
  padding: 3px 10px;
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  border-radius: 20px;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.header-right {
  display: flex;
  align-items: center;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 16px;
}

.user-name {
  color: #a0a0b8;
  font-size: 14px;
}

.logout-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  color: #e8e8e8;
  font-size: 13px;
  font-family: inherit;
  cursor: pointer;
  transition: all 0.2s ease;
}

.logout-btn:hover {
  background: rgba(248, 113, 113, 0.15);
  border-color: rgba(248, 113, 113, 0.3);
  color: #f87171;
}

/* Dashboard Content */
.dashboard-content {
  max-width: 1600px;
  margin: 0 auto;
  padding: 24px 32px;
}

/* Filters */
.filters-section {
  background: rgba(20, 20, 35, 0.6);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 16px;
  padding: 20px 24px;
  margin-bottom: 20px;
}

.filters-row {
  display: flex;
  align-items: flex-end;
  gap: 20px;
  flex-wrap: wrap;
}

.filter-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.filter-group label {
  font-size: 12px;
  font-weight: 600;
  color: #8888a0;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.filter-select {
  min-width: 200px;
  padding: 10px 14px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 10px;
  color: #e8e8e8;
  font-size: 14px;
  font-family: inherit;
  cursor: pointer;
  transition: all 0.2s ease;
}

.filter-select:focus {
  outline: none;
  border-color: #6366f1;
}

.filter-select option {
  background: #1a1a2e;
  color: #e8e8e8;
}

/* Toggle Filter */
.toggle-filter {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 14px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s ease;
  user-select: none;
}

.toggle-filter:hover {
  background: rgba(255, 255, 255, 0.06);
  border-color: rgba(255, 255, 255, 0.15);
}

.toggle-checkbox {
  display: none;
}

.toggle-slider {
  position: relative;
  width: 36px;
  height: 20px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 20px;
  transition: all 0.3s ease;
}

.toggle-slider::after {
  content: '';
  position: absolute;
  top: 3px;
  left: 3px;
  width: 14px;
  height: 14px;
  background: #8888a0;
  border-radius: 50%;
  transition: all 0.3s ease;
}

.toggle-checkbox:checked + .toggle-slider {
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
}

.toggle-checkbox:checked + .toggle-slider::after {
  left: 19px;
  background: #fff;
}

.toggle-label {
  font-size: 13px;
  color: #a0a0b8;
  white-space: nowrap;
}

.toggle-checkbox:checked ~ .toggle-label {
  color: #e8e8e8;
}

.search-group {
  flex: 1;
  min-width: 250px;
}

.search-input-wrapper {
  position: relative;
}

.search-icon {
  position: absolute;
  left: 14px;
  top: 50%;
  transform: translateY(-50%);
  color: #6b6b80;
}

.search-input {
  width: 50%;
  padding: 10px 14px 10px 44px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 10px;
  color: #e8e8e8;
  font-size: 14px;
  font-family: inherit;
  transition: all 0.2s ease;
}

.search-input:focus {
  outline: none;
  border-color: #6366f1;
}

.search-input::placeholder {
  color: #6b6b80;
}

.filter-actions {
  margin-left: auto;
}

.refresh-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 18px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 10px;
  color: #e8e8e8;
  font-size: 14px;
  font-family: inherit;
  cursor: pointer;
  transition: all 0.2s ease;
}

.refresh-btn:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.1);
  border-color: rgba(255, 255, 255, 0.2);
}

.refresh-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.refresh-btn svg.spinning {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* Selection Summary */
.selection-summary {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.15) 0%, rgba(139, 92, 246, 0.15) 100%);
  border: 1px solid rgba(99, 102, 241, 0.3);
  border-radius: 12px;
  padding: 16px 24px;
  margin-bottom: 20px;
}

.selection-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.selection-count {
  font-family: 'Space Mono', monospace;
  font-size: 24px;
  font-weight: 700;
  color: #6366f1;
}

.selection-label {
  font-size: 14px;
  color: #a0a0b8;
}

.file-count {
  font-size: 13px;
  color: #8888a0;
}

.selection-actions {
  display: flex;
  gap: 12px;
}

.clear-btn {
  padding: 10px 18px;
  background: transparent;
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 10px;
  color: #a0a0b8;
  font-size: 14px;
  font-family: inherit;
  cursor: pointer;
  transition: all 0.2s ease;
}

.clear-btn:hover {
  background: rgba(255, 255, 255, 0.05);
  color: #e8e8e8;
}

.download-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 24px;
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  border: none;
  border-radius: 10px;
  color: #fff;
  font-size: 14px;
  font-weight: 600;
  font-family: inherit;
  cursor: pointer;
  transition: all 0.2s ease;
}

.download-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 6px 20px rgba(99, 102, 241, 0.4);
}

.download-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.mark-done-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 24px;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 10px;
  color: #e8e8e8;
  font-size: 14px;
  font-weight: 600;
  font-family: inherit;
  cursor: pointer;
  transition: all 0.2s ease;
}

.mark-done-btn:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.12);
  border-color: rgba(255, 255, 255, 0.25);
}

.mark-done-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

/* Table */
.orders-table-container {
  background: rgba(20, 20, 35, 0.6);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 16px;
  overflow: hidden;
  position: relative;
}

.loading-overlay {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  padding: 80px 20px;
  color: #8888a0;
}

.orders-table {
  width: 100%;
  border-collapse: collapse;
}

.orders-table thead {
  background: rgba(0, 0, 0, 0.3);
}

.orders-table th {
  padding: 14px 16px;
  text-align: left;
  font-size: 12px;
  font-weight: 600;
  color: #8888a0;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}

.orders-table td {
  padding: 14px 16px;
  font-size: 14px;
  color: #c0c0d0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.04);
}

.orders-table tbody tr {
  transition: background 0.15s ease;
}

.orders-table tbody tr:hover {
  background: rgba(255, 255, 255, 0.02);
}

.orders-table tbody tr.selected {
  background: rgba(99, 102, 241, 0.1);
}

.checkbox-col {
  width: 50px;
  text-align: center;
}

.checkbox {
  width: 18px;
  height: 18px;
  accent-color: #6366f1;
  cursor: pointer;
}

.checkbox:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

.mo-name {
  font-family: 'Space Mono', monospace;
  font-weight: 600;
  color: #fff;
}

.product-name {
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.operation-badge {
  display: inline-block;
  padding: 4px 10px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 500;
  background: rgba(255, 255, 255, 0.05);
}

.operation-badge.operation-todo {
  background: rgba(251, 191, 36, 0.15);
  color: #fbbf24;
}

.operation-badge.operation-design {
  background: rgba(34, 197, 94, 0.15);
  color: #22c55e;
}

.files-col {
  width: 80px;
}

.file-indicators {
  display: flex;
  gap: 6px;
}

.file-indicator {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 26px;
  height: 26px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 700;
  font-family: 'Space Mono', monospace;
}

.file-indicator.available {
  background: rgba(34, 197, 94, 0.15);
  color: #22c55e;
  border: 1px solid rgba(34, 197, 94, 0.3);
}

.file-indicator.unavailable {
  background: rgba(255, 255, 255, 0.03);
  color: #4a4a5a;
  border: 1px solid rgba(255, 255, 255, 0.05);
}

.actions-col {
  width: 240px;
}

.action-buttons {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
  width: 100%;
}

.download-actions {
  display: flex;
  gap: 6px;
}

.action-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 10px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 6px;
  color: #a0a0b8;
  font-size: 12px;
  font-weight: 600;
  font-family: 'Space Mono', monospace;
  cursor: pointer;
  transition: all 0.2s ease;
}

.action-btn:hover {
  background: rgba(99, 102, 241, 0.15);
  border-color: rgba(99, 102, 241, 0.3);
  color: #6366f1;
}

.action-btn-done {
  margin-left: auto;
}

.action-btn-done:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-spinner-small {
  width: 12px;
  height: 12px;
  border: 2px solid rgba(255, 255, 255, 0.2);
  border-top-color: #a0a0b8;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

/* Empty State */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 20px;
  color: #6b6b80;
}

.empty-state svg {
  margin-bottom: 20px;
  opacity: 0.5;
}

.empty-state h3 {
  margin: 0 0 8px 0;
  font-size: 18px;
  color: #8888a0;
}

.empty-state p {
  margin: 0;
  font-size: 14px;
}

/* Pagination */
.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 20px;
  padding: 24px;
}

.pagination-btn {
  padding: 10px 20px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 10px;
  color: #e8e8e8;
  font-size: 14px;
  font-family: inherit;
  cursor: pointer;
  transition: all 0.2s ease;
}

.pagination-btn:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.1);
}

.pagination-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.pagination-info {
  font-size: 14px;
  color: #8888a0;
}

/* Spinner */
.btn-spinner {
  width: 18px;
  height: 18px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 3px solid rgba(99, 102, 241, 0.2);
  border-top-color: #6366f1;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

/* Responsive */
@media (max-width: 768px) {
  .header-content {
    flex-direction: column;
    gap: 16px;
  }

  .filters-row {
    flex-direction: column;
    align-items: stretch;
  }

  .filter-actions {
    margin-left: 0;
  }

  .selection-summary {
    flex-direction: column;
    gap: 16px;
    text-align: center;
  }

  .orders-table {
    font-size: 13px;
  }

  .orders-table th,
  .orders-table td {
    padding: 10px 12px;
  }
}
</style>

