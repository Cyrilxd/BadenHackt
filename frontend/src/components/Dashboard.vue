<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { roomsApi, whitelistsApi, type Room, type Whitelist } from '../api'
import { copy } from '../constants/copy'
import DashboardPageTitle from './dashboard/DashboardPageTitle.vue'
import RoomCard from './dashboard/RoomCard.vue'
import WhitelistModal from './dashboard/WhitelistModal.vue'

const rooms = ref<Room[]>([])
const whitelists = ref<Whitelist[]>([])
const selectedRoomId = ref<number | null>(null)
const fetching = ref(false)
const loadingRoomId = ref<number | null>(null)
const loadingModal = ref(false)
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

async function toggleInternet(room: Room) {
  loadingRoomId.value = room.id
  error.value = ''

  try {
    const newState = !room.internet_enabled
    await roomsApi.toggleInternet(room.id, newState)
    room.internet_enabled = newState
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
      selectedRoomId.value
    )

    whitelists.value.push(whitelist)

    newWhitelistName.value = ''
    newWhitelistUrls.value = ''
    showWhitelistForm.value = false
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
      selectedRoomId.value
    )

    const index = whitelists.value.findIndex(w => w.id === updatedWhitelist.id)
    if (index !== -1) {
      whitelists.value[index] = updatedWhitelist
    }

    cancelEditWhitelist()
  } catch (err: any) {
    error.value =
      err?.response?.data?.detail || copy.dashboard.whitelistUpdateError
  } finally {
    loadingModal.value = false
  }
}

async function deleteWhitelist(id: number) {
  if (!confirm(copy.dashboard.deleteConfirm)) return

  loadingModal.value = true
  error.value = ''

  try {
    await whitelistsApi.deleteWhitelist(id)
    whitelists.value = whitelists.value.filter(w => w.id !== id)

    if (editingWhitelistId.value === id) {
      cancelEditWhitelist()
    }
  } catch (err: any) {
    error.value = err?.response?.data?.detail || copy.dashboard.whitelistDeleteError
  } finally {
    loadingModal.value = false
  }
}

const selectedRoom = computed(() =>
  rooms.value.find(r => r.id === selectedRoomId.value) ?? null
)
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
        @toggle="toggleInternet"
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
      @delete="deleteWhitelist"
      @edit="startEditWhitelist"
    />
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

@media (min-width: 1100px) {
  .room-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

.loading {
  border: 1px dashed var(--color-border);
  border-radius: var(--radius-lg);
  background: var(--color-surface);
  padding: 1rem;
  color: var(--color-muted);
}
</style>
