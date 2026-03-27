<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { roomsApi, whitelistsApi, type Room, type Whitelist } from '../api'

const rooms = ref<Room[]>([])
const whitelists = ref<Whitelist[]>([])
const selectedRoomId = ref<number | null>(null)
const loading = ref(false)
const error = ref('')

// Create form
const showWhitelistForm = ref(false)
const newWhitelistName = ref('')
const newWhitelistUrls = ref('')

// Edit form
const editingWhitelistId = ref<number | null>(null)
const editWhitelistName = ref('')
const editWhitelistUrls = ref('')

const selectedRoomWhitelists = computed(() => {
  if (!selectedRoomId.value) return []
  return whitelists.value.filter(w => w.room_id === selectedRoomId.value)
})

onMounted(async () => {
  await loadData()
})

async function loadData() {
  loading.value = true
  error.value = ''
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

function selectRoom(roomId: number) {
  selectedRoomId.value = roomId
  showWhitelistForm.value = false
  cancelEditWhitelist()
}

async function createWhitelist() {
  if (!selectedRoomId.value) {
    error.value = 'Bitte zuerst ein Zimmer auswählen'
    return
  }

  const cleanedName = newWhitelistName.value.trim()
  const urls = newWhitelistUrls.value
    .split('\n')
    .map(url => url.trim())
    .filter(Boolean)

  if (!cleanedName) {
    error.value = 'Bitte einen Namen für die Whitelist eingeben'
    return
  }

  if (urls.length === 0) {
    error.value = 'Bitte mindestens eine URL eingeben'
    return
  }

  loading.value = true
  error.value = ''

  try {
    const whitelist = await whitelistsApi.createWhitelist(
      cleanedName,
      urls,
      selectedRoomId.value
    )

    whitelists.value.push(whitelist)

    newWhitelistName.value = ''
    newWhitelistUrls.value = ''
    showWhitelistForm.value = false
  } catch (err: any) {
    error.value =
      err?.response?.data?.detail ||
      'Fehler beim Erstellen der Whitelist'
  } finally {
    loading.value = false
  }
}

function startEditWhitelist(wl: Whitelist) {
  editingWhitelistId.value = wl.id
  editWhitelistName.value = wl.name
  editWhitelistUrls.value = wl.urls.join('\n')
  showWhitelistForm.value = false
  error.value = ''
}

function cancelEditWhitelist() {
  editingWhitelistId.value = null
  editWhitelistName.value = ''
  editWhitelistUrls.value = ''
}

async function updateWhitelist() {
  if (editingWhitelistId.value === null || selectedRoomId.value === null) {
    error.value = 'Keine Whitelist oder kein Zimmer ausgewählt'
    return
  }

  const cleanedName = editWhitelistName.value.trim()
  const urls = editWhitelistUrls.value
    .split('\n')
    .map(url => url.trim())
    .filter(Boolean)

  if (!cleanedName) {
    error.value = 'Bitte einen Namen für die Whitelist eingeben'
    return
  }

  if (urls.length === 0) {
    error.value = 'Bitte mindestens eine URL eingeben'
    return
  }

  loading.value = true
  error.value = ''

  try {
    const updatedWhitelist = await whitelistsApi.updateWhitelist(
      editingWhitelistId.value,
      cleanedName,
      urls,
      selectedRoomId.value
    )

    const index = whitelists.value.findIndex(w => w.id === updatedWhitelist.id)
    if (index !== -1) {
      whitelists.value[index] = updatedWhitelist
    }

    cancelEditWhitelist()
  } catch (err: any) {
    error.value =
      err?.response?.data?.detail ||
      'Fehler beim Aktualisieren der Whitelist'
  } finally {
    loading.value = false
  }
}

async function deleteWhitelist(id: number) {
  if (!confirm('Whitelist wirklich löschen?')) return

  loading.value = true
  error.value = ''

  try {
    await whitelistsApi.deleteWhitelist(id)
    whitelists.value = whitelists.value.filter(w => w.id !== id)

    if (editingWhitelistId.value === id) {
      cancelEditWhitelist()
    }
  } catch (err: any) {
    error.value =
      err?.response?.data?.detail ||
      'Fehler beim Löschen'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="dashboard">
    <div class="container">
      <div v-if="error" class="error-banner">{{ error }}</div>

      <section class="section">
        <h2>🌐 Internet-Steuerung (Alle Zimmer)</h2>

        <div v-if="loading && rooms.length === 0" class="loading">Lädt...</div>

        <div v-else class="room-grid">
          <div
            v-for="room in rooms"
            :key="room.id"
            class="room-card"
            :class="{ selected: selectedRoomId === room.id }"
            @click="selectRoom(room.id)"
          >
            <div class="room-header">
              <h3>{{ room.name }}</h3>
              <span class="subnet">VLAN {{ room.vlan_id }}</span>
            </div>

            <div class="room-status">
              <span :class="['status-indicator', room.internet_enabled ? 'enabled' : 'disabled']">
                {{ room.internet_enabled ? '🟢 Aktiv' : '🔴 Gesperrt' }}
              </span>
            </div>

            <button
              @click.stop="toggleInternet(room)"
              :disabled="loading"
              :class="['btn-toggle', room.internet_enabled ? 'btn-danger' : 'btn-success']"
            >
              {{ room.internet_enabled ? '🚫 Sperren' : '✅ Freigeben' }}
            </button>
          </div>
        </div>
      </section>

      <section v-if="selectedRoomId" class="section">
        <div class="section-header">
          <h2>📋 Whitelist: {{ rooms.find(r => r.id === selectedRoomId)?.name }}</h2>
          <button @click="showWhitelistForm = !showWhitelistForm" class="btn-add">
            {{ showWhitelistForm ? '❌ Abbrechen' : '➕ Neue Whitelist' }}
          </button>
        </div>

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

        <div v-if="selectedRoomWhitelists.length === 0 && !showWhitelistForm" class="empty-state">
          Keine Whitelists für dieses Zimmer
        </div>

        <div v-else class="whitelist-grid">
          <div v-for="wl in selectedRoomWhitelists" :key="wl.id" class="whitelist-card">
            <div v-if="editingWhitelistId === wl.id">
              <div class="edit-form">
                <input
                  v-model="editWhitelistName"
                  type="text"
                  placeholder="Whitelist-Name"
                  class="input"
                />
                <textarea
                  v-model="editWhitelistUrls"
                  rows="5"
                  class="textarea"
                  placeholder="URLs (eine pro Zeile)"
                ></textarea>
                <div class="edit-actions">
                  <button @click.stop="updateWhitelist" :disabled="loading" class="btn-primary">
                    💾 Speichern
                  </button>
                  <button @click.stop="cancelEditWhitelist" :disabled="loading" class="btn-secondary">
                    Abbrechen
                  </button>
                </div>
              </div>
            </div>

            <div v-else>
              <div class="whitelist-header">
                <h4>{{ wl.name }}</h4>
                <div class="whitelist-actions">
                  <button @click.stop="startEditWhitelist(wl)" class="btn-edit">✏️</button>
                  <button @click.stop="deleteWhitelist(wl.id)" class="btn-delete">🗑️</button>
                </div>
              </div>
              <ul class="url-list">
                <li v-for="(url, idx) in wl.urls" :key="idx">{{ url }}</li>
              </ul>
            </div>
          </div>
        </div>
      </section>

      <div v-else class="info-box">
        👆 Wähle ein Zimmer aus, um Whitelists zu verwalten
      </div>
    </div>
  </div>
</template>

<style scoped>
.dashboard {
  width: 100%;
  max-width: 1400px;
}

.container {
  padding: 2rem;
}

.section {
  background: var(--bg);
  border-radius: var(--radius-lg);
  padding: 2rem;
  margin-bottom: 2rem;
  box-shadow: var(--shadow);
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

h2 {
  margin: 0 0 1.5rem 0;
  color: var(--text);
}

.error-banner {
  background: #fee;
  color: #c00;
  padding: 1rem;
  border-radius: var(--radius);
  margin-bottom: 1rem;
  text-align: center;
}

.room-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 1.5rem;
}

.room-card {
  border: 2px solid var(--border);
  border-radius: 12px;
  padding: 1.5rem;
  transition: all 0.3s;
  cursor: pointer;
}

.room-card:hover {
  border-color: var(--primary);
  box-shadow: var(--shadow-hover);
}

.room-card.selected {
  border-color: var(--primary);
  background: #f8f9ff;
  box-shadow: 0 4px 20px rgba(102, 126, 234, 0.3);
}

.room-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.room-header h3 {
  margin: 0;
  color: var(--text);
  font-size: 1.2rem;
}

.subnet {
  color: var(--text-light);
  font-size: 0.75rem;
  background: var(--bg-light);
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-weight: 600;
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
  padding: 0.875rem;
  border: none;
  border-radius: var(--radius);
  font-size: 0.95rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-danger {
  background: linear-gradient(135deg, var(--danger) 0%, var(--danger-light) 100%);
  color: white;
}

.btn-success {
  background: linear-gradient(135deg, var(--success) 0%, var(--success-light) 100%);
  color: white;
}

.btn-toggle:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
}

.btn-add {
  padding: 0.75rem 1.5rem;
  background: var(--primary);
  color: white;
  border: none;
  border-radius: var(--radius);
  cursor: pointer;
  font-weight: 600;
  transition: all 0.3s;
}

.btn-add:hover {
  background: var(--primary-dark);
  transform: translateY(-2px);
}

.whitelist-form {
  background: var(--bg-light);
  padding: 1.5rem;
  border-radius: var(--radius);
  margin-bottom: 1.5rem;
}

.input,
.textarea {
  width: 100%;
  padding: 0.75rem;
  border: 2px solid var(--border);
  border-radius: var(--radius);
  font-size: 1rem;
  margin-bottom: 1rem;
  box-sizing: border-box;
}

.textarea {
  font-family: monospace;
  resize: vertical;
}

.btn-primary {
  padding: 0.75rem 1.5rem;
  background: linear-gradient(135deg, var(--primary) 0%, var(--accent) 100%);
  color: white;
  border: none;
  border-radius: var(--radius);
  cursor: pointer;
  font-weight: 600;
  transition: all 0.3s;
}

.btn-primary:hover {
  transform: translateY(-2px);
}

.btn-secondary {
  padding: 0.75rem 1.5rem;
  background: var(--bg-light);
  color: var(--text);
  border: 2px solid var(--border);
  border-radius: var(--radius);
  cursor: pointer;
  font-weight: 600;
  transition: all 0.3s;
}

.btn-secondary:hover {
  border-color: var(--primary);
}

.empty-state {
  text-align: center;
  color: var(--text-muted);
  padding: 2rem;
}

.info-box {
  background: var(--bg);
  border-radius: var(--radius-lg);
  padding: 3rem;
  text-align: center;
  color: var(--text-light);
  font-size: 1.1rem;
  box-shadow: var(--shadow);
}

.whitelist-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1rem;
}

.whitelist-card {
  border: 2px solid var(--border);
  border-radius: var(--radius);
  padding: 1rem;
  transition: all 0.3s;
}

.whitelist-card:hover {
  border-color: var(--primary);
  box-shadow: var(--shadow-hover);
}

.whitelist-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.whitelist-header h4 {
  margin: 0;
  color: var(--text);
}

.whitelist-actions {
  display: flex;
  gap: 0.5rem;
  align-items: center;
}

.btn-edit {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 1.1rem;
  opacity: 0.7;
  transition: opacity 0.3s;
}

.btn-edit:hover {
  opacity: 1;
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
  color: var(--text-light);
  font-size: 0.875rem;
  font-family: var(--mono);
  word-break: break-all;
}

.loading {
  text-align: center;
  padding: 2rem;
  color: var(--text-muted);
}

.edit-form {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.edit-actions {
  display: flex;
  gap: 0.75rem;
}
</style>