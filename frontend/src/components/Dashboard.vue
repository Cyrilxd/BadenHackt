<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { roomsApi, whitelistsApi, type Room, type Whitelist } from '../api'

const rooms = ref<Room[]>([])
const whitelists = ref<Whitelist[]>([])
const selectedRoomId = ref<number | null>(null)
const loading = ref(false)
const error = ref('')
const modalVisible = ref(false)

const showWhitelistForm = ref(false)
const newWhitelistName = ref('')
const newWhitelistUrls = ref('')
const newWhitelistIsActive = ref(true)

const editingWhitelistId = ref<number | null>(null)
const editWhitelistName = ref('')
const editWhitelistUrls = ref('')
const editWhitelistIsActive = ref(true)

const selectedRoomWhitelists = computed(() => {
  if (!selectedRoomId.value) return []
  return whitelists.value.filter(w => w.room_id === selectedRoomId.value)
})

const selectedRoom = computed(() =>
  rooms.value.find(r => r.id === selectedRoomId.value) ?? null
)

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
  newWhitelistIsActive.value = true
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
      selectedRoomId.value,
      newWhitelistIsActive.value
    )

    whitelists.value.push(whitelist)

    newWhitelistName.value = ''
    newWhitelistUrls.value = ''
    newWhitelistIsActive.value = true
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
  editWhitelistIsActive.value = wl.is_active
  showWhitelistForm.value = false
  error.value = ''
}

function cancelEditWhitelist() {
  editingWhitelistId.value = null
  editWhitelistName.value = ''
  editWhitelistUrls.value = ''
  editWhitelistIsActive.value = true
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
      selectedRoomId.value,
      editWhitelistIsActive.value
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

async function toggleWhitelistActive(wl: Whitelist) {
  loading.value = true
  error.value = ''

  try {
    const updatedWhitelist = await whitelistsApi.toggleWhitelist(
      wl.id,
      !wl.is_active
    )

    const index = whitelists.value.findIndex(w => w.id === updatedWhitelist.id)
    if (index !== -1) {
      whitelists.value[index] = updatedWhitelist
    }

    if (editingWhitelistId.value === updatedWhitelist.id) {
      editWhitelistIsActive.value = updatedWhitelist.is_active
    }
  } catch (err: any) {
    error.value =
      err?.response?.data?.detail ||
      'Fehler beim Aktivieren/Deaktivieren der Whitelist'
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
    <div class="dashboard-header">
      <div>
        <p class="dashboard-eyebrow">Übersicht</p>
        <h2>Zimmersteuerung</h2>
      </div>
      <img src="/zB_Logo.png" alt="zB Logo" class="header-logo" />
    </div>

    <p v-if="error" class="error-banner">{{ error }}</p>

    <div v-if="loading && rooms.length === 0" class="loading">Lädt Daten...</div>

    <section v-else class="room-grid">
      <article
        v-for="room in rooms"
        :key="room.id"
        class="room-card"
        :class="{
          'room-card-selected': selectedRoomId === room.id,
          'room-card-disabled': !room.internet_enabled
        }"
        @click="handleRoomCardClick(room)"
      >
        <header class="room-head">
          <h3>{{ room.name }}</h3>
          <span class="vlan-badge">VLAN {{ room.vlan_id }}</span>
        </header>

        <p class="subnet">{{ room.subnet }}</p>

        <p class="status-pill" :class="room.internet_enabled ? 'status-on' : 'status-off'">
          {{ room.internet_enabled ? 'Internet aktiv' : 'Internet gesperrt' }}
        </p>

        <div class="room-actions">
          <button
            class="btn-toggle"
            :class="room.internet_enabled ? 'btn-disable' : 'btn-enable'"
            :disabled="loading"
            @click.stop="toggleInternet(room)"
          >
            {{ room.internet_enabled ? 'Sperren' : 'Freigeben' }}
          </button>

          <button
            class="btn-manage"
            :disabled="loading"
            @click.stop="openWhitelistModal(room.id, !room.internet_enabled)"
          >
            {{ room.internet_enabled ? 'Whitelist verwalten' : 'Whitelist direkt erfassen' }}
          </button>
        </div>
      </article>
    </section>

    <div v-if="modalVisible" class="modal-backdrop" @click.self="closeWhitelistModal">
      <section class="modal-card">
        <header class="modal-header">
          <div>
            <p class="dashboard-eyebrow">Whitelist</p>
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

          <label class="checkbox-row">
            <input v-model="newWhitelistIsActive" type="checkbox" />
            Whitelist aktiv
          </label>

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

              <label class="checkbox-row">
                <input v-model="editWhitelistIsActive" type="checkbox" />
                Whitelist aktiv
              </label>

              <div class="inline-actions">
                <button class="btn-primary" :disabled="loading" @click.stop="updateWhitelist">Speichern</button>
                <button class="btn-light" :disabled="loading" @click.stop="cancelEditWhitelist">Abbrechen</button>
              </div>
            </div>

            <div v-else>
              <header class="whitelist-head">
                <div>
                  <h4>{{ wl.name }}</h4>
                  <p
                    class="whitelist-status"
                    :class="wl.is_active ? 'whitelist-status-active' : 'whitelist-status-inactive'"
                  >
                    {{ wl.is_active ? 'Aktiv' : 'Inaktiv' }}
                  </p>
                </div>

                <div class="inline-actions">
                  <button class="icon-btn" @click.stop="toggleWhitelistActive(wl)">
                    {{ wl.is_active ? 'Deaktivieren' : 'Aktivieren' }}
                  </button>
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
  width: min(1200px, 100%);
  margin: 0 auto;
  padding: 1.5rem;
}

.dashboard-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1.2rem;
}

.dashboard-eyebrow {
  margin: 0;
  color: var(--color-muted);
  font-size: 0.8rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.dashboard-header h2 {
  margin: 0.25rem 0 0;
  color: var(--color-text);
  font-size: 1.5rem;
}

.header-logo {
  width: 72px;
  height: auto;
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
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  gap: 1rem;
}

.room-card {
  border: 1px solid var(--color-border);
  border-radius: 16px;
  background: #fff;
  padding: 1rem;
  transition: border-color 0.15s ease, box-shadow 0.15s ease;
  cursor: pointer;
}

.room-card:hover {
  border-color: var(--color-primary);
  box-shadow: 0 12px 26px rgba(44, 100, 36, 0.1);
}

.room-card-selected {
  border-color: var(--color-primary);
}

.room-card-disabled {
  border-color: #e3c9c9;
  background: #fffdfd;
}

.room-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 0.5rem;
}

.room-head h3 {
  margin: 0;
  color: var(--color-text);
  font-size: 1.05rem;
}

.vlan-badge {
  border-radius: 999px;
  background: #edf6ea;
  padding: 0.3rem 0.6rem;
  font-size: 0.75rem;
  color: #3a7440;
  font-weight: 700;
}

.subnet {
  margin: 0.75rem 0;
  color: var(--color-muted);
  font-family: var(--mono);
  font-size: 0.82rem;
}

.status-pill {
  display: inline-block;
  border-radius: 999px;
  padding: 0.35rem 0.65rem;
  font-size: 0.78rem;
  font-weight: 700;
}

.status-on {
  background: #e7f7e3;
  color: #2f7c22;
}

.status-off {
  background: #faecec;
  color: #a13333;
}

.room-actions {
  margin-top: 0.9rem;
  display: flex;
  gap: 0.55rem;
}

.btn-toggle,
.btn-manage {
  flex: 1;
  border: 0;
  border-radius: 10px;
  padding: 0.58rem 0.7rem;
  font-size: 0.82rem;
  font-weight: 700;
  cursor: pointer;
}

.btn-manage {
  border: 1px solid var(--color-border);
  background: #fff;
  color: var(--color-text);
}

.btn-enable {
  background: var(--color-primary);
  color: #fff;
}

.btn-disable {
  background: var(--color-danger);
  color: #fff;
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

.checkbox-row {
  display: flex;
  align-items: center;
  gap: 0.55rem;
  margin-bottom: 0.75rem;
  color: var(--color-text);
  font-size: 0.9rem;
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

.whitelist-status {
  margin: 0.35rem 0 0;
  font-size: 0.78rem;
  font-weight: 700;
}

.whitelist-status-active {
  color: #2f7c22;
}

.whitelist-status-inactive {
  color: #a13333;
}

.inline-actions {
  display: flex;
  gap: 0.45rem;
  flex-wrap: wrap;
  justify-content: flex-end;
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