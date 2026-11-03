<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import PasswordInput from '../components/shared/PasswordInput.vue'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const auth = useAuthStore()

const username = ref('')
const password = ref('')
const confirmPassword = ref('')
const confirmTouched = ref(false)
const error = ref('')
const submitting = ref(false)

// Mirrors _PASSWORD_RE in app/routes/auth.py
const passwordValid = computed(() => /^(?=.*[A-Za-z])(?=.*\d).{8,}$/.test(password.value))
const passwordsMatch = computed(() => confirmPassword.value === password.value)
// While the confirmation is still a correct start of the password, wait for the field to lose focus
const showMismatch = computed(
  () =>
    confirmPassword.value !== '' &&
    !passwordsMatch.value &&
    (confirmTouched.value || !password.value.startsWith(confirmPassword.value)),
)
const canSubmit = computed(
  () =>
    !submitting.value &&
    username.value.trim() !== '' &&
    passwordValid.value &&
    confirmPassword.value !== '' &&
    passwordsMatch.value,
)

async function handleRegister() {
  if (!canSubmit.value) return
  error.value = ''
  submitting.value = true
  try {
    await auth.register(username.value.trim(), password.value)
    router.push('/keeps')
  } catch (e: any) {
    const detail = e?.data?.detail ?? e?.message
    error.value = detail || 'Registration failed'
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="auth-container">
    <div class="auth-card card">
      <h1 class="mb-2">VentureKeep</h1>
      <p class="text-muted mb-3">Create an account</p>
      <form @submit.prevent="handleRegister">
        <div class="form-group mb-2">
          <label class="form-label" for="register-username">Username</label>
          <input
            id="register-username"
            v-model="username"
            class="form-input"
            type="text"
            placeholder="Choose a username"
            autocomplete="username"
            autofocus
            required
          />
        </div>
        <div class="form-group mb-2">
          <label class="form-label" for="register-password">Password</label>
          <PasswordInput
            id="register-password"
            v-model="password"
            placeholder="Choose a password"
            autocomplete="new-password"
            aria-describedby="register-password-rule"
            required
          />
          <p id="register-password-rule" class="field-hint" :class="{ 'is-ok': passwordValid }">
            Password must contain 8 characters or more, with at least 1 letter and 1 number.
          </p>
        </div>
        <div class="form-group mb-3">
          <label class="form-label" for="register-confirm">Confirm password</label>
          <PasswordInput
            id="register-confirm"
            v-model="confirmPassword"
            placeholder="Confirm password"
            autocomplete="new-password"
            :aria-invalid="showMismatch || undefined"
            :aria-describedby="showMismatch ? 'register-confirm-error' : undefined"
            required
            @blur="confirmTouched = true"
          />
          <p v-if="showMismatch" id="register-confirm-error" class="field-hint is-error" role="alert">
            Passwords don't match
          </p>
        </div>
        <p v-if="error" class="error-text mb-2">{{ error }}</p>
        <button
          type="submit"
          class="btn btn-primary"
          :disabled="!canSubmit"
          style="width: 100%"
        >
          {{ submitting ? 'Creating...' : 'Create Account' }}
        </button>
      </form>
      <p class="mt-2 text-muted" style="text-align: center">
        Already have an account? <router-link to="/login">Sign in</router-link>
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

.field-hint {
  margin-top: 0.25rem;
  font-size: 12px;
  color: var(--text-muted);
}

.field-hint.is-ok {
  color: var(--accent-green);
}

.field-hint.is-error {
  color: var(--accent-red, #e74c3c);
}
</style>
