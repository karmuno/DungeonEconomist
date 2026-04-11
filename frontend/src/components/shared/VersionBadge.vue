<script setup lang="ts">
const version = __APP_VERSION__
const isDev = import.meta.env.DEV
</script>

<template>
  <div class="version-badge">
    <span v-if="isDev" class="dev-indicator">DEV</span>
    <span class="version-text">{{ version }}</span>
  </div>
</template>

<style scoped>
.version-badge {
  position: fixed;
  bottom: 6px;
  left: 8px;
  display: flex;
  align-items: center;
  gap: 6px;
  font-family: monospace;
  font-size: 10px;
  color: var(--text-muted, #6b7280);
  opacity: 0.5;
  z-index: 9999;
  user-select: text;
}

.dev-indicator {
  background: var(--accent-gold, #fbbf24);
  color: #000;
  padding: 1px 4px;
  border-radius: 2px;
  font-weight: bold;
  font-size: 9px;
  letter-spacing: 0.5px;
}

.version-text {
  letter-spacing: 0.3px;
}
</style>
