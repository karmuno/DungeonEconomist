<script setup lang="ts">
import type { AdventurerOut } from '../../types'
import StatusBadge from '../shared/StatusBadge.vue'
import ProgressBar from '../shared/ProgressBar.vue'
import Purse from '../shared/Purse.vue'
import { displayStatus } from '../../utils/adventurer'

defineProps<{
  adventurer: AdventurerOut
  partyName?: string
}>()

const emit = defineEmits<{
  select: [id: number]
}>()
</script>

<template>
  <div class="adventurer-card card" @click="emit('select', adventurer.id)">
    <div class="flex flex-between mb-1">
      <strong>{{ adventurer.name }}</strong>
      <StatusBadge :status="displayStatus(adventurer)" />
    </div>
    <div class="text-muted mb-1">
      {{ adventurer.adventurer_class }} &middot; Level {{ adventurer.level }}
      <template v-if="partyName"> &middot; <span style="color: var(--accent-green)">{{ partyName }}</span></template>
    </div>
    <div class="mb-1">
      <ProgressBar :value="adventurer.hp_current" :max="adventurer.hp_max" />
    </div>
    <div class="flex flex-between text-muted">
      <span>XP: {{ adventurer.xp }}</span>
      <span><Purse :g="adventurer.gold" :s="adventurer.silver" :c="adventurer.copper" /></span>
    </div>
    <div v-if="adventurer.is_bankrupt" class="mt-1 text-muted">
      <strong>Bankrupt</strong>
    </div>
  </div>
</template>
