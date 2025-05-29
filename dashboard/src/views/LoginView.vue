<template>
  <div class="login-container">
    <div class="login-box">
      <div class="login-header">
        <img src="../assets/logo.svg" alt="Hardbake Logo" class="login-logo">
        <h2>{{ $t('auth.welcome') }}</h2>
        <p class="subtitle">{{ $t('auth.signInPrompt') }}</p>
      </div>
      <form @submit.prevent="handleLogin" class="login-form">
        <div class="form-group">
          <label for="username">
            {{ $t('auth.username') }}
          </label>
          <input
            type="text"
            id="username"
            v-model="username"
            required
            :placeholder="$t('auth.usernamePlaceholder')"
          />
        </div>
        <div class="form-group">
          <label for="password">
            {{ $t('auth.password') }}
          </label>
          <input
            type="password"
            id="password"
            v-model="password"
            required
            :placeholder="$t('auth.passwordPlaceholder')"
          />
        </div>
        <div v-if="error" class="error-message">
          {{ error }}
        </div>
        <button type="submit" :disabled="loading" class="login-button">
          {{ loading ? $t('auth.loggingIn') : $t('auth.login') }}
        </button>
      </form>
      <LanguageSwitcher />
    </div>
  </div>
</template>

<script>
import axios from 'axios'
import { serviceHosts } from '../config/hosts';
import { useI18n } from 'vue-i18n';
import LanguageSwitcher from '../components/LanguageSwitcher.vue';

export default {
  name: 'LoginView',
  components: {
    LanguageSwitcher
  },
  setup() {
    const { t } = useI18n();
    return { t };
  },
  data() {
    return {
      username: '',
      password: '',
      error: '',
      loading: false
    }
  },
  methods: {
    async handleLogin() {
      this.loading = true
      this.error = ''
      
      try {
        const response = await axios.post(`${serviceHosts.auth}/auth/token`, null, {
          params: {
            username: this.username,
            password: this.password
          }
        })
        
        // Store the token in a cookie
        document.cookie = `access_token=${response.data.access_token}; path=/`
        
        // Redirect to home page
        this.$router.push('/')
      } catch (err) {
        this.error = err.response?.status === 401 
          ? this.t('auth.errors.invalidCredentials')
          : this.t('auth.errors.generalError')
      } finally {
        this.loading = false
      }
    }
  }
}
</script>

<style scoped>
:global(html), :global(body) {
  height: 100%;
  width: 100%;
  margin: 0;
  padding: 0;
}

.login-container {
  position: fixed;
  inset: 0;
  width: 100vw;
  height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background: linear-gradient(135deg, #2c3e50 0%, #3498db 100%);
  box-sizing: border-box;
  z-index: 1000;
}

.login-box {
  background: white;
  padding: clamp(1.5rem, 4vw, 2.5rem);
  border-radius: clamp(8px, 2vw, 12px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
  width: 100%;
  max-width: min(420px, 90vw);
  animation: fadeIn 0.5s ease-out;
}

.login-header {
  text-align: center;
  margin-bottom: clamp(1.5rem, 4vw, 2rem);
}

.login-logo {
  width: clamp(50px, 15vw, 80px);
  height: clamp(50px, 15vw, 80px);
  margin-bottom: clamp(0.75rem, 2vw, 1rem);
}

h2 {
  color: #2c3e50;
  font-size: clamp(1.3rem, 4vw, 1.8rem);
  margin-bottom: 0.5rem;
  line-height: 1.2;
}

.subtitle {
  color: #7f8c8d;
  font-size: clamp(0.9rem, 2.5vw, 1rem);
  margin-bottom: clamp(0.75rem, 2vw, 1rem);
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: clamp(1rem, 3vw, 1.25rem);
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: clamp(0.375rem, 1.5vw, 0.5rem);
}

label {
  color: #2c3e50;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: clamp(0.9rem, 2.5vw, 1rem);
}

label i {
  color: #3498db;
  font-size: clamp(0.9rem, 2.5vw, 1rem);
}

input {
  width: 100%;
  padding: clamp(0.75rem, 2vw, 0.875rem);
  border: 2px solid #e0e0e0;
  border-radius: clamp(6px, 1.5vw, 8px);
  font-size: clamp(0.9rem, 2.5vw, 1rem);
  transition: all 0.3s ease;
  background-color: #f8f9fa;
}

input:focus {
  outline: none;
  border-color: #3498db;
  background-color: white;
  box-shadow: 0 0 0 3px rgba(52, 152, 219, 0.1);
}

.login-button {
  width: 100%;
  padding: clamp(0.875rem, 2.5vw, 1rem);
  background-color: #3498db;
  color: white;
  border: none;
  border-radius: clamp(6px, 1.5vw, 8px);
  font-size: clamp(0.9rem, 2.5vw, 1rem);
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  margin-top: clamp(0.375rem, 1.5vw, 0.5rem);
}

.login-button:hover:not(:disabled) {
  background-color: #2980b9;
  transform: translateY(-1px);
}

.login-button:disabled {
  background-color: #bdc3c7;
  cursor: not-allowed;
}

.error-message {
  color: #e74c3c;
  background-color: #fde8e8;
  padding: clamp(0.625rem, 2vw, 0.75rem);
  border-radius: clamp(6px, 1.5vw, 8px);
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: clamp(0.8rem, 2.5vw, 0.9rem);
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Responsive Design */
/* Large screens (1200px and up) */
@media (min-width: 1200px) {
  .login-box {
    max-width: 480px;
  }
}

/* Medium screens (768px to 1199px) */
@media (max-width: 1199px) {
  .login-box {
    max-width: 420px;
  }
}

/* Small screens (480px to 767px) */
@media (max-width: 767px) {
  .login-box {
    max-width: 380px;
  }
}

/* Extra small screens (up to 479px) */
@media (max-width: 479px) {
  .login-box {
    max-width: 100%;
  }
}

/* Landscape orientation */
@media (max-height: 600px) and (orientation: landscape) {
  .login-container {
    padding: 1rem;
  }
  
  .login-box {
    padding: 1.25rem;
  }
  
  .login-logo {
    width: 40px;
    height: 40px;
    margin-bottom: 0.5rem;
  }
  
  h2 {
    margin-bottom: 0.25rem;
  }
  
  .subtitle {
    margin-bottom: 0.5rem;
  }
}

/* Dark mode support */
@media (prefers-color-scheme: dark) {
  .login-box {
    background: #1a1a1a;
  }

  h2 {
    color: #ffffff;
  }

  .subtitle {
    color: #a0a0a0;
  }

  label {
    color: #ffffff;
  }

  input {
    background-color: #2d2d2d;
    border-color: #404040;
    color: #ffffff;
  }

  input:focus {
    background-color: #2d2d2d;
  }

  .error-message {
    background-color: rgba(231, 76, 60, 0.1);
  }
}

/* High contrast mode */
@media (forced-colors: active) {
  .login-button {
    border: 2px solid currentColor;
  }
  
  input {
    border: 2px solid currentColor;
  }
}

/* Reduced motion */
@media (prefers-reduced-motion: reduce) {
  .login-box {
    animation: none;
  }
  
  .login-button:hover:not(:disabled) {
    transform: none;
  }
}

.language-switcher {
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid rgba(0, 0, 0, 0.1);
}

/* Dark mode support */
@media (prefers-color-scheme: dark) {
  .language-switcher {
    border-top-color: rgba(255, 255, 255, 0.1);
  }
}
</style> 