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
    localStorage.setItem('refreshToken', res.refresh_token)
    await fetchAccount()
  }

  async function register(username: string, password: string) {
    const res = await authApi.register(username, password)
    token.value = res.access_token
    localStorage.setItem('token', res.access_token)
    localStorage.setItem('refreshToken', res.refresh_token)
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

  async function changePassword(currentPassword: string, newPassword: string) {
    const res = await authApi.changePassword(currentPassword, newPassword)
    // Replace tokens so this session stays alive
    token.value = res.access_token
    localStorage.setItem('token', res.access_token)
    localStorage.setItem('refreshToken', res.refresh_token)
  }

  // Forget the session locally. The server is not told; logout() does that.
  function clearSession() {
    token.value = null
    account.value = null
    currentKeep.value = null
    localStorage.removeItem('token')
    localStorage.removeItem('refreshToken')
    localStorage.removeItem('keepId')
  }

  async function logout() {
    try {
      await authApi.logout()
    } catch {
      // Best-effort server-side revocation
    }
    clearSession()
  }

  // One restore per page load, shared by the router guard and App.vue: the
  // first caller does the work, later callers await the same promise.
  let _restore: Promise<boolean> | null = null

  function ensureSession(): Promise<boolean> {
    if (!token.value) return Promise.resolve(false)
    if (account.value) return Promise.resolve(true)
    if (!_restore) {
      _restore = tryRestore().finally(() => {
        _restore = null
      })
    }
    return _restore
  }

  // Validate the stored token against the server and load the account and
  // keep. False means the session is gone and storage has been cleared.
  async function tryRestore() {
    if (!token.value) return false
    try {
      account.value = await authApi.getMe()
    } catch {
      clearSession()
      return false
    }
    // Restore keep separately — don't logout if this fails
    const keepId = localStorage.getItem('keepId')
    if (keepId && !currentKeep.value) {
      try {
        const keeps = await keepsApi.list()
        const match = keeps.find(k => k.id === Number(keepId))
        if (match) {
          currentKeep.value = match
        } else {
          localStorage.removeItem('keepId')
        }
      } catch {
        // Keep restore failed but account is fine — user can re-select
      }
    }
    return true
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
    changePassword,
    clearSession,
    logout,
    ensureSession,
    tryRestore,
  }
})
