import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { useAuthStore } from './auth'
import * as tutorialApi from '../api/tutorial'

const TUTORIAL_COMPLETE = 7

const TUTORIAL_HINTS: Record<number, string> = {
  0: 'Welcome to Venturekeep! Form your first party to begin your adventure.',
  1: 'Form your first party -- head to the Tavern and recruit adventurers into a party.',
  2: 'Launch an expedition! Select your party and send them into the dungeon.',
  3: 'Your party is delving -- advance days or use Skip to Event to see what happens.',
  4: 'An event! Press On to keep exploring, Retreat to leave safely, or You Decide to let the party choose.',
  5: 'Expedition complete! Check the summary to see your loot and how your party fared.',
  6: 'Your adventurers need rest -- injured adventurers heal over time as you advance days.',
}

export const useTutorialStore = defineStore('tutorial', () => {
  const auth = useAuthStore()
  const minimized = ref(false)
  // Track which step the player dismissed so we don't re-show it
  const dismissedStep = ref<number | null>(null)

  const currentStep = computed(() => auth.account?.tutorial_step ?? TUTORIAL_COMPLETE)
  const isTutorialComplete = computed(() => currentStep.value >= TUTORIAL_COMPLETE)
  const currentHint = computed(() => {
    // Don't show if the player already dismissed this step's popup
    if (dismissedStep.value === currentStep.value) return null
    return TUTORIAL_HINTS[currentStep.value] ?? null
  })

  async function advance(step: number) {
    if (!auth.account || step <= auth.account.tutorial_step) return
    auth.account.tutorial_step = step
    minimized.value = false
    dismissedStep.value = null
    try {
      const updated = await tutorialApi.advanceTutorial(step)
      auth.account.tutorial_step = updated.tutorial_step
    } catch {
      // Optimistic update stays
    }
  }

  function dismiss() {
    // Just hide the current popup; the next step shows when conditions are met
    dismissedStep.value = currentStep.value
  }

  function minimize() {
    minimized.value = true
  }

  function restore() {
    minimized.value = false
  }

  return {
    currentStep,
    isTutorialComplete,
    currentHint,
    minimized,
    advance,
    dismiss,
    minimize,
    restore,
  }
})
