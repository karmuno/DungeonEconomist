<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useGameTimeStore } from '../../stores/gameTime'
import { usePlayerStore } from '../../stores/player'
import { useNotificationsStore } from '../../stores/notifications'
import { formatCurrency } from '../../utils/currency'
import { formatGameDay } from '../../utils/calendar'

const router = useRouter()
const gameTime = useGameTimeStore()
const player = usePlayerStore()
const notifications = useNotificationsStore()

function handleAction(notification: (typeof notifications.messages.value)[0]) {
  if (notification.action?.callback) {
    notification.action.callback()
  } else if (notification.action?.route) {
    router.push(notification.action.route)
  }
  notifications.remove(notification.id)
}

const typeMap: Record<string, 'info' | 'success' | 'error' | 'warning'> = {
  recruitment: 'info',
  auto_start: 'info',
  loot: 'info',
  healing: 'success',
  expedition_complete: 'success',
  death: 'error',
  upkeep: 'warning',
}

function processEvents(result: { current_day: number; events: Array<{ type: string; message: string; expedition_id?: number | null }> }) {
  notifications.onDayAdvanced(result.current_day)
  for (const event of result.events) {
    const opts: Parameters<typeof notifications.add>[1] = {
      type: typeMap[event.type] ?? 'info',
    }
    if (event.type === 'expedition_complete' && event.expedition_id) {
      opts.action = {
        label: 'View Summary',
        route: `/expedition/${event.expedition_id}/summary`,
      }
    }
    notifications.add(event.message, opts)
  }
}

const skipping = ref(false)

async function advanceDay() {
  try {
    const result = await gameTime.advanceDay()
    await player.fetchPlayer()
    processEvents(result)
  } catch {
    notifications.add('Failed to advance time', 'error')
  }
}

async function skipToEvent() {
  skipping.value = true
  try {
    const result = await gameTime.skipToEvent()
    await player.fetchPlayer()
    processEvents(result)
  } catch {
    notifications.add('Failed to skip time', 'error')
  } finally {
    skipping.value = false
  }
}
</script>

<template>
  <aside class="side-panel">
    <div class="panel-section">
      <h3 class="section-label">Game Day</h3>
      <div class="day-value">{{ gameTime.currentDay }}</div>
      <div class="day-calendar">{{ formatGameDay(gameTime.currentDay) }}</div>
    </div>

    <div class="panel-section">
      <h3 class="section-label">Treasury</h3>
      <div class="treasury-value">{{ formatCurrency(player.treasuryGold, player.treasurySilver, player.treasuryCopper) }}</div>
    </div>

    <div class="panel-section">
      <h3 class="section-label">Score</h3>
      <div class="score-value">{{ player.totalScore }}</div>
    </div>

    <hr class="divider" />

    <div class="time-controls">
      <button class="advance-btn" @click="advanceDay">Advance Day</button>
      <button class="skip-btn" :disabled="skipping" @click="skipToEvent">
        {{ skipping ? 'Skipping...' : 'Skip to Event' }}
      </button>
    </div>

    <div v-if="notifications.messages.length > 0" class="notif-header">
      <button class="clear-btn" @click="notifications.clear()">Clear</button>
    </div>
    <div v-if="notifications.messages.length > 0" class="notification-feed">
      <div
        v-for="notification in notifications.messages"
        :key="notification.id"
        class="notif"
        :class="notification.type"
      >
        <span class="notif-text">{{ notification.text }}</span>
        <span
          v-if="notification.action"
          class="notif-action"
          @click.stop="handleAction(notification)"
        >
          {{ notification.action.label }}
        </span>
        <button
          class="notif-dismiss"
          @click.stop="notifications.remove(notification.id)"
        >
          &times;
        </button>
      </div>
    </div>
  </aside>
</template>

<style scoped>
.side-panel {
  position: fixed;
  left: 0;
  top: 56px;
  width: 260px;
  height: calc(100vh - 56px);
  background: var(--bg-primary);
  border-right: 1px solid var(--border-color);
  padding: 24px 20px;
  box-sizing: border-box;
  overflow-y: auto;
}

.panel-section {
  margin-bottom: 24px;
}

.section-label {
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 1.5px;
  color: var(--text-muted);
  margin: 0 0 8px;
}

.day-value {
  font-size: 2.5rem;
  font-weight: 700;
  color: var(--text-primary);
  line-height: 1;
}

.day-calendar {
  font-size: 0.75rem;
  color: var(--text-muted);
  margin-top: 4px;
}

.treasury-value {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--accent-green);
}

.score-value {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--text-primary);
}

.divider {
  border: none;
  border-top: 1px solid var(--border-color);
  margin: 24px 0;
}

.time-controls {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.advance-btn {
  width: 100%;
  padding: 10px 16px;
  background: var(--accent-green-dark);
  color: #000;
  border: none;
  border-radius: var(--border-radius);
  font-family: var(--font-mono);
  font-size: 14px;
  font-weight: 700;
  cursor: pointer;
  transition: background-color 0.15s;
}

.advance-btn:hover {
  background: var(--accent-green);
}

.skip-btn {
  width: 100%;
  padding: 8px 16px;
  background: var(--bg-secondary);
  color: var(--text-muted);
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius);
  font-family: var(--font-mono);
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: background-color 0.15s, color 0.15s;
}

.skip-btn:hover:not(:disabled) {
  background: var(--bg-tertiary);
  color: var(--text-primary);
}

.skip-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.notif-header {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}

.clear-btn {
  background: none;
  border: none;
  color: var(--text-muted);
  font-family: var(--font-mono);
  font-size: 11px;
  cursor: pointer;
  padding: 0;
}

.clear-btn:hover {
  color: var(--text-primary);
}

.notification-feed {
  margin-top: 6px;
  max-height: calc(100vh - 380px);
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.notif {
  display: flex;
  align-items: flex-start;
  gap: 6px;
  padding: 6px 8px;
  border-radius: var(--border-radius);
  font-size: 11px;
  line-height: 1.3;
  border: 1px solid transparent;
  background: var(--bg-secondary);
  color: var(--text-muted);
}

.notif.success {
  background-color: #052e16;
  border-color: var(--accent-green-dim);
  color: var(--accent-green);
}

.notif.error {
  background-color: #450a0a;
  border-color: #7f1d1d;
  color: var(--accent-red);
}

.notif.info {
  background-color: #0c1929;
  border-color: #1e3a5f;
  color: var(--accent-blue);
}

.notif.warning {
  background-color: #422006;
  border-color: #78350f;
  color: #fbbf24;
}

.notif-text {
  flex: 1;
  word-break: break-word;
}

.notif-action {
  cursor: pointer;
  text-decoration: underline;
  font-weight: 600;
  white-space: nowrap;
  opacity: 0.9;
}

.notif-action:hover {
  opacity: 1;
}

.notif-dismiss {
  background: none;
  border: none;
  color: inherit;
  cursor: pointer;
  font-size: 14px;
  opacity: 0.6;
  padding: 0;
  line-height: 1;
  flex-shrink: 0;
}

.notif-dismiss:hover {
  opacity: 1;
}
</style>
