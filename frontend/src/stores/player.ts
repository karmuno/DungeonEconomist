import { defineStore } from 'pinia'
import { ref } from 'vue'
import * as playersApi from '../api/players'

export const usePlayerStore = defineStore('player', () => {
  const id = ref<number | null>(null)
  const name = ref('')
  const treasuryGold = ref(0)
  const treasurySilver = ref(0)
  const treasuryCopper = ref(0)
  const totalScore = ref(0)

  async function fetchPlayer() {
    const players = await playersApi.list()
    if (players.length > 0) {
      const player = players[0]
      id.value = player.id
      name.value = player.name
      treasuryGold.value = player.treasury_gold
      treasurySilver.value = player.treasury_silver
      treasuryCopper.value = player.treasury_copper
      totalScore.value = player.total_score
    }
  }

  return {
    id,
    name,
    treasuryGold,
    treasurySilver,
    treasuryCopper,
    totalScore,
    fetchPlayer,
  }
})
