import { defineStore } from 'pinia'
import { ref } from 'vue'

// The feedback modal is mounted once in App.vue; the entry control lives in the
// sidebar (and on the auth pages), so open state and the session counter are shared here.
export const useFeedbackStore = defineStore('feedback', () => {
  const isOpen = ref(false)
  const sentThisSession = ref(0)
  let trigger: HTMLElement | null = null

  function open(from?: HTMLElement | null) {
    trigger = from ?? null
    isOpen.value = true
  }

  function close() {
    isOpen.value = false
    // Focus goes back to the control that opened the modal.
    trigger?.focus()
    trigger = null
  }

  return { isOpen, sentThisSession, open, close }
})
