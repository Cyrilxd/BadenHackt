<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { roomsApi, whitelistsApi, type Room, type Whitelist } from '../api'

defineProps<{
  user: { username: string; room_name: string } | null
}>()

const rooms = ref<Room[]>([])
const whitelists = ref<Whitelist[]>([])
const loading = ref(false)
const error = ref('')

// Whitelist form
const showWhitelistForm = ref(false)
const newWhitelistName = ref('')
const newWhitelistUrls = ref('')

onMounted(async () => {
  await loadData()
})

async function loadData() {
  loading.value = true
  try {
    rooms.value = await roomsApi.getRooms()
    whitelists.value = await whitelistsApi.getWhitelists()
  } catch (err: any) {
    error.value = 'Fehler beim Laden der Daten'
  } finally {
    loading.value = false
  }
}

async function toggleInternet(room: Room) {
  loading.value = true
  error.value = ''
  
  try {
    const newState = !room.internet_enabled
    await roomsApi.toggleInternet(room.id, newState)
    room.internet_enabled = newState
  } catch (err: any) {
    error.value = 'Fehler beim Umschalten'
  } finally {
    loading.value = false
  }
}

async function createWhitelist() {
  if (!newWhitelistName.value || !newWhitelistUrls.value) return

  loading.value = true
  error.value = ''

  try {
    const urls = newWhitelistUrls.value.split('\n').filter(url => url.trim())
    const whitelist = await whitelistsApi.createWhitelist(newWhitelistName.value, urls)
    whitelists.value.push(whitelist)
    
    // Reset form
    newWhitelistName.value = ''
    newWhitelistUrls.value = ''
    showWhitelistForm.value = false
  } catch (err: any) {
    error.value = 'Fehler beim Erstellen der Whitelist'
  } finally {
    loading.value = false
  }
}

async function deleteWhitelist(id: number) {
  if (!confirm('Whitelist wirklich löschen?')) return

  loading.value = true
  try {
    await whitelistsApi.deleteWhitelist(id)
    whitelists.value = whitelists.value.filter(w => w.id !== id)
  } catch (err: any) {
    error.value = 'Fehler beim Löschen'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="dashboard">
    <div class="container">
      <div v-if="error" class="error-banner">{{ error }}</div>

      <!-- Internet Control -->
      <section class="section">
        <h2>🌐 Internet-Steuerung</h2>
        
        <div v-if="loading && rooms.length === 0" class="loading">Lädt...</div>
        
        <div v-else class="room-grid">
          <div v-for="room in rooms" :key="room.id" class="room-card">
            <div class="room-header">
              <h3>{{ room.name }}</h3>
              <span class="subnet">{{ room.subnet }}</span>
            </div>
            
            <div class="room-status">
              <span :class="['status-indicator', room.internet_enabled ? 'enabled' : 'disabled']">
                {{ room.internet_enabled ? '🟢 Aktiv' : '🔴 Gesperrt' }}
              </span>
            </div>

            <button
              @click="toggleInternet(room)"
              :disabled="loading"
              :class="['btn-toggle', room.internet_enabled ? 'btn-danger' : 'btn-success']"
            >
              {{ room.internet_enabled ? '🚫 Internet sperren' : '✅ Internet freigeben' }}
            </button>
          </div>
        </div>
      </section>

      <!-- Whitelists -->
      <section class="section">
        <div class="section-header">
          <h2>📋 Whitelist-Management</h2>
          <button @click="showWhitelistForm = !showWhitelistForm" class="btn-add">
            {{ showWhitelistForm ? '❌ Abbrechen' : '➕ Neue Whitelist' }}
          </button>
        </div>

        <!-- Create Form -->
        <div v-if="showWhitelistForm" class="whitelist-form">
          <input
            v-model="newWhitelistName"
            type="text"
            placeholder="Name (z.B. 'Google Suite')"
            class="input"
          />
          <textarea
            v-model="newWhitelistUrls"
            placeholder="URLs (eine pro Zeile)&#10;Beispiel:&#10;google.com&#10;gmail.com&#10;drive.google.com"
            rows="5"
            class="textarea"
          ></textarea>
          <button @click="createWhitelist" :disabled="loading" class="btn-primary">
            Whitelist erstellen
          </button>
        </div>

        <!-- List -->
        <div v-if="whitelists.length === 0" class="empty-state">
          Keine Whitelists vorhanden
        </div>

        <div v-else class="whitelist-grid">
          <div v-for="wl in whitelists" :key="wl.id" class="whitelist-card">
            <div class="whitelist-header">
              <h4>{{ wl.name }}</h4>
              <button @click="deleteWhitelist(wl.id)" class="btn-delete">🗑️</button>
            </div>
            <ul class="url-list">
              <li v-for="(url, idx) in wl.urls" :key="idx">{{ url }}</li>
            </ul>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<style scoped>
.dashboard {
  width: 100%;
  max-width: 1200px;
}

.container {
  padding: 2rem;
}

.section {
  background: white;
  border-radius: 20px;
  padding: 2rem;
  margin-bottom: 2rem;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

h2 {
  margin: 0 0 1.5rem 0;
  color: #333;
}

.error-banner {
  background: #fee;
  color: #c00;
  padding: 1rem;
  border-radius: 8px;
  margin-bottom: 1rem;
  text-align: center;
}

.room-grid {
  display: grid;
  gap: 1.5rem;
}

.room-card {
  border: 2px solid #e0e0e0;
  border-radius: 12px;
  padding: 1.5rem;
  transition: all 0.3s;
}

.room-card:hover {
  border-color: #667eea;
  box-shadow: 0 4px 20px rgba(102, 126, 234, 0.2);
}

.room-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.room-header h3 {
  margin: 0;
  color: #333;
}

.subnet {
  color: #666;
  font-size: 0.875rem;
  font-family: monospace;
}

.room-status {
  margin-bottom: 1rem;
}

.status-indicator {
  display: inline-block;
  padding: 0.5rem 1rem;
  border-radius: 20px;
  font-weight: 600;
  font-size: 0.875rem;
}

.status-indicator.enabled {
  background: #d4edda;
  color: #155724;
}

.status-indicator.disabled {
  background: #f8d7da;
  color: #721c24;
}

.btn-toggle {
  width: 100%;
  padding: 1rem;
  border: none;
  border-radius: 8px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-danger {
  background: linear-gradient(135deg, #ee0979 0%, #ff6a00 100%);
  color: white;
}

.btn-success {
  background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
  color: white;
}

.btn-toggle:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
}

.btn-add {
  padding: 0.75rem 1.5rem;
  background: #667eea;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
}

.whitelist-form {
  background: #f8f9fa;
  padding: 1.5rem;
  border-radius: 8px;
  margin-bottom: 1.5rem;
}

.input, .textarea {
  width: 100%;
  padding: 0.75rem;
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  font-size: 1rem;
  margin-bottom: 1rem;
}

.textarea {
  font-family: monospace;
  resize: vertical;
}

.btn-primary {
  padding: 0.75rem 1.5rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
}

.empty-state {
  text-align: center;
  color: #999;
  padding: 2rem;
}

.whitelist-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1rem;
}

.whitelist-card {
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  padding: 1rem;
}

.whitelist-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.whitelist-header h4 {
  margin: 0;
  color: #333;
}

.btn-delete {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 1.2rem;
  opacity: 0.6;
  transition: opacity 0.3s;
}

.btn-delete:hover {
  opacity: 1;
}

.url-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.url-list li {
  padding: 0.25rem 0;
  color: #666;
  font-size: 0.875rem;
  font-family: monospace;
}

.loading {
  text-align: center;
  padding: 2rem;
  color: #999;
}
</style>
