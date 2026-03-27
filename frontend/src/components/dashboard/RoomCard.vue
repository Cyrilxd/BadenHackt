<script setup lang="ts">
import type { Room } from '../../api'

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
      <span class="vlan-badge">VLAN {{ room.vlan_id }}</span>
    </header>

    <p class="subnet">{{ room.subnet }}</p>

    <p class="status-pill" :class="room.internet_enabled ? 'status-on' : 'status-off'">
      {{ room.internet_enabled ? 'Internet aktiv' : 'Internet gesperrt' }}
    </p>

    <div class="room-actions">
      <button
        type="button"
        class="btn btn-slim"
        :class="room.internet_enabled ? 'btn-lock' : 'btn-unlock'"
        :disabled="loading"
        @click.stop="emit('toggle', room)"
      >
        {{ room.internet_enabled ? 'Sperren' : 'Freigeben' }}
      </button>

      <button
        type="button"
        class="btn btn-slim btn-outline"
        :disabled="loading"
        @click.stop="emit('manage', room)"
      >
        {{ room.internet_enabled ? 'Whitelist verwalten' : 'Whitelist direkt erfassen' }}
      </button>
    </div>
  </article>
</template>

<style scoped>
.room-card {
  display: flex;
  flex-direction: column;
  min-height: 168px;
  cursor: pointer;
  border: 1px solid var(--color-border);
  border-radius: 16px;
  background: #fff;
  padding: 1rem 1.15rem 0.85rem;
  transition:
    border-color 0.15s ease,
    box-shadow 0.15s ease;
}

.room-card:hover {
  border-color: var(--color-primary);
  box-shadow: 0 12px 26px rgba(44, 100, 36, 0.1);
}

.room-card-selected {
  border-color: var(--color-primary);
}

.room-card-disabled {
  border-color: #e3d4d4;
  background: #fffdfd;
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
  border-radius: 999px;
  background: var(--color-status-on-bg);
  padding: 0.25rem 0.55rem;
  color: var(--color-status-on-fg);
  font-size: 0.72rem;
  font-weight: 700;
}

.subnet {
  margin: 0.55rem 0 0.45rem;
  color: var(--color-muted);
  font-family: var(--mono);
  font-size: 0.82rem;
}

.status-pill {
  display: inline-block;
  align-self: flex-start;
  border-radius: 999px;
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

.btn {
  flex: 1;
  border-radius: 8px;
  font-size: 0.78rem;
  font-weight: 700;
  cursor: pointer;
}

.btn-slim {
  padding: 0.38rem 0.55rem;
  line-height: 1.2;
}

.btn:disabled {
  cursor: not-allowed;
  opacity: 0.65;
}

/* „Sperren“ im gleichen Grün-Ton wie Status „Internet aktiv“ */
.btn-lock {
  border: 1px solid var(--color-status-on-border);
  background: var(--color-status-on-bg);
  color: var(--color-status-on-fg);
}

.btn-lock:hover:not(:disabled) {
  background: #d8f0d0;
}

.btn-unlock {
  border: 1px solid transparent;
  background: linear-gradient(135deg, var(--color-primary), var(--color-primary-strong));
  color: #fff;
}

.btn-outline {
  border: 1px solid var(--color-border);
  background: #fff;
  color: var(--color-text);
}

.btn-outline:hover:not(:disabled) {
  border-color: var(--color-primary);
}
</style>
