<script setup lang="ts">
import { useRouter } from 'vue-router'
import StatusBadge from '../shared/StatusBadge.vue'
import EmptyState from '../shared/EmptyState.vue'
import type { DashboardStats } from '../../types'
import { formatCurrency } from '../../utils/currency'

const router = useRouter()

defineProps<{
  expeditions: DashboardStats['recent_expeditions']
}>()

function viewSummary(id: number) {
  router.push(`/expedition/${id}/summary`)
}

function statusLabel(result: string): string {
  if (result === 'in_progress') return 'In Progress'
  if (result === 'awaiting_choice') return 'Awaiting Decision'
  return 'Completed'
}
</script>

<template>
  <div class="card">
    <h3 class="mb-2">Recent Expeditions</h3>
    <table v-if="expeditions.length > 0" class="table">
      <thead>
        <tr>
          <th>Party</th>
          <th>Depth</th>
          <th>Loot</th>
          <th>XP</th>
          <th>Status</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="exp in expeditions" :key="exp.id" class="clickable-row" @click="viewSummary(exp.id)">
          <td>{{ exp.party_name }}</td>
          <td>{{ exp.dungeon_level }}</td>
          <td class="text-gold">{{ formatCurrency(exp.treasure_total, exp.treasure_silver ?? 0, exp.treasure_copper ?? 0) }}</td>
          <td>{{ exp.xp_earned }}</td>
          <td><StatusBadge :status="statusLabel(exp.result)" /></td>
        </tr>
      </tbody>
    </table>
    <EmptyState v-else message="No expeditions yet" />
  </div>
</template>

<style scoped>
.clickable-row {
  cursor: pointer;
}
.clickable-row:hover {
  background-color: var(--bg-input);
}
</style>
