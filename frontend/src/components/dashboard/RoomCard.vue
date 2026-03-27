<script setup lang="ts">
import type { Room, Whitelist } from "../../api";
import { copy } from "../../constants/copy";
import UiButton from "../ui/UiButton.vue";

defineProps<{
    room: Room;
    loading: boolean;
    activeWhitelists?: Whitelist[];
}>();

const emit = defineEmits<{
    cardClick: [room: Room];
    toggle: [room: Room];
    manage: [room: Room];
    schedule: [room: Room];
}>();
</script>

<template>
    <article
        class="room-card"
        :class="{
            'room-card-disabled': !room.internet_enabled,
        }"
        @click="emit('cardClick', room)"
    >
        <header class="room-head">
            <h3>{{ room.name }}</h3>
            <span class="vlan-badge"
                >{{ copy.room.vlanPrefix }} {{ room.vlan_id }}</span
            >
        </header>

        <p class="subnet">{{ room.subnet }}</p>

        <p
            class="status-pill"
            :class="room.internet_enabled ? 'status-on' : 'status-off'"
        >
            <span class="status-dot"></span>
            {{
                room.internet_enabled ? copy.room.statusOn : copy.room.statusOff
            }}
        </p>

        <div v-if="activeWhitelists && activeWhitelists.length > 0" class="whitelist-tags">
            <span
                v-for="wl in activeWhitelists.slice(0, 3)"
                :key="wl.id"
                class="whitelist-tag"
            >{{ wl.name }}</span>
            <span v-if="activeWhitelists.length > 3" class="whitelist-tag whitelist-tag-more">
                +{{ activeWhitelists.length - 3 }}
            </span>
        </div>

        <p v-if="room.schedule_enabled" class="meta-pill meta-schedule">
            {{
                copy.room.scheduleWindow(
                    room.schedule_open_time,
                    room.schedule_lock_time,
                )
            }}
        </p>

        <p v-if="room.manual_override_active" class="meta-pill meta-override">
            {{
                room.manual_override_enabled
                    ? copy.room.overrideOn
                    : copy.room.overrideOff
            }}
        </p>

        <div class="room-actions">
            <!-- Primäre Aktion: volle Breite -->
            <UiButton
                type="button"
                slim
                block
                :variant="room.internet_enabled ? 'roomLock' : 'roomUnlock'"
                :disabled="loading"
                @click.stop="emit('toggle', room)"
            >
                {{ room.internet_enabled ? copy.room.lock : copy.room.unlock }}
            </UiButton>

            <!-- Sekundäre Aktionen: nebeneinander -->
            <div class="room-actions-secondary">
                <UiButton
                    type="button"
                    slim
                    variant="roomOutline"
                    :disabled="loading"
                    @click.stop="emit('manage', room)"
                >
                    {{
                        room.internet_enabled
                            ? copy.room.manageWhitelist
                            : copy.room.whitelistDirect
                    }}
                </UiButton>

                <UiButton
                    type="button"
                    slim
                    variant="roomOutline"
                    :disabled="loading"
                    @click.stop="emit('schedule', room)"
                >
                    {{ copy.room.schedule }}
                </UiButton>
            </div>
        </div>
    </article>
</template>

<style scoped>
.room-card {
    display: flex;
    min-height: 200px;
    flex-direction: column;
    cursor: pointer;
    border: 1px solid var(--color-border);
    border-left: 4px solid var(--color-border);
    border-radius: var(--radius-xl);
    background: var(--color-surface);
    padding: 1.1rem 1.25rem 1rem;
    transition:
        border-color 0.15s ease,
        box-shadow 0.15s ease,
        background 0.15s ease;
}

.room-card:hover {
    border-color: var(--color-primary);
    border-left-color: var(--color-primary);
    box-shadow: var(--shadow-room-hover);
}

.room-card-disabled {
    border-color: var(--color-room-locked-border);
    border-left-color: var(--color-room-locked-accent);
    background: var(--color-room-locked-bg);
}

.room-card-disabled:hover {
    border-color: var(--color-room-locked-accent);
    border-left-color: var(--color-room-locked-accent);
    box-shadow: var(--color-room-locked-hover-shadow);
}

.room-head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 0.5rem;
}

.room-head h3 {
    margin: 0;
    color: var(--color-text);
    font-size: 1.08rem;
    font-weight: 700;
}

.vlan-badge {
    flex-shrink: 0;
    border: 1px solid var(--color-border);
    border-radius: var(--radius-pill);
    background: var(--color-surface-muted);
    padding: 0.2rem 0.55rem;
    color: var(--color-muted);
    font-size: 0.72rem;
    font-weight: 600;
}

.subnet {
    margin: 0.5rem 0 0.4rem;
    color: var(--color-muted);
    font-family: var(--font-mono);
    font-size: 0.75rem;
    opacity: 0.75;
}

.status-pill {
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
    align-self: flex-start;
    border-radius: var(--radius-pill);
    padding: 0.28rem 0.65rem 0.28rem 0.5rem;
    font-size: 0.76rem;
    font-weight: 700;
}

.status-dot {
    display: inline-block;
    width: 7px;
    height: 7px;
    border-radius: 50%;
    flex-shrink: 0;
}

.status-on {
    background: var(--color-status-on-bg);
    color: var(--color-status-on-fg);
}

.status-on .status-dot {
    background: var(--color-status-on-fg);
}

.status-off {
    background: var(--color-status-off-bg);
    color: var(--color-status-off-fg);
}

.status-off .status-dot {
    background: var(--color-status-off-fg);
}

.meta-pill {
    display: inline-block;
    align-self: flex-start;
    margin-top: 0.45rem;
    border-radius: var(--radius-pill);
    padding: 0.28rem 0.6rem;
    font-size: 0.76rem;
    font-weight: 700;
}

.meta-schedule {
    background: color-mix(in srgb, var(--color-primary) 12%, white);
    color: var(--color-primary);
}

.meta-override {
    background: color-mix(in srgb, var(--color-status-off-fg) 12%, white);
    color: var(--color-status-off-fg);
}

.whitelist-tags {
    display: flex;
    flex-wrap: wrap;
    gap: 0.3rem;
    margin-top: 0.45rem;
}

.whitelist-tag {
    display: inline-block;
    border: 1px solid var(--color-status-on-border);
    border-radius: var(--radius-pill);
    background: var(--color-status-on-bg);
    padding: 0.15rem 0.5rem;
    color: var(--color-status-on-fg);
    font-size: 0.7rem;
    font-weight: 600;
    max-width: 120px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.room-card-disabled .whitelist-tag {
    border-color: var(--color-border);
    background: var(--color-surface-muted);
    color: var(--color-muted);
}

.whitelist-tag-more {
    border-color: var(--color-border);
    background: var(--color-surface-muted);
    color: var(--color-muted);
}

.room-actions {
    display: flex;
    flex-direction: column;
    gap: 0.45rem;
    margin-top: auto;
    padding-top: 0.85rem;
}

.room-actions-secondary {
    display: flex;
    gap: 0.45rem;
}

.room-actions-secondary .ui-btn {
    flex: 1;
}
</style>
