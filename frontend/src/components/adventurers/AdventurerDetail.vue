<script setup lang="ts">
import { computed } from 'vue'
import type { AdventurerOut } from '../../types'
import ProgressBar from '../shared/ProgressBar.vue'
import StatusBadge from '../shared/StatusBadge.vue'
import { formatCurrency } from '../../utils/currency'
import { displayStatus } from '../../utils/adventurer'

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
</script>

<template>
  <div>
    <div class="flex flex-between mb-2">
      <h2>{{ adventurer.name }}</h2>
      <StatusBadge :status="displayStatus(adventurer)" />
    </div>

    <div class="detail-stats mb-2">
      <span><strong>{{ adventurer.adventurer_class }}</strong> Lv.{{ adventurer.level }}</span>
      <span class="text-gold">{{ formatCurrency(adventurer.gold, adventurer.silver, adventurer.copper) }}</span>
    </div>

    <div class="mb-1">
      <span class="bar-label">HP</span>
      <ProgressBar :value="adventurer.hp_current" :max="adventurer.hp_max" />
    </div>

    <div class="mb-1">
      <span class="bar-label">XP: {{ adventurer.xp }}<template v-if="adventurer.next_level_xp != null"> / {{ adventurer.next_level_xp }}</template></span>
      <ProgressBar
        v-if="adventurer.next_level_xp != null"
        :value="adventurer.xp"
        :max="adventurer.next_level_xp!"
        color="var(--accent-blue)"
      />
    </div>

    <div v-if="adventurer.is_dead" class="mb-1 text-danger">
      Died on day {{ adventurer.death_day }}
    </div>

    <div v-if="adventurer.is_bankrupt" class="mb-1 text-danger">
      Sent to debtor's prison on day {{ adventurer.bankruptcy_day }}
    </div>

    <div class="flex gap-1 mt-2">
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

<style scoped>
.detail-stats {
  display: flex;
  justify-content: space-between;
  font-size: 0.9rem;
}

.bar-label {
  font-size: 0.75rem;
  font-weight: 600;
}
</style>
