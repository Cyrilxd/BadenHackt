<script setup lang="ts">
import { ref } from 'vue'
import { authApi } from '../api'
import { copy } from '../constants/copy'
import UiButton from './ui/UiButton.vue'

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
    error.value = err.response?.data?.detail || copy.login.errorFallback
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login-layout">
    <section class="login-card">
      <div class="login-brand">
        <img src="/zB_Logo.png" alt="" class="logo" width="150" height="60" />
      </div>

      <div class="login-headline">
        <h1>{{ copy.login.title }}</h1>
        <p>{{ copy.login.subtitle }}</p>
      </div>

      <form class="login-form" @submit.prevent="handleSubmit">
        <label for="username">{{ copy.login.usernameLabel }}</label>
        <input
          id="username"
          v-model="username"
          type="text"
          :placeholder="copy.login.usernamePlaceholder"
          autocomplete="username"
          required
          autofocus
        />

        <label for="password">{{ copy.login.passwordLabel }}</label>
        <input
          id="password"
          v-model="password"
          type="password"
          :placeholder="copy.login.passwordPlaceholder"
          autocomplete="current-password"
          required
        />

        <p v-if="error" class="error-alert">{{ error }}</p>

        <div class="submit-row">
          <UiButton type="submit" variant="primary" block comfortable :disabled="loading">
            {{ loading ? copy.login.submitting : copy.login.submit }}
          </UiButton>
        </div>
      </form>
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
  width: min(var(--layout-login-card-max), 100%);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-2xl);
  background: var(--color-surface);
  padding: 2rem;
  box-shadow: var(--shadow-login);
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
  margin-top: 0.4rem;
  color: var(--color-text);
  font-size: 0.87rem;
  font-weight: 600;
}

input {
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: 0.7rem 0.8rem;
  font-size: 0.95rem;
}

input:focus {
  border-color: var(--color-primary);
  box-shadow: var(--focus-ring);
  outline: none;
}

.error-alert {
  margin: 0.7rem 0 0.2rem;
  border: 1px solid var(--color-error-border);
  border-radius: var(--radius-md);
  background: var(--color-error-bg);
  padding: 0.6rem 0.75rem;
  color: var(--color-error-text);
  font-size: 0.86rem;
}

.submit-row {
  margin-top: 0.6rem;
}
</style>
