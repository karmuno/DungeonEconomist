<script setup lang="ts">
import { ref } from 'vue'
import { useGameTimeStore } from '../../stores/gameTime'
import { usePlayerStore } from '../../stores/player'
import { useNotificationsStore, type NotificationType } from '../../stores/notifications'
import type { GameEvent } from '../../types'
import { formatGameDay } from '../../utils/calendar'

const gameTime = useGameTimeStore()
const player = usePlayerStore()
const notifications = useNotificationsStore()

const emit = defineEmits<{
  'day-advanced': []
}>()

const loading = ref(false)

function eventNotificationType(event: GameEvent): NotificationType {
  switch (event.type) {
    case 'death':
      return 'error'
    case 'expedition_complete':
      return 'success'
    case 'healing':
      return 'success'
    case 'upkeep':
      return 'warning'
    case 'recruitment':
    case 'auto_start':
    case 'loot':
    default:
      return 'info'
  }
}

async function advance(days: number) {
  loading.value = true
  try {
    const allEvents: GameEvent[] = []
    for (let i = 0; i < days; i++) {
      const result = await gameTime.advanceDay()
      allEvents.push(...result.events)
    }
    await player.fetchPlayer()

    // Show individual event notifications
    for (const event of allEvents) {
      const opts: Parameters<typeof notifications.add>[1] = {
        type: eventNotificationType(event),
      }
      if (event.type === 'expedition_complete' && event.expedition_id) {
        opts.action = {
          label: 'View Summary',
          route: `/expedition/${event.expedition_id}/summary`,
        }
      }
      notifications.add(event.message, opts)
    }

    emit('day-advanced')
  } catch {
    notifications.add('Failed to advance time', 'error')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="card">
    <h3 class="mb-2">Time Controls</h3>
    <p class="mb-1">Current Day: <strong>{{ gameTime.currentDay }}</strong></p>
    <p class="mb-2 text-muted">{{ formatGameDay(gameTime.currentDay) }}</p>
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
