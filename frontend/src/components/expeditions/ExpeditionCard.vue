<script setup lang="ts">
import type { ExpeditionResult } from '../../types'
import StatusBadge from '../shared/StatusBadge.vue'

defineProps<{
  expedition: ExpeditionResult
}>()

const emit = defineEmits<{
  select: []
}>()
</script>

<template>
  <div class="expedition-card card" @click="emit('select')" style="cursor: pointer">
    <div class="card-header flex flex-between">
      <h3>Expedition #{{ expedition.expedition_id }}</h3>
      <StatusBadge :status="expedition.end_time ? 'Completed' : 'In Progress'" />
    </div>
    <div class="card-body">
      <p>Party ID: {{ expedition.party_id }}</p>
      <p>Dungeon Level: {{ expedition.dungeon_level }}</p>
      <p>Duration: {{ expedition.duration_days }} days ({{ expedition.turns }} turns)</p>
      <p class="text-gold">Treasure: {{ expedition.treasure_total }} GP</p>
      <p>XP Earned: {{ expedition.xp_earned }}</p>
      <p v-if="expedition.dead_members.length > 0" class="text-danger">
        {{ expedition.dead_members.length }} fallen
      </p>
    </div>
  </div>
</template>
