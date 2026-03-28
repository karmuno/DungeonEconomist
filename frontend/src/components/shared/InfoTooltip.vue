<script setup lang="ts">
defineProps<{
  text: string
}>()
</script>

<template>
  <span class="info-tooltip">
    <span class="info-icon">?</span>
    <span class="tooltip-text">{{ text }}</span>
  </span>
</template>

<style scoped>
.info-tooltip {
  position: relative;
  display: inline-flex;
  align-items: center;
  cursor: help;
}

.info-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 14px;
  height: 14px;
  border-radius: 50%;
  border: 1px solid var(--text-muted);
  color: var(--text-muted);
  font-size: 9px;
  font-weight: 700;
  font-family: var(--font-mono);
  line-height: 1;
  flex-shrink: 0;
}

.info-tooltip:hover .info-icon {
  border-color: var(--accent-blue, #60a5fa);
  color: var(--accent-blue, #60a5fa);
}

.tooltip-text {
  visibility: hidden;
  opacity: 0;
  position: absolute;
  bottom: calc(100% + 6px);
  left: 50%;
  transform: translateX(-50%);
  width: max-content;
  max-width: 250px;
  padding: 6px 10px;
  background: var(--bg-primary, #1a1a2e);
  border: 1px solid var(--border-color, #333);
  border-radius: var(--border-radius, 4px);
  color: var(--text-secondary, #ccc);
  font-size: 11px;
  line-height: 1.4;
  font-weight: 400;
  font-family: var(--font-mono);
  z-index: 1000;
  pointer-events: none;
  transition: opacity 0.15s;
  white-space: normal;
}

.info-tooltip:hover .tooltip-text {
  visibility: visible;
  opacity: 1;
}
</style>
