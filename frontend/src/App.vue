<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useGameTimeStore } from './stores/gameTime'
import { usePlayerStore } from './stores/player'
import { useNotificationsStore } from './stores/notifications'
import AppHeader from './components/layout/AppHeader.vue'
import SidePanel from './components/layout/SidePanel.vue'

const router = useRouter()
const route = useRoute()
const gameTime = useGameTimeStore()
const player = usePlayerStore()
const notifications = useNotificationsStore()

const isNewGame = computed(() => route.name === 'new-game')

function handleAction(notification: (typeof notifications.messages.value)[0]) {
  if (notification.action?.callback) {
    notification.action.callback()
  } else if (notification.action?.route) {
    router.push(notification.action.route)
  }
  notifications.remove(notification.id)
}

onMounted(() => {
  gameTime.fetchTime()
  player.fetchPlayer()
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

  <div class="toast-container">
    <div
      v-for="notification in notifications.messages"
      :key="notification.id"
      class="toast"
      :class="notification.type"
    >
      <span class="toast-text">{{ notification.text }}</span>
      <span
        v-if="notification.action"
        class="toast-action"
        @click.stop="handleAction(notification)"
      >
        {{ notification.action.label }}
      </span>
      <button
        class="toast-dismiss"
        @click.stop="notifications.remove(notification.id)"
      >
        &times;
      </button>
    </div>
  </div>
</template>
