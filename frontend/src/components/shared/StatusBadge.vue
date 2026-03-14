<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  status: string
}>()

const badgeClass = computed(() => {
  switch (props.status.toLowerCase()) {
    case 'available':
    case 'alive':
    case 'completed':
      return 'badge-success'
    case 'resting':
    case 'recovering':
    case 'on expedition':
    case 'in_progress':
      return 'badge-info'
    case 'injured':
    case 'bankrupt':
    case 'unavailable':
      return 'badge-warning'
    case 'dead':
      return 'badge-danger'
    default:
      return 'badge-info'
  }
})
</script>

<template>
  <span class="badge" :class="badgeClass">{{ status }}</span>
</template>
