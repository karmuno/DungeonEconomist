<script setup lang="ts">
import { computed } from 'vue'
import type { AdventurerOut } from '../../types'
import ProgressBar from '../shared/ProgressBar.vue'
import StatusBadge from '../shared/StatusBadge.vue'
import { formatCurrency } from '../../utils/currency'

const props = defineProps<{
  adventurer: AdventurerOut
}>()

const emit = defineEmits<{
  close: []
  levelUp: []
}>()

const canLevelUp = computed(() => {
  const adv = props.adventurer
  if (adv.xp_progress != null && adv.xp_progress >= 100) return true
  if (adv.next_level_xp != null && adv.xp >= adv.next_level_xp) return true
  return false
})

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
  <div>
    <div class="flex flex-between mb-2">
      <h2>{{ adventurer.name }}</h2>
      <StatusBadge :status="displayStatus(adventurer)" />
    </div>

    <div class="stats-grid mb-3">
      <div class="stat-card">
        <div class="stat-value">{{ adventurer.adventurer_class }}</div>
        <div class="stat-label">Class</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ adventurer.level }}</div>
        <div class="stat-label">Level</div>
      </div>
      <div class="stat-card">
        <div class="stat-value text-gold">{{ formatCurrency(adventurer.gold, adventurer.silver, adventurer.copper) }}</div>
        <div class="stat-label">Wealth</div>
      </div>
    </div>

    <div class="mb-2">
      <strong>HP</strong>
      <ProgressBar :value="adventurer.hp_current" :max="adventurer.hp_max" />
    </div>

    <div class="mb-2">
      <strong>XP: {{ adventurer.xp }}</strong>
      <template v-if="adventurer.next_level_xp != null">
        / {{ adventurer.next_level_xp }}
      </template>
      <ProgressBar
        v-if="adventurer.next_level_xp != null"
        :value="adventurer.xp"
        :max="adventurer.next_level_xp!"
        color="var(--accent-blue)"
      />
    </div>

    <div v-if="adventurer.is_dead" class="mb-2 text-danger">
      Died on day {{ adventurer.death_day }}
    </div>

    <div v-if="adventurer.is_bankrupt" class="mb-2 text-danger">
      Sent to debtor's prison on day {{ adventurer.bankruptcy_day }}
    </div>

    <div class="flex gap-1 mt-3">
      <button
        v-if="canLevelUp"
        class="btn btn-primary"
        @click="emit('levelUp')"
      >
        Level Up
      </button>
      <button class="btn" @click="emit('close')">Close</button>
    </div>
  </div>
</template>
