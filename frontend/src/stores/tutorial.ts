import { defineStore } from 'pinia'
import { computed } from 'vue'
import { useAuthStore } from './auth'
import * as tutorialApi from '../api/tutorial'

const TUTORIAL_COMPLETE = 7

export const useTutorialStore = defineStore('tutorial', () => {
  const auth = useAuthStore()

  const currentStep = computed(() => auth.account?.tutorial_step ?? TUTORIAL_COMPLETE)
  const isTutorialComplete = computed(() => currentStep.value >= TUTORIAL_COMPLETE)

  async function advance(step: number) {
    if (!auth.account || step <= auth.account.tutorial_step) return
    // Optimistic update
    auth.account.tutorial_step = step
    try {
      const updated = await tutorialApi.advanceTutorial(step)
      auth.account.tutorial_step = updated.tutorial_step
    } catch {
      // Optimistic update stays — not critical if server fails
    }
  }

  return {
    currentStep,
    isTutorialComplete,
    advance,
  }
})
