import { defineStore } from 'pinia'
import { ref } from 'vue'
import * as gameApi from '../api/game'

export const useGameTimeStore = defineStore('gameTime', () => {
  const currentDay = ref(0)
  const dayStartedAt = ref<string | null>(null)
  const lastUpdated = ref<string | null>(null)

  async function fetchTime() {
    const data = await gameApi.getTime()
    currentDay.value = data.current_day
    dayStartedAt.value = data.day_started_at
    lastUpdated.value = data.last_updated
  }

  async function advanceDay() {
    const data = await gameApi.advanceDay()
    currentDay.value = data.current_day
    dayStartedAt.value = data.day_started_at
    lastUpdated.value = data.last_updated
  }

  return {
    currentDay,
    dayStartedAt,
    lastUpdated,
    fetchTime,
    advanceDay,
  }
})
