<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { roomsApi, whitelistsApi, type Room, type Whitelist } from '../api'
import { copy } from '../constants/copy'
import DashboardPageTitle from './dashboard/DashboardPageTitle.vue'
import RoomCard from './dashboard/RoomCard.vue'
import WhitelistModal from './dashboard/WhitelistModal.vue'
import UiToast from './ui/UiToast.vue'
import UiConfirm from './ui/UiConfirm.vue'

const rooms = ref<Room[]>([])
const whitelists = ref<Whitelist[]>([])
const selectedRoomId = ref<number | null>(null)
const fetching = ref(false)
const loadingRoomId = ref<number | null>(null)
const loadingModal = ref(false)
const error = ref('')
const modalVisible = ref(false)

// Toast
const toast = ref<{ message: string; type: 'success' | 'error' } | null>(null)
let _toastTimer: ReturnType<typeof setTimeout> | null = null

function showToast(message: string, type: 'success' | 'error' = 'success') {
  if (_toastTimer) clearTimeout(_toastTimer)
  toast.value = { message, type }
  _toastTimer = setTimeout(() => { toast.value = null }, 3000)
}

// Confirm-Dialog
interface ConfirmOptions {
  title: string
  message: string
  danger?: boolean
  onConfirm: () => void
}
const confirmDialog = ref<ConfirmOptions | null>(null)

function showConfirm(options: ConfirmOptions) {
  confirmDialog.value = options
}
function handleConfirmOk() {
  confirmDialog.value?.onConfirm()
  confirmDialog.value = null
}
function handleConfirmCancel() {
  confirmDialog.value = null
}

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
  fetching.value = true
  error.value = ''
  try {
    rooms.value = await roomsApi.getRooms()
    whitelists.value = await whitelistsApi.getWhitelists()
  } catch {
    error.value = copy.dashboard.loadError
  } finally {
    fetching.value = false
  }
}

function requestToggle(room: Room) {
  const willEnable = !room.internet_enabled
  showConfirm({
    title: willEnable ? copy.confirm.toggleOnTitle : copy.confirm.toggleOffTitle,
    message: `Alle Geräte in «${room.name}» ${willEnable ? copy.confirm.toggleOnBody : copy.confirm.toggleOffBody}`,
    danger: !willEnable,
    onConfirm: () => toggleInternet(room),
  })
}

async function toggleInternet(room: Room) {
  loadingRoomId.value = room.id
  error.value = ''

  try {
    const newState = !room.internet_enabled
    await roomsApi.toggleInternet(room.id, newState)
    room.internet_enabled = newState
    showToast(newState ? copy.toast.toggleOn : copy.toast.toggleOff)
  } catch {
    error.value = copy.dashboard.toggleError
  } finally {
    loadingRoomId.value = null
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
    error.value = copy.dashboard.selectRoomFirst
    return
  }

  const cleanedName = newWhitelistName.value.trim()
  const urls = newWhitelistUrls.value
    .split('\n')
    .map(u => u.trim())
    .filter(Boolean)

  if (!cleanedName) {
    error.value = copy.dashboard.whitelistNameMissing
    return
  }

  if (urls.length === 0) {
    error.value = copy.dashboard.whitelistUrlsMissing
    return
  }

  loadingModal.value = true
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
    showToast(copy.toast.whitelistCreated)
  } catch (err: any) {
    error.value =
      err?.response?.data?.detail || copy.dashboard.whitelistCreateError
  } finally {
    loadingModal.value = false
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
    error.value = copy.dashboard.noSelection
    return
  }

  const cleanedName = editWhitelistName.value.trim()
  const urls = editWhitelistUrls.value
    .split('\n')
    .map(u => u.trim())
    .filter(Boolean)

  if (!cleanedName) {
    error.value = copy.dashboard.whitelistNameMissing
    return
  }

  if (urls.length === 0) {
    error.value = copy.dashboard.whitelistUrlsMissing
    return
  }

  loadingModal.value = true
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
    showToast(copy.toast.whitelistUpdated)
  } catch (err: any) {
    error.value =
      err?.response?.data?.detail || copy.dashboard.whitelistUpdateError
  } finally {
    loadingModal.value = false
  }
}

<<<<<<< HEAD
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
=======
function requestDelete(id: number) {
  showConfirm({
    title: copy.confirm.deleteTitle,
    message: copy.confirm.deleteBody,
    danger: true,
    onConfirm: () => doDeleteWhitelist(id),
  })
}
>>>>>>> d2e4f3eee608dd6dc5cb2bf45e32f7ab129a9166

async function doDeleteWhitelist(id: number) {
  loadingModal.value = true
  error.value = ''

  try {
    await whitelistsApi.deleteWhitelist(id)
    whitelists.value = whitelists.value.filter(w => w.id !== id)

    if (editingWhitelistId.value === id) {
      cancelEditWhitelist()
    }
    showToast(copy.toast.whitelistDeleted)
  } catch (err: any) {
    error.value = err?.response?.data?.detail || copy.dashboard.whitelistDeleteError
  } finally {
    loadingModal.value = false
  }
}
</script>

<template>
  <div class="dashboard">
    <DashboardPageTitle
      :eyebrow="copy.dashboard.eyebrowOverview"
      :title="copy.dashboard.titleRooms"
    />

    <p v-if="error" class="error-banner">{{ error }}</p>

    <div v-if="fetching && rooms.length === 0" class="loading">
      {{ copy.dashboard.loading }}
    </div>

    <section v-else class="room-grid">
      <RoomCard
        v-for="room in rooms"
        :key="room.id"
        :room="room"
        :selected="selectedRoomId === room.id"
        :loading="loadingRoomId === room.id"
        @card-click="handleRoomCardClick"
        @toggle="requestToggle"
        @manage="(r) => openWhitelistModal(r.id, !r.internet_enabled)"
      />
    </section>

    <WhitelistModal
      :open="modalVisible"
      :room-title="selectedRoom?.name ?? ''"
      :lists="selectedRoomWhitelists"
      :loading="loadingModal"
      :editing-id="editingWhitelistId"
      v-model:new-name="newWhitelistName"
      v-model:new-urls="newWhitelistUrls"
      v-model:show-form="showWhitelistForm"
      v-model:edit-name="editWhitelistName"
      v-model:edit-urls="editWhitelistUrls"
      @close="closeWhitelistModal"
      @toggleForm="showWhitelistForm = !showWhitelistForm"
      @create="createWhitelist"
      @saveWhitelist="updateWhitelist"
      @cancelEdit="cancelEditWhitelist"
      @delete="requestDelete"
      @edit="startEditWhitelist"
    />

    <Transition name="toast">
      <UiToast v-if="toast" :message="toast.message" :type="toast.type" />
    </Transition>

<<<<<<< HEAD
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
=======
    <UiConfirm
      v-if="confirmDialog"
      :title="confirmDialog.title"
      :message="confirmDialog.message"
      :confirm-label="copy.confirm.ok"
      :cancel-label="copy.confirm.cancel"
      :danger="confirmDialog.danger"
      @confirm="handleConfirmOk"
      @cancel="handleConfirmCancel"
    />
>>>>>>> d2e4f3eee608dd6dc5cb2bf45e32f7ab129a9166
  </div>
</template>

<style scoped>
.dashboard {
  width: min(var(--layout-dashboard-max), 100%);
  margin: 0 auto;
  padding: 1.5rem;
}

.error-banner {
  border: 1px solid var(--color-error-banner-border);
  border-radius: var(--radius-md);
  background: var(--color-error-banner-bg);
  padding: 0.8rem;
  margin-bottom: 1rem;
  color: var(--color-error-banner-text);
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

<<<<<<< HEAD
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
=======
@media (min-width: 1100px) {
  .room-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
>>>>>>> d2e4f3eee608dd6dc5cb2bf45e32f7ab129a9166
}

.loading {
  border: 1px dashed var(--color-border);
  border-radius: var(--radius-lg);
  background: var(--color-surface);
  padding: 1rem;
  color: var(--color-muted);
}

/* Toast slide-in from bottom-right */
.toast-enter-active,
.toast-leave-active {
  transition: opacity 0.22s ease, transform 0.22s ease;
}

.toast-enter-from,
.toast-leave-to {
  opacity: 0;
  transform: translateY(0.5rem);
}
</style>
