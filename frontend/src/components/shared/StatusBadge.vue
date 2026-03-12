<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  status: string
}>()

const badgeClass = computed(() => {
  switch (props.status) {
    case 'available':
    case 'alive':
    case 'completed':
      return 'badge-success'
    case 'resting':
    case 'in_progress':
      return 'badge-info'
    case 'injured':
    case 'Bankrupt':
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
