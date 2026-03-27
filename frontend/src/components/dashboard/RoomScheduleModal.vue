<script setup lang="ts">
import { computed } from "vue";
import type { Room } from "../../api";
import { copy } from "../../constants/copy";
import UiButton from "../ui/UiButton.vue";
import UiModal from "../ui/UiModal.vue";

const props = defineProps<{
    open: boolean;
    room: Room | null;
    loading: boolean;
    errorMessage: string;
}>();

const scheduleEnabled = defineModel<boolean>("scheduleEnabled", {
    required: true,
});
const scheduleOpenTime = defineModel<string>("scheduleOpenTime", {
    required: true,
});
const scheduleLockTime = defineModel<string>("scheduleLockTime", {
    required: true,
});
const clearOverride = defineModel<boolean>("clearOverride", {
    required: true,
});

const emit = defineEmits<{
    close: [];
    save: [];
}>();

const scheduleSummary = computed(() => {
    if (!props.room?.schedule_enabled) {
        return copy.schedule.summaryDisabled;
    }
    return copy.schedule.summaryTemplate(
        props.room.schedule_open_time ?? "--:--",
        props.room.schedule_lock_time ?? "--:--",
    );
});
</script>

<template>
    <UiModal :open="open" @close="emit('close')">
        <header class="modal-header">
            <div>
                <p class="modal-eyebrow">{{ copy.schedule.eyebrow }}</p>
                <h3>{{ room?.name ?? "" }}</h3>
            </div>
            <UiButton variant="ghost" type="button" @click="emit('close')">
                {{ copy.schedule.close }}
            </UiButton>
        </header>

        <p class="modal-summary">{{ scheduleSummary }}</p>
        <p v-if="errorMessage" class="error-alert">{{ errorMessage }}</p>

        <label class="toggle-row">
            <input v-model="scheduleEnabled" type="checkbox" />
            <span>{{ copy.schedule.enabled }}</span>
        </label>

        <div
            class="time-grid"
            :class="{ 'time-grid-disabled': !scheduleEnabled }"
        >
            <label>
                <span>{{ copy.schedule.lockTime }}</span>
                <input
                    v-model="scheduleLockTime"
                    type="time"
                    class="field"
                    :disabled="!scheduleEnabled"
                />
            </label>

            <label>
                <span>{{ copy.schedule.openTime }}</span>
                <input
                    v-model="scheduleOpenTime"
                    type="time"
                    class="field"
                    :disabled="!scheduleEnabled"
                />
            </label>
        </div>

        <label
            v-if="room?.manual_override_active"
            class="toggle-row override-toggle"
        >
            <input v-model="clearOverride" type="checkbox" />
            <span>{{ copy.schedule.clearOverride }}</span>
        </label>

        <div class="modal-actions">
            <UiButton
                variant="primary"
                type="button"
                :disabled="loading"
                @click="emit('save')"
            >
                {{ copy.schedule.save }}
            </UiButton>
        </div>
    </UiModal>
</template>

<style scoped>
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

.modal-summary {
    margin: 0 0 1rem;
    color: var(--color-muted);
}

.error-alert {
    margin: 0 0 0.8rem;
    border: 1px solid var(--color-error-border);
    border-radius: var(--radius-md);
    background: var(--color-error-bg);
    padding: 0.7rem 0.8rem;
    color: var(--color-error-text);
}

.toggle-row {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    margin-bottom: 0.9rem;
    color: var(--color-muted);
    font-size: 0.92rem;
}

.time-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 0.8rem;
}

.time-grid label {
    display: grid;
    gap: 0.35rem;
    color: var(--color-text);
    font-size: 0.9rem;
}

.time-grid-disabled {
    opacity: 0.55;
}

.field {
    width: 100%;
    border: 1px solid var(--color-border);
    border-radius: var(--radius-md);
    background: var(--color-surface);
    padding: 0.62rem 0.7rem;
    font-size: 0.9rem;
}

.override-toggle {
    margin-top: 1rem;
}

.modal-actions {
    display: flex;
    justify-content: flex-end;
    margin-top: 1rem;
}

@media (max-width: 640px) {
    .time-grid {
        grid-template-columns: 1fr;
    }
}
</style>
