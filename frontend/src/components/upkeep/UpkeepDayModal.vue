<script setup lang="ts">
import { computed } from 'vue'
import type { UpkeepDayData } from '../../types/upkeep'
import { formatCp } from '../../utils/currency'
import ModalDialog from '../shared/ModalDialog.vue'

const props = defineProps<{
  isOpen: boolean
  data: UpkeepDayData | null
  reopened: boolean
}>()

const emit = defineEmits<{
  collect: []
  openSheet: [adventurerId: number]
}>()

const headerMeta = computed(() => {
  const d = props.data
  if (!d) return ''
  return `Day ${d.day} · ${d.adventurer_count} adventurer${d.adventurer_count === 1 ? '' : 's'} · 1cp per XP`
})

const collectedXp = computed(() =>
  (props.data?.rows ?? []).filter(r => r.outcome === 'paid').reduce((s, r) => s + r.xp, 0)
)

function fmtXp(xp: number): string {
  return xp.toLocaleString('en-US')
}
</script>

<template>
  <ModalDialog :is-open="isOpen" title="Upkeep Day" width="760px" @close="emit('collect')">
    <template #header>
      <div class="uk-header">
        <h3 class="uk-title">Upkeep Day</h3>
        <span class="uk-meta">{{ headerMeta }}</span>
      </div>
    </template>

    <div v-if="data" class="uk-body">
      <!-- 1. Outcome row -->
      <div class="outcome-row">
        <span class="outcome-label">Treasury</span>
        <span class="outcome-before">{{ formatCp(data.treasury_before_cp) }}</span>
        <span class="outcome-arrow">→</span>
        <span class="outcome-after">{{ formatCp(data.treasury_after_cp) }}</span>
        <span v-if="data.prison_names.length" class="outcome-prison">
          {{ data.prison_names.length }} to debtor's prison
        </span>
        <button class="collect-btn" @click="emit('collect')">
          {{ reopened ? 'Close' : 'Collect' }}
        </button>
      </div>

      <!-- 2. Ledger -->
      <div v-if="data.rows.length" class="uk-section">
        <div class="ledger-grid">
          <div class="grid-head">Adventurer</div>
          <div class="grid-head num">XP</div>
          <div class="grid-head num">Upkeep</div>
          <div class="grid-head num">Purse</div>
          <div class="grid-head num">After</div>
          <template v-for="row in data.rows" :key="row.id">
            <div class="cell name-cell">
              <span
                class="adv-link"
                :class="{ 'text-prison': row.outcome === 'prison' }"
                @click="emit('openSheet', row.id)"
              >{{ row.name }}</span>
              <span class="cell-sub">{{ row.adventurer_class }} Lv {{ row.level }}</span>
              <span v-if="row.outcome === 'prison'" class="prison-badge">Debtor's Prison</span>
              <span v-else-if="row.outcome === 'sacrificed'" class="sacrificed-badge">Items sacrificed</span>
              <span v-else-if="row.outcome === 'owed'" class="owed-badge">Pays on return</span>
            </div>
            <div class="cell num xp-cell">{{ fmtXp(row.xp) }}</div>
            <div class="cell num upkeep-cell" :class="{ 'text-prison': row.outcome === 'prison' }">
              {{ formatCp(row.upkeep_cp) }}
            </div>
            <div class="cell num purse-cell" :class="{ 'text-prison': row.outcome === 'prison' }">
              {{ formatCp(row.purse_cp) }}
            </div>
            <div class="cell num after-cell" :class="{ 'text-prison': row.outcome === 'prison' }">
              {{ formatCp(row.outcome === 'sacrificed' ? row.purse_cp : row.after_cp) }}
            </div>
          </template>
          <!-- Totals -->
          <div class="cell totals-cell totals-label">Collected</div>
          <div class="cell totals-cell num xp-cell">{{ fmtXp(collectedXp) }}</div>
          <div class="cell totals-cell num collected-cell">{{ formatCp(data.collected_cp) }}</div>
          <div v-if="data.unpaid_cp > 0" class="cell totals-cell num unpaid-cell span-2">
            {{ formatCp(data.unpaid_cp) }} unpaid
          </div>
          <template v-else>
            <div class="cell totals-cell"></div>
            <div class="cell totals-cell"></div>
          </template>
        </div>
      </div>

    </div>
  </ModalDialog>
</template>

<style scoped>
.uk-header {
  display: flex;
  align-items: baseline;
  gap: 10px;
  min-width: 0;
}

.uk-title {
  font-size: 15px;
  font-weight: 700;
  color: #4ade80;
  margin: 0;
}

.uk-meta {
  font-size: 11px;
  color: #6b7280;
  white-space: nowrap;
}

.uk-body {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 2px 0;
}

/* Outcome row */
.outcome-row {
  display: flex;
  align-items: baseline;
  gap: 12px;
  padding-bottom: 14px;
  border-bottom: 1px solid #374151;
}

.outcome-label {
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  color: #6b7280;
}

.outcome-before,
.outcome-arrow {
  font-size: 15px;
  color: #6b7280;
}

.outcome-after {
  font-size: 20px;
  font-weight: 700;
  color: #4ade80;
}

.outcome-prison {
  font-size: 11px;
  color: #ef4444;
}

.outcome-deferred {
  font-size: 11px;
  color: #60a5fa;
}

.collect-btn {
  margin-left: auto;
  padding: 9px 24px;
  background: #22c55e;
  color: #000;
  border: none;
  border-radius: 6px;
  font-family: var(--font-mono);
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
  transition: background-color 0.12s;
}

.collect-btn:hover {
  background: #4ade80;
}

/* Sections */
.section-label {
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  color: #6b7280;
  margin-bottom: 4px;
}

.label-sub {
  text-transform: none;
  letter-spacing: normal;
}

.ledger-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 72px 104px 104px 104px;
  gap: 0 8px;
}

.deferred-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 72px 104px 180px;
  gap: 0 8px;
}

.grid-head {
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: #6b7280;
  padding-bottom: 6px;
  border-bottom: 1px solid #374151;
}

.grid-head.num {
  text-align: right;
}

.cell {
  display: flex;
  align-items: center;
  padding: 6px 0;
  border-bottom: 1px solid rgba(55, 65, 81, 0.5);
  min-width: 0;
}

.cell.num {
  justify-content: flex-end;
  white-space: nowrap;
}

.name-cell {
  gap: 6px;
}

.adv-link {
  font-size: 13px;
  color: #e5e7eb;
  cursor: pointer;
  text-decoration: underline;
  text-decoration-color: #374151;
  text-underline-offset: 2px;
}

.adv-link:hover {
  text-decoration-color: #4ade80;
}

.cell-sub {
  font-size: 10px;
  color: #6b7280;
}

.prison-badge {
  font-size: 9.5px;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  padding: 1px 6px;
  border-radius: 4px;
  color: #ef4444;
  background: rgba(239, 68, 68, 0.15);
  white-space: nowrap;
}

.owed-badge {
  font-size: 9.5px;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  padding: 1px 6px;
  border-radius: 4px;
  color: #60a5fa;
  background: rgba(96, 165, 250, 0.15);
}

.sacrificed-badge {
  font-size: 9.5px;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  padding: 1px 6px;
  border-radius: 4px;
  color: #fbbf24;
  background: rgba(251, 191, 36, 0.15);
  white-space: nowrap;
}

.xp-cell {
  font-size: 12px;
  color: #60a5fa;
}

.upkeep-cell {
  font-size: 13px;
  color: #4ade80;
}

.purse-cell {
  font-size: 12px;
  color: #6b7280;
}

.after-cell {
  font-size: 12px;
  color: #fbbf24;
}

.deferred-cell {
  font-size: 13px;
  color: #60a5fa;
}

.due-cell {
  font-size: 11px;
  color: #6b7280;
}

.text-prison {
  color: #ef4444 !important;
}

.totals-cell {
  border-bottom: none;
  padding-top: 7px;
}

.totals-label {
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: #6b7280;
}

.collected-cell {
  font-size: 13px;
  font-weight: 700;
  color: #4ade80;
}

.unpaid-cell {
  font-size: 11px;
  color: #ef4444;
  grid-column: span 2;
}
</style>
