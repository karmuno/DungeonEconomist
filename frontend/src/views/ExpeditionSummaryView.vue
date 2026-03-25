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
  spells_left?: number
  heals_left?: number
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
      const msg = result.auto_choice
        ? `The party decided to press on!`
        : 'The expedition continues...'
      notifications.add(msg, 'info')
    } else if (result.status === 'completed') {
      await player.fetchPlayer()
      const retMsg = result.auto_choice === 'retreat'
        ? 'The party decided to retreat!'
        : result.retreated ? 'The party retreated safely' : 'The expedition is complete!'
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

interface AttackEntry {
  attacker: string
  target: string
  roll: number
  needed: number
  hit: boolean
  damage: number
  target_died: boolean
}

interface TurnUndeadEntry {
  monster: string
  result: 'destroyed' | 'turned' | 'resisted'
  roll?: number
  needed?: number
}

interface RoundEntry {
  round: number
  event?: string
  caster?: string
  spell?: string
  monsters_destroyed?: number
  halfling_pre_round?: AttackEntry[]
  initiative?: string
  initiative_winner?: string
  attacks?: AttackEntry[]
  morale_checks?: Array<{ side: string; roll: number; morale: number; passed: boolean }>
  cleric_turn?: { cleric: string; turn_log: TurnUndeadEntry[] }
  cleric_turns?: Array<{ cleric: string; turn_log: TurnUndeadEntry[] }>
}

interface TurnLog {
  turn: number
  deaths?: string[]
  events: Array<{
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
      mu_spell_used?: string | null
      cleric_turned?: boolean
      healed_adventurers?: Array<{ name: string; hp: number }>
      round_log?: RoundEntry[]
    }
    treasure?: { gold: number; silver: number; copper: number; xp_value: number; name: string }
    trap_damage?: number
  }>
}

const pcNames = computed(() => new Set(summary.value?.member_results.map(m => m.name) ?? []))

function sideAttacks(r: RoundEntry, side: 'party' | 'monsters'): AttackEntry[] {
  const all = r.halfling_pre_round ?? r.attacks ?? []
  return all.filter(a => side === 'party' ? pcNames.value.has(a.attacker) : !pcNames.value.has(a.attacker))
}

function sideSummary(attacks: AttackEntry[]): string {
  if (!attacks.length) return '—'
  const hits = attacks.filter(a => a.hit)
  const dmg = hits.reduce((s, a) => s + a.damage, 0)
  return `${hits.length}/${attacks.length} · ${dmg} dmg`
}

function roundLabel(r: RoundEntry): string {
  if (r.event === 'spell') return `${r.caster} casts ${r.spell} — ${r.monsters_destroyed} destroyed`
  if (r.halfling_pre_round) return `Halflings pre-round`
  const initiative = r.initiative_winner ?? r.initiative
  const label = initiative === 'party' ? 'party first' : initiative === 'monsters' ? 'monsters first' : 'simultaneous'
  return `Round ${r.round} (${label})`
}

function turnUndeadSummary(ct: RoundEntry['cleric_turns']): string {
  if (!ct || ct.length === 0) return ''
  return ct.map(c => {
    const destroyed = c.turn_log.filter(e => e.result !== 'resisted').length
    const resisted = c.turn_log.filter(e => e.result === 'resisted').length
    const parts: string[] = []
    if (destroyed > 0) parts.push(`${destroyed} turned`)
    if (resisted > 0) parts.push(`${resisted} resisted`)
    return `${c.cleric}: ${parts.join(', ') || 'failed'}`
  }).join('; ')
}

const expandedRounds = ref<Set<string>>(new Set())

function toggleRound(turnNum: number, eventIdx: number, roundIdx: number, e: Event) {
  e.stopPropagation()
  const key = `${turnNum}-${eventIdx}-${roundIdx}`
  if (expandedRounds.value.has(key)) {
    expandedRounds.value.delete(key)
  } else {
    expandedRounds.value.add(key)
  }
}

function isRoundExpanded(turnNum: number, eventIdx: number, roundIdx: number): boolean {
  return expandedRounds.value.has(`${turnNum}-${eventIdx}-${roundIdx}`)
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

const expandedCombats = ref<Set<string>>(new Set())

function toggleCombat(turnNum: number, idx: number) {
  const key = `${turnNum}-${idx}`
  if (expandedCombats.value.has(key)) {
    expandedCombats.value.delete(key)
  } else {
    expandedCombats.value.add(key)
  }
}

function isCombatExpanded(turnNum: number, idx: number): boolean {
  return expandedCombats.value.has(`${turnNum}-${idx}`)
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
          <span v-if="summary.spells_left !== undefined" class="text-info">Spells: {{ summary.spells_left }}</span>
          <span v-if="summary.heals_left !== undefined" class="text-success">Heals: {{ summary.heals_left }}</span>
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
            <div v-for="(event, idx) in turn.events" :key="idx" class="event-entry" :class="{ 'combat-expandable': event.type === 'Monster' }" @click="event.type === 'Monster' ? toggleCombat(turn.turn, idx) : undefined">
              <template v-if="event.type === 'Monster'">
                <div class="combat-summary">
                  <span class="combat-toggle">{{ isCombatExpanded(turn.turn, idx) ? '\u25BC' : '\u25B6' }}</span>
                  <span>Encountered <strong>{{ (event.combat?.monster_count ?? 1) > 1 ? `${event.combat?.monster_count} ${event.combat?.monster_type}s` : event.combat?.monster_type }}</strong></span>
                  <span :class="['badge', outcomeClass(event.combat?.outcome ?? '')]">
                    {{ event.combat?.outcome }}
                  </span>
                  <span class="text-muted">{{ event.combat?.hp_lost }} HP lost, +{{ event.combat?.xp_earned }} XP</span>
                  <span v-if="event.combat?.monsters_killed" class="monster-fate killed">{{ event.combat.monsters_killed }} killed</span>
                  <span v-if="event.combat?.monsters_fled" class="monster-fate fled">{{ event.combat.monsters_fled }} fled</span>
                  <span v-if="event.combat?.party_fled" class="monster-fate fled">party fled</span>
                  <span v-if="event.treasure" class="text-gold">
                    Loot: {{ formatCurrency(event.treasure.gold, event.treasure.silver ?? 0, event.treasure.copper ?? 0) }}
                  </span>
                </div>
                <div v-if="isCombatExpanded(turn.turn, idx)" class="combat-details">
                  <template v-if="event.combat?.mu_spell_used">
                    <div class="round-row">
                      <span class="text-muted">Spell:</span>
                      <span><strong>{{ event.combat.mu_caster || 'A caster' }}</strong> cast <strong>{{ event.combat.mu_spell_used }}</strong> and ended the fight instantly</span>
                    </div>
                  </template>
                  <template v-else-if="event.combat?.round_log?.length">
                    <div v-for="(r, ri) in event.combat.round_log" :key="ri" class="round-block">
                      <!-- Round header row -->
                      <div class="round-row round-expandable" @click="toggleRound(turn.turn, idx, ri, $event)">
                        <span class="round-toggle">{{ isRoundExpanded(turn.turn, idx, ri) ? '▼' : '▶' }}</span>
                        <span class="round-label">{{ roundLabel(r) }}</span>
                        <template v-if="!r.event && !r.halfling_pre_round">
                          <span class="side-pill party">Party: {{ sideSummary(sideAttacks(r, 'party')) }}</span>
                          <span class="side-pill monsters">Monsters: {{ sideSummary(sideAttacks(r, 'monsters')) }}</span>
                        </template>
                        <template v-if="r.cleric_turns?.length">
                          <span class="side-pill party">Turn Undead: {{ turnUndeadSummary(r.cleric_turns) }}</span>
                        </template>
                        <template v-if="r.morale_checks?.length">
                          <span v-for="(mc, mi) in r.morale_checks" :key="mi" :class="['morale-tag', mc.passed ? '' : 'morale-break']">
                            {{ mc.side }} morale {{ mc.passed ? 'holds' : 'breaks' }}
                          </span>
                        </template>
                      </div>
                      <!-- Round expanded: attacks by side -->
                      <template v-if="isRoundExpanded(turn.turn, idx, ri)">
                        <template v-if="r.event === 'spell'">
                          <div class="attack-line">{{ r.caster }} casts {{ r.spell }} — {{ r.monsters_destroyed }} destroyed</div>
                        </template>
                        <template v-else>
                          <!-- Turn Undead details -->
                          <template v-if="r.cleric_turns?.length">
                            <div v-for="(ct, cti) in r.cleric_turns" :key="'ct'+cti" class="side-header">
                              {{ ct.cleric }} Turn Attempt
                              <div v-for="(tl, tli) in ct.turn_log" :key="'tl'+tli" class="attack-line" style="padding-left: 20px;">
                                <span class="atk-name">{{ tl.monster }}</span>
                                <span class="atk-arrow">→</span>
                                <span :class="tl.result === 'resisted' ? 'text-muted' : 'text-success'">{{ tl.result }}</span>
                                <span v-if="tl.roll" class="text-muted" style="font-size: 0.8em"> (rolled {{ tl.roll }} vs {{ tl.needed }})</span>
                              </div>
                            </div>
                          </template>
                          <!-- Party attacks -->
                          <template v-if="sideAttacks(r, 'party').length">
                            <div class="side-header">Party</div>
                            <div v-for="(atk, ai) in sideAttacks(r, 'party').filter(a => a.hit)" :key="'p'+ai" class="attack-line">
                              <span class="atk-name">{{ atk.attacker }}</span>
                              <span class="atk-arrow">→</span>
                              <span class="atk-target">{{ atk.target }}</span>
                              <span class="atk-dmg">{{ atk.damage }} dmg<span v-if="atk.target_died"> ☠</span></span>
                            </div>
                          </template>
                          <!-- Monster attacks -->
                          <template v-if="sideAttacks(r, 'monsters').length">
                            <div class="side-header">Monsters</div>
                            <div v-for="(atk, ai) in sideAttacks(r, 'monsters').filter(a => a.hit)" :key="'m'+ai" class="attack-line">
                              <span class="atk-name">{{ atk.attacker }}</span>
                              <span class="atk-arrow">→</span>
                              <span class="atk-target">{{ atk.target }}</span>
                              <span class="atk-dmg">{{ atk.damage }} dmg<span v-if="atk.target_died"> ☠</span></span>
                            </div>
                          </template>
                        </template>
                      </template>
                    </div>
                  </template>
                  <template v-else-if="!event.combat?.mu_spell_used">
                    <span class="text-muted">{{ event.combat?.rounds_fought ?? 0 }} round(s) fought</span>
                  </template>
                  <template v-if="event.combat?.healed_adventurers?.length">
                    <div v-for="(h, hi) in event.combat.healed_adventurers" :key="hi" class="round-row heal-row">
                      <span class="heal-icon">✚</span>
                      <span>{{ h.name }} healed for <strong>{{ h.hp }}</strong> HP</span>
                    </div>
                  </template>
                </div>
              </template>
              <template v-else-if="event.type === 'Trap' || event.type === 'Trap/Hazard'">
                <span class="badge badge-warning">Trap</span>
                <span>{{ event.trap_damage }} damage dealt to party</span>
              </template>
              <template v-else-if="event.type === 'Unguarded Treasure'">
                <span class="badge badge-success">Treasure</span>
                <span class="text-gold">Found {{ formatCurrency(event.treasure?.gold ?? 0, event.treasure?.silver ?? 0, event.treasure?.copper ?? 0) }}</span>
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
        <button class="btn btn-primary" @click="router.push('/')">
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
  flex-direction: column;
  gap: 0;
  padding: 3px 0;
  border-bottom: 1px solid var(--border-color);
  font-size: 12px;
}

.event-entry:not(.combat-expandable) {
  flex-direction: row;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}

.combat-expandable {
  cursor: pointer;
}

.combat-expandable:hover {
  background: rgba(255, 255, 255, 0.03);
}

.combat-summary {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}

.combat-toggle {
  font-size: 9px;
  color: var(--text-muted);
  width: 10px;
  flex-shrink: 0;
}

.combat-details {
  display: flex;
  flex-direction: column;
  gap: 1px;
  padding: 4px 0 2px 16px;
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--text-secondary);
}

.round-block {
  display: flex;
  flex-direction: column;
}

.round-row {
  display: flex;
  align-items: baseline;
  gap: 6px;
  flex-wrap: wrap;
  padding: 2px 0;
}

.round-expandable {
  cursor: pointer;
}

.round-expandable:hover {
  color: var(--text-primary);
}

.round-toggle {
  font-size: 8px;
  color: var(--text-muted);
  width: 8px;
  flex-shrink: 0;
}

.round-label {
  color: var(--text-secondary);
}

.side-pill {
  font-size: 10px;
  padding: 1px 5px;
  border-radius: 3px;
}

.side-pill.party {
  background: rgba(74, 222, 128, 0.1);
  color: #4ade80;
}

.side-pill.monsters {
  background: rgba(231, 76, 60, 0.1);
  color: #e74c3c;
}

.morale-tag {
  font-size: 10px;
  color: var(--text-muted);
}

.morale-break {
  color: #f1c40f;
}

.side-header {
  padding: 2px 0 0 12px;
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: var(--text-muted);
}

.attack-line {
  display: flex;
  align-items: baseline;
  gap: 4px;
  padding: 1px 0 1px 12px;
  color: var(--text-secondary);
}

.atk-name {
  color: var(--text-primary);
  min-width: 80px;
}

.atk-arrow {
  color: var(--text-muted);
}

.atk-target {
  color: var(--text-secondary);
  min-width: 70px;
}

.atk-dmg {
  color: #e74c3c;
}

.heal-row {
  color: #4ade80;
}

.heal-icon {
  font-size: 10px;
  width: 8px;
  flex-shrink: 0;
}

.death-entry {
  color: var(--accent-red, #e74c3c);
}

.monster-fate {
  font-size: 11px;
  padding: 1px 5px;
  border-radius: 3px;
}

.monster-fate.killed {
  background: rgba(231, 76, 60, 0.12);
  color: #e74c3c;
}

.monster-fate.fled {
  background: rgba(241, 196, 15, 0.12);
  color: #f1c40f;
}
</style>
