<template>
  <UiModal :open="open" @close="$emit('close')" style="--layout-modal-max: 1040px">
    <div class="al">

      <!-- Header -->
      <div class="al-header">
        <div>
          <span class="al-eyebrow">{{ copy.audit.eyebrow }}</span>
          <h2 class="al-title">{{ copy.audit.title }}</h2>
        </div>
        <div class="al-header-right">
          <span v-if="!loading && !error" class="al-count">{{ filtered.length }} / {{ entries.length }}</span>
          <UiButton variant="light" slim @click="$emit('close')">{{ copy.audit.close }}</UiButton>
        </div>
      </div>

      <!-- Filter -->
      <div class="al-filters">
        <button
          v-for="f in FILTERS" :key="f.key"
          class="al-chip" :class="{ active: activeFilter === f.key }"
          @click="activeFilter = f.key"
        >
          {{ f.label }}
          <span class="al-chip-n">{{ countFor(f.key) }}</span>
        </button>
      </div>

      <!-- States -->
      <div v-if="loading" class="al-state">
        <span class="al-spinner" />{{ copy.audit.loading }}
      </div>
      <div v-else-if="error" class="al-state al-state--err">{{ copy.audit.loadError }}</div>
      <div v-else-if="filtered.length === 0" class="al-state">{{ copy.audit.empty }}</div>

      <!-- Tabelle -->
      <div v-else class="al-table-wrap">
        <table class="al-table">
          <thead>
            <tr>
              <th>{{ copy.audit.colTime }}</th>
              <th>{{ copy.audit.colUser }}</th>
              <th>{{ copy.audit.colAction }}</th>
              <th>{{ copy.audit.colTarget }}</th>
              <th class="th-center">{{ copy.audit.colStatus }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="e in filtered" :key="e.id" :class="{ 'row-fail': !e.success }">
              <td class="td-time">
                <span>{{ fmtDate(e.timestamp) }}</span>
                <span class="muted">{{ fmtClock(e.timestamp) }}</span>
              </td>
              <td><span class="user-pill">{{ e.username }}</span></td>
              <td><span class="action-chip" :class="chipClass(e.action)">{{ labelAction(e.action) }}</span></td>
              <td class="td-target">{{ e.target ?? '–' }}</td>
              <td class="th-center">
                <span :class="e.success ? 'badge-ok' : 'badge-fail'">
                  {{ e.success ? copy.audit.ok : copy.audit.failed }}
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

    </div>
  </UiModal>
</template>

<script setup lang="ts">
import { computed, ref, watch, onMounted } from 'vue'
import { auditApi, type AuditEntry } from '../../api'
import { copy } from '../../constants/copy'
import UiModal from '../ui/UiModal.vue'
import UiButton from '../ui/UiButton.vue'

const props = defineProps<{ open: boolean }>()
defineEmits<{ (e: 'close'): void }>()

const entries      = ref<AuditEntry[]>([])
const loading      = ref(false)
const error        = ref(false)
const activeFilter = ref('all')

const FILTERS = [
  { key: 'all',             label: 'Alle' },
  { key: 'internet_toggle', label: 'Internet' },
  { key: 'whitelist',       label: 'Whitelist' },
  { key: 'login',           label: 'Login' },
  { key: 'failed',          label: 'Fehler' },
]

function countFor(key: string) {
  if (key === 'all')       return entries.value.length
  if (key === 'failed')    return entries.value.filter(e => !e.success).length
  if (key === 'whitelist') return entries.value.filter(e => e.action.startsWith('whitelist')).length
  if (key === 'login')     return entries.value.filter(e => e.action.startsWith('login')).length
  return entries.value.filter(e => e.action === key).length
}

const filtered = computed(() => {
  const k = activeFilter.value
  if (k === 'all')       return entries.value
  if (k === 'failed')    return entries.value.filter(e => !e.success)
  if (k === 'whitelist') return entries.value.filter(e => e.action.startsWith('whitelist'))
  if (k === 'login')     return entries.value.filter(e => e.action.startsWith('login'))
  return entries.value.filter(e => e.action === k)
})

async function load() {
  loading.value = true; error.value = false
  try { entries.value = await auditApi.getAuditLogs({ limit: 100 }) }
  catch { error.value = true }
  finally { loading.value = false }
}

watch(() => props.open, open => { if (open) load() })
onMounted(() => { if (props.open) load() })

const fmtDate  = (s: string) => new Date(s).toLocaleDateString('de-CH',  { day: '2-digit', month: '2-digit', year: '2-digit' })
const fmtClock = (s: string) => new Date(s).toLocaleTimeString('de-CH',  { hour: '2-digit', minute: '2-digit' })
const labelAction = (a: string) => copy.audit.actions[a] ?? a

function chipClass(a: string) {
  if (a.startsWith('login'))    return 'chip-login'
  if (a === 'internet_toggle')  return 'chip-internet'
  if (a === 'whitelist_create') return 'chip-create'
  if (a === 'whitelist_delete') return 'chip-delete'
  if (a === 'whitelist_update') return 'chip-update'
  if (a === 'whitelist_toggle') return 'chip-toggle'
  return 'chip-default'
}
</script>

<style scoped>
.al { display: flex; flex-direction: column; gap: 1rem; }

/* Header */
.al-header { display: flex; align-items: flex-start; justify-content: space-between; gap: 1rem; padding-bottom: 0.75rem; border-bottom: 1px solid var(--color-border); }
.al-header-right { display: flex; align-items: center; gap: 0.75rem; flex-shrink: 0; }
.al-eyebrow { display: block; font-size: 0.7rem; font-weight: 700; letter-spacing: 0.07em; text-transform: uppercase; color: var(--color-primary-strong); margin-bottom: 0.15rem; }
.al-title   { margin: 0; font-size: 1.2rem; font-weight: 700; color: var(--color-text); }
.al-count   { font-size: 0.78rem; color: var(--color-muted); background: var(--color-surface-muted); border: 1px solid var(--color-border); border-radius: var(--radius-pill); padding: 0.18rem 0.6rem; }

/* Filters */
.al-filters { display: flex; flex-wrap: wrap; gap: 0.35rem; }
.al-chip    { display: inline-flex; align-items: center; gap: 0.3rem; padding: 0.28rem 0.7rem; border: 1px solid var(--color-border); border-radius: var(--radius-pill); background: var(--color-surface); color: var(--color-muted); font-size: 0.78rem; font-weight: 500; cursor: pointer; transition: border-color 0.12s, background 0.12s, color 0.12s; }
.al-chip:hover,
.al-chip.active { background: var(--color-primary); border-color: var(--color-primary); color: #fff; }
.al-chip-n  { min-width: 1.1rem; text-align: center; font-size: 0.67rem; font-weight: 700; background: rgba(0,0,0,0.1); border-radius: var(--radius-pill); padding: 0 0.25rem; }

/* States */
.al-state      { display: flex; align-items: center; gap: 0.6rem; color: var(--color-muted); font-size: 0.88rem; padding: 2.5rem 0; justify-content: center; }
.al-state--err { color: var(--color-error-text); }
.al-spinner    { width: 22px; height: 22px; border: 2.5px solid var(--color-border); border-top-color: var(--color-primary); border-radius: 50%; animation: spin 0.7s linear infinite; flex-shrink: 0; }
@keyframes spin { to { transform: rotate(360deg); } }

/* Table */
.al-table-wrap { overflow-x: auto; border: 1px solid var(--color-border); border-radius: var(--radius-md); }
.al-table      { width: 100%; border-collapse: collapse; font-size: 0.85rem; }
.al-table th   { padding: 0.55rem 1rem; text-align: left; background: var(--color-surface-muted); border-bottom: 1px solid var(--color-border); color: var(--color-muted); font-size: 0.7rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; white-space: nowrap; }
.al-table td   { padding: 0.65rem 1rem; border-bottom: 1px solid var(--color-border); vertical-align: middle; }
.al-table tr:last-child td { border-bottom: none; }
.al-table tr:hover td { background: var(--color-surface-muted); }

.row-fail td { background: #fffafa; }
.row-fail:hover td { background: #fff3f3; }

.th-center { text-align: center; }
.muted { color: var(--color-muted); font-size: 0.75rem; }
.td-time   { display: flex; flex-direction: column; gap: 0.05rem; white-space: nowrap; font-variant-numeric: tabular-nums; font-size: 0.82rem; }
.td-target { color: var(--color-muted); font-size: 0.82rem; max-width: 220px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

/* Pills / Chips */
.user-pill    { display: inline-block; padding: 0.15rem 0.5rem; background: var(--color-code-bg); border-radius: var(--radius-pill); color: var(--color-primary-strong); font-size: 0.78rem; font-weight: 600; }
.action-chip  { display: inline-block; padding: 0.18rem 0.55rem; border-radius: var(--radius-pill); font-size: 0.76rem; font-weight: 600; white-space: nowrap; }
.chip-login   { background: #e8f0fe; color: #3b55c9; }
.chip-internet{ background: #e7f7e3; color: var(--color-primary-strong); }
.chip-create  { background: #e7f7e3; color: #2a7c1e; }
.chip-update  { background: #fff8e1; color: #a06a00; }
.chip-delete  { background: #fce8e8; color: #c0392b; }
.chip-toggle  { background: #f0eafc; color: #6b3fa0; }
.chip-default { background: var(--color-code-bg); color: var(--color-muted); }

.badge-ok, .badge-fail { display: inline-block; padding: 0.15rem 0.55rem; border-radius: var(--radius-pill); font-size: 0.73rem; font-weight: 700; }
.badge-ok   { background: #e7f7e3; color: var(--color-primary-strong); }
.badge-fail { background: #fce8e8; color: #c0392b; }
</style>
