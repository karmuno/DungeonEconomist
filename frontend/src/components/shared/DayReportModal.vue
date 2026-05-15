<script setup lang="ts">
import { ref, computed, onUnmounted, watch } from 'vue'
import type { DayReport, DayReportTreasury } from '../../types'
import Purse from './Purse.vue'

const props = defineProps<{
  isOpen: boolean
  report: DayReport | null
}>()

const emit = defineEmits<{
  dismiss: []
  advance: []
  skip: []
}>()

const revealedCount = ref(0)
const animationRunning = ref(false)
let revealInterval: number | null = null

const totalEntries = computed(() => {
  if (!props.report) return 0
  return props.report.sections.reduce((sum, section) => sum + section.entries.length, 0)
})

const allEntriesRevealed = computed(
  () => totalEntries.value > 0 && revealedCount.value >= totalEntries.value,
)

const visibleSections = computed(() => {
  if (!props.report) return []
  let idx = 0
  return props.report.sections.map((section) => {
    const visibleEntries = section.entries.filter(() => {
      const isVisible = idx < revealedCount.value
      idx++
      return isVisible
    })
    return { ...section, entries: visibleEntries }
  })
})

function toCp(t: DayReportTreasury): number {
  return t.g * 100 + t.s * 10 + t.c
}

function normalizeCp(cp: number): string {
  const gp = cp / 100
  const abs = Math.abs(gp)
  if (abs >= 10) return gp.toFixed(0)
  if (abs >= 1) return gp.toFixed(1)
  return gp.toFixed(2)
}

const deltaString = computed(() => {
  if (!props.report) return ''
  const delta = toCp(props.report.treasuryAfter) - toCp(props.report.treasuryBefore)
  const sign = delta > 0 ? '+' : delta < 0 ? '−' : ''
  return `${sign}${normalizeCp(Math.abs(delta))}gp`
})

const deltaClass = computed(() => {
  if (!props.report) return ''
  const delta = toCp(props.report.treasuryAfter) - toCp(props.report.treasuryBefore)
  if (delta > 0) return 'delta-positive'
  if (delta < 0) return 'delta-negative'
  return 'delta-zero'
})

function startReveal() {
  stopReveal()
  animationRunning.value = true
  revealedCount.value = 0

  if (totalEntries.value === 0) {
    animationRunning.value = false
    return
  }

  revealInterval = window.setInterval(() => {
    if (revealedCount.value < totalEntries.value) {
      revealedCount.value += 1
    }
    if (revealedCount.value >= totalEntries.value) {
      stopReveal()
    }
  }, 250)
}

function stopReveal() {
  if (revealInterval !== null) {
    clearInterval(revealInterval)
    revealInterval = null
  }
  animationRunning.value = false
}

function skipAnimation() {
  stopReveal()
  revealedCount.value = totalEntries.value
}

function replayAnimation() {
  startReveal()
}

function handleKeydown(e: KeyboardEvent) {
  if (e.key === 'Escape' && props.isOpen) {
    // Explicit action required - Escape does not dismiss
    e.preventDefault()
  }
}

function onDismiss() {
  stopReveal()
  emit('dismiss')
}

function onAdvance() {
  stopReveal()
  emit('advance')
}

function onSkip() {
  stopReveal()
  emit('skip')
}

watch(
  () => [props.isOpen, props.report] as const,
  ([open, report]) => {
    if (open && report) {
      document.addEventListener('keydown', handleKeydown)
      startReveal()
    } else {
      document.removeEventListener('keydown', handleKeydown)
      stopReveal()
    }
  },
  { immediate: true },
)

onUnmounted(() => {
  stopReveal()
  document.removeEventListener('keydown', handleKeydown)
})

function getEntryColor(type: string): string {
  const colors: Record<string, string> = {
    info: 'var(--text-muted, #6b7280)',
    combat: 'var(--accent-red, #ef4444)',
    loot: 'var(--accent-gold, #fbbf24)',
    choice: 'var(--accent-blue, #60a5fa)',
    healing: 'var(--accent-green, #4ade80)',
    upkeep: 'var(--accent-gold, #fbbf24)',
    tavern: 'var(--accent-green, #4ade80)',
  }
  return colors[type] || 'var(--text-muted, #6b7280)'
}
</script>

<template>
  <Teleport to="body">
    <div v-if="isOpen && report" class="day-report-overlay">
      <div class="day-report-modal">
        <!-- Header -->
        <div class="report-header">
          <div>
            <div class="report-eyebrow">Day Report</div>
            <div class="report-title-row">
              <h2 class="report-title">Day {{ report.day }}</h2>
              <span class="calendar-text">{{ report.calendar }}</span>
            </div>
          </div>
          <button class="btn btn-secondary btn-sm" @click="replayAnimation">⟲ Replay</button>
        </div>

        <!-- Body -->
        <div class="report-body">
          <div v-for="(section, sIdx) in visibleSections" :key="`section-${sIdx}`" class="report-section">
            <div class="section-header">
              <h3 :class="{ 'section-expedition': section.kind === 'expedition', 'section-keep': section.kind === 'keep' }">
                {{ section.title }}
              </h3>
              <span v-if="section.subtitle" class="section-subtitle">· {{ section.subtitle }}</span>
            </div>

            <div class="section-entries">
              <div
                v-for="(entry, eIdx) in section.entries"
                :key="`entry-${sIdx}-${eIdx}`"
                class="entry"
                :class="{ 'entry-revealed': true }"
              >
                <div
                  class="entry-dot"
                  :style="{ backgroundColor: getEntryColor(entry.t) }"
                />
                <div class="entry-content">
                  <div class="entry-text">{{ entry.text }}</div>
                  <div
                    v-if="entry.detail"
                    class="entry-detail"
                    :class="{ 'entry-detail-choice': entry.choice }"
                  >
                    {{ entry.detail }}
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Skip animation button (while animating) -->
          <div v-if="animationRunning && !allEntriesRevealed" class="skip-animation-wrap">
            <button class="btn btn-secondary btn-sm" @click="skipAnimation">
              Skip animation
            </button>
          </div>

          <!-- Treasury footer (after all entries revealed) -->
          <div v-if="allEntriesRevealed" class="report-footer">
            <div class="treasury-info">
              <div class="treasury-eyebrow">Treasury</div>
              <div class="treasury-values">
                <span class="treasury-before">
                  <Purse
                    :g="report.treasuryBefore.g"
                    :s="report.treasuryBefore.s"
                    :c="report.treasuryBefore.c"
                  />
                </span>
                <span class="treasury-arrow">→</span>
                <span class="treasury-after">
                  <Purse
                    :g="report.treasuryAfter.g"
                    :s="report.treasuryAfter.s"
                    :c="report.treasuryAfter.c"
                  />
                </span>
                <span class="treasury-delta" :class="deltaClass">{{ deltaString }}</span>
              </div>
            </div>
            <div class="footer-actions">
              <button class="btn btn-secondary btn-sm" @click="onDismiss">Dismiss</button>
              <button class="btn btn-secondary btn-sm" @click="onSkip">Skip to Event</button>
              <button class="btn btn-primary btn-sm" @click="onAdvance">Advance Day ▸</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.day-report-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.75);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
}

.day-report-modal {
  background: var(--bg-card, #1f2937);
  border: 1px solid var(--border-color, #4b5563);
  border-radius: var(--radius, 6px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.5);
  width: 100%;
  max-width: 560px;
  max-height: 90vh;
  margin: 20px;
  display: flex;
  flex-direction: column;
  animation: dayIn 300ms ease-out;
}

@keyframes dayIn {
  from {
    opacity: 0;
    transform: translateY(8px);
  }
  to {
    opacity: 1;
    transform: none;
  }
}

.report-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid var(--border-color, #4b5563);
}

.report-eyebrow {
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: var(--text-muted, #6b7280);
  margin-bottom: 2px;
}

.report-title-row {
  display: flex;
  align-items: baseline;
  gap: 8px;
}

.report-title {
  font-size: 1.4rem;
  color: var(--accent-green, #4ade80);
  margin: 0;
  line-height: 1;
}

.calendar-text {
  font-size: 11px;
  color: var(--text-muted, #6b7280);
}

.report-body {
  padding: 16px;
  overflow-y: auto;
  flex: 1;
}

.report-section {
  margin-bottom: 16px;
}

.report-section .section-header {
  display: flex;
  align-items: baseline;
  gap: 8px;
  margin-bottom: 4px;
  padding-bottom: 4px;
  border-bottom: 1px solid var(--border-color, #4b5563);
}

.report-section h3 {
  font-size: 13px;
  margin: 0;
  font-weight: 700;
}

.section-expedition {
  color: var(--accent-blue, #60a5fa);
}

.section-keep {
  color: var(--accent-green, #4ade80);
}

.section-subtitle {
  font-size: 11px;
  color: var(--text-muted, #6b7280);
}

.section-entries {
  display: flex;
  flex-direction: column;
}

.entry {
  display: flex;
  gap: 10px;
  padding: 6px 0;
  border-bottom: 1px solid var(--border-subtle, #374151);
  animation: entryReveal 300ms ease-out forwards;
  opacity: 0;
  transform: translateY(4px);
}

@keyframes entryReveal {
  to {
    opacity: 1;
    transform: none;
  }
}

.entry-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  margin-top: 6px;
  flex-shrink: 0;
}

.entry-content {
  flex: 1;
}

.entry-text {
  font-size: 12px;
  color: var(--text-primary, #f3f4f6);
}

.entry-detail {
  font-size: 11px;
  color: var(--text-muted, #6b7280);
  margin-top: 2px;
}

.entry-detail-choice {
  color: var(--accent-blue, #60a5fa);
  font-style: italic;
}

.skip-animation-wrap {
  margin-top: 10px;
  text-align: center;
}

.report-footer {
  margin-top: 16px;
  padding: 10px;
  background: var(--bg-secondary, #0f1419);
  border: 1px solid var(--border-color, #4b5563);
  border-radius: var(--radius, 6px);
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  animation: dayIn 300ms ease-out;
}

.treasury-info {
  flex: 1;
  min-width: 0;
}

.treasury-eyebrow {
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--text-muted, #6b7280);
  margin-bottom: 3px;
}

.treasury-values {
  display: flex;
  align-items: baseline;
  gap: 0;
  font-size: 13px;
  flex-wrap: wrap;
}

.treasury-before {
  color: var(--text-muted, #6b7280);
}

.treasury-before :deep(.purse-trigger) {
  color: var(--text-muted, #6b7280);
  border-bottom-color: var(--text-muted, #6b7280);
}

.treasury-arrow {
  color: var(--text-muted, #6b7280);
  margin: 0 6px;
}

.treasury-after {
  font-weight: 700;
}

.treasury-delta {
  font-size: 11px;
  margin-left: 8px;
  font-weight: 600;
}

.delta-positive {
  color: var(--accent-green, #4ade80);
}

.delta-negative {
  color: var(--accent-red, #ef4444);
}

.delta-zero {
  color: var(--text-muted, #6b7280);
}

.footer-actions {
  display: flex;
  gap: 6px;
  flex-shrink: 0;
}
</style>
