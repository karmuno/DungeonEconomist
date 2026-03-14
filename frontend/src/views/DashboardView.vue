<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { getDashboardStats } from '../api/game'
import type { DashboardStats } from '../types'
import { useGameTimeStore } from '../stores/gameTime'
import DashboardStatsComponent from '../components/dashboard/DashboardStats.vue'
import RecentExpeditions from '../components/dashboard/RecentExpeditions.vue'
import LoadingSpinner from '../components/shared/LoadingSpinner.vue'

const gameTime = useGameTimeStore()
const stats = ref<DashboardStats | null>(null)
const loading = ref(true)

async function fetchStats() {
  try {
    stats.value = await getDashboardStats()
  } finally {
    loading.value = false
  }
}

watch(() => gameTime.currentDay, fetchStats)
onMounted(fetchStats)
</script>

<template>
  <div>
    <h1 class="mb-2">Dashboard</h1>
    <LoadingSpinner v-if="loading" />
    <template v-else-if="stats">
      <DashboardStatsComponent :stats="stats" class="mb-2" />
      <RecentExpeditions :expeditions="stats.recent_expeditions" />
    </template>
  </div>
</template>
