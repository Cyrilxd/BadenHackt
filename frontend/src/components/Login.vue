<script setup lang="ts">
import { ref } from 'vue'
import { authApi } from '../api'

const emit = defineEmits<{
  login: [data: { token: string; user: { username: string; role: string } }]
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
  <div class="login-layout">
    <section class="login-card">
      <div class="login-brand">
        <img src="/zB_Logo.png" alt="zB Logo" class="logo" />
      </div>

      <div class="login-headline">
        <h1>Anmeldung</h1>
        <p>Internetzugang für Schulzimmer zentral steuern</p>
      </div>

      <form class="login-form" @submit.prevent="handleSubmit">
        <label for="username">Benutzername</label>
        <input
          id="username"
          v-model="username"
          type="text"
          placeholder="lehrer"
          autocomplete="username"
          required
          autofocus
        />

        <label for="password">Passwort</label>
        <input
          id="password"
          v-model="password"
          type="password"
          placeholder="••••••••"
          autocomplete="current-password"
          required
        />

        <p v-if="error" class="error-alert">{{ error }}</p>

        <button type="submit" :disabled="loading" class="btn-primary">
          {{ loading ? 'Anmeldung läuft...' : 'Anmelden' }}
        </button>
      </form>

      <div class="credentials-box">
        <p class="credentials-title">Test-Zugänge</p>
        <p>Benutzer: <code>lehrer</code>, <code>mueller</code>, <code>schmidt</code></p>
        <p>Passwort: <code>admin123</code></p>
      </div>
    </section>
  </div>
</template>

<style scoped>
.login-layout {
  display: flex;
  width: 100%;
  justify-content: center;
}

.login-card {
  width: min(460px, 100%);
  border: 1px solid var(--color-border);
  border-radius: 18px;
  background: #fff;
  padding: 2rem;
  box-shadow: 0 18px 40px rgba(38, 89, 31, 0.09);
}

.login-brand {
  display: flex;
  justify-content: center;
  margin-bottom: 1rem;
}

.logo {
  width: 150px;
  height: auto;
}

.login-headline {
  text-align: center;
  margin-bottom: 1.6rem;
}

.login-headline h1 {
  margin: 0;
  color: var(--color-text);
  font-size: 1.4rem;
}

.login-headline p {
  margin-top: 0.4rem;
  color: var(--color-muted);
  font-size: 0.92rem;
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: 0.55rem;
}

label {
  color: var(--color-text);
  font-size: 0.87rem;
  font-weight: 600;
  margin-top: 0.4rem;
}

input {
  border: 1px solid var(--color-border);
  border-radius: 10px;
  padding: 0.7rem 0.8rem;
  font-size: 0.95rem;
}

input:focus {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px rgba(101, 173, 65, 0.15);
}

.error-alert {
  margin: 0.7rem 0 0.2rem;
  border: 1px solid #f3c8c8;
  border-radius: 10px;
  background: #fff4f4;
  padding: 0.6rem 0.75rem;
  color: #9f2a2a;
  font-size: 0.86rem;
}

.btn-primary {
  margin-top: 0.6rem;
  border: 0;
  border-radius: 10px;
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-primary-strong) 100%);
  padding: 0.75rem 0.9rem;
  color: #fff;
  font-size: 0.95rem;
  font-weight: 600;
  cursor: pointer;
}

.btn-primary:hover:not(:disabled) {
  filter: brightness(1.03);
}

.btn-primary:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.credentials-box {
  margin-top: 1.5rem;
  border: 1px solid var(--color-border);
  border-radius: 12px;
  background: #f8fcf6;
  padding: 0.9rem 1rem;
  color: var(--color-muted);
  font-size: 0.84rem;
}

.credentials-title {
  margin-bottom: 0.35rem;
  color: var(--color-text);
  font-weight: 700;
}

.credentials-box p {
  margin: 0.22rem 0;
}

code {
  border-radius: 6px;
  background: #edf3ea;
  padding: 0.1rem 0.35rem;
  font-size: 0.8rem;
}
</style>
