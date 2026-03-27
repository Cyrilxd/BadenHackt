<script setup lang="ts">
import { onMounted, ref } from 'vue'
import Login from './components/Login.vue'
import Dashboard from './components/Dashboard.vue'

type User = { username: string; role: string }

const isAuthenticated = ref(false)
const user = ref<User | null>(null)

onMounted(() => {
  const token = localStorage.getItem('token')
  const userData = localStorage.getItem('user')

  if (!token || !userData) return

  try {
    user.value = JSON.parse(userData)
    isAuthenticated.value = true
  } catch {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
  }
})

function handleLogin(loginData: { token: string; user: User }) {
  localStorage.setItem('token', loginData.token)
  localStorage.setItem('user', JSON.stringify(loginData.user))
  user.value = loginData.user
  isAuthenticated.value = true
}

function handleLogout() {
  localStorage.removeItem('token')
  localStorage.removeItem('user')
  user.value = null
  isAuthenticated.value = false
}
</script>

<template>
  <div class="app-shell">
    <header v-if="isAuthenticated" class="topbar">
      <div class="topbar-inner">
        <div class="brand">
          <img src="/zB_Logo.png" alt="zB Logo" class="brand-logo" />
          <div class="brand-copy">
            <p class="brand-title">Internet Steuerung</p>
            <p class="brand-subtitle">Schulzimmer VLAN Verwaltung</p>
          </div>
        </div>

        <div class="session">
          <span class="session-pill">{{ user?.username }}</span>
          <button type="button" class="session-pill session-pill-button" @click="handleLogout">
            Abmelden
          </button>
        </div>
      </div>
    </header>

    <main class="app-main" :class="{ 'app-main-auth': isAuthenticated }">
      <Login v-if="!isAuthenticated" @login="handleLogin" />
      <Dashboard v-else />
    </main>
  </div>
</template>

<style scoped>
.app-shell {
  min-height: 100vh;
  background: linear-gradient(160deg, #f3f9f1 0%, #ecf8e8 48%, #e4f4de 100%);
}

.topbar {
  border-bottom: 1px solid var(--color-border);
  background: rgba(255, 255, 255, 0.88);
  backdrop-filter: blur(6px);
}

.topbar-inner {
  margin: 0 auto;
  display: flex;
  max-width: 1200px;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding: 1rem 1.5rem;
}

.brand {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.brand-logo {
  width: 66px;
  height: auto;
}

.brand-title {
  font-size: 1rem;
  font-weight: 700;
  color: var(--color-text);
}

.brand-subtitle {
  font-size: 0.8rem;
  color: var(--color-muted);
}

.session {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

/* Gleiche Optik wie die User-Pille: weiss (#fff), Rand, Text grau (--color-muted) */
.session-pill {
  display: inline-flex;
  align-items: center;
  border: 1px solid var(--color-border);
  border-radius: 999px;
  background: #fff;
  padding: 0.4rem 0.8rem;
  font-size: 0.85rem;
  color: var(--color-muted);
}

.session-pill-button {
  margin: 0;
  font: inherit;
  font-weight: 600;
  cursor: pointer;
}

.session-pill-button:hover {
  border-color: var(--color-primary);
  color: var(--color-text);
}

.app-main {
  display: flex;
  min-height: 100vh;
  align-items: center;
  justify-content: center;
  padding: 2rem 1rem;
}

.app-main-auth {
  min-height: calc(100vh - 78px);
  align-items: stretch;
}
</style>
