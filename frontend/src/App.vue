<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useGameTimeStore } from './stores/gameTime'
import { usePlayerStore } from './stores/player'
import AppHeader from './components/layout/AppHeader.vue'
import SidePanel from './components/layout/SidePanel.vue'

const route = useRoute()
const gameTime = useGameTimeStore()
const player = usePlayerStore()

const isNewGame = computed(() => route.name === 'new-game')

onMounted(async () => {
  try {
    await gameTime.fetchTime()
    await player.fetchPlayer()
  } catch {
    // Game doesn't exist yet — nav guard will redirect to /new-game
  }
})
</script>

<template>
  <template v-if="isNewGame">
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
  </template>

</template>
