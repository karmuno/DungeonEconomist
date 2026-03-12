import { defineStore } from 'pinia'
import { ref } from 'vue'
import * as playersApi from '../api/players'

export const usePlayerStore = defineStore('player', () => {
  const id = ref<number | null>(null)
  const name = ref('')
  const treasury = ref(0)
  const totalScore = ref(0)

  async function fetchPlayer() {
    const players = await playersApi.list()
    if (players.length > 0) {
      const player = players[0]
      id.value = player.id
      name.value = player.name
      treasury.value = player.treasury
      totalScore.value = player.total_score
    }
  }

  return {
    id,
    name,
    treasury,
    totalScore,
    fetchPlayer,
  }
})
