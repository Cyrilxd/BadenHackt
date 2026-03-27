<script setup lang="ts">
import { copy } from '../../constants/copy'

defineProps<{
  username: string | undefined
}>()

const emit = defineEmits<{
  logout: []
}>()
</script>

<template>
  <header class="topbar">
    <div class="topbar-inner">
      <div class="brand">
        <img src="/zB_Logo.png" alt="" class="brand-logo" width="66" height="40" />
        <div class="brand-copy">
          <p class="brand-title">{{ copy.app.brandTitle }}</p>
          <p class="brand-subtitle">{{ copy.app.brandSubtitle }}</p>
        </div>
      </div>

      <div class="session">
        <span class="session-pill">{{ username }}</span>
        <button
          type="button"
          class="session-pill session-pill-button"
          @click="emit('logout')"
        >
          {{ copy.app.logout }}
        </button>
      </div>
    </div>
  </header>
</template>

<style scoped>
.topbar {
  border-bottom: 1px solid var(--color-border);
  background: var(--color-topbar-bg);
  backdrop-filter: blur(6px);
}

.topbar-inner {
  display: flex;
  max-width: var(--layout-topbar-max);
  margin: 0 auto;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding: 1rem 1.5rem;
}

.brand {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.brand-logo {
  width: 66px;
  height: auto;
}

.brand-title {
  margin: 0;
  font-size: 1rem;
  font-weight: 700;
  color: var(--color-text);
}

.brand-subtitle {
  margin: 0;
  font-size: 0.8rem;
  color: var(--color-muted);
}

.session {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.session-pill {
  display: inline-flex;
  align-items: center;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-pill);
  background: var(--color-surface);
  padding: 0.4rem 0.8rem;
  font-size: 0.85rem;
  color: var(--color-muted);
}

.session-pill-button {
  margin: 0;
  font: inherit;
  font-weight: 600;
  cursor: pointer;
}

.session-pill-button:hover {
  border-color: var(--color-primary);
  color: var(--color-text);
}
</style>
