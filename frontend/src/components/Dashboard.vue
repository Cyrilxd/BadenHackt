<script setup lang="ts">
import { ref, onMounted, computed } from "vue";
import { roomsApi, whitelistsApi, type Room, type Whitelist } from "../api";
import { copy } from "../constants/copy";
import DashboardPageTitle from "./dashboard/DashboardPageTitle.vue";
import RoomCard from "./dashboard/RoomCard.vue";
import RoomScheduleModal from "./dashboard/RoomScheduleModal.vue";
import WhitelistModal from "./dashboard/WhitelistModal.vue";
import AuditLog from "./dashboard/AuditLog.vue";
import UiButton from "./ui/UiButton.vue";
import UiToast from "./ui/UiToast.vue";
import UiConfirm from "./ui/UiConfirm.vue";
import { parseWhitelistUrlList } from "../utils/whitelistValidation";

const rooms = ref<Room[]>([]);
const whitelists = ref<Whitelist[]>([]);
const selectedRoomId = ref<number | null>(null);
const fetching = ref(false);
const loadingRoomId = ref<number | null>(null);
const bulkLoading = ref(false);
const loadingModal = ref(false);
const scheduleLoading = ref(false);
const error = ref("");
const scheduleError = ref("");
const modalVisible = ref(false);
const scheduleModalVisible = ref(false);

// Toast
const toast = ref<{ message: string; type: "success" | "error" } | null>(null);
let _toastTimer: ReturnType<typeof setTimeout> | null = null;

function showToast(message: string, type: "success" | "error" = "success") {
    if (_toastTimer) clearTimeout(_toastTimer);
    toast.value = { message, type };
    _toastTimer = setTimeout(() => {
        toast.value = null;
    }, 3000);
}

// Confirm-Dialog
interface ConfirmOptions {
    title: string;
    message: string;
    danger?: boolean;
    onConfirm: () => void;
}
const confirmDialog = ref<ConfirmOptions | null>(null);

function showConfirm(options: ConfirmOptions) {
    confirmDialog.value = options;
}
function handleConfirmOk() {
    confirmDialog.value?.onConfirm();
    confirmDialog.value = null;
}
function handleConfirmCancel() {
    confirmDialog.value = null;
}

const auditVisible = ref(false);
const scheduleEnabled = ref(false);
const scheduleOpenTime = ref("07:30");
const scheduleLockTime = ref("17:00");
const clearScheduleOverride = ref(false);

const showWhitelistForm = ref(false);
const newWhitelistName = ref("");
const newWhitelistUrls = ref("");
const newWhitelistIsActive = ref(true);

const editingWhitelistId = ref<number | null>(null);
const editWhitelistName = ref("");
const editWhitelistUrls = ref("");
const editWhitelistIsActive = ref(true);

const selectedRoomWhitelists = computed(() => {
    if (!selectedRoomId.value) return [];
    return whitelists.value
        .filter((w) => w.room_id === selectedRoomId.value)
        .sort((a, b) => {
            if (a.is_active !== b.is_active) {
                return a.is_active ? -1 : 1;
            }
            return a.name.localeCompare(b.name, "de-CH");
        });
});

const selectedRoom = computed(
    () => rooms.value.find((r) => r.id === selectedRoomId.value) ?? null,
);

const allRoomsLocked = computed(
    () =>
        rooms.value.length > 0 &&
        rooms.value.every((room) => !room.internet_enabled),
);

const bulkToggleTargetEnabled = computed(() => allRoomsLocked.value);

const bulkToggleLabel = computed(() => {
    if (bulkLoading.value) return copy.dashboard.toggleAllWorking;
    return bulkToggleTargetEnabled.value
        ? copy.dashboard.unlockAllRooms
        : copy.dashboard.lockAllRooms;
});

const bulkToggleDisabled = computed(
    () =>
        rooms.value.length === 0 ||
        fetching.value ||
        bulkLoading.value ||
        loadingRoomId.value !== null,
);

onMounted(async () => {
    await loadData();
});

async function loadData() {
    fetching.value = true;
    error.value = "";
    try {
        const [loadedRooms, loadedWhitelists] = await Promise.all([
            roomsApi.getRooms(),
            whitelistsApi.getWhitelists(),
        ]);
        rooms.value = loadedRooms;
        whitelists.value = loadedWhitelists;
    } catch {
        error.value = copy.dashboard.loadError;
    } finally {
        fetching.value = false;
    }
}

function requestToggle(room: Room) {
    const willEnable = !room.internet_enabled;
    showConfirm({
        title: willEnable
            ? copy.confirm.toggleOnTitle
            : copy.confirm.toggleOffTitle,
        message: `Alle Geräte in «${room.name}» ${willEnable ? copy.confirm.toggleOnBody : copy.confirm.toggleOffBody}`,
        danger: !willEnable,
        onConfirm: () => toggleInternet(room),
    });
}

async function setRoomInternet(room: Room, enable: boolean) {
    const response = await roomsApi.toggleInternet(room.id, enable);
    room.internet_enabled = response.internet_enabled;
    room.manual_override_active = response.manual_override_active;
    room.manual_override_enabled = response.internet_enabled;
    room.control_mode = response.control_mode;
}

async function toggleInternet(room: Room) {
    loadingRoomId.value = room.id;
    error.value = "";

    try {
        const newState = !room.internet_enabled;
        await setRoomInternet(room, newState);
        showToast(newState ? copy.toast.toggleOn : copy.toast.toggleOff);
    } catch {
        error.value = copy.dashboard.toggleError;
    } finally {
        loadingRoomId.value = null;
    }
}

function requestToggleAll() {
    const enable = bulkToggleTargetEnabled.value;
    showConfirm({
        title: enable
            ? copy.confirm.toggleAllOnTitle
            : copy.confirm.toggleAllOffTitle,
        message: enable
            ? copy.confirm.toggleAllOnBody
            : copy.confirm.toggleAllOffBody,
        danger: !enable,
        onConfirm: () => toggleAllRooms(enable),
    });
}

async function toggleAllRooms(enable: boolean) {
    const roomsToUpdate = rooms.value.filter(
        (room) => room.internet_enabled !== enable,
    );

    if (roomsToUpdate.length === 0) {
        showToast(enable ? copy.toast.toggleAllOn : copy.toast.toggleAllOff);
        return;
    }

    bulkLoading.value = true;
    error.value = "";

    try {
        const results = await Promise.allSettled(
            roomsToUpdate.map((room) =>
                roomsApi.toggleInternet(room.id, enable),
            ),
        );

        if (results.some((result) => result.status === "rejected")) {
            try {
                rooms.value = await roomsApi.getRooms();
            } catch {
                // Keep the visible error focused on the failed bulk action.
            }
            error.value = copy.dashboard.toggleAllError;
            return;
        }

        for (const room of roomsToUpdate) {
            room.internet_enabled = enable;
            room.manual_override_active = true;
            room.manual_override_enabled = enable;
            room.control_mode = "manual_override";
        }

        showToast(enable ? copy.toast.toggleAllOn : copy.toast.toggleAllOff);
    } catch {
        error.value = copy.dashboard.toggleAllError;
    } finally {
        bulkLoading.value = false;
    }
}

function selectRoom(roomId: number) {
    selectedRoomId.value = roomId;
}

function openScheduleModal(room: Room) {
    selectRoom(room.id);
    scheduleEnabled.value = room.schedule_enabled;
    scheduleOpenTime.value = room.schedule_open_time ?? "07:30";
    scheduleLockTime.value = room.schedule_lock_time ?? "17:00";
    clearScheduleOverride.value = false;
    scheduleError.value = "";
    scheduleModalVisible.value = true;
}

function closeScheduleModal() {
    scheduleModalVisible.value = false;
    scheduleError.value = "";
    clearScheduleOverride.value = false;
}

function openWhitelistModal(roomId: number, openCreateForm = false) {
    selectRoom(roomId);
    modalVisible.value = true;
    showWhitelistForm.value = openCreateForm;
    if (openCreateForm) {
        cancelEditWhitelist();
    }
    error.value = "";
}

function closeWhitelistModal() {
    modalVisible.value = false;
    showWhitelistForm.value = false;
    cancelEditWhitelist();
    newWhitelistName.value = "";
    newWhitelistUrls.value = "";
    newWhitelistIsActive.value = true;
}

function handleRoomCardClick(room: Room) {
    selectRoom(room.id);
    if (!room.internet_enabled) {
        openWhitelistModal(room.id, true);
    }
}

async function createWhitelist() {
    if (!selectedRoomId.value) {
        error.value = copy.dashboard.selectRoomFirst;
        return;
    }

    const cleanedName = newWhitelistName.value.trim();
    if (!cleanedName) {
        error.value = copy.dashboard.whitelistNameMissing;
        return;
    }

    let urls: string[];
    try {
        urls = parseWhitelistUrlList(newWhitelistUrls.value);
    } catch (err: any) {
        error.value = err?.message || copy.dashboard.whitelistUrlInvalid;
        return;
    }

    if (urls.length === 0) {
        error.value = copy.dashboard.whitelistUrlsMissing;
        return;
    }

    loadingModal.value = true;
    error.value = "";

    try {
        await whitelistsApi.createWhitelist(
            cleanedName,
            urls,
            selectedRoomId.value,
            newWhitelistIsActive.value,
        );

        await loadData();

        newWhitelistName.value = "";
        newWhitelistUrls.value = "";
        newWhitelistIsActive.value = true;
        showWhitelistForm.value = false;
        showToast(copy.toast.whitelistCreated);
    } catch (err: any) {
        error.value =
            err?.response?.data?.detail || copy.dashboard.whitelistCreateError;
    } finally {
        loadingModal.value = false;
    }
}

function startEditWhitelist(wl: Whitelist) {
    editingWhitelistId.value = wl.id;
    editWhitelistName.value = wl.name;
    editWhitelistUrls.value = wl.urls.join("\n");
    editWhitelistIsActive.value = wl.is_active;
    showWhitelistForm.value = false;
    error.value = "";
}

function cancelEditWhitelist() {
    editingWhitelistId.value = null;
    editWhitelistName.value = "";
    editWhitelistUrls.value = "";
    editWhitelistIsActive.value = true;
}

async function updateWhitelist() {
    if (editingWhitelistId.value === null || selectedRoomId.value === null) {
        error.value = copy.dashboard.noSelection;
        return;
    }

    const cleanedName = editWhitelistName.value.trim();
    if (!cleanedName) {
        error.value = copy.dashboard.whitelistNameMissing;
        return;
    }

    let urls: string[];
    try {
        urls = parseWhitelistUrlList(editWhitelistUrls.value);
    } catch (err: any) {
        error.value = err?.message || copy.dashboard.whitelistUrlInvalid;
        return;
    }

    if (urls.length === 0) {
        error.value = copy.dashboard.whitelistUrlsMissing;
        return;
    }

    loadingModal.value = true;
    error.value = "";

    try {
        await whitelistsApi.updateWhitelist(
            editingWhitelistId.value,
            cleanedName,
            urls,
            selectedRoomId.value,
            editWhitelistIsActive.value,
        );
        await loadData();

        cancelEditWhitelist();
        showToast(copy.toast.whitelistUpdated);
    } catch (err: any) {
        error.value =
            err?.response?.data?.detail || copy.dashboard.whitelistUpdateError;
    } finally {
        loadingModal.value = false;
    }
}

async function toggleWhitelistActive(wl: Whitelist) {
    if (selectedRoomId.value === null) {
        error.value = copy.dashboard.noSelection;
        return;
    }

    loadingModal.value = true;
    error.value = "";

    try {
        const updatedWhitelist = await whitelistsApi.toggleWhitelist(
            wl.id,
            selectedRoomId.value,
            !wl.is_active,
        );
        await loadData();

        if (editingWhitelistId.value === updatedWhitelist.id) {
            editWhitelistIsActive.value = updatedWhitelist.is_active;
        }
    } catch (err: any) {
        error.value =
            err?.response?.data?.detail ||
            "Fehler beim Aktivieren/Deaktivieren der Whitelist";
    } finally {
        loadingModal.value = false;
    }
}

function requestDelete(id: number) {
    showConfirm({
        title: copy.confirm.deleteTitle,
        message: copy.confirm.deleteBody,
        danger: true,
        onConfirm: () => doDeleteWhitelist(id),
    });
}

async function doDeleteWhitelist(id: number) {
    loadingModal.value = true;
    error.value = "";

    try {
        await whitelistsApi.deleteWhitelist(id);
        await loadData();

        if (editingWhitelistId.value === id) {
            cancelEditWhitelist();
        }
        showToast(copy.toast.whitelistDeleted);
    } catch (err: any) {
        error.value =
            err?.response?.data?.detail || copy.dashboard.whitelistDeleteError;
    } finally {
        loadingModal.value = false;
    }
}

async function saveRoomSchedule() {
    if (!selectedRoom.value) {
        scheduleError.value = copy.schedule.noRoomSelected;
        return;
    }

    if (
        scheduleEnabled.value &&
        (!scheduleOpenTime.value || !scheduleLockTime.value)
    ) {
        scheduleError.value = copy.schedule.timeMissing;
        return;
    }

    if (
        scheduleEnabled.value &&
        scheduleOpenTime.value === scheduleLockTime.value
    ) {
        scheduleError.value = copy.schedule.timeSame;
        return;
    }

    scheduleLoading.value = true;
    scheduleError.value = "";

    try {
        const updatedRoom = await roomsApi.updateSchedule(
            selectedRoom.value.id,
            {
                schedule_enabled: scheduleEnabled.value,
                schedule_open_time: scheduleEnabled.value
                    ? scheduleOpenTime.value
                    : null,
                schedule_lock_time: scheduleEnabled.value
                    ? scheduleLockTime.value
                    : null,
                clear_override: clearScheduleOverride.value,
            },
        );

        const roomIndex = rooms.value.findIndex(
            (room) => room.id === updatedRoom.id,
        );
        if (roomIndex >= 0) {
            rooms.value[roomIndex] = updatedRoom;
        }

        closeScheduleModal();
        showToast(copy.toast.scheduleSaved);
    } catch (err: any) {
        scheduleError.value =
            err?.response?.data?.detail || copy.schedule.saveError;
    } finally {
        scheduleLoading.value = false;
    }
}
</script>

<template>
    <div class="dashboard">
        <div class="dashboard-header">
            <DashboardPageTitle
                :eyebrow="copy.dashboard.eyebrowOverview"
                :title="copy.dashboard.titleRooms"
            />
            <div class="dashboard-header-actions">
                <UiButton
                    type="button"
                    slim
                    :variant="bulkToggleTargetEnabled ? 'primary' : 'danger'"
                    :disabled="bulkToggleDisabled"
                    @click="requestToggleAll"
                >
                    {{ bulkToggleLabel }}
                </UiButton>
                <UiButton
                    type="button"
                    variant="light"
                    slim
                    @click="auditVisible = true"
                >
                    {{ copy.audit.openButton }}
                </UiButton>
            </div>
        </div>

        <p v-if="error && !modalVisible" class="error-banner">{{ error }}</p>

        <div v-if="fetching && rooms.length === 0" class="loading">
            {{ copy.dashboard.loading }}
        </div>

        <section v-else class="room-grid">
            <RoomCard
                v-for="room in rooms"
                :key="room.id"
                :room="room"
                :loading="bulkLoading || loadingRoomId === room.id"
                :active-whitelists="whitelists.filter(w => w.room_id === room.id && w.is_active)"
                @card-click="handleRoomCardClick"
                @toggle="requestToggle"
                @manage="(r) => openWhitelistModal(r.id, !r.internet_enabled)"
                @schedule="openScheduleModal"
            />
        </section>

        <RoomScheduleModal
            :open="scheduleModalVisible"
            :room="selectedRoom"
            :loading="scheduleLoading"
            :error-message="scheduleError"
            v-model:schedule-enabled="scheduleEnabled"
            v-model:schedule-open-time="scheduleOpenTime"
            v-model:schedule-lock-time="scheduleLockTime"
            v-model:clear-override="clearScheduleOverride"
            @close="closeScheduleModal"
            @save="saveRoomSchedule"
        />

        <WhitelistModal
            :open="modalVisible"
            :room-title="selectedRoom?.name ?? ''"
            :lists="selectedRoomWhitelists"
            :loading="loadingModal"
            :editing-id="editingWhitelistId"
            :error-message="error"
            v-model:new-name="newWhitelistName"
            v-model:new-urls="newWhitelistUrls"
            v-model:new-active="newWhitelistIsActive"
            v-model:show-form="showWhitelistForm"
            v-model:edit-name="editWhitelistName"
            v-model:edit-urls="editWhitelistUrls"
            v-model:edit-active="editWhitelistIsActive"
            @close="closeWhitelistModal"
            @toggleForm="showWhitelistForm = !showWhitelistForm"
            @create="createWhitelist"
            @saveWhitelist="updateWhitelist"
            @cancelEdit="cancelEditWhitelist"
            @delete="requestDelete"
            @edit="startEditWhitelist"
            @toggle-active="toggleWhitelistActive"
        />

        <AuditLog :open="auditVisible" @close="auditVisible = false" />

        <Transition name="toast">
            <UiToast v-if="toast" :message="toast.message" :type="toast.type" />
        </Transition>

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
    </div>
</template>

<style scoped>
.dashboard {
    width: min(var(--layout-dashboard-max), 100%);
    margin: 0 auto;
    padding: 1.5rem;
}

.dashboard-header {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 1rem;
    margin-bottom: 0.25rem;
}

.dashboard-header-actions {
    display: flex;
    flex-wrap: wrap;
    justify-content: flex-end;
    gap: 0.6rem;
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

@media (max-width: 699px) {
    .dashboard-header {
        flex-direction: column;
    }

    .dashboard-header-actions {
        width: 100%;
        justify-content: flex-start;
    }

    .dashboard-header-actions :deep(button) {
        flex: 1 1 0;
    }
}

@media (min-width: 1380px) {
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

/* Toast slide-in from bottom-right */
.toast-enter-active,
.toast-leave-active {
    transition:
        opacity 0.22s ease,
        transform 0.22s ease;
}

.toast-enter-from,
.toast-leave-to {
    opacity: 0;
    transform: translateY(0.5rem);
}
</style>
