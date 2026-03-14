<script setup lang="ts">
import type { DashboardStats } from '../../types'
import { formatCurrency } from '../../utils/currency'

defineProps<{
  stats: DashboardStats
}>()
</script>

<template>
  <div class="dashboard-stats">
    <div class="stat-card">
      <div class="stat-value">{{ stats.adventurer_count }}</div>
      <div class="stat-label">Adventurers</div>
    </div>
    <div class="stat-card">
      <div class="stat-value">{{ stats.party_count }}</div>
      <div class="stat-label">Parties</div>
    </div>
    <div class="stat-card">
      <div class="stat-value">{{ stats.expedition_count }}</div>
      <div class="stat-label">Expeditions</div>
    </div>
    <div class="stat-card">
      <div class="stat-value text-green">{{ formatCurrency(stats.treasury_gold, stats.treasury_silver, stats.treasury_copper) }}</div>
      <div class="stat-label">Treasury</div>
    </div>
    <div class="stat-card">
      <div class="stat-value">{{ stats.total_score }}</div>
      <div class="stat-label">Score</div>
    </div>
  </div>
</template>

<style scoped>
.dashboard-stats {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 0.5rem;
}

.dashboard-stats .stat-card .stat-value {
  white-space: nowrap;
}
</style>
