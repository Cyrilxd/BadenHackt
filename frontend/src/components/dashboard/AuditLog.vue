<template>
  <UiModal :open="open" @close="$emit('close')">
    <div class="audit-modal">
      <DashboardPageTitle :eyebrow="copy.audit.eyebrow" :title="copy.audit.title" />

      <div v-if="loading" class="audit-state">{{ copy.audit.loading }}</div>
      <div v-else-if="error" class="audit-state audit-state--error">{{ copy.audit.loadError }}</div>

      <div v-else-if="entries.length === 0" class="audit-state">{{ copy.audit.empty }}</div>

      <div v-else class="audit-table-wrap">
        <table class="audit-table">
          <thead>
            <tr>
              <th>{{ copy.audit.colTime }}</th>
              <th>{{ copy.audit.colUser }}</th>
              <th>{{ copy.audit.colAction }}</th>
              <th>{{ copy.audit.colTarget }}</th>
              <th>{{ copy.audit.colStatus }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="entry in entries" :key="entry.id" :class="{ 'row--failed': !entry.success }">
              <td class="col-time">{{ formatTime(entry.timestamp) }}</td>
              <td class="col-user">{{ entry.username }}</td>
              <td class="col-action">{{ labelAction(entry.action) }}</td>
              <td class="col-target">{{ entry.target ?? '–' }}</td>
              <td class="col-status">
                <span :class="entry.success ? 'badge--ok' : 'badge--fail'">
                  {{ entry.success ? copy.audit.ok : copy.audit.failed }}
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="audit-footer">
        <UiButton variant="light" @click="$emit('close')">{{ copy.audit.close }}</UiButton>
      </div>
    </div>
  </UiModal>
</template>

<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { auditApi, type AuditEntry } from '../../api'
import { copy } from '../../constants/copy'
import DashboardPageTitle from './DashboardPageTitle.vue'
import UiButton from '../ui/UiButton.vue'
import UiModal from '../ui/UiModal.vue'

const props = defineProps<{ open: boolean }>()
defineEmits<{ (e: 'close'): void }>()

const entries = ref<AuditEntry[]>([])
const loading = ref(false)
const error   = ref(false)

async function load() {
  loading.value = true
  error.value   = false
  try {
    entries.value = await auditApi.getAuditLogs({ limit: 100 })
  } catch {
    error.value = true
  } finally {
    loading.value = false
  }
}

/** Neu laden sobald das Modal geöffnet wird. */
watch(() => props.open, (isOpen) => { if (isOpen) load() })
onMounted(() => { if (props.open) load() })

function formatTime(iso: string): string {
  return new Date(iso).toLocaleString('de-CH', {
    day:    '2-digit',
    month:  '2-digit',
    year:   '2-digit',
    hour:   '2-digit',
    minute: '2-digit',
  })
}

function labelAction(action: string): string {
  return copy.audit.actions[action] ?? action
}
</script>

<style scoped>
.audit-modal {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
  min-width: min(92vw, 820px);
}

.audit-state {
  color: var(--color-muted);
  font-size: 0.9rem;
  padding: 1rem 0;
}

.audit-state--error {
  color: var(--color-error, #c0392b);
}

.audit-table-wrap {
  overflow-x: auto;
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border);
}

.audit-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.85rem;
}

.audit-table th,
.audit-table td {
  padding: 0.55rem 0.8rem;
  text-align: left;
  white-space: nowrap;
}

.audit-table th {
  background: var(--color-surface-alt, #f4f7f4);
  color: var(--color-muted);
  font-weight: 600;
  font-size: 0.78rem;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  border-bottom: 1px solid var(--color-border);
}

.audit-table td {
  border-bottom: 1px solid var(--color-border);
}

.audit-table tr:last-child td {
  border-bottom: none;
}

.row--failed {
  background: #fff8f8;
}

.col-time   { color: var(--color-muted); font-variant-numeric: tabular-nums; }
.col-user   { font-weight: 500; }
.col-target { color: var(--color-muted); max-width: 200px; overflow: hidden; text-overflow: ellipsis; }

.badge--ok,
.badge--fail {
  display: inline-block;
  padding: 0.15rem 0.5rem;
  border-radius: 99px;
  font-size: 0.75rem;
  font-weight: 600;
}

.badge--ok   { background: #e6f4e1; color: var(--color-primary-strong); }
.badge--fail { background: #fce8e8; color: #c0392b; }

.audit-footer {
  display: flex;
  justify-content: flex-end;
}
</style>
