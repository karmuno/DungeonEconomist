<script setup lang="ts">
import { computed } from 'vue'
import type { AdventurerOut } from '../../types'
import ProgressBar from '../shared/ProgressBar.vue'
import StatusBadge from '../shared/StatusBadge.vue'

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
  if (adv.expedition_status) return adv.expedition_status
  if (adv.on_expedition) return 'on_expedition'
  if (adv.is_bankrupt) return 'Bankrupt'
  if (adv.is_available) return 'available'
  return 'resting'
}

const hasEquipment = computed(() => {
  return props.adventurer.equipment && props.adventurer.equipment.length > 0
})
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
        <div class="stat-value text-gold">{{ adventurer.gold }} GP</div>
        <div class="stat-label">Gold</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ adventurer.carry_capacity }}</div>
        <div class="stat-label">Carry Capacity</div>
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

    <div v-if="hasEquipment" class="mb-3">
      <h3 class="mb-1">Equipment</h3>
      <table class="table">
        <thead>
          <tr>
            <th>Name</th>
            <th>Type</th>
            <th>Qty</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in adventurer.equipment" :key="item.equipment.id">
            <td>{{ item.equipment.name }}</td>
            <td>{{ item.equipment.type }}</td>
            <td>{{ item.quantity }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <div class="mb-2">
      <strong>Status:</strong>
      <span v-if="adventurer.is_available"> Available</span>
      <span v-else-if="adventurer.on_expedition"> On Expedition</span>
      <span v-else> Resting</span>
      <span v-if="adventurer.expedition_status"> ({{ adventurer.expedition_status }})</span>
    </div>

    <div v-if="adventurer.is_bankrupt" class="mb-2">
      <StatusBadge status="Bankrupt" />
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
