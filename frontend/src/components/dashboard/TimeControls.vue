<script setup lang="ts">
import { ref } from 'vue'
import { useGameTimeStore } from '../../stores/gameTime'
import { usePlayerStore } from '../../stores/player'
import { useNotificationsStore } from '../../stores/notifications'

const gameTime = useGameTimeStore()
const player = usePlayerStore()
const notifications = useNotificationsStore()

const loading = ref(false)

async function advance(days: number) {
  loading.value = true
  try {
    for (let i = 0; i < days; i++) {
      await gameTime.advanceDay()
    }
    await player.fetchPlayer()
    notifications.add(`Advanced ${days} day${days > 1 ? 's' : ''}`, 'success')
  } catch (err) {
    notifications.add('Failed to advance time', 'error')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="card">
    <h3 class="mb-2">Time Controls</h3>
    <p class="mb-2">Current Day: <strong>{{ gameTime.currentDay }}</strong></p>
    <div class="flex gap-1">
      <button class="btn btn-primary" :disabled="loading" @click="advance(1)">
        Advance Day
      </button>
      <button class="btn btn-primary" :disabled="loading" @click="advance(7)">
        Skip Week
      </button>
      <button class="btn btn-primary" :disabled="loading" @click="advance(30)">
        Skip Month
      </button>
    </div>
  </div>
</template>
