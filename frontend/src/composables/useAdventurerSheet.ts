import { ref } from 'vue'
import type { AdventurerOut } from '../types'
import * as adventurersApi from '../api/adventurers'

// Shared singleton state — any component can open the sheet
const showSheet = ref(false)
const sheetAdventurer = ref<AdventurerOut | null>(null)
const sheetLoading = ref(false)

export function useAdventurerSheet() {
  async function openByName(name: string) {
    sheetLoading.value = true
    showSheet.value = true
    sheetAdventurer.value = null
    try {
      sheetAdventurer.value = await adventurersApi.getByName(name)
    } catch {
      showSheet.value = false
    } finally {
      sheetLoading.value = false
    }
  }

  async function openById(id: number) {
    sheetLoading.value = true
    showSheet.value = true
    sheetAdventurer.value = null
    try {
      sheetAdventurer.value = await adventurersApi.getById(id)
    } catch {
      showSheet.value = false
    } finally {
      sheetLoading.value = false
    }
  }

  function closeSheet() {
    showSheet.value = false
    sheetAdventurer.value = null
  }

  async function levelUp() {
    if (!sheetAdventurer.value) return
    try {
      await adventurersApi.levelUp(sheetAdventurer.value.id)
      // Re-fetch to get updated stats
      sheetAdventurer.value = await adventurersApi.getById(sheetAdventurer.value.id)
    } catch {
      // handled by caller
    }
  }

  return {
    showSheet,
    sheetAdventurer,
    sheetLoading,
    openByName,
    openById,
    closeSheet,
    levelUp,
  }
}
