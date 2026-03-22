import { defineStore } from 'pinia'
import { ref } from 'vue'
import { useAuthStore } from './auth'
import * as gameApi from '../api/game'

export const usePlayerStore = defineStore('player', () => {
  const id = ref<number | null>(null)
  const name = ref('')
  const treasuryGold = ref(0)
  const treasurySilver = ref(0)
  const treasuryCopper = ref(0)
  const totalScore = ref(0)

  function loadFromKeep() {
    const auth = useAuthStore()
    const keep = auth.currentKeep
    if (keep) {
      id.value = keep.id
      name.value = keep.name
      treasuryGold.value = keep.treasury_gold
      treasurySilver.value = keep.treasury_silver
      treasuryCopper.value = keep.treasury_copper
      totalScore.value = keep.total_score
    }
  }

  async function fetchPlayer() {
    // Refresh from server
    try {
      const stats = await gameApi.getDashboardStats()
      treasuryGold.value = stats.treasury_gold
      treasurySilver.value = stats.treasury_silver
      treasuryCopper.value = stats.treasury_copper
      totalScore.value = stats.total_score
    } catch {
      // If the API fails, use cached keep data (already loaded above)
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
    loadFromKeep,
  }
})
