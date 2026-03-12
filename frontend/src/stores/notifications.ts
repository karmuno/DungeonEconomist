import { defineStore } from 'pinia'
import { ref } from 'vue'

export interface Notification {
  id: number
  text: string
  type: 'success' | 'error' | 'info'
}

let nextId = 0

export const useNotificationsStore = defineStore('notifications', () => {
  const messages = ref<Notification[]>([])

  function add(text: string, type: Notification['type'] = 'info') {
    const id = nextId++
    messages.value.push({ id, text, type })
    setTimeout(() => remove(id), 4000)
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
