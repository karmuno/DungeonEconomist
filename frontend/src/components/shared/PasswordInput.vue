<script setup lang="ts">
import { ref } from 'vue'

// id, placeholder, autocomplete, aria-* and listeners belong on the input, not the wrapper
defineOptions({ inheritAttrs: false })

const model = defineModel<string>({ required: true })
const visible = ref(false)
</script>

<template>
  <div class="password-input">
    <input
      v-bind="$attrs"
      v-model="model"
      class="form-input"
      :type="visible ? 'text' : 'password'"
    />
    <button
      type="button"
      class="password-toggle"
      aria-label="Show password"
      :aria-pressed="visible"
      @click="visible = !visible"
    >
      <svg
        viewBox="0 0 24 24"
        width="18"
        height="18"
        fill="none"
        stroke="currentColor"
        stroke-width="1.75"
        stroke-linecap="round"
        stroke-linejoin="round"
        aria-hidden="true"
      >
        <path d="M2 12s3.6-7 10-7 10 7 10 7-3.6 7-10 7S2 12 2 12z" />
        <circle cx="12" cy="12" r="3" />
        <line v-if="visible" x1="3" y1="3" x2="21" y2="21" />
      </svg>
    </button>
  </div>
</template>

<style scoped>
.password-input {
  position: relative;
}

.password-input .form-input {
  padding-right: 2.5rem;
}

.password-toggle {
  position: absolute;
  top: 50%;
  right: 0.25rem;
  transform: translateY(-50%);
  display: flex;
  padding: 0.35rem;
  color: var(--text-muted);
  background: none;
  border: none;
  border-radius: var(--border-radius);
  cursor: pointer;
}

.password-toggle:hover,
.password-toggle[aria-pressed='true'] {
  color: var(--text-primary);
}

.password-toggle:focus-visible {
  outline: 2px solid var(--accent-green);
  outline-offset: 1px;
}
</style>
