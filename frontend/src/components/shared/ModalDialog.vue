<script setup lang="ts">
import { onMounted, onUnmounted, watch } from 'vue'

const props = defineProps<{
  isOpen: boolean
  title: string
  width?: string
}>()

const emit = defineEmits<{
  close: []
}>()

function onKeydown(e: KeyboardEvent) {
  if (e.key === 'Escape') {
    emit('close')
  }
}

watch(
  () => props.isOpen,
  (open) => {
    if (open) {
      document.addEventListener('keydown', onKeydown)
    } else {
      document.removeEventListener('keydown', onKeydown)
    }
  },
  { immediate: true }
)

onMounted(() => {
  if (props.isOpen) {
    document.addEventListener('keydown', onKeydown)
  }
})

onUnmounted(() => {
  document.removeEventListener('keydown', onKeydown)
})
</script>

<template>
  <Teleport to="body">
    <div v-if="isOpen" class="modal-overlay" @click.self="emit('close')">
      <div class="modal-content" :style="width ? { maxWidth: width, width: '100%' } : undefined">
        <div class="card-header">
          <slot name="header">
            <h3>{{ title }}</h3>
          </slot>
          <button class="btn btn-secondary btn-sm" @click="emit('close')">✕</button>
        </div>
        <div class="card-body">
          <slot />
        </div>
      </div>
    </div>
  </Teleport>
</template>
