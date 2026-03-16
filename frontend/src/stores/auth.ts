import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import * as authApi from '../api/auth'
import * as keepsApi from '../api/keeps'
import type { AccountOut, KeepOut } from '../types'

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(localStorage.getItem('token'))
  const account = ref<AccountOut | null>(null)
  const currentKeep = ref<KeepOut | null>(null)

  const isLoggedIn = computed(() => !!token.value)
  const hasKeep = computed(() => !!currentKeep.value)

  async function login(username: string, password: string) {
    const res = await authApi.login(username, password)
    token.value = res.access_token
    localStorage.setItem('token', res.access_token)
    await fetchAccount()
  }

  async function register(username: string, password: string) {
    const res = await authApi.register(username, password)
    token.value = res.access_token
    localStorage.setItem('token', res.access_token)
    await fetchAccount()
  }

  async function fetchAccount() {
    try {
      account.value = await authApi.getMe()
    } catch {
      logout()
    }
  }

  function selectKeep(keep: KeepOut) {
    currentKeep.value = keep
    localStorage.setItem('keepId', String(keep.id))
  }

  function clearKeep() {
    currentKeep.value = null
    localStorage.removeItem('keepId')
  }

  function logout() {
    token.value = null
    account.value = null
    currentKeep.value = null
    localStorage.removeItem('token')
    localStorage.removeItem('keepId')
  }

  // Try to restore session on store init
  async function tryRestore() {
    if (!token.value) return false
    try {
      await fetchAccount()
      // Restore keep from localStorage if not already set
      const keepId = localStorage.getItem('keepId')
      if (keepId && !currentKeep.value) {
        const keeps = await keepsApi.list()
        const match = keeps.find(k => k.id === Number(keepId))
        if (match) {
          currentKeep.value = match
        } else {
          localStorage.removeItem('keepId')
        }
      }
      return true
    } catch {
      logout()
      return false
    }
  }

  return {
    token,
    account,
    currentKeep,
    isLoggedIn,
    hasKeep,
    login,
    register,
    fetchAccount,
    selectKeep,
    clearKeep,
    logout,
    tryRestore,
  }
})
