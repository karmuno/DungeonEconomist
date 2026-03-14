<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(
  defineProps<{
    value: number
    max: number
    color?: string
  }>(),
  {
    color: 'var(--accent-green)',
  }
)

const percentage = computed(() => {
  if (props.max <= 0) return 0
  return Math.min(100, Math.round((props.value / props.max) * 100))
})
</script>

<template>
  <div class="progress-bar">
    <div
      class="progress-fill"
      :style="{ width: percentage + '%', backgroundColor: color }"
    />
    <span class="progress-label">{{ value }} / {{ max }}</span>
  </div>
</template>
