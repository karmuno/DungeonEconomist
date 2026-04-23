<script setup lang="ts">
import { ref, computed } from 'vue'

const props = defineProps<{
  g: number
  s: number
  c: number
}>()

const tooltipId = `purse-tooltip-${Math.random().toString(36).slice(2)}`
const showTooltip = ref(false)

function normalizeGp(g: number, s: number, c: number): string {
  const totalCp = g * 100 + s * 10 + c
  const gpFloat = totalCp / 100
  if (gpFloat >= 10) return gpFloat.toFixed(0)
  if (gpFloat >= 1) return gpFloat.toFixed(1)
  return gpFloat.toFixed(2)
}

const normalized = computed(() => normalizeGp(props.g, props.s, props.c))
</script>

<template>
  <span
    :aria-describedby="showTooltip ? tooltipId : undefined"
    class="purse-trigger"
    tabindex="0"
    @mouseenter="showTooltip = true"
    @mouseleave="showTooltip = false"
    @focusin="showTooltip = true"
    @focusout="showTooltip = false"
  >
    {{ normalized }}gp
    <div
      v-if="showTooltip"
      :id="tooltipId"
      role="tooltip"
      class="purse-tooltip"
    >
      <div class="purse-eyebrow">Purse</div>
      <div class="purse-value">
        <span class="amount">{{ g }}</span>gp
        <span class="muted">·</span>
        <span class="amount">{{ s }}</span>sp
        <span class="muted">·</span>
        <span class="amount">{{ c }}</span>cp
      </div>
      <div class="purse-arrow" />
    </div>
  </span>
</template>

<style scoped>
.purse-trigger {
  position: relative;
  display: inline-block;
  color: var(--accent-gold, #fbbf24);
  border-bottom: 1px dotted var(--accent-gold, #fbbf24);
  cursor: help;
  outline: none;
}

.purse-trigger:focus {
  outline: 1px dotted var(--accent-gold, #fbbf24);
  outline-offset: 2px;
}

.purse-tooltip {
  position: absolute;
  bottom: calc(100% + 6px);
  right: 0;
  z-index: 20;
  background: #0a0a0a;
  border: 1px solid var(--accent-gold, #fbbf24);
  border-radius: 4px;
  padding: 6px 10px;
  white-space: nowrap;
  font-size: 11px;
  color: var(--text-primary, #f3f4f6);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.6);
}

.purse-eyebrow {
  color: var(--text-muted, #6b7280);
  font-size: 9px;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  margin-bottom: 3px;
}

.purse-value {
  color: var(--accent-gold, #fbbf24);
}

.purse-value .amount {
  color: var(--accent-gold, #fbbf24);
}

.purse-value .muted {
  color: var(--text-muted, #6b7280);
}

.purse-arrow {
  position: absolute;
  bottom: -5px;
  right: 12px;
  width: 8px;
  height: 8px;
  background: #0a0a0a;
  border-right: 1px solid var(--accent-gold, #fbbf24);
  border-bottom: 1px solid var(--accent-gold, #fbbf24);
  transform: rotate(45deg);
}
</style>
