<script setup lang="ts">
import UiButton from './UiButton.vue'

defineProps<{
  title: string
  message: string
  confirmLabel: string
  cancelLabel: string
  danger?: boolean
}>()

const emit = defineEmits<{
  confirm: []
  cancel: []
}>()
</script>

<template>
  <div
    class="confirm-backdrop"
    role="presentation"
    @click.self="emit('cancel')"
  >
    <div class="confirm-card" role="alertdialog" aria-modal="true">
      <h3 class="confirm-title">{{ title }}</h3>
      <p class="confirm-message">{{ message }}</p>
      <div class="confirm-actions">
        <UiButton variant="light" type="button" @click="emit('cancel')">
          {{ cancelLabel }}
        </UiButton>
        <button
          type="button"
          class="confirm-btn"
          :class="danger ? 'confirm-btn--danger' : 'confirm-btn--primary'"
          @click="emit('confirm')"
        >
          {{ confirmLabel }}
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.confirm-backdrop {
  position: fixed;
  inset: 0;
  z-index: 40;
  display: grid;
  place-items: center;
  background: var(--color-modal-backdrop);
  padding: 1rem;
}

.confirm-card {
  width: min(420px, 100%);
  border-radius: var(--radius-xl);
  border: 1px solid var(--color-modal-border);
  background: var(--color-surface);
  padding: 1.4rem 1.4rem 1.1rem;
}

.confirm-title {
  margin: 0 0 0.5rem;
  font-size: 1.05rem;
  color: var(--color-text);
}

.confirm-message {
  margin: 0 0 1.2rem;
  font-size: 0.9rem;
  color: var(--color-muted);
  line-height: 1.5;
}

.confirm-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.5rem;
}

.confirm-btn {
  margin: 0;
  cursor: pointer;
  border-radius: var(--radius-md);
  border: 0;
  padding: 0.62rem 0.9rem;
  font: inherit;
  font-size: inherit;
  font-weight: 700;
}

.confirm-btn--primary {
  background: linear-gradient(135deg, var(--color-primary), var(--color-primary-strong));
  color: var(--color-surface);
}

.confirm-btn--danger {
  background: linear-gradient(135deg, var(--color-danger), var(--color-danger-strong));
  color: #fff;
}

.confirm-btn:hover {
  filter: brightness(1.05);
}
</style>
