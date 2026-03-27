<script setup lang="ts">
defineProps<{
  eyebrow: string
  title: string
}>()
</script>

<template>
  <div class="page-title">
    <p class="eyebrow">{{ eyebrow }}</p>
    <h2 class="heading">{{ title }}</h2>
  </div>
</template>

<style scoped>
.page-title {
  margin-bottom: 1.2rem;
}

.eyebrow {
  margin: 0;
  color: var(--color-muted);
  font-size: 0.8rem;
  font-weight: 600;
  letter-spacing: 0.05em;
  text-transform: uppercase;
}

.heading {
  margin: 0.25rem 0 0;
  color: var(--color-text);
  font-size: 1.5rem;
  font-weight: 700;
}
</style>
