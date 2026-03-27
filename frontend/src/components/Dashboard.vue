<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { roomsApi, whitelistsApi, type Room, type Whitelist } from '../api'
import DashboardPageTitle from './dashboard/DashboardPageTitle.vue'
import RoomCard from './dashboard/RoomCard.vue'

const rooms = ref<Room[]>([])
const whitelists = ref<Whitelist[]>([])
const selectedRoomId = ref<number | null>(null)
const loading = ref(false)
const error = ref('')
const modalVisible = ref(false)

const showWhitelistForm = ref(false)
const newWhitelistName = ref('')
const newWhitelistUrls = ref('')

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
}

function openWhitelistModal(roomId: number, openCreateForm = false) {
  selectRoom(roomId)
  modalVisible.value = true
  showWhitelistForm.value = openCreateForm
  if (openCreateForm) {
    cancelEditWhitelist()
  }
  error.value = ''
}

function closeWhitelistModal() {
  modalVisible.value = false
  showWhitelistForm.value = false
  cancelEditWhitelist()
  newWhitelistName.value = ''
  newWhitelistUrls.value = ''
}

function handleRoomCardClick(room: Room) {
  selectRoom(room.id)
  if (!room.internet_enabled) {
    openWhitelistModal(room.id, true)
  }
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

const selectedRoom = computed(() =>
  rooms.value.find(r => r.id === selectedRoomId.value) ?? null
)
</script>

<template>
  <div class="dashboard">
    <DashboardPageTitle eyebrow="Übersicht" title="Zimmersteuerung" />

    <p v-if="error" class="error-banner">{{ error }}</p>

    <div v-if="loading && rooms.length === 0" class="loading">Lädt Daten...</div>

    <section v-else class="room-grid">
      <RoomCard
        v-for="room in rooms"
        :key="room.id"
        :room="room"
        :selected="selectedRoomId === room.id"
        :loading="loading"
        @card-click="handleRoomCardClick"
        @toggle="toggleInternet"
        @manage="(r) => openWhitelistModal(r.id, !r.internet_enabled)"
      />
    </section>

    <div v-if="modalVisible" class="modal-backdrop" @click.self="closeWhitelistModal">
      <section class="modal-card">
        <header class="modal-header">
          <div>
            <p class="modal-eyebrow">Whitelist</p>
            <h3>{{ selectedRoom?.name }}</h3>
          </div>
          <button class="btn-close" @click="closeWhitelistModal">Schliessen</button>
        </header>

        <div class="modal-toolbar">
          <button class="btn-primary" @click="showWhitelistForm = !showWhitelistForm">
            {{ showWhitelistForm ? 'Formular ausblenden' : 'Neue Whitelist' }}
          </button>
        </div>

        <div v-if="showWhitelistForm" class="editor-box">
          <input
            v-model="newWhitelistName"
            type="text"
            class="field"
            placeholder="Name, z. B. Schulplattform"
          />
          <textarea
            v-model="newWhitelistUrls"
            rows="5"
            class="field field-area"
            placeholder="Domains oder Hosts, eine Zeile pro Eintrag"
          ></textarea>
          <button class="btn-primary" :disabled="loading" @click="createWhitelist">Erstellen</button>
        </div>

        <p v-if="selectedRoomWhitelists.length === 0 && !showWhitelistForm" class="empty">
          Keine Whitelists für dieses Zimmer.
        </p>

        <div class="whitelist-list">
          <article v-for="wl in selectedRoomWhitelists" :key="wl.id" class="whitelist-card">
            <div v-if="editingWhitelistId === wl.id" class="editor-box editor-inline">
              <input v-model="editWhitelistName" type="text" class="field" placeholder="Whitelist-Name" />
              <textarea
                v-model="editWhitelistUrls"
                rows="5"
                class="field field-area"
                placeholder="Hosts eine Zeile pro Eintrag"
              ></textarea>
              <div class="inline-actions">
                <button class="btn-primary" :disabled="loading" @click.stop="updateWhitelist">Speichern</button>
                <button class="btn-light" :disabled="loading" @click.stop="cancelEditWhitelist">Abbrechen</button>
              </div>
            </div>

            <div v-else>
              <header class="whitelist-head">
                <h4>{{ wl.name }}</h4>
                <div class="inline-actions">
                  <button class="icon-btn" @click.stop="startEditWhitelist(wl)">Bearbeiten</button>
                  <button class="icon-btn icon-btn-danger" @click.stop="deleteWhitelist(wl.id)">Löschen</button>
                </div>
              </header>

              <ul class="url-list">
                <li v-for="(url, idx) in wl.urls" :key="idx">{{ url }}</li>
              </ul>
            </div>
          </article>
        </div>
      </section>
    </div>
  </div>
</template>

<style scoped>
.dashboard {
  width: min(1280px, 100%);
  margin: 0 auto;
  padding: 1.5rem;
}

.error-banner {
  border: 1px solid #f0c8c8;
  border-radius: 10px;
  background: #fff5f5;
  padding: 0.8rem;
  margin-bottom: 1rem;
  color: #a03333;
  font-size: 0.9rem;
}

.room-grid {
  display: grid;
  gap: 1.25rem;
  grid-template-columns: 1fr;
}

@media (min-width: 700px) {
  .room-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (min-width: 1100px) {
  .room-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

.modal-backdrop {
  position: fixed;
  inset: 0;
  z-index: 30;
  display: grid;
  place-items: center;
  background: rgba(20, 26, 18, 0.4);
  padding: 1rem;
}

.modal-card {
  width: min(840px, 100%);
  max-height: 85vh;
  overflow: auto;
  border-radius: 16px;
  border: 1px solid #dbead6;
  background: #fff;
  padding: 1rem;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  margin-bottom: 0.8rem;
}

.modal-header h3 {
  margin: 0;
  font-size: 1.1rem;
}

.modal-eyebrow {
  margin: 0;
  color: var(--color-muted);
  font-size: 0.8rem;
  font-weight: 600;
  letter-spacing: 0.05em;
  text-transform: uppercase;
}

.btn-close {
  border: 1px solid var(--color-border);
  border-radius: 10px;
  background: #fff;
  padding: 0.5rem 0.75rem;
  cursor: pointer;
}

.modal-toolbar {
  margin-bottom: 0.8rem;
}

.btn-primary {
  border: 0;
  border-radius: 10px;
  background: linear-gradient(135deg, var(--color-primary), var(--color-primary-strong));
  padding: 0.62rem 0.9rem;
  color: #fff;
  font-weight: 700;
  cursor: pointer;
}

.btn-light {
  border: 1px solid var(--color-border);
  border-radius: 10px;
  background: #fff;
  padding: 0.62rem 0.9rem;
  font-weight: 700;
  cursor: pointer;
}

.editor-box {
  border: 1px solid var(--color-border);
  border-radius: 12px;
  background: #f9fcf7;
  padding: 0.8rem;
  margin-bottom: 0.8rem;
}

.field {
  width: 100%;
  border: 1px solid var(--color-border);
  border-radius: 10px;
  background: #fff;
  padding: 0.62rem 0.7rem;
  margin-bottom: 0.5rem;
  font-size: 0.9rem;
}

.field-area {
  min-height: 120px;
  resize: vertical;
  font-family: var(--mono);
}

.empty {
  border: 1px dashed var(--color-border);
  border-radius: 12px;
  padding: 0.8rem;
  color: var(--color-muted);
}

.whitelist-list {
  display: grid;
  gap: 0.7rem;
}

.whitelist-card {
  border: 1px solid var(--color-border);
  border-radius: 12px;
  background: #fff;
  padding: 0.75rem;
}

.whitelist-head {
  display: flex;
  justify-content: space-between;
  gap: 0.5rem;
  align-items: flex-start;
  margin-bottom: 0.45rem;
}

.whitelist-head h4 {
  margin: 0;
  font-size: 0.98rem;
}

.inline-actions {
  display: flex;
  gap: 0.45rem;
}

.icon-btn {
  border: 1px solid var(--color-border);
  border-radius: 8px;
  background: #fff;
  padding: 0.3rem 0.55rem;
  font-size: 0.76rem;
  cursor: pointer;
}

.icon-btn-danger {
  border-color: #f2d3d3;
  color: #9e3c3c;
}

.url-list {
  margin: 0;
  padding-left: 1rem;
  color: var(--color-muted);
  font-size: 0.86rem;
}

.url-list li {
  margin-bottom: 0.2rem;
  font-family: var(--mono);
  word-break: break-all;
}

.loading {
  border: 1px dashed var(--color-border);
  border-radius: 12px;
  background: #fff;
  padding: 1rem;
  color: var(--color-muted);
}

.editor-inline {
  margin-bottom: 0;
}
</style>