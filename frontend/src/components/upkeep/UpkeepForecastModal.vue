<script setup lang="ts">
import { computed } from 'vue'
import type { UpkeepForecast } from '../../types/upkeep'
import { formatCp } from '../../utils/currency'
import ModalDialog from '../shared/ModalDialog.vue'

const props = defineProps<{
  isOpen: boolean
  forecast: UpkeepForecast | null
}>()

const emit = defineEmits<{
  close: []
  openSheet: [adventurerId: number]
}>()

const headerMeta = computed(() => {
  const f = props.forecast
  if (!f) return ''
  return `Day ${f.next_day} · in ${f.days_until} day${f.days_until === 1 ? '' : 's'}`
})

const totalXp = computed(() =>
  (props.forecast?.rows ?? []).reduce((s, r) => s + r.xp, 0)
)

function fmtXp(xp: number): string {
  return xp.toLocaleString('en-US')
}
</script>

<template>
  <ModalDialog :is-open="isOpen" title="Upkeep Forecast" width="640px" @close="emit('close')">
    <template #header>
      <div class="uf-header">
        <h3 class="uf-title">Upkeep Forecast</h3>
        <span class="uf-meta">{{ headerMeta }}</span>
      </div>
    </template>

    <div v-if="forecast" class="uf-body">
      <!-- Top row: now + collecting = then -->
      <div class="figures-row">
        <div class="figure">
          <span class="figure-label">Treasury now</span>
          <span class="figure-value now">{{ formatCp(forecast.treasury_now_cp) }}</span>
        </div>
        <span class="figure-glyph">+</span>
        <div class="figure">
          <span class="figure-label">Collecting</span>
          <span class="figure-value collecting">{{ formatCp(forecast.total_cp) }}</span>
        </div>
        <span class="figure-glyph">=</span>
        <div class="figure">
          <span class="figure-label">Treasury day {{ forecast.next_day }}</span>
          <span class="figure-value result">{{ formatCp(forecast.treasury_now_cp + forecast.total_cp) }}</span>
        </div>
      </div>

      <!-- Table -->
      <div class="forecast-grid">
        <div class="fcell head left">Adventurer</div>
        <div class="fcell head"></div>
        <div class="fcell head"></div>
        <div class="fcell head"></div>
        <div class="fcell head num">XP</div>
        <div class="fcell head num">Upkeep</div>
        <div class="fcell head num">Purse</div>
        <template v-for="row in forecast.rows" :key="row.id">
          <div class="fcell left">
            <span
              class="adv-link"
              :class="{ short: row.short_cp > 0 }"
              @click="emit('openSheet', row.id)"
            >{{ row.name }}</span>
          </div>
          <div class="fcell left sub">{{ row.adventurer_class }}</div>
          <div class="fcell left sub">Lv {{ row.level }}</div>
          <div class="fcell left">
            <span v-if="row.short_cp > 0" class="short-badge">Short {{ formatCp(row.short_cp) }}</span>
          </div>
          <div class="fcell num xp">{{ fmtXp(row.xp) }}</div>
          <div class="fcell num upkeep" :class="{ 'short-text': row.short_cp > 0 }">{{ formatCp(row.upkeep_cp) }}</div>
          <div class="fcell num purse" :class="{ 'short-text': row.short_cp > 0 }">{{ formatCp(row.purse_cp) }}</div>
        </template>
        <!-- Totals -->
        <div class="fcell left totals">{{ forecast.rows.length }} adventurer{{ forecast.rows.length === 1 ? '' : 's' }}</div>
        <div class="fcell totals"></div>
        <div class="fcell totals"></div>
        <div class="fcell totals"></div>
        <div class="fcell num totals xp">{{ fmtXp(totalXp) }}</div>
        <div class="fcell num totals collected">{{ formatCp(forecast.total_cp) }}</div>
        <div class="fcell totals"></div>
      </div>
    </div>
  </ModalDialog>
</template>

<style scoped>
.uf-header {
  display: flex;
  align-items: baseline;
  gap: 10px;
  min-width: 0;
}

.uf-title {
  font-size: 15px;
  font-weight: 700;
  color: #4ade80;
  margin: 0;
}

.uf-meta {
  font-size: 11px;
  color: #6b7280;
  white-space: nowrap;
}

.uf-body {
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding: 2px 0;
}

/* Figures */
.figures-row {
  display: flex;
  align-items: flex-end;
  gap: 12px;
  padding-bottom: 14px;
  border-bottom: 1px solid #374151;
}

.figure {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.figure-label {
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: #6b7280;
}

.figure-value.now {
  font-size: 20px;
  font-weight: 700;
  color: #e5e7eb;
}

.figure-value.collecting {
  font-size: 20px;
  font-weight: 700;
  color: #4ade80;
}

.figure-value.result {
  font-size: 26px;
  font-weight: 700;
  color: #4ade80;
}

.figure-glyph {
  font-size: 18px;
  color: #6b7280;
  padding-bottom: 2px;
}

/* Table — no column gaps; padding lives inside cells so row rules run unbroken */
.forecast-grid {
  display: grid;
  grid-template-columns: 176px 76px 40px 90px 56px 80px 72px;
}

.fcell {
  display: flex;
  align-items: center;
  padding: 5px 0 5px 8px;
  justify-content: flex-end;
  border-bottom: 1px solid rgba(55, 65, 81, 0.5);
  min-width: 0;
}

.fcell.left {
  padding: 5px 8px 5px 0;
  justify-content: flex-start;
}

.fcell.head {
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: #6b7280;
  padding-bottom: 6px;
  border-bottom: 1px solid #374151;
}

.adv-link {
  font-size: 12px;
  color: #e5e7eb;
  cursor: pointer;
  text-decoration: underline;
  text-decoration-color: #374151;
  text-underline-offset: 2px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.adv-link:hover {
  text-decoration-color: #4ade80;
}

.adv-link.short {
  color: #ef4444;
}

.sub {
  font-size: 10px;
  color: #6b7280;
}

.short-badge {
  font-size: 9.5px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  padding: 1px 6px;
  border-radius: 4px;
  color: #ef4444;
  background: rgba(239, 68, 68, 0.15);
  white-space: nowrap;
}

.xp {
  font-size: 10px;
  color: #60a5fa;
}

.upkeep {
  font-size: 12px;
  color: #4ade80;
}

.purse {
  font-size: 12px;
  color: #6b7280;
}

.short-text {
  color: #ef4444 !important;
}

.totals {
  border-bottom: none;
  padding-top: 7px;
  font-size: 11px;
  color: #6b7280;
}

.totals.collected {
  font-size: 12px;
  font-weight: 700;
  color: #4ade80;
}
</style>
