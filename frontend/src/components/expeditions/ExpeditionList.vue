<script setup lang="ts">
import type { ExpeditionSummary } from '../../types'
import StatusBadge from '../shared/StatusBadge.vue'
import EmptyState from '../shared/EmptyState.vue'
import { formatGameDayShort } from '../../utils/calendar'

defineProps<{
  expeditions: ExpeditionSummary[]
}>()

const emit = defineEmits<{
  select: [id: number]
}>()
</script>

<template>
  <div>
    <EmptyState v-if="expeditions.length === 0" message="No expeditions to show" />
    <table v-else class="table">
      <thead>
        <tr>
          <th>ID</th>
          <th>Party</th>
          <th>Days</th>
          <th>Departs</th>
          <th>Returns</th>
          <th>Status</th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="exp in expeditions"
          :key="exp.id"
          style="cursor: pointer"
          @click="emit('select', exp.id)"
        >
          <td>{{ exp.id }}</td>
          <td>{{ exp.party_id }}</td>
          <td>{{ exp.duration_days }}</td>
          <td>{{ formatGameDayShort(exp.start_day) }}</td>
          <td>{{ formatGameDayShort(exp.return_day) }}</td>
          <td>
            <StatusBadge :status="exp.result === 'in_progress' ? 'On Expedition' : 'Completed'" />
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
