<script setup lang="ts">
import { ref } from 'vue'
import { authApi } from '../api'

const emit = defineEmits<{
  login: [data: { token: string; user: any }]
}>()

const username = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)

async function handleSubmit() {
  error.value = ''
  loading.value = true

  try {
    const response = await authApi.login(username.value, password.value)
    emit('login', { token: response.access_token, user: response.user })
  } catch (err: any) {
    error.value = err.response?.data?.detail || 'Login fehlgeschlagen'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login-container">
    <div class="login-card">
      <h2>🔐 Login</h2>
      <p class="subtitle">Internet EIN/AUS Steuerung</p>

      <form @submit.prevent="handleSubmit">
        <div class="form-group">
          <label for="username">Benutzername</label>
          <input
            id="username"
            v-model="username"
            type="text"
            placeholder="lehrer"
            required
            autofocus
          />
        </div>

        <div class="form-group">
          <label for="password">Passwort</label>
          <input
            id="password"
            v-model="password"
            type="password"
            placeholder="••••••••"
            required
          />
        </div>

        <div v-if="error" class="error">{{ error }}</div>

        <button type="submit" :disabled="loading" class="btn-primary">
          {{ loading ? 'Anmeldung...' : 'Anmelden' }}
        </button>
      </form>

      <div class="info-box">
        <p><strong>🏫 Alle Lehrer können alle Zimmer steuern</strong></p>
        <p><strong>Test-Login:</strong></p>
        <p>Benutzername: <code>lehrer</code> oder <code>mueller</code> oder <code>schmidt</code></p>
        <p>Passwort: <code>admin123</code></p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.login-container {
  width: 100%;
  max-width: 450px;
}

.login-card {
  background: white;
  border-radius: 20px;
  padding: 3rem;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
}

h2 {
  margin: 0 0 0.5rem 0;
  color: #333;
  font-size: 2rem;
  text-align: center;
}

.subtitle {
  color: #666;
  text-align: center;
  margin-bottom: 2rem;
}

.form-group {
  margin-bottom: 1.5rem;
}

label {
  display: block;
  margin-bottom: 0.5rem;
  color: #333;
  font-weight: 600;
}

input {
  width: 100%;
  padding: 0.75rem;
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  font-size: 1rem;
  transition: border-color 0.3s;
}

input:focus {
  outline: none;
  border-color: #667eea;
}

.error {
  background: #fee;
  color: #c00;
  padding: 0.75rem;
  border-radius: 8px;
  margin-bottom: 1rem;
  text-align: center;
}

.btn-primary {
  width: 100%;
  padding: 1rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: transform 0.3s;
}

.btn-primary:hover:not(:disabled) {
  transform: translateY(-2px);
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.info-box {
  margin-top: 2rem;
  padding: 1rem;
  background: #f8f9fa;
  border-radius: 8px;
  font-size: 0.875rem;
  text-align: center;
}

.info-box code {
  background: #e0e0e0;
  padding: 0.2rem 0.4rem;
  border-radius: 4px;
  font-family: monospace;
}

.info-box p {
  margin: 0.5rem 0;
}
</style>
