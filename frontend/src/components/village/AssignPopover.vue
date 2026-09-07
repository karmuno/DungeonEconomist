<script setup lang="ts">
import type { AdventurerOut } from '../../types'
import { formatCurrency } from '../../utils/currency'

defineProps<{
  className: string
  minLevel: number
  bonusLabel: string
  candidates: AdventurerOut[]
}>()

const emit = defineEmits<{
  pick: [adventurerId: number]
  close: []
}>()

function fmtXp(xp: number): string {
  return xp.toLocaleString('en-US')
}
</script>

<template>
  <div class="assign-popover">
    <div class="pop-header">
      <span class="pop-req">{{ className }} · Lv {{ minLevel }}+</span>
      <span v-if="bonusLabel" class="pop-bonus">{{ bonusLabel }}</span>
      <button class="pop-close" @click.stop="emit('close')">×</button>
    </div>
    <div v-if="candidates.length === 0" class="pop-empty">No eligible adventurers</div>
    <div
      v-for="a in candidates"
      :key="a.id"
      class="pop-row"
      @click.stop="emit('pick', a.id)"
    >
      <span class="pop-name">{{ a.name }}</span>
      <span class="pop-sub">Lv {{ a.level }}</span>
      <span class="pop-hp">{{ a.hp_current }}/{{ a.hp_max }}</span>
      <span class="pop-xp">{{ fmtXp(a.xp) }} XP</span>
      <span class="pop-purse">{{ formatCurrency(a.gold, a.silver, a.copper) }}</span>
      <span class="pop-posting">{{ a.party_name ?? 'Unassigned' }}</span>
    </div>
  </div>
</template>

<style scoped>
.assign-popover {
  position: absolute;
  top: 26px;
  left: 0;
  width: 100%;
  z-index: 5;
  background: #111827;
  border: 1px solid #4b5563;
  border-radius: 6px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.5);
  padding: 6px;
}

.pop-header {
  display: flex;
  align-items: baseline;
  gap: 8px;
  padding: 2px 8px 6px;
  border-bottom: 1px solid #374151;
}

.pop-req {
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: #6b7280;
}

.pop-bonus {
  font-size: 10px;
  color: #4ade80;
}

.pop-close {
  margin-left: auto;
  background: none;
  border: none;
  color: #6b7280;
  font-size: 11px;
  cursor: pointer;
  padding: 0;
}

.pop-close:hover {
  color: #e5e7eb;
}

.pop-empty {
  padding: 8px;
  font-size: 11px;
  color: #6b7280;
}

.pop-row {
  display: grid;
  grid-template-columns: 112px 40px 52px 64px 60px 1fr;
  align-items: center;
  gap: 4px;
  padding: 5px 8px;
  border-radius: 3px;
  cursor: pointer;
}

.pop-row:hover {
  background: rgba(74, 222, 128, 0.06);
}

.pop-name {
  font-size: 12px;
  color: #e5e7eb;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.pop-sub {
  font-size: 10px;
  color: #6b7280;
}

.pop-hp {
  font-size: 10px;
  color: #4ade80;
}

.pop-xp {
  font-size: 10px;
  color: #60a5fa;
}

.pop-purse {
  font-size: 10px;
  color: #fbbf24;
}

.pop-posting {
  font-size: 10px;
  color: #6b7280;
  text-align: right;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
</style>
