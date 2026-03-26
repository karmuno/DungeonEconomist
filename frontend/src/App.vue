<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from './stores/auth'
import { useGameTimeStore } from './stores/gameTime'
import { usePlayerStore } from './stores/player'
import AppHeader from './components/layout/AppHeader.vue'
import SidePanel from './components/layout/SidePanel.vue'
import AdminConsole from './components/layout/AdminConsole.vue'
import MetricsPanel from './components/layout/MetricsPanel.vue'

const route = useRoute()
const auth = useAuthStore()
const gameTime = useGameTimeStore()
const player = usePlayerStore()

const isAuthPage = computed(() =>
  ['login', 'register', 'keeps'].includes(route.name as string)
)

onMounted(async () => {
  const restored = await auth.tryRestore()
  if (restored && auth.currentKeep) {
    // Load from cached keep data immediately (no API call)
    player.loadFromKeep()
    gameTime.currentDay = auth.currentKeep.current_day
    // Then refresh from server
    try {
      await gameTime.fetchTime()
      await player.fetchPlayer()
    } catch {
      // API failed — cached data from keep is still showing
    }
  }
})
</script>

<template>
  <template v-if="isAuthPage">
    <div class="main-content" style="margin-left: 0">
      <router-view />
    </div>
  </template>
  <template v-else>
    <AppHeader />
    <div class="app-layout">
      <SidePanel />
      <div class="main-content">
        <router-view />
      </div>
    </div>
    <AdminConsole />
    <MetricsPanel />
  </template>
</template>
