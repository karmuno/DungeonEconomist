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
  /** Auto-dismiss after ms. Set to 0 to keep until manually dismissed. Default: 7000 */
  duration?: number
  /** Action link/button shown in the notification */
  action?: NotificationAction
}

export interface Notification {
  id: number
  text: string
  type: NotificationType
  duration: number
  action?: NotificationAction
}

let nextId = 0

export const useNotificationsStore = defineStore('notifications', () => {
  const messages = ref<Notification[]>([])

  function add(text: string, opts: NotificationOptions | NotificationType = 'info') {
    const options: NotificationOptions = typeof opts === 'string' ? { type: opts } : opts
    const id = nextId++
    const type = options.type ?? 'info'
    const duration = options.duration ?? 7000

    messages.value.push({ id, text, type, duration, action: options.action })

    if (duration > 0) {
      setTimeout(() => remove(id), duration)
    }
  }

  function remove(id: number) {
    messages.value = messages.value.filter((m) => m.id !== id)
  }

  return {
    messages,
    add,
    remove,
  }
})
