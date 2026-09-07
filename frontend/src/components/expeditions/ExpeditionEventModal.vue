<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import * as expeditionsApi from '../../api/expeditions'
import type { ExpeditionSummaryDetail, ExpeditionMemberResult } from '../../api/expeditions'
import { useGameTimeStore } from '../../stores/gameTime'
import { formatCurrency } from '../../utils/currency'
import ModalDialog from '../shared/ModalDialog.vue'
import ExpeditionLogTree from './ExpeditionLogTree.vue'
import type { TurnLog } from '../../types/expeditionLog'

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

const gameTime = useGameTimeStore()

const loading = ref(false)
const summary = ref<ExpeditionSummaryDetail | null>(null)
const logOpen = ref(false)

// Fetch expedition summary whenever the modal opens or the event changes
watch([() => props.isOpen, () => props.eventMessage], async ([open]) => {
  if (open && props.expeditionId) {
    loading.value = true
    summary.value = null
    logOpen.value = false
    try {
      summary.value = await expeditionsApi.getSummary(props.expeditionId)
    } catch {
      // Fail silently — the modal still shows the message and buttons
    } finally {
      loading.value = false
    }
  }
})

// --- Header meta -------------------------------------------------------------

const daysElapsed = computed(() => {
  const s = summary.value
  if (!s) return 1
  const elapsed = gameTime.currentDay - s.start_day + 1
  return Math.min(Math.max(elapsed, 1), s.duration_days)
})

const headerMeta = computed(() => {
  const s = summary.value
  if (!s) return ''
  const parts = [s.party_name]
  const place = [s.dungeon_name, s.dungeon_level ? `Depth ${s.dungeon_level}` : null]
    .filter(Boolean).join(', ')
  if (place) parts.push(place)
  parts.push(`Day ${daysElapsed.value} of ${s.duration_days}`)
  return parts.join(' · ')
})

// --- Event badge -------------------------------------------------------------

const badgeLabel = computed(() => {
  const t = props.eventType || 'event'
  return t.replace(/_/g, ' ').toUpperCase()
})

const badgeTone = computed(() => {
  const t = props.eventType
  if (t === 'tpk' || t === 'death') return 'badge-red'
  if (t === 'treasure' || t === 'stairs' || t === 'big_haul') return 'badge-green'
  return 'badge-gold'
})

// --- Damage bookkeeping ------------------------------------------------------

interface DamageTotals {
  dealt: Map<string, number>
  taken: Map<string, number>
  casts: Map<string, number>
  healed: Map<string, number>
}

function tallyTurns(turns: TurnLog[], names: Set<string>): DamageTotals {
  const dealt = new Map<string, number>()
  const taken = new Map<string, number>()
  const casts = new Map<string, number>()
  const healed = new Map<string, number>()
  for (const turn of turns) {
    for (const ev of turn.events ?? []) {
      for (const v of ev.trap_victims ?? []) {
        if (names.has(v.name)) taken.set(v.name, (taken.get(v.name) ?? 0) + v.damage)
      }
      // Credit the healer, not the patient (older logs name no healer and are skipped)
      for (const h of ev.combat?.healed_adventurers ?? []) {
        if (h.healer && names.has(h.healer)) healed.set(h.healer, (healed.get(h.healer) ?? 0) + h.hp)
      }
      // Revives count as healing too: a potion credits the adventurer who held it
      for (const rv of ev.combat?.revivals ?? []) {
        if (names.has(rv.healer)) healed.set(rv.healer, (healed.get(rv.healer) ?? 0) + rv.hp)
      }
      for (const r of ev.combat?.round_log ?? []) {
        if (r.event === 'spell' && r.caster && names.has(r.caster)) {
          casts.set(r.caster, (casts.get(r.caster) ?? 0) + 1)
        }
        for (const sc of r.spell_casts ?? []) {
          if (names.has(sc.caster)) casts.set(sc.caster, (casts.get(sc.caster) ?? 0) + 1)
        }
        for (const a of [...(r.halfling_pre_round ?? []), ...(r.attacks ?? [])]) {
          if (!a.hit) continue
          if (names.has(a.attacker)) dealt.set(a.attacker, (dealt.get(a.attacker) ?? 0) + a.damage)
          if (names.has(a.target)) taken.set(a.target, (taken.get(a.target) ?? 0) + a.damage)
        }
      }
    }
  }
  return { dealt, taken, casts, healed }
}

const memberNames = computed(() => summary.value?.member_results.map(m => m.name) ?? [])

const turns = computed<TurnLog[]>(() => {
  const log = (summary.value?.events_log ?? []) as TurnLog[]
  return log.filter(t => (t.events?.length ?? 0) > 0 || (t.deaths?.length ?? 0) > 0)
})

const currentTurn = computed<TurnLog | null>(() =>
  turns.value.length ? turns.value[turns.value.length - 1] : null
)

// --- "This Event" table ------------------------------------------------------

interface EventRow {
  member: ExpeditionMemberResult
  damage: number
}

const eventRows = computed<EventRow[]>(() => {
  const s = summary.value
  if (!s) return []
  const turn = currentTurn.value
  const names = new Set(memberNames.value)
  const taken = turn ? tallyTurns([turn], names).taken : new Map<string, number>()
  return s.member_results.map(m => ({ member: m, damage: taken.get(m.name) ?? 0 }))
})

// --- "Expedition So Far" ledger ----------------------------------------------

interface LedgerRow {
  member: ExpeditionMemberResult
  dealt: number
  taken: number
  casts: number
  healed: number
}

const ledgerRows = computed<LedgerRow[]>(() => {
  const s = summary.value
  if (!s) return []
  const names = new Set(memberNames.value)
  const { dealt, taken, casts, healed } = tallyTurns(turns.value, names)
  return s.member_results.map(m => ({
    member: m,
    dealt: dealt.get(m.name) ?? 0,
    taken: taken.get(m.name) ?? 0,
    casts: casts.get(m.name) ?? 0,
    healed: healed.get(m.name) ?? 0,
  }))
})

const ledgerTotals = computed(() => {
  const rows = ledgerRows.value
  return {
    dealt: rows.reduce((sum, r) => sum + r.dealt, 0),
    taken: rows.reduce((sum, r) => sum + r.taken, 0),
    casts: rows.reduce((sum, r) => sum + r.casts, 0),
    healed: rows.reduce((sum, r) => sum + r.healed, 0),
  }
})

const totalKills = computed(() =>
  turns.value.reduce((sum, t) =>
    sum + t.events.reduce((s, ev) => s + (ev.combat?.monsters_killed ?? 0), 0), 0)
)

function hpPct(member: ExpeditionMemberResult): number {
  if (!member.alive || member.hp_max <= 0) return 0
  return Math.min(100, Math.round((member.hp_current / member.hp_max) * 100))
}

function hpColor(member: ExpeditionMemberResult): string {
  if (!member.alive) return '#ef4444'
  const pct = member.hp_max > 0 ? member.hp_current / member.hp_max : 0
  if (pct > 0.5) return '#4ade80'
  if (pct > 0.25) return '#fbbf24'
  return '#ef4444'
}

</script>

<template>
  <ModalDialog :is-open="isOpen" title="Expedition Event" width="760px" @close="emit('close')">
    <template #header>
      <div class="em-header">
        <h3 class="em-title">Expedition Event</h3>
        <span v-if="headerMeta" class="em-meta">{{ headerMeta }}</span>
      </div>
    </template>

    <div class="event-modal">
      <!-- 1. Event line -->
      <div class="event-line">
        <span :class="['event-badge', badgeTone]">{{ badgeLabel }}</span>
        <p class="event-narrative">{{ eventMessage }}</p>
      </div>

      <!-- Loading -->
      <div v-if="loading" class="loading-text">Loading expedition data...</div>

      <!-- 2. Decision block — up front so the choice is on screen immediately -->
      <div v-if="eventType === 'tpk'" class="tpk-actions">
        <button class="btn btn-secondary" @click="emit('close')">Rest in Peace</button>
      </div>
      <div v-else class="decision-block">
        <div class="decision-col">
          <button
            class="decide-btn primary"
            :disabled="choosing"
            title="Continue into the dungeon."
            @click="emit('choose', 'press_on')"
          >
            Press On
          </button>
        </div>
        <div class="decision-col">
          <button
            class="decide-btn"
            :disabled="choosing"
            title="Return early."
            @click="emit('choose', 'retreat')"
          >
            Retreat
          </button>
        </div>
        <div class="decision-col">
          <button
            class="decide-btn auto-hover"
            :disabled="choosing"
            title="The party decides whether to press on or retreat."
            @click="emit('choose', 'auto')"
          >
            You Decide
          </button>
        </div>
      </div>
      <div v-if="summary && !loading && (summary.spells_left !== undefined || summary.heals_left !== undefined)" class="resources-line">
        <span
          v-if="summary.spells_left !== undefined"
          class="res-spells"
          title="Spells: Automatically dispatch enemies of a similar level to the caster."
        >{{ summary.spells_left }} {{ summary.spells_left === 1 ? 'spell' : 'spells' }} left</span>
        <span
          v-if="summary.heals_left !== undefined"
          class="res-cures"
          title="Cures: Heal a wounded adventurer after a fight."
        >{{ summary.heals_left }} {{ summary.heals_left === 1 ? 'cure' : 'cures' }} left</span>
      </div>

      <template v-if="summary && !loading">
        <!-- 3. This Event — the whole party; damage marked where it landed -->
        <div class="section section-divided">
          <div class="this-event-grid">
            <div class="grid-head">Party</div>
            <div class="grid-head num">Dmg</div>
            <div class="grid-head num">HP</div>
            <template v-for="row in eventRows" :key="row.member.name">
              <div class="cell name-cell" :class="{ 'row-dead': !row.member.alive }">
                <span class="member-name" :class="{ 'adv-dead': !row.member.alive }">{{ row.member.name }}</span>
                <span class="member-class">{{ row.member.adventurer_class }}</span>
              </div>
              <div class="cell num dmg-cell">
                <template v-if="row.damage > 0">−{{ row.damage }}</template>
              </div>
              <div class="cell num hp-cell">
                <div class="hp-track">
                  <div
                    class="hp-fill"
                    :style="{ width: hpPct(row.member) + '%', backgroundColor: hpColor(row.member) }"
                  ></div>
                </div>
                <span class="hp-label" :style="{ color: hpColor(row.member) }">
                  {{ row.member.alive ? row.member.hp_current : 0 }}/{{ row.member.hp_max }}
                </span>
              </div>
            </template>
          </div>

          <div class="ledger-footer">
            <span class="val-gold">{{ formatCurrency(summary.total_loot, summary.total_silver ?? 0, summary.total_copper ?? 0) }}</span>
            <span class="val-xp">{{ summary.total_xp }} XP</span>
            <span class="val-kills">{{ totalKills }} {{ totalKills === 1 ? 'kill' : 'kills' }}</span>
            <span v-if="summary.stairs_found" class="stairs-note">Stairs found!</span>
            <button class="log-toggle" @click="logOpen = !logOpen">
              Expedition Log {{ logOpen ? '▴' : '▾' }}
            </button>
          </div>
        </div>

        <!-- 4. Expedition Log disclosure: the So Far ledger + the full log -->
        <div v-if="logOpen" class="section">
          <div class="ledger-label-row">
            <span class="section-label">Expedition So Far</span>
            <span class="ledger-days">Days 1–{{ daysElapsed }}</span>
          </div>
          <div class="ledger-grid">
            <div class="grid-head">Adventurer</div>
            <div class="grid-head">HP</div>
            <div class="grid-head num">Dmg Dealt</div>
            <div class="grid-head num">Dmg Taken</div>
            <div class="grid-head num">Spells Cast</div>
            <div class="grid-head num">Damage Healed</div>
            <template v-for="row in ledgerRows" :key="row.member.name">
              <div class="cell name-cell" :class="{ 'row-dead': !row.member.alive }">
                <span class="member-name" :class="{ 'adv-dead': !row.member.alive }">{{ row.member.name }}</span>
                <span class="member-class">{{ row.member.adventurer_class }}</span>
              </div>
              <div class="cell hp-cell">
                <div class="hp-track">
                  <div
                    class="hp-fill"
                    :style="{ width: hpPct(row.member) + '%', backgroundColor: hpColor(row.member) }"
                  ></div>
                </div>
                <span class="hp-label" :style="{ color: hpColor(row.member) }">
                  {{ row.member.alive ? row.member.hp_current : 0 }}/{{ row.member.hp_max }}
                </span>
              </div>
              <div class="cell num dealt-cell">{{ row.dealt || '—' }}</div>
              <div class="cell num taken-cell">{{ row.taken || '—' }}</div>
              <div class="cell num spells-cell">{{ row.casts || '—' }}</div>
              <div class="cell num cures-cell">{{ row.healed || '—' }}</div>
            </template>
            <!-- Totals row -->
            <div class="cell totals-cell totals-label">Expedition total</div>
            <div class="cell totals-cell"></div>
            <div class="cell totals-cell num dealt-cell">{{ ledgerTotals.dealt }}</div>
            <div class="cell totals-cell num taken-cell">{{ ledgerTotals.taken }}</div>
            <div class="cell totals-cell num spells-cell">{{ ledgerTotals.casts }}</div>
            <div class="cell totals-cell num cures-cell">{{ ledgerTotals.healed }}</div>
          </div>

          <ExpeditionLogTree
            :turns="turns"
            :member-names="memberNames"
            :mark-current="true"
            class="log-block"
          />
        </div>
      </template>

    </div>
  </ModalDialog>
</template>

<style scoped>
.em-header {
  display: flex;
  align-items: baseline;
  gap: 10px;
  min-width: 0;
}

.em-title {
  font-size: 15px;
  font-weight: 700;
  color: #4ade80;
  margin: 0;
}

.em-meta {
  font-size: 11px;
  color: #6b7280;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.event-modal {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 2px 0;
}

/* 1. Event line */
.event-line {
  display: flex;
  align-items: flex-start;
  gap: 12px;
}

.event-badge {
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.08em;
  padding: 3px 8px;
  border-radius: 4px;
  white-space: nowrap;
  flex-shrink: 0;
  margin-top: 2px;
}

.badge-gold {
  color: #fbbf24;
  background: rgba(251, 191, 36, 0.15);
  border: 1px solid rgba(251, 191, 36, 0.3);
}

.badge-green {
  color: #4ade80;
  background: rgba(74, 222, 128, 0.15);
  border: 1px solid rgba(74, 222, 128, 0.3);
}

.badge-red {
  color: #ef4444;
  background: rgba(239, 68, 68, 0.15);
  border: 1px solid rgba(239, 68, 68, 0.3);
}

.event-narrative {
  font-size: 15px;
  line-height: 1.5;
  color: #e5e7eb;
  margin: 0;
  text-wrap: pretty;
}

.loading-text {
  text-align: center;
  color: #6b7280;
  font-size: 12px;
  padding: 12px 0;
}

/* Sections */
.section-divided {
  border-top: 1px solid #374151;
  padding-top: 10px;
}

.section-label {
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  color: #6b7280;
  font-weight: 600;
}

/* 2. This Event */
.this-event-grid {
  display: grid;
  grid-template-columns: 1fr 52px 132px;
  gap: 2px 8px;
  margin-top: 2px;
}

.grid-head {
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: #6b7280;
  padding-bottom: 4px;
  border-bottom: 1px solid #374151;
}

.grid-head.num {
  text-align: right;
}

.cell {
  display: flex;
  align-items: center;
  padding: 3px 0;
  border-bottom: 1px solid rgba(55, 65, 81, 0.5);
  min-width: 0;
}

.cell.num {
  justify-content: flex-end;
}

.name-cell {
  gap: 6px;
}

.member-name {
  font-size: 13px;
  color: #e5e7eb;
}

.member-class {
  font-size: 10px;
  color: #6b7280;
}

.dmg-cell {
  font-size: 13px;
  color: #ef4444;
}

.hp-cell {
  gap: 6px;
}

.hp-track {
  flex: 1;
  height: 6px;
  background: #0b1220;
  border-radius: 3px;
  overflow: hidden;
}

.hp-fill {
  height: 100%;
  border-radius: 3px;
  transition: width 0.3s ease;
}

.hp-label {
  font-size: 11px;
  white-space: nowrap;
}

/* 3. Ledger */
.ledger-section {
  border-top: 1px solid #374151;
  padding-top: 14px;
}

.ledger-label-row {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
}

.ledger-days {
  font-size: 10px;
  color: #6b7280;
}

.ledger-grid {
  display: grid;
  grid-template-columns: 1fr 106px 78px 78px 78px 78px;
  gap: 6px 8px;
  align-items: center;
  margin-top: 6px;
}

.ledger-grid .cell {
  padding: 3px 0;
}

.row-dead {
  opacity: 0.6;
}

.adv-dead {
  text-decoration: line-through;
  opacity: 0.7;
  color: #ef4444;
}

.dealt-cell {
  font-size: 13px;
  color: #4ade80;
}

.taken-cell {
  font-size: 13px;
  color: #ef4444;
}

.spells-cell {
  font-size: 13px;
  color: #60a5fa;
}

.cures-cell {
  font-size: 13px;
  color: #a78bfa;
}

.totals-cell {
  border-bottom: none;
  padding-top: 7px;
}

.totals-label {
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: #6b7280;
}

.totals-cell.num {
  font-size: 12px;
}

.muted {
  font-size: 11px;
  color: #6b7280;
}

/* Ledger footer */
.ledger-footer {
  display: flex;
  align-items: baseline;
  gap: 10px;
  font-size: 12px;
  margin-top: 6px;
}

.stairs-note {
  color: #fbbf24;
  font-weight: 700;
}

.val-gold {
  color: #fbbf24;
}

.val-xp {
  color: #60a5fa;
}

.val-kills {
  color: #4ade80;
}

/* Party resources */
.resources-line {
  display: flex;
  align-items: baseline;
  gap: 12px;
  font-size: 12px;
}

.res-spells {
  color: #60a5fa;
}

.res-cures {
  color: #a78bfa;
}

.log-toggle {
  margin-left: auto;
  background: none;
  border: none;
  font-family: var(--font-mono);
  font-size: 12px;
  color: #6b7280;
  text-decoration: underline;
  cursor: pointer;
  padding: 0;
}

.log-toggle:hover {
  color: #e5e7eb;
}

.log-block {
  margin-top: 8px;
}

/* 5. Decision block */
.decision-block {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 10px;
  border-top: 1px solid #374151;
  padding-top: 10px;
}

.decision-col {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.decide-btn {
  font-family: var(--font-mono);
  font-size: 13px;
  font-weight: 700;
  padding: 7px 12px;
  border-radius: 6px;
  text-align: center;
  width: 100%;
  cursor: pointer;
  background: none;
  border: 1px solid #4b5563;
  color: #d1d5db;
  transition: background-color 0.12s, border-color 0.12s, color 0.12s;
}

.decide-btn:hover:not(:disabled) {
  border-color: #4ade80;
  color: #e5e7eb;
}

.decide-btn.auto-hover:hover:not(:disabled) {
  border-color: #60a5fa;
}

.decide-btn.primary {
  background: #22c55e;
  border-color: #22c55e;
  color: #000;
}

.decide-btn.primary:hover:not(:disabled) {
  background: #4ade80;
  border-color: #4ade80;
  color: #000;
}

.decide-btn:disabled {
  opacity: 0.5;
  cursor: default;
}


.tpk-actions {
  display: flex;
  justify-content: center;
  border-top: 1px solid #374151;
  padding-top: 14px;
}
</style>
