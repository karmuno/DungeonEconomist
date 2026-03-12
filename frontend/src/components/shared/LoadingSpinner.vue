<script setup lang="ts">
withDefaults(
  defineProps<{
    message?: string
  }>(),
  {
    message: 'Loading...',
  }
)
</script>

<template>
  <div class="loading-spinner">
    <span class="spinner-message">{{ message }}</span>
  </div>
</template>
