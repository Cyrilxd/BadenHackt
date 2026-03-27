<script setup lang="ts">
import type { Room } from '../../api'
import { copy } from '../../constants/copy'
import UiButton from '../ui/UiButton.vue'

defineProps<{
  room: Room
  selected: boolean
  loading: boolean
}>()

const emit = defineEmits<{
  cardClick: [room: Room]
  toggle: [room: Room]
  manage: [room: Room]
}>()
</script>

<template>
  <article
    class="room-card"
    :class="{
      'room-card-selected': selected,
      'room-card-disabled': !room.internet_enabled
    }"
    @click="emit('cardClick', room)"
  >
    <header class="room-head">
      <h3>{{ room.name }}</h3>
      <span class="vlan-badge">{{ copy.room.vlanPrefix }} {{ room.vlan_id }}</span>
    </header>

    <p class="subnet">{{ room.subnet }}</p>

    <p class="status-pill" :class="room.internet_enabled ? 'status-on' : 'status-off'">
      {{ room.internet_enabled ? copy.room.statusOn : copy.room.statusOff }}
    </p>

    <div class="room-actions">
      <UiButton
        type="button"
        slim
        :variant="room.internet_enabled ? 'roomLock' : 'roomUnlock'"
        :disabled="loading"
        @click.stop="emit('toggle', room)"
      >
        {{ room.internet_enabled ? copy.room.lock : copy.room.unlock }}
      </UiButton>

      <UiButton
        type="button"
        slim
        variant="roomOutline"
        :disabled="loading"
        @click.stop="emit('manage', room)"
      >
        {{ room.internet_enabled ? copy.room.manageWhitelist : copy.room.whitelistDirect }}
      </UiButton>
    </div>
  </article>
</template>

<style scoped>
.room-card {
  display: flex;
  min-height: 168px;
  flex-direction: column;
  cursor: pointer;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-xl);
  background: var(--color-surface);
  padding: 1rem 1.15rem 0.85rem;
  transition:
    border-color 0.15s ease,
    box-shadow 0.15s ease;
}

.room-card:hover {
  border-color: var(--color-primary);
  box-shadow: var(--shadow-room-hover);
}

.room-card-selected {
  border-color: var(--color-primary);
}

.room-card-disabled {
  border-color: var(--color-room-disabled-border);
  background: var(--color-room-disabled-bg);
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
  border-radius: var(--radius-pill);
  background: var(--color-status-on-bg);
  padding: 0.25rem 0.55rem;
  color: var(--color-status-on-fg);
  font-size: 0.72rem;
  font-weight: 700;
}

.subnet {
  margin: 0.55rem 0 0.45rem;
  color: var(--color-muted);
  font-family: var(--font-mono);
  font-size: 0.82rem;
}

.status-pill {
  display: inline-block;
  align-self: flex-start;
  border-radius: var(--radius-pill);
  padding: 0.28rem 0.6rem;
  font-size: 0.76rem;
  font-weight: 700;
}

.status-on {
  background: var(--color-status-on-bg);
  color: var(--color-status-on-fg);
}

.status-off {
  background: var(--color-status-off-bg);
  color: var(--color-status-off-fg);
}

.room-actions {
  display: flex;
  gap: 0.5rem;
  margin-top: auto;
  padding-top: 0.75rem;
}
</style>
