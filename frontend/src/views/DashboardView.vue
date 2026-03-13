<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { getDashboardStats } from '../api/game'
import type { DashboardStats } from '../types'
import DashboardStatsComponent from '../components/dashboard/DashboardStats.vue'
import TimeControls from '../components/dashboard/TimeControls.vue'
import RecentExpeditions from '../components/dashboard/RecentExpeditions.vue'
import LoadingSpinner from '../components/shared/LoadingSpinner.vue'

const stats = ref<DashboardStats | null>(null)
const loading = ref(true)

async function fetchStats() {
  try {
    stats.value = await getDashboardStats()
  } finally {
    loading.value = false
  }
}

onMounted(fetchStats)
</script>

<template>
  <div>
    <h1 class="mb-3">Dashboard</h1>
    <LoadingSpinner v-if="loading" />
    <template v-else-if="stats">
      <DashboardStatsComponent :stats="stats" class="mb-3" />
      <TimeControls class="mb-3" @day-advanced="fetchStats" />
      <RecentExpeditions :expeditions="stats.recent_expeditions" />
    </template>
  </div>
</template>
