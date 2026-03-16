<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import * as expeditionsApi from '../api/expeditions'
import type { PendingEvent } from '../api/expeditions'
import { useNotificationsStore } from '../stores/notifications'
import { useGameTimeStore } from '../stores/gameTime'
import { usePlayerStore } from '../stores/player'
import { formatCurrency } from '../utils/currency'
import { formatGameDayShort } from '../utils/calendar'
import ProgressBar from '../components/shared/ProgressBar.vue'
import LoadingSpinner from '../components/shared/LoadingSpinner.vue'

const router = useRouter()
const route = useRoute()
const notifications = useNotificationsStore()
const gameTime = useGameTimeStore()
const player = usePlayerStore()

interface SummaryData {
  expedition_id: number
  party_id: number
  party_name: string
  start_day: number
  return_day: number
  duration_days: number
  result: string
  dungeon_level?: number
  member_results: Array<{
    name: string
    adventurer_class: string
    level: number
    alive: boolean
    hp_current: number
    hp_max: number
    xp_gained: number
    gold: number
    silver: number
    copper: number
  }>
  total_loot: number
  total_xp: number
  events_log: unknown[]
  estimated_readiness_day: number | null
  pending_event?: PendingEvent | null
}

const summary = ref<SummaryData | null>(null)
const loading = ref(true)
const choosing = ref(false)

const isActive = computed(() =>
  summary.value?.result === 'in_progress' || summary.value?.result === 'awaiting_choice'
)

const hasPendingChoice = computed(() =>
  summary.value?.result === 'awaiting_choice' && summary.value?.pending_event
)

async function fetchSummary() {
  const id = Number(route.params.id)
  summary.value = await expeditionsApi.getSummary(id) as SummaryData
}

watch(() => gameTime.currentDay, () => fetchSummary())
watch(() => gameTime.expeditionVersion, () => fetchSummary())

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

async function makeChoice(choice: string) {
  if (!summary.value) return
  choosing.value = true
  try {
    const result = await expeditionsApi.choose(summary.value.expedition_id, choice)

    for (const evt of result.events ?? []) {
      const typeMap: Record<string, string> = {
        death: 'error', loot: 'info', stairs: 'success',
        upkeep: 'warning', expedition_complete: 'success',
      }
      notifications.add(evt.message, { type: (typeMap[evt.type] ?? 'info') as any })
    }

    if (result.status === 'in_progress') {
      notifications.add('The expedition continues...', 'info')
    } else if (result.status === 'completed') {
      await player.fetchPlayer()
      notifications.add(
        result.retreated ? 'The party retreated safely' : 'The expedition is complete!',
        result.retreated ? 'info' : 'success',
      )
    }

    // Signal other components and refresh
    gameTime.expeditionVersion++
    await fetchSummary()
  } catch (e: any) {
    const detail = e?.data?.detail ?? e?.message ?? 'Failed to submit choice'
    notifications.add(detail, 'error')
    // Refetch in case state changed (e.g. auto-resolved)
    await fetchSummary()
  } finally {
    choosing.value = false
  }
}

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
  deaths?: string[]
  events: Array<{
    type: string
    combat?: { outcome: string; monster_type: string; hp_lost: number; xp_earned: number }
    treasure?: { gold: number; xp_value: number }
    trap_damage?: number
  }>
}

const turnsWithActivity = computed(() => {
  if (!summary.value) return []
  return (summary.value.events_log as TurnLog[]).filter(
    (turn) => (turn.events && turn.events.length > 0) || (turn.deaths && turn.deaths.length > 0)
  )
})

function outcomeClass(outcome: string): string {
  if (outcome === 'Clear Victory' || outcome === 'Victory') return 'badge-success'
  if (outcome === 'Tough Fight') return 'badge-warning'
  return 'badge-danger'
}

function statusLabel(result: string): string {
  if (result === 'in_progress') return 'In Progress'
  if (result === 'awaiting_choice') return 'Awaiting Decision'
  return result.charAt(0).toUpperCase() + result.slice(1)
}

function statusClass(result: string): string {
  if (result === 'in_progress') return 'badge-info'
  if (result === 'awaiting_choice') return 'badge-warning'
  return 'badge-success'
}
</script>

<template>
  <div>
    <h1>Expedition Summary</h1>

    <LoadingSpinner v-if="loading" />
    <template v-else-if="summary">
      <!-- Header card -->
      <div class="card mb-2">
        <div class="flex flex-between mb-2">
          <h2>{{ summary.party_name }}</h2>
          <span class="badge" :class="statusClass(summary.result)">{{ statusLabel(summary.result) }}</span>
        </div>
        <p class="text-muted mb-2">
          <template v-if="summary.dungeon_level">Depth {{ summary.dungeon_level }} &mdash; </template>
          {{ formatGameDayShort(summary.start_day) }} &mdash; {{ formatGameDayShort(summary.return_day) }}
          ({{ summary.duration_days }} days)
        </p>
        <div class="summary-stats">
          <span class="text-gold">Loot: {{ formatCurrency(lootCopper(summary.total_loot).gold, lootCopper(summary.total_loot).silver, lootCopper(summary.total_loot).copper) }}</span>
          <span>XP: {{ summary.total_xp }}</span>
          <template v-if="summary.estimated_readiness_day">
            <span class="text-muted">Ready by: {{ formatGameDayShort(summary.estimated_readiness_day) }}</span>
          </template>
        </div>
      </div>

      <!-- Pending Decision -->
      <div v-if="hasPendingChoice" class="card mb-2 decision-card">
        <h3 class="mb-1">Decision Required</h3>
        <p class="decision-msg">{{ summary.pending_event!.message }}</p>
        <div v-if="summary.pending_event!.loot_so_far" class="decision-detail">
          Loot secured so far: {{ summary.pending_event!.loot_so_far }} gp
        </div>
        <div class="decision-buttons">
          <button class="btn btn-primary" :disabled="choosing" @click="makeChoice('press_on')">
            Press On
          </button>
          <button class="btn btn-secondary" :disabled="choosing" @click="makeChoice('retreat')">
            Retreat
          </button>
        </div>
      </div>

      <!-- Party Members -->
      <div class="card mb-2">
        <h3 class="mb-2">Party Members</h3>
        <table class="table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Class</th>
              <th>Level</th>
              <th>Status</th>
              <th>HP</th>
              <th v-if="!isActive">XP Gained</th>
              <th v-if="!isActive">Wealth</th>
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
                <span v-if="member.alive" class="badge badge-alive">{{ isActive ? 'Active' : 'Alive' }}</span>
                <span v-else class="badge badge-dead">Dead</span>
              </td>
              <td>
                <ProgressBar v-if="member.alive" :value="member.hp_current" :max="member.hp_max" />
                <span v-else>&mdash;</span>
              </td>
              <td v-if="!isActive">+{{ member.xp_gained }}</td>
              <td v-if="!isActive" class="text-gold">{{ formatCurrency(member.gold, member.silver, member.copper) }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Events Log -->
      <div v-if="turnsWithActivity.length > 0" class="card mb-2">
        <h3 class="mb-2">Expedition Log</h3>
        <div class="events-log">
          <div v-for="turn in turnsWithActivity" :key="turn.turn" class="turn-entry">
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
            <div v-for="dead in (turn.deaths || [])" :key="dead" class="event-entry death-entry">
              <span class="badge badge-dead">Death</span>
              <span><strong>{{ dead }}</strong> has fallen</span>
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

.decision-card {
  border-color: #fbbf24;
  text-align: center;
}

.decision-msg {
  font-size: 1rem;
  color: var(--text-secondary);
  line-height: 1.5;
  margin-bottom: 0.75rem;
}

.decision-detail {
  font-family: var(--font-mono);
  font-size: 0.85rem;
  color: var(--accent-green);
  margin-bottom: 0.75rem;
}

.decision-buttons {
  display: flex;
  gap: 12px;
  justify-content: center;
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

.badge-info {
  background: rgba(96, 165, 250, 0.15);
  color: #60a5fa;
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

.death-entry {
  color: var(--accent-red, #e74c3c);
}
</style>
