<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import * as expeditionsApi from '../api/expeditions'
import type { ExpeditionSummaryDetail } from '../api/expeditions'
import { useNotificationsStore } from '../stores/notifications'
import { useGameTimeStore } from '../stores/gameTime'
import { formatCurrency } from '../utils/currency'
import { formatGameDayShort } from '../utils/calendar'
import ProgressBar from '../components/shared/ProgressBar.vue'
import LoadingSpinner from '../components/shared/LoadingSpinner.vue'

const router = useRouter()
const route = useRoute()
const notifications = useNotificationsStore()
const gameTime = useGameTimeStore()

const summary = ref<ExpeditionSummaryDetail | null>(null)
const loading = ref(true)

async function fetchSummary() {
  const id = Number(route.params.id)
  summary.value = await expeditionsApi.getSummary(id)
}

watch(() => gameTime.currentDay, () => {
  fetchSummary()
})

onMounted(async () => {
  try {
    await fetchSummary()
  } catch {
    notifications.add('Failed to load expedition summary', 'error')
    router.push('/')
  } finally {
    loading.value = false
  }
})

function lootCopper(total: number): { gold: number; silver: number; copper: number } {
  const copper_total = total * 100
  return {
    gold: Math.floor(copper_total / 100),
    silver: Math.floor((copper_total % 100) / 10),
    copper: copper_total % 10,
  }
}

interface TurnLog {
  turn: number
  events: Array<{
    type: string
    combat?: { outcome: string; monster_type: string; hp_lost: number; xp_earned: number }
    treasure?: { gold: number; xp_value: number }
    trap_damage?: number
  }>
}

const turnsWithEvents = computed(() => {
  if (!summary.value) return []
  return (summary.value.events_log as TurnLog[]).filter(
    (turn) => turn.events && turn.events.length > 0
  )
})

function outcomeClass(outcome: string): string {
  if (outcome === 'Clear Victory' || outcome === 'Victory') return 'badge-success'
  if (outcome === 'Tough Fight') return 'badge-warning'
  return 'badge-danger'
}
</script>

<template>
  <div>
    <h1>Expedition Summary</h1>

    <LoadingSpinner v-if="loading" />
    <template v-else-if="summary">
      <div class="card mb-3">
        <div class="flex flex-between mb-2">
          <h2>{{ summary.party_name }}</h2>
          <span class="badge">{{ summary.result }}</span>
        </div>
        <p class="text-muted mb-2">
          {{ formatGameDayShort(summary.start_day) }} &mdash; {{ formatGameDayShort(summary.return_day) }}
          ({{ summary.duration_days }} days)
        </p>
        <div class="summary-stats">
          <span class="text-gold">Loot: {{ formatCurrency(lootCopper(summary.total_loot).gold, lootCopper(summary.total_loot).silver, lootCopper(summary.total_loot).copper) }}</span>
          <span>XP: {{ summary.total_xp }}</span>
          <span class="text-muted">Ready by: {{ formatGameDayShort(summary.estimated_readiness_day) }}</span>
        </div>
      </div>

      <!-- Party Member Results -->
      <div class="card mb-3">
        <h3 class="mb-2">Party Members</h3>
        <table class="table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Class</th>
              <th>Level</th>
              <th>Status</th>
              <th>HP</th>
              <th>XP Gained</th>
              <th>Wealth</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="member in summary.member_results"
              :key="member.name"
              :class="{ 'text-danger': !member.alive }"
            >
              <td>{{ member.name }}</td>
              <td>{{ member.adventurer_class }}</td>
              <td>{{ member.level }}</td>
              <td>
                <span v-if="member.alive" class="badge badge-alive">Alive</span>
                <span v-else class="badge badge-dead">Dead</span>
              </td>
              <td>
                <ProgressBar
                  v-if="member.alive"
                  :value="member.hp_current"
                  :max="member.hp_max"
                />
                <span v-else>&mdash;</span>
              </td>
              <td>+{{ member.xp_gained }}</td>
              <td class="text-gold">{{ formatCurrency(member.gold, member.silver, member.copper) }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Events Log -->
      <div v-if="turnsWithEvents.length > 0" class="card mb-3">
        <h3 class="mb-2">Expedition Log</h3>
        <div class="events-log">
          <div v-for="turn in turnsWithEvents" :key="turn.turn" class="turn-entry">
            <div class="turn-header">Turn {{ turn.turn }}</div>
            <div v-for="(event, idx) in turn.events" :key="idx" class="event-entry">
              <template v-if="event.type === 'Monster'">
                <span>Encountered <strong>{{ event.combat?.monster_type }}</strong></span>
                <span :class="['badge', outcomeClass(event.combat?.outcome ?? '')]">
                  {{ event.combat?.outcome }}
                </span>
                <span class="text-muted">{{ event.combat?.hp_lost }} HP lost, +{{ event.combat?.xp_earned }} XP</span>
                <span v-if="event.treasure" class="text-gold">
                  Loot: {{ event.treasure.gold }}gp
                </span>
              </template>
              <template v-else-if="event.type === 'Trap'">
                <span class="badge badge-warning">Trap</span>
                <span>{{ event.trap_damage }} damage dealt to party</span>
              </template>
              <template v-else-if="event.type === 'Unguarded Treasure'">
                <span class="badge badge-success">Treasure</span>
                <span class="text-gold">Found {{ event.treasure?.gold }}gp</span>
              </template>
              <template v-else>
                <span class="badge">{{ event.type }}</span>
              </template>
            </div>
          </div>
        </div>
      </div>

      <!-- Actions -->
      <div class="flex gap-1">
        <button class="btn btn-primary" @click="router.push('/adventurers')">
          Examine Roster
        </button>
        <button class="btn btn-secondary" @click="router.push('/')">
          Back to Dashboard
        </button>
      </div>
    </template>
  </div>
</template>

<style scoped>
.summary-stats {
  display: flex;
  gap: 12px;
  font-size: 12px;
}

.badge-alive {
  background: rgba(74, 222, 128, 0.15);
  color: #4ade80;
}

.badge-dead {
  background: rgba(231, 76, 60, 0.15);
  color: #e74c3c;
}

.badge-success {
  background: rgba(74, 222, 128, 0.15);
  color: #4ade80;
}

.badge-danger {
  background: rgba(231, 76, 60, 0.15);
  color: #e74c3c;
}

.badge-warning {
  background: rgba(241, 196, 15, 0.15);
  color: #f1c40f;
}

.events-log {
  max-height: 300px;
  overflow-y: auto;
}

.turn-entry {
  margin-bottom: 8px;
}

.turn-header {
  font-weight: 600;
  font-size: 11px;
  color: var(--text-muted);
  margin-bottom: 2px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.event-entry {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 3px 0;
  border-bottom: 1px solid var(--border-color);
  font-size: 12px;
  flex-wrap: wrap;
}
</style>
