<script setup lang="ts">
import { ref, nextTick } from 'vue'

defineProps<{
  text: string
}>()

const iconRef = ref<HTMLElement | null>(null)
const tooltipRef = ref<HTMLElement | null>(null)
const visible = ref(false)

async function show() {
  visible.value = true
  await nextTick()
  positionTooltip()
}

function hide() {
  visible.value = false
}

function positionTooltip() {
  if (!iconRef.value || !tooltipRef.value) return
  const rect = iconRef.value.getBoundingClientRect()
  const tt = tooltipRef.value

  // Position above the icon, centered
  let left = rect.left + rect.width / 2
  const top = rect.top - 6

  // Measure the tooltip to clamp it within the viewport
  const ttRect = tt.getBoundingClientRect()
  const halfWidth = ttRect.width / 2
  const margin = 8

  // Clamp so left/right edges don't spill off screen
  if (left - halfWidth < margin) {
    left = halfWidth + margin
  } else if (left + halfWidth > window.innerWidth - margin) {
    left = window.innerWidth - halfWidth - margin
  }

  tt.style.left = `${left}px`
  tt.style.top = `${top}px`
}
</script>

<template>
  <span class="info-tooltip" @mouseenter="show" @mouseleave="hide">
    <span ref="iconRef" class="info-icon">?</span>
    <Teleport to="body">
      <span
        v-if="visible"
        ref="tooltipRef"
        class="info-tooltip-text"
      >{{ text }}</span>
    </Teleport>
  </span>
</template>

<style scoped>
.info-tooltip {
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
</style>

<style>
.info-tooltip-text {
  position: fixed;
  transform: translate(-50%, -100%);
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
  z-index: 99999;
  pointer-events: none;
  white-space: normal;
}
</style>
