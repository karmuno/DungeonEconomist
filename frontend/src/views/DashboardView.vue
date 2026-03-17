<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { getDashboardStats } from '../api/game'
import type { DashboardStats } from '../types'
import { useGameTimeStore } from '../stores/gameTime'
import { formatCurrency } from '../utils/currency'
import { formatGameDayShort } from '../utils/calendar'
import RecentExpeditions from '../components/dashboard/RecentExpeditions.vue'
import LoadingSpinner from '../components/shared/LoadingSpinner.vue'

const router = useRouter()
const gameTime = useGameTimeStore()
const stats = ref<DashboardStats | null>(null)
const loading = ref(true)

async function fetchStats() {
  try {
    stats.value = await getDashboardStats()
  } finally {
    loading.value = false
  }
}

watch(() => gameTime.currentDay, fetchStats)
watch(() => gameTime.expeditionVersion, fetchStats)
onMounted(fetchStats)

function progressPct(exp: DashboardStats['active_expeditions'][0]): number {
  if (exp.duration_days <= 0) return 100
  return Math.min(100, Math.round((exp.days_elapsed / exp.duration_days) * 100))
}
</script>

<template>
  <div>
    <LoadingSpinner v-if="loading" />
    <template v-else-if="stats">
      <!-- Dungeon header -->
      <div class="dungeon-header mb-2" v-if="stats.dungeon_name">
        <h1 class="dungeon-name">{{ stats.dungeon_name }}</h1>
        <span class="dungeon-depth">Depth {{ stats.max_dungeon_level }} reached</span>
      </div>
      <h1 v-else>Dashboard</h1>

      <!-- Hint -->
      <div v-if="stats.hint" class="hint-bar mb-2">
        {{ stats.hint }}
      </div>

      <!-- Stat cards -->
      <div class="stat-row mb-2">
        <div class="stat-card clickable" @click="router.push('/adventurers')">
          <div class="stat-value">{{ stats.adventurer_count }}</div>
          <div class="stat-label">Adventurers</div>
        </div>
        <div class="stat-card clickable" @click="router.push('/parties')">
          <div class="stat-value">{{ stats.party_count }}</div>
          <div class="stat-label">Parties</div>
        </div>
        <div class="stat-card clickable" @click="router.push('/expeditions')">
          <div class="stat-value">{{ stats.expedition_count }}</div>
          <div class="stat-label">Expeditions</div>
        </div>
        <div class="stat-card">
          <div class="stat-value text-green">{{ formatCurrency(stats.treasury_gold, stats.treasury_silver, stats.treasury_copper) }}</div>
          <div class="stat-label">Treasury</div>
        </div>
        <div class="stat-card">
          <div class="stat-value">{{ stats.total_score }}</div>
          <div class="stat-label">Score</div>
        </div>
      </div>

      <!-- Active Expeditions -->
      <div v-if="stats.active_expeditions.length > 0" class="card mb-2">
        <h3 class="mb-1">Active Expeditions</h3>
        <div class="active-list">
          <div
            v-for="exp in stats.active_expeditions"
            :key="exp.id"
            class="active-exp clickable"
            @click="router.push(`/expedition/${exp.id}/summary`)"
          >
            <div class="active-exp-info">
              <span class="active-exp-party">{{ exp.party_name }}</span>
              <span class="active-exp-meta">Depth {{ exp.dungeon_level }}</span>
              <span v-if="exp.result === 'awaiting_choice'" class="badge badge-warning">Decision</span>
            </div>
            <div class="active-exp-progress">
              <div class="progress-track">
                <div class="progress-fill" :style="{ width: progressPct(exp) + '%' }"></div>
              </div>
              <span class="active-exp-days">Day {{ exp.days_elapsed }}/{{ exp.duration_days }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Village summary -->
      <div v-if="stats.buildings.length > 0" class="card mb-2 clickable" @click="router.push('/village')">
        <h3 class="mb-1">Village</h3>
        <div class="buildings-row">
          <div v-for="b in stats.buildings" :key="b.building_type" class="building-chip">
            <span class="building-chip-name">{{ b.name }}</span>
            <span class="building-chip-detail">{{ b.assigned_count }} {{ b.adventurer_class }}{{ b.assigned_count !== 1 ? 's' : '' }}</span>
          </div>
        </div>
      </div>
      <div v-else class="card mb-2 clickable" @click="router.push('/village')">
        <h3 class="mb-1">Village</h3>
        <p class="text-muted" style="font-size: 12px">No buildings yet. Visit the Village to build.</p>
      </div>

      <!-- Recent completed expeditions -->
      <RecentExpeditions :expeditions="stats.recent_expeditions" />
    </template>
  </div>
</template>

<style scoped>
.dungeon-header {
  display: flex;
  align-items: baseline;
  gap: 12px;
}

.dungeon-name {
  font-size: 1.3rem;
}

.dungeon-depth {
  font-family: var(--font-mono);
  font-size: 12px;
  color: var(--text-muted);
}

.hint-bar {
  padding: 8px 12px;
  background: rgba(96, 165, 250, 0.08);
  border: 1px solid rgba(96, 165, 250, 0.2);
  border-radius: var(--border-radius);
  color: var(--accent-blue, #60a5fa);
  font-size: 13px;
}

.stat-row {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 0.5rem;
}

.stat-card {
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius);
  padding: 10px 12px;
  text-align: center;
}

.stat-card.clickable {
  cursor: pointer;
  transition: border-color 0.15s;
}

.stat-card.clickable:hover {
  border-color: var(--accent-green);
}

.stat-value {
  font-family: var(--font-mono);
  font-size: 1.2rem;
  font-weight: 700;
  white-space: nowrap;
}

.stat-label {
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 1px;
  color: var(--text-muted);
  margin-top: 2px;
}

.text-green {
  color: var(--accent-green);
}

/* Active expeditions */
.active-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.active-exp {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 6px 0;
  border-bottom: 1px solid var(--border-color);
}

.active-exp.clickable {
  cursor: pointer;
}

.active-exp-info {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 200px;
}

.active-exp-party {
  font-weight: 600;
  font-size: 13px;
}

.active-exp-meta {
  font-size: 11px;
  color: var(--text-muted);
  font-family: var(--font-mono);
}

.active-exp-progress {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 8px;
}

.progress-track {
  flex: 1;
  height: 6px;
  background: var(--bg-primary);
  border-radius: 3px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: var(--accent-green);
  border-radius: 3px;
  transition: width 0.3s;
}

.active-exp-days {
  font-size: 11px;
  font-family: var(--font-mono);
  color: var(--text-muted);
  white-space: nowrap;
}

/* Village */
.buildings-row {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.building-chip {
  display: flex;
  flex-direction: column;
  padding: 6px 12px;
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius);
}

.building-chip-name {
  font-weight: 600;
  font-size: 12px;
  color: var(--text-primary);
}

.building-chip-detail {
  font-size: 10px;
  color: var(--text-muted);
}

.badge-warning {
  background: rgba(241, 196, 15, 0.15);
  color: #fbbf24;
}
</style>
