<script setup lang="ts">
import { onMounted } from 'vue'
import { useGameTimeStore } from './stores/gameTime'
import { usePlayerStore } from './stores/player'
import { useNotificationsStore } from './stores/notifications'
import AppHeader from './components/layout/AppHeader.vue'
import SidePanel from './components/layout/SidePanel.vue'

const gameTime = useGameTimeStore()
const player = usePlayerStore()
const notifications = useNotificationsStore()

onMounted(() => {
  gameTime.fetchTime()
  player.fetchPlayer()
})
</script>

<template>
  <AppHeader />
  <div class="app-layout">
    <SidePanel />
    <div class="main-content">
      <router-view />
    </div>
  </div>

  <div class="toast-container">
    <div
      v-for="notification in notifications.messages"
      :key="notification.id"
      class="toast"
      :class="notification.type"
      @click="notifications.remove(notification.id)"
    >
      {{ notification.text }}
    </div>
  </div>
</template>
