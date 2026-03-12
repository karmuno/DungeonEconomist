<script setup lang="ts">
import type { AdventurerOut } from '../../types'
import ProgressBar from '../shared/ProgressBar.vue'
import StatusBadge from '../shared/StatusBadge.vue'
import EmptyState from '../shared/EmptyState.vue'

defineProps<{
  adventurers: AdventurerOut[]
}>()

const emit = defineEmits<{
  select: [id: number]
}>()

function displayStatus(adv: AdventurerOut): string {
  if (adv.expedition_status) return adv.expedition_status
  if (adv.on_expedition) return 'on_expedition'
  if (adv.is_bankrupt) return 'Bankrupt'
  if (adv.is_available) return 'available'
  return 'resting'
}
</script>

<template>
  <table v-if="adventurers.length > 0" class="table">
    <thead>
      <tr>
        <th>Name</th>
        <th>Class</th>
        <th>Level</th>
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
        <td><ProgressBar :value="adv.hp_current" :max="adv.hp_max" /></td>
        <td>{{ adv.xp }}</td>
        <td class="text-gold">{{ adv.gold }} GP</td>
        <td><StatusBadge :status="displayStatus(adv)" /></td>
      </tr>
    </tbody>
  </table>
  <EmptyState v-else message="No adventurers found" />
</template>
