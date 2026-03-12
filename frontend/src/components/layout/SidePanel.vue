<script setup lang="ts">
import { useGameTimeStore } from '../../stores/gameTime'
import { usePlayerStore } from '../../stores/player'

const gameTime = useGameTimeStore()
const player = usePlayerStore()

async function advanceDay() {
  await gameTime.advanceDay()
  await player.fetchPlayer()
}
</script>

<template>
  <aside class="side-panel">
    <div class="panel-section">
      <h3 class="section-label">Game Day</h3>
      <div class="day-value">{{ gameTime.currentDay }}</div>
    </div>

    <div class="panel-section">
      <h3 class="section-label">Treasury</h3>
      <div class="treasury-value">{{ player.treasury }} GP</div>
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
