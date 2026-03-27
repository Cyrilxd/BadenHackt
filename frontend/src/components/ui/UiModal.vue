<script setup lang="ts">
defineProps<{
  open: boolean
}>()

const emit = defineEmits<{
  close: []
}>()
</script>

<template>
  <div
    v-if="open"
    class="modal-backdrop"
    role="presentation"
    @click.self="emit('close')"
  >
    <section class="modal-card" role="dialog" aria-modal="true" @click.stop>
      <slot />
    </section>
  </div>
</template>

<style scoped>
.modal-backdrop {
  position: fixed;
  inset: 0;
  z-index: 30;
  display: grid;
  place-items: center;
  background: var(--color-modal-backdrop);
  padding: 1rem;
}

.modal-card {
  width: min(var(--layout-modal-max), 100%);
  max-height: 85vh;
  overflow: auto;
  border-radius: var(--radius-xl);
  border: 1px solid var(--color-modal-border);
  background: var(--color-surface);
  padding: 1rem;
}
</style>
