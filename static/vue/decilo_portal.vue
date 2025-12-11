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
          <h2>{{ $t('login.title') }}</h2>
          <p class="login-subtitle">{{ $t('login.subtitle') }}</p>
        </div>
        <form @submit.prevent="login" class="login-form">
          <div class="form-group">
            <div class="input-wrapper">
              <input
                id="email"
                type="email"
                v-model="email"
                :placeholder="$t('login.emailPlaceholder')"
                required
                autocomplete="email"
              >
            </div>
          </div>
          <div class="form-group">
            <div class="input-wrapper">
              <input
                id="password"
                :type="showPassword ? 'text' : 'password'"
                v-model="password"
                :placeholder="$t('login.passwordPlaceholder')"
                required
                autocomplete="current-password"
              >
            </div>
          </div>
          <button type="submit" class="login-button">
            {{ $t('login.signIn') }}
          </button>
          <p class="support-link">
            {{ $t('login.supportPrefix') }} <a href="mailto:support@decilo.be">support@decilo.be</a>
          </p>
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
              :class="{ active: activeTab === 'products' }"
              @click="activeTab = 'products'"
            >
              {{ $t('nav.products') }}
            </button>
            <button 
              class="tab-btn" 
              :class="{ active: activeTab === 'orders' }"
              @click="activeTab = 'orders'"
            >
              {{ $t('nav.orders') }}
            </button>
          </div>
          <div class="profile-menu">
            <div class="profile-icon" @click="toggleProfileMenu">
              <span class="profile-initial">{{ customerInfo.name?.charAt(0).toUpperCase() }}</span>
              <div v-if="showProfileMenu" class="profile-dropdown" @click.stop>
                <div class="profile-info">
                  <strong>{{ customerInfo.name }}</strong>
                  <span>{{ customerInfo.email }}</span>
                </div>
                <div class="profile-language">
                  <div class="language-label">{{ $t('nav.language') }}</div>
                  <button class="language-select" @click.stop="toggleLanguageDropdown">
                    <span class="language-select-inner">
                      <span
                        class="language-flag"
                        :class="languageOptions.find(opt => opt.value === selectedLanguage)?.flagClass"
                        aria-hidden="true"
                      ></span>
                      <span>{{ languageOptions.find(opt => opt.value === selectedLanguage)?.label }}</span>
                    </span>
                    <svg class="language-chevron" :class="{ open: isLanguageOpen }" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <polyline points="6,9 12,15 18,9"></polyline>
                    </svg>
                  </button>
                  <div v-if="isLanguageOpen" class="language-options">
                    <button
                      v-for="option in languageOptions"
                      :key="option.value"
                      class="language-option"
                      :class="{ active: option.value === selectedLanguage }"
                      @click.stop="selectLanguage(option.value)"
                    >
                      <span class="language-option-inner">
                        <span class="language-flag" :class="option.flagClass" aria-hidden="true"></span>
                        <span>{{ option.label }}</span>
                      </span>
                    </button>
                  </div>
                </div>
                <button @click="logout" class="logout-btn">
                  {{ $t('nav.signOut') }}
                </button>
              </div>
            </div>
          </div>
        </div>
      </header>

      <main class="dashboard-content">
        <decilo-product-catalog
          v-if="activeTab === 'products'"
          @go-to-orders="activeTab = 'orders'"
          @token-expired="handleTokenExpired"
        />
        <div v-else-if="activeTab === 'orders'">
          <decilo-orders :customer-info="customerInfo" @token-expired="handleTokenExpired" />
        </div>
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
      activeTab: 'products',
      email: '',
      password: '',
      error: '',
      isLoggedIn: false,
      showPassword: false,
      isLoading: false,
      showProfileMenu: false,
      isSignupMode: false,
      isPasswordResetMode: false,
      customerInfo: {
        name: '',
        email: '',
        id: null
      },
      languageOptions: [
        { value: 'en', label: 'English', flagClass: 'flag-en' },
        { value: 'fr', label: 'Français', flagClass: 'flag-fr' },
        { value: 'nl', label: 'Nederlands', flagClass: 'flag-nl' }
      ],
      selectedLanguage: 'fr',
      isLanguageOpen: false
    }
  },
  mounted() {
    this.installLocaleFetchInterceptor();

    const storedLocale = localStorage.getItem('decilo_locale');
    if (storedLocale) {
      this.selectedLanguage = this.normalizeLanguage(storedLocale);
    }
    this.setLocale(this.selectedLanguage);

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
        this.selectedLanguage = this.normalizeLanguage(this.customerInfo.lang);
        localStorage.setItem('decilo_locale', this.selectedLanguage);
        this.setLocale(this.selectedLanguage);
      }
    }
  },
  methods: {
    setLocale(value) {
      if (!this.$i18n) return;
      if (this.$i18n.global && this.$i18n.global.locale !== undefined) {
        if (typeof this.$i18n.global.locale === 'object' && 'value' in this.$i18n.global.locale) {
          this.$i18n.global.locale.value = value;
        } else {
          this.$i18n.global.locale = value;
        }
      } else if (this.$i18n.locale !== undefined) {
        if (typeof this.$i18n.locale === 'object' && 'value' in this.$i18n.locale) {
          this.$i18n.locale.value = value;
        } else {
          this.$i18n.locale = value;
        }
      }
    },
    async login() {
      if (!this.email || !this.password) {
        this.error = this.$t('login.missingFields');
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
          this.error = data.error || this.$t('login.failed');
          return;
        }
        
        // Store token and user info
        localStorage.setItem('decilo_token', data.token);
        localStorage.setItem('decilo_user', JSON.stringify(data.user));
        
        this.customerInfo = data.user;
        this.isLoggedIn = true;
        this.selectedLanguage = this.normalizeLanguage(data.user?.lang);
        localStorage.setItem('decilo_locale', this.selectedLanguage);
        
      } catch (err) {
        this.error = this.$t('login.failed');
      } finally {
        this.isLoading = false;
      }
    },
    toggleProfileMenu() {
      this.showProfileMenu = !this.showProfileMenu;
      if (!this.showProfileMenu) {
        this.isLanguageOpen = false;
      }
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
      this.isLanguageOpen = false;
      this.selectedLanguage = 'fr';
      localStorage.removeItem('decilo_locale');
    },
    toggleLanguageDropdown() {
      this.isLanguageOpen = !this.isLanguageOpen;
    },
    normalizeLanguage(lang) {
      const map = {
        en: 'en',
        'en_us': 'en',
        'en-gb': 'en',
        'en_gb': 'en',
        fr: 'fr',
        'fr_fr': 'fr',
        'fr-be': 'fr',
        'fr_be': 'fr',
        nl: 'nl',
        'nl_nl': 'nl',
        'nl-be': 'nl',
        'nl_be': 'nl'
      };
      if (!lang) return 'fr';
      return map[String(lang).toLowerCase()] || 'fr';
    },
    installLocaleFetchInterceptor() {
      if (window.__deciloFetchPatched) return;
      window.__deciloFetchPatched = true;

      const originalFetch = window.fetch.bind(window);
      window.fetch = (input, init = {}) => {
        const headers = new Headers(init.headers || {});
        const locale = localStorage.getItem('decilo_locale');
        if (locale) {
          headers.set('X-Locale', locale);
        }
        return originalFetch(input, { ...init, headers });
      };
    },
    selectLanguage(value) {
      this.selectedLanguage = value;
      this.setLocale(value);
      this.isLanguageOpen = false;
      this.customerInfo = { ...this.customerInfo, lang: value };
      localStorage.setItem('decilo_locale', value);
      const storedUser = localStorage.getItem('decilo_user');
      if (storedUser) {
        const parsed = JSON.parse(storedUser);
        parsed.lang = value;
        localStorage.setItem('decilo_user', JSON.stringify(parsed));
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
        console.warn('Could not decode token, treating as expired:', error);
        return true;
      }
    },
    handleTokenExpired() {
      // Clear all authentication data
      this.logout();

      // Show a message to the user
      this.error = this.$t('login.sessionExpired');

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

.input-wrapper {
  display: flex;
  justify-content: center;
}

.form-group input {
  width: 80%;
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
  width: 60%;
  padding: 14px;
  background-color: #ffffff;
  color: #000000;
  border: none;
  border-radius: 6px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
  position: relative;
  overflow: hidden;
}

.login-button:hover {
  background-color: #d0d0d0;
  transform: translateY(-6px) scale(1.02);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.25);
}

.login-button:active {
  transform: translateY(-2px) scale(1.01);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}

.login-button::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.4), transparent);
  transition: left 0.6s ease-out;
}

.login-button:hover::before {
  left: 100%;
}

.error-message {
  color: #ff4444;
  font-size: 14px;
  margin-top: 16px;
  text-align: center;
}

.support-link {
  font-size: 14px;
  color: #888888;
  text-align: center;
  margin-top: 12px;
}

.support-link a {
  color: #ffffff;
  text-decoration: none;
  font-weight: 500;
  transition: color 0.2s;
}

.support-link a:hover {
  color: #cccccc;
  text-decoration: underline;
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
  height: 60px;
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

.profile-language {
  padding: 12px 15px;
  border-bottom: 1px solid #333333;
}

.language-label {
  font-size: 12px;
  color: #888888;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  margin-bottom: 8px;
}

.language-select {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #191919;
  color: #ffffff;
  border: 1px solid #2a2a2a;
  border-radius: 6px;
  padding: 10px 12px;
  cursor: pointer;
  transition: border-color 0.2s, background-color 0.2s;
}

.language-select:hover {
  border-color: #3a3a3a;
  background: #1f1f1f;
}

.language-select-inner {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.language-flag {
  width: 18px;
  height: 12px;
  border-radius: 2px;
  box-shadow: 0 0 0 1px rgba(255, 255, 255, 0.05);
  background: #444444;
  background-size: cover;
  background-position: center;
  background-repeat: no-repeat;
}

.flag-en {
  background-image: url('/static/images/uk_flag.png');
}

.flag-fr {
  background: linear-gradient(90deg, #1b3b8f 0%, #1b3b8f 33.33%, #ffffff 33.33%, #ffffff 66.66%, #c8102e 66.66%, #c8102e 100%);
}

.flag-nl {
  background: linear-gradient(180deg, #ae1c28 0%, #ae1c28 33.33%, #ffffff 33.33%, #ffffff 66.66%, #21468b 66.66%, #21468b 100%);
}

.language-chevron {
  width: 16px;
  height: 16px;
  transform: rotate(0deg);
  transition: transform 0.2s;
}

.language-chevron.open {
  transform: rotate(180deg);
}

.language-options {
  margin-top: 8px;
  background: #161616;
  border: 1px solid #2a2a2a;
  border-radius: 6px;
  overflow: hidden;
}

.language-option {
  width: 100%;
  text-align: left;
  background: none;
  border: none;
  color: #ffffff;
  padding: 10px 12px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.language-option:hover {
  background: #1f1f1f;
}

.language-option.active {
  background: #222222;
  color: #e0e0e0;
}

.language-option-inner {
  display: inline-flex;
  align-items: center;
  gap: 8px;
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
  width: 90%;
  margin: 0 auto;
  padding: 20px 20px;
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
