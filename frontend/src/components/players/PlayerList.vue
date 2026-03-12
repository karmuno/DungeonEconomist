<script setup lang="ts">
import type { PlayerOut } from '../../types'
import EmptyState from '../shared/EmptyState.vue'

defineProps<{
  players: PlayerOut[]
}>()
</script>

<template>
  <div>
    <EmptyState v-if="players.length === 0" message="No players yet" />
    <table v-else class="table">
      <thead>
        <tr>
          <th>ID</th>
          <th>Name</th>
          <th>Treasury (GP)</th>
          <th>Total Score</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="player in players" :key="player.id">
          <td>{{ player.id }}</td>
          <td>{{ player.name }}</td>
          <td class="text-gold">{{ player.treasury }}</td>
          <td>{{ player.total_score }}</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
