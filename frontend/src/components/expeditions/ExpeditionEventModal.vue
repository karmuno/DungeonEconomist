<script setup lang="ts">
import { ref, watch } from 'vue'
import * as expeditionsApi from '../../api/expeditions'
import type { ExpeditionSummaryDetail, ExpeditionMemberResult } from '../../api/expeditions'
import { formatCurrency } from '../../utils/currency'
import ModalDialog from '../shared/ModalDialog.vue'
import ProgressBar from '../shared/ProgressBar.vue'
import AdventurerLink from '../adventurers/AdventurerLink.vue'

const props = defineProps<{
  isOpen: boolean
  expeditionId: number | null
  eventMessage: string
  eventType: string
  choosing: boolean
}>()

const emit = defineEmits<{
  choose: [choice: string]
  close: []
}>()

const loading = ref(false)
const summary = ref<ExpeditionSummaryDetail | null>(null)

// Fetch expedition summary whenever the modal opens or the event changes
watch([() => props.isOpen, () => props.eventMessage], async ([open]) => {
  if (open && props.expeditionId) {
    loading.value = true
    summary.value = null
    try {
      summary.value = await expeditionsApi.getSummary(props.expeditionId)
    } catch {
      // Fail silently — the modal still shows the message and buttons
    } finally {
      loading.value = false
    }
  }
})

function pluralMonster(name: string, count: number): string {
  if (count <= 1) return name
  if (name.endsWith('f')) return `${count} ${name.slice(0, -1)}ves`
  if (name.endsWith('fe')) return `${count} ${name.slice(0, -2)}ves`
  return `${count} ${name}s`
}

function hpColor(member: ExpeditionMemberResult): string {
  if (!member.alive) return 'var(--accent-red, #e74c3c)'
  const pct = member.hp_max > 0 ? member.hp_current / member.hp_max : 0
  if (pct > 0.5) return 'var(--accent-green, #4ade80)'
  if (pct > 0.25) return '#fbbf24'
  return 'var(--accent-red, #e74c3c)'
}

interface TurnEvent {
  type: string
  combat?: {
    outcome: string
    monster_type: string
    monster_count?: number
    rounds_fought?: number
    hp_lost: number
    xp_earned: number
    monsters_killed?: number
    monsters_fled?: number
    party_fled?: boolean
    round_log?: unknown[]
    healed_adventurers?: Array<{ name: string; hp: number }>
  }
  treasure?: { gold: number; silver: number; copper: number; xp_value: number; name: string }
  trap_damage?: number
  trap_victims?: Array<{ name: string; damage: number }>
}

interface TurnLog {
  turn: number
  deaths?: string[]
  events: TurnEvent[]
}

// Get the current (latest) turn from events_log
function getCurrentTurn(): TurnLog | null {
  if (!summary.value?.events_log) return null
  const log = summary.value.events_log as TurnLog[]
  if (log.length === 0) return null
  // Return last turn with activity
  for (let i = log.length - 1; i >= 0; i--) {
    if ((log[i].events?.length > 0) || (log[i].deaths?.length ?? 0) > 0) {
      return log[i]
    }
  }
  return log[log.length - 1]
}

// Get turn summaries up to but not including the current turn
function getPastSummaries(): string[] {
  if (!summary.value?.turn_summaries) return []
  const all = summary.value.turn_summaries
  // Show all except the last non-empty one (which is the "current turn" shown in detail)
  if (all.length <= 1) return []
  return all.slice(0, -1)
}
</script>

<template>
  <ModalDialog
    :is-open="isOpen"
    title="Expedition Event"
    @close="emit('close')"
  >
    <div class="event-modal">
      <!-- Event message -->
      <p class="event-message">{{ eventMessage }}</p>

      <!-- Loading -->
      <div v-if="loading" class="loading-text">Loading expedition data...</div>

      <template v-if="summary && !loading">
        <!-- Party Status -->
        <div class="section">
          <h4 class="section-title">Party Status</h4>
          <div class="party-roster">
            <div
              v-for="member in summary.member_results"
              :key="member.name"
              class="member-row"
              :class="{ dead: !member.alive }"
            >
              <AdventurerLink :adv-name="member.name" class="member-name" />
              <span class="member-class">{{ member.adventurer_class }}</span>
              <template v-if="member.alive">
                <ProgressBar
                  :value="member.hp_current"
                  :max="member.hp_max"
                  :color="hpColor(member)"
                  class="member-hp"
                />
              </template>
              <span v-else class="dead-badge">DEAD</span>
            </div>
          </div>
        </div>

        <!-- Turn Log (collapsed) -->
        <details v-if="getPastSummaries().length > 0" class="section turn-log-details">
          <summary class="section-title clickable">
            Expedition Log ({{ getPastSummaries().length }} previous {{ getPastSummaries().length === 1 ? 'turn' : 'turns' }})
          </summary>
          <div class="turn-log">
            <div
              v-for="(line, idx) in getPastSummaries()"
              :key="idx"
              class="turn-line"
            >
              {{ line }}
            </div>
          </div>
        </details>

        <!-- Current Turn Detail -->
        <div v-if="getCurrentTurn()" class="section">
          <h4 class="section-title">This Turn</h4>
          <div class="current-turn">
            <template v-for="(event, idx) in getCurrentTurn()!.events" :key="idx">
              <div v-if="event.combat" class="turn-detail">
                <span class="detail-badge combat">Combat</span>
                <span>
                  {{ pluralMonster(event.combat.monster_type, event.combat.monster_count ?? 1) }}
                  — <strong>{{ event.combat.outcome }}</strong>
                </span>
                <span class="detail-stat">{{ event.combat.hp_lost }} HP lost</span>
                <span class="detail-stat xp">+{{ event.combat.xp_earned }} XP</span>
                <span v-if="event.combat.monsters_killed" class="detail-stat killed">{{ event.combat.monsters_killed }} killed</span>
                <span v-if="event.combat.monsters_fled" class="detail-stat fled">{{ event.combat.monsters_fled }} fled</span>
                <span v-if="event.combat.party_fled" class="detail-stat fled">party fled</span>
                <template v-if="event.combat.healed_adventurers?.length">
                  <div v-for="(h, hi) in event.combat.healed_adventurers" :key="hi" class="heal-line">
                    ✚ {{ h.name }} healed for {{ h.hp }} HP
                  </div>
                </template>
              </div>
              <div v-else-if="event.treasure" class="turn-detail">
                <span class="detail-badge treasure">Treasure</span>
                <span class="text-gold">
                  Found {{ formatCurrency(event.treasure.gold, event.treasure.silver ?? 0, event.treasure.copper ?? 0) }}
                </span>
              </div>
              <div v-else-if="event.trap_damage" class="turn-detail">
                <span class="detail-badge trap">Trap</span>
                <span>{{ event.trap_damage }} total damage</span>
                <template v-if="event.trap_victims?.length">
                  <span class="trap-victims">
                    ({{ event.trap_victims.map(v => `${v.name} ${v.damage}`).join(', ') }})
                  </span>
                </template>
              </div>
              <div v-else class="turn-detail">
                <span class="detail-badge">{{ event.type }}</span>
              </div>
            </template>
            <div
              v-for="dead in (getCurrentTurn()!.deaths || [])"
              :key="dead"
              class="turn-detail death-line"
            >
              <span class="detail-badge death">Death</span>
              <strong><AdventurerLink :adv-name="dead" :dead="true" /></strong> has fallen
            </div>
          </div>
        </div>

        <!-- Totals -->
        <div class="section totals">
          <span class="text-gold">Loot: {{ formatCurrency(summary.total_loot, summary.total_silver ?? 0, summary.total_copper ?? 0) }}</span>
          <span>XP: {{ summary.total_xp }}</span>
          <span v-if="summary.spells_left !== undefined" class="text-info">Spells: {{ summary.spells_left }}</span>
          <span v-if="summary.heals_left !== undefined" class="text-success">Heals: {{ summary.heals_left }}</span>
          <span v-if="summary.stairs_found" class="text-stairs">Stairs found!</span>
        </div>
      </template>

      <!-- Action Buttons -->
      <div v-if="eventType === 'tpk'" class="action-buttons">
        <button
          class="btn btn-secondary"
          @click="emit('close')"
        >
          Rest in Peace
        </button>
      </div>
      <div v-else class="action-buttons">
        <button
          class="btn btn-primary"
          :disabled="choosing"
          @click="emit('choose', 'press_on')"
        >
          Press On
        </button>
        <button
          class="btn btn-secondary"
          :disabled="choosing"
          @click="emit('choose', 'retreat')"
        >
          Retreat
        </button>
        <button
          class="btn btn-secondary"
          :disabled="choosing"
          @click="emit('choose', 'auto')"
        >
          You Decide
        </button>
      </div>
      <button
        v-if="eventType !== 'tpk'"
        class="btn btn-sm view-details-link"
        @click="emit('close')"
      >
        View Full Expedition Details
      </button>
    </div>
  </ModalDialog>
</template>

<style scoped>
.event-modal {
  padding: 0.25rem 0;
}

.event-message {
  font-size: 1rem;
  color: var(--text-secondary);
  line-height: 1.5;
  margin-bottom: 0.75rem;
  text-align: center;
  font-weight: 600;
}

.loading-text {
  text-align: center;
  color: var(--text-muted);
  font-size: 0.85rem;
  padding: 1rem 0;
}

.section {
  margin-bottom: 0.75rem;
}

.section-title {
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 1px;
  color: var(--text-muted);
  margin: 0 0 4px;
  font-weight: 600;
}

.section-title.clickable {
  cursor: pointer;
}

.section-title.clickable:hover {
  color: var(--text-primary);
}

/* Party Roster */
.party-roster {
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.member-row {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  padding: 2px 4px;
  border-radius: 3px;
  background: var(--bg-secondary);
}

.member-row.dead {
  opacity: 0.5;
}

.member-name {
  font-weight: 600;
  color: var(--text-primary);
  min-width: 90px;
}

.member-class {
  color: var(--text-muted);
  font-size: 11px;
  min-width: 70px;
}

.member-hp {
  width: 140px;
  flex-shrink: 0;
  margin-left: auto;
}

.dead-badge {
  font-size: 10px;
  font-weight: 700;
  color: var(--accent-red, #e74c3c);
  background: rgba(231, 76, 60, 0.15);
  padding: 1px 6px;
  border-radius: 3px;
  margin-left: auto;
}

/* Turn Log */
.turn-log-details {
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius);
  padding: 6px 8px;
  background: var(--bg-secondary);
}

.turn-log {
  max-height: 150px;
  overflow-y: auto;
  margin-top: 4px;
}

.turn-line {
  font-size: 11px;
  color: var(--text-secondary);
  padding: 1px 0;
  font-family: var(--font-mono);
  border-bottom: 1px solid var(--border-color);
}

.turn-line:last-child {
  border-bottom: none;
}

/* Current Turn */
.current-turn {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.turn-detail {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
  font-size: 12px;
  padding: 3px 4px;
  border-radius: 3px;
  background: var(--bg-secondary);
}

.detail-badge {
  font-size: 10px;
  font-weight: 600;
  padding: 1px 5px;
  border-radius: 3px;
  text-transform: uppercase;
  letter-spacing: 0.3px;
}

.detail-badge.combat {
  background: rgba(231, 76, 60, 0.15);
  color: #e74c3c;
}

.detail-badge.treasure {
  background: rgba(74, 222, 128, 0.15);
  color: #4ade80;
}

.detail-badge.trap {
  background: rgba(241, 196, 15, 0.15);
  color: #f1c40f;
}

.detail-badge.death {
  background: rgba(231, 76, 60, 0.25);
  color: #e74c3c;
}

.detail-stat {
  font-size: 11px;
  color: var(--text-muted);
}

.detail-stat.xp {
  color: var(--accent-blue, #60a5fa);
}

.detail-stat.killed {
  color: #e74c3c;
}

.detail-stat.fled {
  color: #f1c40f;
}

.death-line {
  color: var(--accent-red, #e74c3c);
}

.trap-victims {
  font-size: 11px;
  color: var(--text-muted);
}

.heal-line {
  font-size: 11px;
  color: #4ade80;
  padding: 1px 0 1px 8px;
}

/* Totals */
.totals {
  display: flex;
  gap: 12px;
  font-size: 12px;
  padding: 4px 6px;
  background: var(--bg-secondary);
  border-radius: 3px;
}

.text-gold {
  color: var(--accent-green, #4ade80);
}

.text-info {
  color: var(--accent-blue, #60a5fa);
}

.text-success {
  color: #4ade80;
}

.text-stairs {
  color: #fbbf24;
  font-weight: 700;
}

/* Action Buttons */
.action-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  justify-content: center;
  margin: 0.75rem 0;
}

.action-buttons .btn {
  min-width: 110px;
}

.view-details-link {
  display: block;
  margin: 0 auto;
  color: var(--text-muted);
  text-decoration: underline;
}
</style>
