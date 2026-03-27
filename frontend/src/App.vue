<script setup lang="ts">
import { onMounted, ref } from 'vue'
import AppTopBar from './components/layout/AppTopBar.vue'
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
    <AppTopBar v-if="isAuthenticated" :username="user?.username" @logout="handleLogout" />

    <main class="app-main" :class="{ 'app-main-auth': isAuthenticated }">
      <Login v-if="!isAuthenticated" @login="handleLogin" />
      <Dashboard v-else />
    </main>
  </div>
</template>

<style scoped>
.app-shell {
  min-height: 100vh;
  background: linear-gradient(
    160deg,
    var(--color-page-bg-1) 0%,
    var(--color-page-bg-2) 48%,
    var(--color-page-bg-3) 100%
  );
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
