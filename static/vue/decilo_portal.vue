<template>
  <div class="portal-container">
    <!-- Global Loading Overlay -->
    <div v-if="isLoading && !isLoggedIn" class="main-loading">
      <div class="spinner">
        <div class="spinner-inner"></div>
      </div>
    </div>

    <!-- Login Section -->
    <div v-if="!isLoggedIn && !isSignupMode && !isPasswordResetMode" class="login-section">
      <div class="login-card">
        <div class="login-header">
          <img 
            src="/static/images/decilo_logo_white.png" 
            alt="Decilo Logo" 
            class="login-logo"
          >
          <h2>B2Audio Portal</h2>
          <p class="login-subtitle">Enter your credentials to access your account</p>
        </div>
        <form @submit.prevent="login" class="login-form">
          <div class="form-group">
            <label for="email">Email address</label>
            <input 
              id="email"
              type="email" 
              v-model="email" 
              placeholder="Enter your email address"
              required
              autocomplete="email"
            >
          </div>
          <div class="form-group">
            <label for="password">Password</label>
            <div class="password-input-wrapper">
              <input 
                id="password"
                :type="showPassword ? 'text' : 'password'"
                v-model="password" 
                placeholder="Enter your password"
                required
                autocomplete="current-password"
              >
            </div>
          </div>
          <button type="submit" class="login-button">
            Sign In
          </button>
          <p v-if="error" class="error-message">{{ error }}</p>
        </form>
      </div>
    </div>

    <!-- Dashboard Section -->
    <div v-else class="dashboard">
      <header class="dashboard-header">
        <div class="header-content">
          <img 
            src="https://static.wixstatic.com/media/27ee73_f8e9ade35c8a4e20805057874a658892~mv2.png/v1/crop/x_193,y_0,w_2613,h_1576/fill/w_160,h_100,al_c,q_85,usm_0.66_1.00_0.01,enc_avif,quality_auto/Logo_blanc-01_edited.png" 
            alt="Decilo Logo" 
            class="dashboard-logo"
          >
          <div class="nav-tabs">
            <button 
              class="tab-btn" 
              :class="{ active: activeTab === 'orders' }"
              @click="activeTab = 'orders'"
            >
              Orders
            </button>
            <button 
              class="tab-btn" 
              :class="{ active: activeTab === 'products' }"
              @click="activeTab = 'products'"
            >
              Products
            </button>
          </div>
          <div class="profile-menu">
            <div class="profile-icon" @click="toggleProfileMenu">
              <span class="profile-initial">{{ customerInfo.name?.charAt(0).toUpperCase() }}</span>
              <div v-if="showProfileMenu" class="profile-dropdown">
                <div class="profile-info">
                  <strong>{{ customerInfo.name }}</strong>
                  <span>{{ customerInfo.email }}</span>
                </div>
                <button @click="logout" class="logout-btn">
                  Sign Out
                </button>
              </div>
            </div>
          </div>
        </div>
      </header>

      <main class="dashboard-content">
        <div v-if="activeTab === 'orders'">
          <div class="welcome-section">
            <h1>Welcome, {{ customerInfo.name }}</h1>
            <p class="subtitle">Follow your custom hearing tips orders</p>
          </div>
          <decilo-orders :customer-info="customerInfo" @token-expired="handleTokenExpired" />
        </div>
        <decilo-product-catalog
          v-else-if="activeTab === 'products'"
          @go-to-orders="activeTab = 'orders'"
          @token-expired="handleTokenExpired"
        />
      </main>
    </div>
  </div>
</template>

<script>
import DeciloProductCatalog from './decilo_product_catalog.vue'
import DeciloOrders from './decilo_orders.vue'

export default {
  name: 'DeciloPortal',
  components: {
    DeciloProductCatalog,
    DeciloOrders
  },
  data() {
    return {
      activeTab: 'orders',
      email: '',
      password: '',
      error: '',
      isLoggedIn: false,
      showPassword: false,
      isLoading: false,
      showProfileMenu: false,
      customerInfo: {
        name: '',
        email: '',
        id: null
      }
    }
  },
  mounted() {
    // Check for stored token on component creation
    const storedToken = localStorage.getItem('decilo_token');
    const storedUser = localStorage.getItem('decilo_user');
    if (storedToken && storedUser) {
      // Check if token is expired before using it
      if (this.isTokenExpired(storedToken)) {
        this.logout();
      } else {
        this.customerInfo = JSON.parse(storedUser);
        this.isLoggedIn = true;
      }
    }
  },
  methods: {
    async login() {
      if (!this.email || !this.password) {
        this.error = 'Please enter your email and password';
        return;
      }

      this.isLoading = true;
      this.error = '';

      try {
        const response = await fetch('/decilo-api/customer-login', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ 
            email: this.email,
            password: this.password 
          })
        });
        
        const data = await response.json();
        
        if (!response.ok) {
          this.error = data.error || 'Login failed. Please try again.';
          return;
        }
        
        // Store token and user info
        localStorage.setItem('decilo_token', data.token);
        localStorage.setItem('decilo_user', JSON.stringify(data.user));
        
        this.customerInfo = data.user;
        this.isLoggedIn = true;
        
      } catch (err) {
        this.error = 'Login failed. Please try again.';
      } finally {
        this.isLoading = false;
      }
    },
    toggleProfileMenu() {
      this.showProfileMenu = !this.showProfileMenu;
    },
    logout() {
      localStorage.removeItem('decilo_token');
      localStorage.removeItem('decilo_user');
      this.isLoggedIn = false;
      this.customerInfo = {
        name: '',
        email: '',
        id: null
      };
      this.email = '';
      this.password = '';
      this.error = '';
      this.showProfileMenu = false;
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
        console.warn('Could not decode token, treating as expired:', error);
        return true;
      }
    },
    handleTokenExpired() {
      // Clear all authentication data
      this.logout();

      // Show a message to the user
      this.error = 'Your session has expired. Please log in again.';

      // Switch to login view
      this.isLoggedIn = false;
    }
  }
}
</script>

<style>
.portal-container {
  min-height: 100vh;
  background-color: #000000;
  color: #ffffff;
  font-family: 'Inter', sans-serif;
}

.login-section {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  padding: 20px;
}

.login-card {
  background: #111111;
  border-radius: 12px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.5);
  padding: 40px;
  width: 100%;
  max-width: 400px;
  text-align: center;
}

.login-logo {
  width: 160px;
  height: 100px;
  margin-bottom: 24px;
  object-fit: contain;
}

.login-header h2 {
  font-size: 28px;
  margin: 0;
  margin-bottom: 10px;
  color: #ffffff;
}

.login-subtitle {
  color: #888888;
  font-size: 14px;
  margin: 0;
  margin-bottom: 32px;
}

.form-group {
  margin-bottom: 24px;
  text-align: left;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  color: #ffffff;
  font-size: 14px;
  font-weight: 500;
}

.form-group input {
  width: 100%;
  padding: 12px 16px;
  background: #222222;
  border: 1px solid #333333;
  border-radius: 6px;
  color: #ffffff;
  font-size: 16px;
  transition: all 0.2s;
}

.form-group input:focus {
  border-color: #ffffff;
  outline: none;
  box-shadow: 0 0 0 2px rgba(255, 255, 255, 0.1);
}

.login-button {
  width: 100%;
  padding: 14px;
  background-color: #ffffff;
  color: #000000;
  border: none;
  border-radius: 6px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.login-button:hover {
  background-color: #f0f0f0;
}

.error-message {
  color: #ff4444;
  font-size: 14px;
  margin-top: 16px;
  text-align: center;
}

.dashboard {
  min-height: 100vh;
}

.dashboard-header {
  background-color: #111111;
  padding: 20px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

.header-content {
  max-width: 1200px;
  margin: 0 auto;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.nav-tabs {
  display: flex;
  gap: 20px;
}

.tab-btn {
  background: none;
  border: none;
  color: #888888;
  font-size: 16px;
  font-weight: 500;
  padding: 8px 16px;
  cursor: pointer;
  transition: color 0.2s;
  position: relative;
}

.tab-btn::after {
  content: '';
  position: absolute;
  bottom: -4px;
  left: 0;
  width: 100%;
  height: 2px;
  background-color: transparent;
  transition: background-color 0.2s;
}

.tab-btn:hover {
  color: #ffffff;
}

.tab-btn.active {
  color: #ffffff;
}

.tab-btn.active::after {
  background-color: #ffffff;
}

.dashboard-logo {
  height: 40px;
  width: auto;
}

.profile-menu {
  position: relative;
}

.profile-icon {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: #333333;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: background-color 0.2s;
}

.profile-initial {
  color: #ffffff;
  font-size: 18px;
  font-weight: bold;
}

.profile-dropdown {
  position: absolute;
  top: 50px;
  right: 0;
  background: #111111;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.3);
  width: 220px;
  z-index: 1000;
}

.profile-info {
  padding: 15px;
  border-bottom: 1px solid #333333;
}

.profile-info strong {
  display: block;
  margin-bottom: 4px;
}

.profile-info span {
  color: #888888;
  font-size: 0.9em;
}

.logout-btn {
  width: 100%;
  padding: 15px;
  background: none;
  border: none;
  color: #ff4444;
  text-align: left;
  cursor: pointer;
  transition: background-color 0.2s;
}

.logout-btn:hover {
  background: #222222;
}

.dashboard-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 40px 20px;
}

.welcome-section {
  margin-bottom: 40px;
}

.welcome-section h1 {
  font-size: 32px;
  margin: 0;
  margin-bottom: 8px;
}

.subtitle {
  color: #888888;
  font-size: 16px;
  margin: 0;
}

.main-loading {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.8);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.spinner {
  width: 40px;
  height: 40px;
  position: relative;
}

.spinner-inner {
  position: absolute;
  width: 100%;
  height: 100%;
  border: 3px solid transparent;
  border-top-color: #ffffff;
  border-radius: 50%;
  animation: spin 1s cubic-bezier(0.76, 0.35, 0.2, 0.75) infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
</style>