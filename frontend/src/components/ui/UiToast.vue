<script setup lang="ts">
defineProps<{
  message: string
  type: 'success' | 'error'
}>()
</script>

<template>
  <div class="toast" :class="`toast--${type}`" role="status" aria-live="polite">
    {{ message }}
  </div>
</template>

<style scoped>
.toast {
  position: fixed;
  bottom: 1.5rem;
  right: 1.5rem;
  z-index: 100;
  border-radius: var(--radius-lg);
  padding: 0.75rem 1.1rem;
  font-size: 0.9rem;
  font-weight: 600;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
  pointer-events: none;
}

.toast--success {
  border: 1px solid var(--color-status-on-border);
  background: var(--color-status-on-bg);
  color: var(--color-status-on-fg);
}

.toast--error {
  border: 1px solid var(--color-error-banner-border);
  background: var(--color-error-banner-bg);
  color: var(--color-error-banner-text);
}
</style>
