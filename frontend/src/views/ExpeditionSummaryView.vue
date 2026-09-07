<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import * as expeditionsApi from '../api/expeditions'
import type { ExpeditionSummaryDetail } from '../api/expeditions'
import { useNotificationsStore } from '../stores/notifications'
import { useGameTimeStore } from '../stores/gameTime'
import { usePlayerStore } from '../stores/player'
import { formatCurrency } from '../utils/currency'
import { formatGameDayShort } from '../utils/calendar'
import ProgressBar from '../components/shared/ProgressBar.vue'
import LoadingSpinner from '../components/shared/LoadingSpinner.vue'
import ExpeditionLogTree from '../components/expeditions/ExpeditionLogTree.vue'
import type { TurnLog } from '../types/expeditionLog'

const router = useRouter()
const route = useRoute()
const notifications = useNotificationsStore()
const gameTime = useGameTimeStore()
const player = usePlayerStore()

const summary = ref<ExpeditionSummaryDetail | null>(null)
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
  summary.value = await expeditionsApi.getSummary(id) as ExpeditionSummaryDetail
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

    const who = result.party_name ?? summary.value?.party_name ?? 'The party'
    if (result.status === 'in_progress') {
      const msg = result.auto_choice
        ? `${who} decided to press on!`
        : `${who} continues the expedition`
      notifications.add(msg, 'info')
    } else if (result.status === 'completed') {
      await player.fetchPlayer()
      const retMsg = result.auto_choice === 'retreat'
        ? `${who} decided to retreat!`
        : result.retreated ? `${who} retreated safely` : `${who} completed the expedition`
      notifications.add(retMsg,
        {
          type: result.retreated ? 'info' : 'success',
          action: {
            label: 'View Summary',
            route: `/expedition/${summary.value!.expedition_id}/summary`,
          },
        },
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

const turnsWithActivity = computed(() => {
  if (!summary.value) return []
  return (summary.value.events_log as TurnLog[]).filter(
    (turn) => (turn.events && turn.events.length > 0) || (turn.deaths && turn.deaths.length > 0)
  )
})

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

// Early retreats keep the planned return_day; actual_return_day records when
// the party really came home. Show PLANNED/ACTUAL only when the plan broke.
const showPlannedActual = computed(() => {
  const s = summary.value
  return !!s && s.actual_return_day != null && s.actual_return_day !== s.return_day
})

const actualDurationDays = computed(() => {
  const s = summary.value
  if (!s || s.actual_return_day == null) return 0
  return s.actual_return_day - s.start_day + 1
})
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
        <p v-if="summary.dungeon_level" class="text-muted mb-1">Depth {{ summary.dungeon_level }}</p>
        <div v-if="showPlannedActual" class="date-block mb-2">
          <div class="date-line">
            <span class="date-label planned">Planned</span>
            <span class="date-value muted-value">
              {{ formatGameDayShort(summary.start_day) }} → {{ formatGameDayShort(summary.return_day) }} · {{ summary.duration_days }} days
            </span>
          </div>
          <div class="date-line">
            <span class="date-label actual">Actual</span>
            <span class="date-value">
              {{ formatGameDayShort(summary.start_day) }} → {{ formatGameDayShort(summary.actual_return_day!) }} · {{ actualDurationDays }} {{ actualDurationDays === 1 ? 'day' : 'days' }}
            </span>
          </div>
        </div>
        <p v-else class="text-muted mb-2">
          {{ formatGameDayShort(summary.start_day) }} &mdash; {{ formatGameDayShort(summary.return_day) }}
          ({{ summary.duration_days }} days)
        </p>
        <div class="summary-stats">
          <span class="text-gold">Loot: {{ formatCurrency(lootCopper(summary.total_loot).gold, lootCopper(summary.total_loot).silver, lootCopper(summary.total_loot).copper) }}</span>
          <span>XP: {{ summary.total_xp }}</span>
          <span v-if="summary.spells_left !== undefined" class="text-info">Spells Left: {{ summary.spells_left }}</span>
          <span v-if="summary.heals_left !== undefined" class="text-success">Cures Left: {{ summary.heals_left }}</span>
          <span v-if="summary.stairs_found" class="text-stairs">Stairs to {{ summary.stairs_found.new_level_name }} found!</span>
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
          <template v-if="summary.pending_event!.type === 'stairs'">
            <button class="btn btn-primary" :disabled="choosing" @click="makeChoice('press_on_same')">
              Continue This Level
            </button>
            <button class="btn btn-success" :disabled="choosing" @click="makeChoice('press_on_next')">
              Descend Deeper
            </button>
            <button class="btn btn-secondary" :disabled="choosing" @click="makeChoice('retreat')">
              Retreat (Level Saved)
            </button>
          </template>
          <template v-else>
            <button class="btn btn-primary" :disabled="choosing" @click="makeChoice('press_on')">
              Press On
            </button>
            <button class="btn btn-secondary" :disabled="choosing" @click="makeChoice('retreat')">
              Retreat
            </button>
          </template>
          <button class="btn btn-secondary" :disabled="choosing" @click="makeChoice('auto')">
            You Decide
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
              <td><span :class="{ 'adv-dead': !member.alive }">{{ member.name }}</span></td>
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
        <ExpeditionLogTree
          :turns="turnsWithActivity"
          :member-names="summary.member_results.map(m => m.name)"
        />
      </div>

      <!-- Actions -->
      <div class="flex gap-1">
        <button class="btn btn-primary" @click="router.push('/')">
          Back to Dashboard
        </button>
      </div>
    </template>
  </div>
</template>

<style scoped>
.adv-dead {
  text-decoration: line-through;
  opacity: 0.6;
}

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

.date-block {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.date-line {
  display: flex;
  align-items: baseline;
  gap: 10px;
}

.date-label {
  width: 62px;
  flex-shrink: 0;
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.1em;
}

.date-label.planned {
  color: #6b7280;
}

.date-label.actual {
  color: #4ade80;
}

.date-value {
  font-size: 15px;
  color: #e5e7eb;
}

.date-value.muted-value {
  font-size: 13px;
  color: #6b7280;
}

.text-stairs {
  color: #fbbf24;
  font-weight: 700;
}
</style>
