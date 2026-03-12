<script setup lang="ts">
import type { ExpeditionResult } from '../../types'
import StatusBadge from '../shared/StatusBadge.vue'
import EmptyState from '../shared/EmptyState.vue'

defineProps<{
  expeditions: ExpeditionResult[]
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
          <th>Dungeon Lvl</th>
          <th>Turns</th>
          <th>Treasure</th>
          <th>XP</th>
          <th>Status</th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="exp in expeditions"
          :key="exp.expedition_id"
          style="cursor: pointer"
          @click="emit('select', exp.expedition_id)"
        >
          <td>{{ exp.expedition_id }}</td>
          <td>{{ exp.party_id }}</td>
          <td>{{ exp.dungeon_level }}</td>
          <td>{{ exp.turns }}</td>
          <td class="text-gold">{{ exp.treasure_total }} GP</td>
          <td>{{ exp.xp_earned }}</td>
          <td>
            <StatusBadge :status="exp.end_time ? 'Completed' : 'In Progress'" />
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
