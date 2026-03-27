<script setup lang="ts">
withDefaults(
  defineProps<{
    variant?:
      | 'primary'
      | 'light'
      | 'ghost'
      | 'roomLock'
      | 'roomUnlock'
      | 'roomOutline'
      | 'icon'
      | 'iconDanger'
    type?: 'button' | 'submit'
    disabled?: boolean
    slim?: boolean
    block?: boolean
    /** Etwas grosszügigeres Padding (z. B. Login-CTA) */
    comfortable?: boolean
  }>(),
  {
    variant: 'primary',
    type: 'button',
    disabled: false,
    slim: false,
    block: false,
    comfortable: false,
  }
)
</script>

<template>
  <button
    :type="type"
    class="ui-btn"
    :class="[
      `ui-btn--${variant}`,
      {
        'ui-btn--slim': slim,
        'ui-btn--block': block,
        'ui-btn--comfortable': comfortable,
      },
    ]"
    :disabled="disabled"
  >
    <slot />
  </button>
</template>

<style scoped>
.ui-btn {
  margin: 0;
  font: inherit;
  font-weight: 700;
  cursor: pointer;
  border-radius: var(--radius-md);
}

.ui-btn:disabled {
  cursor: not-allowed;
  opacity: 0.65;
}

.ui-btn--block {
  width: 100%;
}

.ui-btn--slim {
  padding: 0.38rem 0.55rem;
  font-size: 0.78rem;
  line-height: 1.2;
  border-radius: var(--radius-sm);
}

.ui-btn:not(.ui-btn--slim):not(.ui-btn--comfortable) {
  padding: 0.62rem 0.9rem;
  font-size: inherit;
}

.ui-btn--comfortable:not(.ui-btn--slim) {
  padding: 0.75rem 0.9rem;
  font-size: 0.95rem;
  font-weight: 600;
}

.ui-btn--primary {
  border: 0;
  background: linear-gradient(135deg, var(--color-primary), var(--color-primary-strong));
  color: var(--color-surface);
}

.ui-btn--primary:hover:not(:disabled) {
  filter: brightness(1.03);
}

.ui-btn--light {
  border: 1px solid var(--color-border);
  background: var(--color-surface);
  color: var(--color-text);
}

.ui-btn--ghost {
  border: 1px solid var(--color-border);
  background: var(--color-surface);
  padding: 0.5rem 0.75rem;
  font-weight: 600;
}

.ui-btn--roomLock {
  flex: 1;
  border: 1px solid var(--color-danger-outline-border);
  background: var(--color-error-bg);
  color: var(--color-danger);
}

.ui-btn--roomLock:hover:not(:disabled) {
  background: var(--color-danger);
  border-color: var(--color-danger);
  color: var(--color-surface);
}

.ui-btn--roomUnlock {
  flex: 1;
  border: 1px solid transparent;
  background: linear-gradient(135deg, var(--color-primary), var(--color-primary-strong));
  color: var(--color-surface);
}

.ui-btn--roomUnlock:hover:not(:disabled) {
  background: linear-gradient(135deg, var(--color-primary-strong), var(--color-primary-strong));
}

.ui-btn--roomOutline {
  flex: 1;
  border: 1px solid var(--color-border);
  background: var(--color-surface);
  color: var(--color-text);
}

.ui-btn--roomOutline:hover:not(:disabled) {
  border-color: var(--color-primary);
}

.ui-btn--icon {
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: var(--color-surface);
  padding: 0.3rem 0.55rem;
  font-size: 0.76rem;
  font-weight: 600;
}

.ui-btn--iconDanger {
  border: 1px solid var(--color-danger-outline-border);
  border-radius: var(--radius-sm);
  background: var(--color-surface);
  padding: 0.3rem 0.55rem;
  font-size: 0.76rem;
  font-weight: 600;
  color: var(--color-danger-outline-text);
}
</style>
