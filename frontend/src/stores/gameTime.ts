import { defineStore } from 'pinia'
import { ref } from 'vue'
import * as gameApi from '../api/game'
import type { AdvanceDayResult } from '../types'

export const useGameTimeStore = defineStore('gameTime', () => {
  const currentDay = ref(0)
  const dayStartedAt = ref<string | null>(null)
  const lastUpdated = ref<string | null>(null)
  // Increments when expedition state changes (choice made, etc.)
  const expeditionVersion = ref(0)

  async function fetchTime() {
    const data = await gameApi.getTime()
    currentDay.value = data.current_day
    dayStartedAt.value = data.day_started_at
    lastUpdated.value = data.last_updated
  }

  async function advanceDay(): Promise<AdvanceDayResult> {
    const data = await gameApi.advanceDay()
    currentDay.value = data.current_day
    dayStartedAt.value = data.day_started_at
    lastUpdated.value = data.last_updated
    expeditionVersion.value++
    return data
  }

  async function skipToEvent(): Promise<AdvanceDayResult> {
    const oldDay = currentDay.value
    const data = await gameApi.skipToEvent()
    dayStartedAt.value = data.day_started_at
    lastUpdated.value = data.last_updated
    expeditionVersion.value++

    // Animate the day counter ticking up
    const newDay = data.current_day
    const gap = newDay - oldDay
    if (gap > 1) {
      const delay = Math.min(80, 400 / gap) // faster tick for bigger jumps
      for (let d = oldDay + 1; d <= newDay; d++) {
        currentDay.value = d
        await new Promise(r => setTimeout(r, delay))
      }
    } else {
      currentDay.value = newDay
    }

    return data
  }

  return {
    currentDay,
    dayStartedAt,
    lastUpdated,
    expeditionVersion,
    fetchTime,
    advanceDay,
    skipToEvent,
  }
})
