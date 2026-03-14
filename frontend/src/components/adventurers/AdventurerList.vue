<script setup lang="ts">
import type { AdventurerOut } from '../../types'
import ProgressBar from '../shared/ProgressBar.vue'
import StatusBadge from '../shared/StatusBadge.vue'
import EmptyState from '../shared/EmptyState.vue'
import { formatCurrency } from '../../utils/currency'

defineProps<{
  adventurers: AdventurerOut[]
  partyNameMap?: Record<number, string>
}>()

const emit = defineEmits<{
  select: [id: number]
}>()

function displayStatus(adv: AdventurerOut): string {
  if (adv.is_dead) return 'Dead'
  if (adv.is_bankrupt) return 'Bankrupt'
  if (adv.on_expedition) return 'On Expedition'
  if (adv.is_available) return 'Available'
  if (adv.hp_current < adv.hp_max) return 'Recovering'
  return 'Unavailable'
}
</script>

<template>
  <table v-if="adventurers.length > 0" class="table">
    <thead>
      <tr>
        <th>Name</th>
        <th>Class</th>
        <th>Level</th>
        <th>Party</th>
        <th>HP</th>
        <th>XP</th>
        <th>Gold</th>
        <th>Status</th>
      </tr>
    </thead>
    <tbody>
      <tr
        v-for="adv in adventurers"
        :key="adv.id"
        style="cursor: pointer"
        @click="emit('select', adv.id)"
      >
        <td>{{ adv.name }}</td>
        <td>{{ adv.adventurer_class }}</td>
        <td>{{ adv.level }}</td>
        <td>{{ partyNameMap?.[adv.id] ?? '—' }}</td>
        <td><ProgressBar :value="adv.hp_current" :max="adv.hp_max" /></td>
        <td>{{ adv.xp }}</td>
        <td class="text-gold">{{ formatCurrency(adv.gold, adv.silver, adv.copper) }}</td>
        <td><StatusBadge :status="displayStatus(adv)" /></td>
      </tr>
    </tbody>
  </table>
  <EmptyState v-else message="No adventurers found" />
</template>
