<script setup lang="ts">
import type { ExpeditionResult } from '../../types'
import ExpeditionLog from './ExpeditionLog.vue'

defineProps<{
  expedition: ExpeditionResult
}>()

defineEmits<{
  close: []
}>()
</script>

<template>
  <div>
    <div class="stats-grid mb-3">
      <div class="stat-card">
        <span class="text-muted">Expedition ID</span>
        <strong>{{ expedition.expedition_id }}</strong>
      </div>
      <div class="stat-card">
        <span class="text-muted">Party ID</span>
        <strong>{{ expedition.party_id }}</strong>
      </div>
      <div class="stat-card">
        <span class="text-muted">Dungeon Level</span>
        <strong>{{ expedition.dungeon_level }}</strong>
      </div>
      <div class="stat-card">
        <span class="text-muted">Duration</span>
        <strong>{{ expedition.duration_days }} days ({{ expedition.turns }} turns)</strong>
      </div>
      <div class="stat-card">
        <span class="text-muted">Status</span>
        <strong>{{ expedition.end_time ? 'Completed' : 'In Progress' }}</strong>
      </div>
    </div>

    <h4 class="mb-1">Loot</h4>
    <p class="text-gold mb-1">Treasure: {{ expedition.treasure_total }} GP</p>
    <div v-if="expedition.special_items.length > 0" class="mb-2">
      <span v-for="(item, i) in expedition.special_items" :key="i" class="badge">{{ item }}</span>
    </div>
    <p v-else class="text-muted mb-2">No special items</p>

    <h4 class="mb-1">Experience</h4>
    <p class="mb-1">Total XP: {{ expedition.xp_earned }}</p>
    <p class="mb-2 text-muted">Per member: {{ expedition.xp_per_party_member }}</p>

    <div v-if="expedition.dead_members.length > 0" class="mb-2">
      <h4 class="text-danger mb-1">Casualties</h4>
      <p v-for="(name, i) in expedition.dead_members" :key="i" class="text-danger">{{ name }}</p>
    </div>

    <div v-if="expedition.supplies_consumed" class="mb-2">
      <h4 class="mb-1">Supplies Consumed</h4>
      <p v-for="(qty, name) in expedition.supplies_consumed" :key="String(name)">
        {{ name }}: {{ qty }}
      </p>
    </div>

    <div v-if="expedition.equipment_lost" class="mb-2">
      <h4 class="mb-1">Equipment Lost</h4>
      <p v-for="(ids, name) in expedition.equipment_lost" :key="String(name)">
        {{ name }}: {{ Array.isArray(ids) ? ids.length : ids }} items
      </p>
    </div>

    <ExpeditionLog :log="expedition.log" />
  </div>
</template>
