<script setup lang="ts">
import { ref, onUnmounted } from 'vue'

const props = withDefaults(
  defineProps<{
    label: string
    confirmLabel?: string
    variant?: string
  }>(),
  {
    confirmLabel: 'Confirm?',
    variant: 'primary',
  }
)

const emit = defineEmits<{
  confirm: []
}>()

const confirming = ref(false)
let timeout: ReturnType<typeof setTimeout> | null = null

function handleClick() {
  if (confirming.value) {
    confirming.value = false
    if (timeout) clearTimeout(timeout)
    emit('confirm')
  } else {
    confirming.value = true
    timeout = setTimeout(() => {
      confirming.value = false
    }, 3000)
  }
}

onUnmounted(() => {
  if (timeout) clearTimeout(timeout)
})
</script>

<template>
  <button
    class="btn"
    :class="confirming ? 'btn-danger' : `btn-${variant}`"
    @click="handleClick"
  >
    {{ confirming ? confirmLabel : label }}
  </button>
</template>
