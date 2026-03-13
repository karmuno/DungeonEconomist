<script setup lang="ts">
import { useGameTimeStore } from '../../stores/gameTime'
import { usePlayerStore } from '../../stores/player'
import { useNotificationsStore } from '../../stores/notifications'
import { formatCurrency } from '../../utils/currency'
import { formatGameDay } from '../../utils/calendar'

const gameTime = useGameTimeStore()
const player = usePlayerStore()
const notifications = useNotificationsStore()

async function advanceDay() {
  try {
    const result = await gameTime.advanceDay()
    await player.fetchPlayer()
    for (const event of result.events) {
      const typeMap: Record<string, 'info' | 'success' | 'error' | 'warning'> = {
        recruitment: 'info',
        auto_start: 'info',
        loot: 'info',
        healing: 'success',
        expedition_complete: 'success',
        death: 'error',
        upkeep: 'warning',
      }
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
    if (result.events.length === 0) {
      notifications.add('Day advanced — nothing happened', { type: 'info', duration: 3000 })
    }
  } catch {
    notifications.add('Failed to advance time', 'error')
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

    <button class="advance-btn" @click="advanceDay">Advance Day</button>
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
</style>
