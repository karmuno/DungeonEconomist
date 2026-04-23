<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import type { DayReport } from '../../types'
import Purse from './Purse.vue'

const props = defineProps<{
  isOpen: boolean
  report: DayReport | null
}>()

const emit = defineEmits<{
  dismiss: []
  advance: []
  close: []
}>()

const revealedCount = ref(0)
const animationRunning = ref(false)
let revealInterval: number | null = null

const totalEntries = computed(() => {
  if (!props.report) return 0
  return props.report.sections.reduce((sum, section) => sum + section.entries.length, 0)
})

const allEntriesRevealed = computed(() => revealedCount.value >= totalEntries.value)

const visibleSections = computed(() => {
  if (!props.report) return []
  return props.report.sections.map((section) => {
    let entryCount = 0
    const visibleEntries = section.entries.filter(() => {
      const isVisible = entryCount < revealedCount.value
      entryCount++
      return isVisible
    })
    return { ...section, entries: visibleEntries }
  })
})

function startReveal() {
  if (animationRunning.value) return
  animationRunning.value = true
  revealedCount.value = 0

  let currentEntry = 0
  revealInterval = window.setInterval(() => {
    if (currentEntry < totalEntries.value) {
      revealedCount.value = currentEntry + 1
      currentEntry++
    } else {
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
  stopReveal()
  startReveal()
}

function handleKeydown(e: KeyboardEvent) {
  if (e.key === 'Escape' && props.isOpen) {
    // Don't close on Escape - explicit action required
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

onMounted(() => {
  if (props.isOpen && props.report) {
    startReveal()
    document.addEventListener('keydown', handleKeydown)
  }
})

onUnmounted(() => {
  stopReveal()
  document.removeEventListener('keydown', handleKeydown)
})

function getEntryColor(type: string): string {
  const colors: Record<string, string> = {
    info: '#6b7280',
    combat: '#ef4444',
    loot: '#fbbf24',
    choice: '#60a5fa',
    healing: '#4ade80',
    upkeep: '#fbbf24',
    tavern: '#4ade80',
  }
  return colors[type] || '#6b7280'
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
            <h2 class="report-title">
              Day {{ report.day }} <span class="calendar-text">{{ report.calendar }}</span>
            </h2>
          </div>
          <button class="btn btn-secondary btn-sm" @click="replayAnimation">⟲ Replay</button>
        </div>

        <!-- Body -->
        <div class="report-body">
          <div v-for="(section, sIdx) in visibleSections" :key="`section-${sIdx}`" class="report-section">
            <h3 :class="{ 'section-expedition': section.kind === 'expedition', 'section-keep': section.kind === 'keep' }">
              {{ section.title }}
              <span v-if="section.subtitle" class="section-subtitle">· {{ section.subtitle }}</span>
            </h3>

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
          <button
            v-if="animationRunning && !allEntriesRevealed"
            class="btn btn-secondary btn-sm skip-animation-btn"
            @click="skipAnimation"
          >
            Skip animation
          </button>

          <!-- Treasury footer (after all entries revealed) -->
          <transition name="fadeIn">
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
                  <span class="treasury-delta">
                    <span class="delta-sign">+</span
                    ><Purse
                      :g="report.treasuryAfter.g - report.treasuryBefore.g"
                      :s="report.treasuryAfter.s - report.treasuryBefore.s"
                      :c="report.treasuryAfter.c - report.treasuryBefore.c"
                    />
                  </span>
                </div>
              </div>
              <div class="footer-actions">
                <button class="btn btn-secondary btn-sm" @click="onDismiss">Dismiss</button>
                <button class="btn btn-primary btn-sm" @click="onAdvance">Advance Day ▸</button>
              </div>
            </div>
          </transition>
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
  max-width: 560px;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  animation: modalIn 300ms ease-out;
}

@keyframes modalIn {
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

.report-title {
  font-size: 1.4rem;
  color: var(--accent-green, #4ade80);
  margin: 0;
}

.calendar-text {
  font-size: 11px;
  color: var(--text-muted, #6b7280);
  margin-left: 6px;
}

.report-body {
  padding: 16px;
  overflow-y: auto;
  flex: 1;
}

.report-section {
  margin-bottom: 16px;
}

.report-section h3 {
  font-size: 1rem;
  margin: 0 0 4px 0;
  padding-bottom: 4px;
  border-bottom: 1px solid var(--border-color, #4b5563);
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

.skip-animation-btn {
  margin-top: 10px;
  width: 100%;
  justify-content: center;
}

.report-footer {
  margin-top: 12px;
  padding: 10px;
  background: var(--bg-secondary, #0f1419);
  border: 1px solid var(--border-color, #4b5563);
  border-radius: var(--radius, 6px);
  display: flex;
  justify-content: space-between;
  align-items: center;
  animation: fadeInFooter 300ms ease-out;
}

@keyframes fadeInFooter {
  from {
    opacity: 0;
    transform: translateY(4px);
  }
  to {
    opacity: 1;
    transform: none;
  }
}

.treasury-info {
  flex: 1;
}

.treasury-eyebrow {
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: var(--text-muted, #6b7280);
  margin-bottom: 3px;
}

.treasury-values {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
}

.treasury-before {
  color: var(--text-muted, #6b7280);
  text-decoration: line-through;
}

.treasury-arrow {
  color: var(--text-muted, #6b7280);
  margin: 0 6px;
}

.treasury-after {
  color: var(--accent-gold, #fbbf24);
  font-weight: 700;
}

.treasury-delta {
  color: var(--accent-green, #4ade80);
  font-size: 11px;
  margin-left: 8px;
}

.delta-sign {
  margin-right: 2px;
}

.footer-actions {
  display: flex;
  gap: 6px;
}

.fadeIn-enter-active,
.fadeIn-leave-active {
  transition: all 300ms ease-out;
}

.fadeIn-enter-from,
.fadeIn-leave-to {
  opacity: 0;
  transform: translateY(4px);
}
</style>
