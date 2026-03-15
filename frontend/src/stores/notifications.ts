import { defineStore } from 'pinia'
import { ref } from 'vue'

export type NotificationType = 'success' | 'error' | 'info' | 'warning'

export interface NotificationAction {
  label: string
  /** Route path or callback */
  route?: string
  callback?: () => void
}

export interface NotificationOptions {
  type?: NotificationType
  /** Action link/button shown in the notification */
  action?: NotificationAction
}

export interface Notification {
  id: number
  text: string
  type: NotificationType
  createdDay: number
  action?: NotificationAction
}

const EXPIRY_DAYS = 7
let nextId = 0

export const useNotificationsStore = defineStore('notifications', () => {
  const messages = ref<Notification[]>([])
  let currentDay = 0

  function add(text: string, opts: NotificationOptions | NotificationType = 'info') {
    const options: NotificationOptions = typeof opts === 'string' ? { type: opts } : opts
    const id = nextId++
    const type = options.type ?? 'info'

    // Deduplicate: don't add if an identical message already exists for this day
    if (messages.value.some((m) => m.text === text && m.createdDay === currentDay)) return
    messages.value.unshift({ id, text, type, createdDay: currentDay, action: options.action })
  }

  function remove(id: number) {
    messages.value = messages.value.filter((m) => m.id !== id)
  }

  /** Call when the game day advances to expire old notifications. */
  function onDayAdvanced(day: number) {
    currentDay = day
    messages.value = messages.value.filter((m) => day - m.createdDay < EXPIRY_DAYS)
  }

  function clear() {
    messages.value = []
  }

  return {
    messages,
    add,
    remove,
    onDayAdvanced,
    clear,
  }
})
