<script setup lang="ts">
import type { ExpeditionSummary } from '../../types'
import StatusBadge from '../shared/StatusBadge.vue'
import EmptyState from '../shared/EmptyState.vue'
import { expeditionEnd, formatGameDayShort } from '../../utils/calendar'

defineProps<{
  expeditions: ExpeditionSummary[]
}>()

const emit = defineEmits<{
  select: [id: number]
}>()

function statusLabel(result: string): string {
  if (result === 'in_progress') return 'In Progress'
  if (result === 'awaiting_choice') return 'Awaiting Decision'
  return 'Completed'
}

// Show what actually happened; an early retreat's plan lives in the tooltip.
function ended(exp: ExpeditionSummary) {
  return expeditionEnd(exp.start_day, exp.return_day, exp.actual_return_day)
}

function plannedTitle(exp: ExpeditionSummary): string | undefined {
  if (!ended(exp).early) return undefined
  return `Planned: ${formatGameDayShort(exp.return_day)} · ${exp.duration_days} days`
}
</script>

<template>
  <div>
    <EmptyState v-if="expeditions.length === 0" message="No expeditions to show" />
    <table v-else class="table">
      <thead>
        <tr>
          <th>Party</th>
          <th>Depth</th>
          <th>Days</th>
          <th>Departs</th>
          <th>Returns</th>
          <th>Loot</th>
          <th>XP</th>
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
          <td>{{ exp.party_name }}</td>
          <td>{{ exp.dungeon_level }}</td>
          <td :title="plannedTitle(exp)">{{ ended(exp).days }}</td>
          <td>{{ formatGameDayShort(exp.start_day) }}</td>
          <td :title="plannedTitle(exp)">{{ formatGameDayShort(ended(exp).day) }}</td>
          <td class="text-gold">{{ exp.treasure_total }}gp</td>
          <td>{{ exp.xp_earned }}</td>
          <td>
            <StatusBadge :status="statusLabel(exp.result)" />
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
