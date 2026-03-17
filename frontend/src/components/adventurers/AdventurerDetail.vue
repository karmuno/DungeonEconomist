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
      <span class="adv-id">#{{ adventurer.id }}</span>
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

    <!-- Magic Items -->
    <div v-if="adventurer.magic_items && adventurer.magic_items.length > 0" class="mb-2 mt-2">
      <span class="bar-label">Equipment</span>
      <div class="item-list">
        <div v-for="item in adventurer.magic_items" :key="item.id" class="item-row">
          <span class="item-icon">{{ item.item_type === 'weapon' ? '\u2694' : '\u1F6E1' }}</span>
          <span class="item-name">{{ item.name }}</span>
          <span class="item-bonus">+{{ item.bonus }} {{ item.item_type === 'weapon' ? 'ATK' : 'DEF' }}</span>
        </div>
      </div>
    </div>
    <div v-else class="mb-2 mt-2">
      <span class="bar-label">Equipment</span>
      <div class="text-muted" style="font-size: 12px">No magic items</div>
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

.adv-id {
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--text-muted);
}

.bar-label {
  font-size: 0.75rem;
  font-weight: 600;
}

.item-list {
  margin-top: 4px;
}

.item-row {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 3px 0;
  border-bottom: 1px solid var(--border-color);
  font-size: 12px;
}

.item-icon {
  font-size: 14px;
}

.item-name {
  flex: 1;
  color: #fbbf24;
  font-weight: 600;
}

.item-bonus {
  font-family: var(--font-mono);
  color: var(--accent-green);
  font-size: 11px;
}
</style>
