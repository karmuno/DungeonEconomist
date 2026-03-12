<script setup lang="ts">
import type { AdventurerOut } from '../../types'
import StatusBadge from '../shared/StatusBadge.vue'
import ProgressBar from '../shared/ProgressBar.vue'

const props = defineProps<{
  adventurer: AdventurerOut
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
  <div class="adventurer-card card" @click="emit('select', adventurer.id)">
    <div class="flex flex-between mb-1">
      <strong>{{ adventurer.name }}</strong>
      <StatusBadge :status="displayStatus(adventurer)" />
    </div>
    <div class="text-muted mb-1">{{ adventurer.adventurer_class }} &middot; Level {{ adventurer.level }}</div>
    <div class="mb-1">
      <ProgressBar :value="adventurer.hp_current" :max="adventurer.hp_max" />
    </div>
    <div class="flex flex-between text-muted">
      <span>XP: {{ adventurer.xp }}</span>
      <span class="text-gold">{{ adventurer.gold }} GP</span>
    </div>
    <div v-if="adventurer.is_bankrupt" class="mt-1 text-muted">
      <strong>Bankrupt</strong>
    </div>
  </div>
</template>
