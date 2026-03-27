<script setup lang="ts">
import { ref, onMounted } from 'vue'
import Login from './components/Login.vue'
import Dashboard from './components/Dashboard.vue'

const isAuthenticated = ref(false)
const user = ref<{ username: string; role: string } | null>(null)

onMounted(() => {
  const token = localStorage.getItem('token')
  const userData = localStorage.getItem('user')
  
  if (token && userData) {
    isAuthenticated.value = true
    user.value = JSON.parse(userData)
  }
})

function handleLogin(loginData: { token: string; user: any }) {
  localStorage.setItem('token', loginData.token)
  localStorage.setItem('user', JSON.stringify(loginData.user))
  isAuthenticated.value = true
  user.value = loginData.user
}

function handleLogout() {
  localStorage.removeItem('token')
  localStorage.removeItem('user')
  isAuthenticated.value = false
  user.value = null
}
</script>

<template>
  <div class="app">
    <header v-if="isAuthenticated" class="header">
      <div class="container">
        <h1>🌐 Internet EIN/AUS</h1>
        <div class="user-info">
          <span>👤 {{ user?.username }}</span>
          <button @click="handleLogout" class="btn-logout">Abmelden</button>
        </div>
      </div>
    </header>

    <main class="main">
      <Login v-if="!isAuthenticated" @login="handleLogin" />
      <Dashboard v-else :user="user" />
    </main>

    <footer class="footer">
      <p>zB. Zentrum Bildung Baden | Hackathon 2026 🦇</p>
    </footer>
  </div>
</template>

<style scoped>
.app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.header {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  padding: 1.5rem 0;
}

.header .container {
  max-width: 1400px;
  margin: 0 auto;
  padding: 0 2rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header h1 {
  margin: 0;
  color: #333;
  font-size: 1.8rem;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 1rem;
  color: #666;
  font-weight: 500;
}

.btn-logout {
  padding: 0.5rem 1rem;
  background: #ee0979;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
  transition: all 0.3s;
}

.btn-logout:hover {
  background: #ff6a00;
  transform: translateY(-2px);
}

.main {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem;
}

.footer {
  background: rgba(0, 0, 0, 0.2);
  color: white;
  text-align: center;
  padding: 1rem;
}
</style>
