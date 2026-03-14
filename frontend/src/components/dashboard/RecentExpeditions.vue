<script setup lang="ts">
import { useRouter } from 'vue-router'
import StatusBadge from '../shared/StatusBadge.vue'
import EmptyState from '../shared/EmptyState.vue'
import type { DashboardStats } from '../../types'
import { formatGameDayShort } from '../../utils/calendar'

const router = useRouter()

defineProps<{
  expeditions: DashboardStats['recent_expeditions']
}>()

function viewSummary(id: number) {
  router.push(`/expedition/${id}/summary`)
}
</script>

<template>
  <div class="card">
    <h3 class="mb-2">Recent Expeditions</h3>
    <table v-if="expeditions.length > 0" class="table">
      <thead>
        <tr>
          <th>Party</th>
          <th>Duration</th>
          <th>Status</th>
          <th>Departs</th>
          <th>Returns</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="exp in expeditions" :key="exp.id" class="clickable-row" @click="viewSummary(exp.id)">
          <td>{{ exp.party_name }}</td>
          <td>{{ exp.duration_days }} days</td>
          <td><StatusBadge :status="exp.result" /></td>
          <td>{{ formatGameDayShort(exp.start_day) }}</td>
          <td>{{ formatGameDayShort(exp.return_day) }}</td>
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
