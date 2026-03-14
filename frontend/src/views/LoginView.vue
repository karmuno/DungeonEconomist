<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const auth = useAuthStore()

const username = ref('')
const password = ref('')
const error = ref('')
const submitting = ref(false)

async function handleLogin() {
  if (!username.value.trim() || !password.value) return
  error.value = ''
  submitting.value = true
  try {
    await auth.login(username.value.trim(), password.value)
    router.push('/keeps')
  } catch (e: any) {
    const detail = e?.data?.detail ?? e?.message
    error.value = detail || 'Login failed'
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="auth-container">
    <div class="auth-card card">
      <h1 class="mb-2">VentureKeep</h1>
      <p class="text-muted mb-3">Sign in to your account</p>
      <form @submit.prevent="handleLogin">
        <div class="form-group mb-2">
          <label class="form-label">Username</label>
          <input
            v-model="username"
            class="form-input"
            type="text"
            placeholder="Username"
            autofocus
            required
          />
        </div>
        <div class="form-group mb-3">
          <label class="form-label">Password</label>
          <input
            v-model="password"
            class="form-input"
            type="password"
            placeholder="Password"
            required
          />
        </div>
        <p v-if="error" class="error-text mb-2">{{ error }}</p>
        <button
          type="submit"
          class="btn btn-primary"
          :disabled="submitting || !username.trim() || !password"
          style="width: 100%"
        >
          {{ submitting ? 'Signing in...' : 'Sign In' }}
        </button>
      </form>
      <p class="mt-2 text-muted" style="text-align: center">
        No account? <router-link to="/register">Register</router-link>
      </p>
    </div>
  </div>
</template>

<style scoped>
.auth-container {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 60vh;
}

.auth-card {
  max-width: 400px;
  width: 100%;
  text-align: center;
}

.auth-card h1 {
  color: var(--accent-green);
}

.error-text {
  color: var(--accent-red, #e74c3c);
  font-size: 13px;
}
</style>
