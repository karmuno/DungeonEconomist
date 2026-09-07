<script setup lang="ts">
import { computed, ref } from 'vue'
import { formatCurrency } from '../../utils/currency'
import { pluralMonster } from '../../types/expeditionLog'
import type { AttackEntry, RoundEntry, TurnLog } from '../../types/expeditionLog'

const props = defineProps<{
  turns: TurnLog[]
  memberNames: string[]
  // When true, the last event of the last turn is badged as the event that
  // opened the current modal, with its damage meta highlighted.
  markCurrent?: boolean
}>()

const pcNames = computed(() => new Set(props.memberNames))

// Turns are expanded by default; combats and rounds are collapsed.
const collapsedTurns = ref<Set<number>>(new Set())
const expandedCombats = ref<Set<string>>(new Set())
const expandedRounds = ref<Set<string>>(new Set())

function toggleTurn(turnNum: number) {
  if (collapsedTurns.value.has(turnNum)) {
    collapsedTurns.value.delete(turnNum)
  } else {
    collapsedTurns.value.add(turnNum)
  }
}

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

function sideAttacks(r: RoundEntry, side: 'party' | 'monsters'): AttackEntry[] {
  const all = r.halfling_pre_round ?? r.attacks ?? []
  return all.filter(a => side === 'party' ? pcNames.value.has(a.attacker) : !pcNames.value.has(a.attacker))
}

function plural(n: number, word: string): string {
  return `${n} ${word}${n === 1 ? '' : 's'}`
}

function sideSummary(attacks: AttackEntry[]): string {
  if (!attacks.length) return '—'
  const hits = attacks.filter(a => a.hit)
  const dmg = hits.reduce((s, a) => s + a.damage, 0)
  return `${plural(attacks.length, 'attack')} · ${plural(hits.length, 'hit')} · ${dmg} dmg`
}

function attackLine(atk: AttackEntry): string {
  const verb = atk.target_died ? 'slays' : atk.hit ? 'hits' : 'misses'
  const dmg = atk.hit ? ` · ${atk.damage} dmg` : ''
  if (atk.attack_bonus == null || atk.target_ac == null) {
    // Logs written before the d20-style fields existed
    return `${atk.attacker} ${verb} ${atk.target} · roll ${atk.roll} vs ${atk.needed}${dmg}`
  }
  const bonus = atk.attack_bonus < 0 ? `− ${Math.abs(atk.attack_bonus)}` : `+ ${atk.attack_bonus}`
  return `${atk.attacker} ${verb} ${atk.target} · ${atk.roll} ${bonus} To-Hit vs ${atk.target_ac} Armor Class${dmg}`
}

function roundLabel(r: RoundEntry): string {
  if (r.event === 'spell') return `${r.caster} casts ${r.spell} — ${r.monsters_destroyed} destroyed`
  if (r.halfling_pre_round) {
    return `Sling Volley – ${sideSummary(r.halfling_pre_round)}`
  }
  const initiative = r.initiative_winner ?? r.initiative
  const label = initiative === 'party' ? 'party first' : initiative === 'monsters' ? 'monsters first' : 'simultaneous'
  const base = `Round ${r.round} (${label})`
  if (r.spell_casts?.length) {
    const s = r.spell_casts[0]
    return `${base} — ${s.caster} casts ${s.spell}`
  }
  return base
}

function roundMeta(r: RoundEntry): string {
  if (r.event === 'spell') return ''
  if (r.cleric_turns?.length) return turnUndeadSummary(r.cleric_turns)
  const party = sideSummary(sideAttacks(r, 'party'))
  const monsters = sideSummary(sideAttacks(r, 'monsters'))
  return `Party – ${party} · Monsters – ${monsters}`
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

function outcomeClass(outcome: string): string {
  if (outcome === 'Clear Victory' || outcome === 'Victory') return 'outcome-success'
  if (outcome === 'Tough Fight') return 'outcome-warning'
  return 'outcome-danger'
}

function combatMeta(turn: TurnLog, idx: number): string {
  const c = turn.events[idx]?.combat
  if (!c) return ''
  const parts = [`${c.hp_lost} HP lost`, `+${c.xp_earned} XP`]
  if (c.monsters_killed) parts.push(`${c.monsters_killed} killed`)
  if (c.monsters_fled) parts.push(`${c.monsters_fled} fled`)
  if (c.party_fled) parts.push('party fled')
  return parts.join(' · ')
}

function trapMeta(turn: TurnLog, idx: number): string {
  const ev = turn.events[idx]
  if (!ev?.trap_damage) return ''
  return `−${ev.trap_damage} HP`
}

const lastTurnNum = computed(() => props.turns.length ? props.turns[props.turns.length - 1].turn : -1)

function isCurrentEvent(turn: TurnLog, idx: number): boolean {
  return !!props.markCurrent && turn.turn === lastTurnNum.value && idx === turn.events.length - 1
}
</script>

<template>
  <div class="log-tree">
    <div v-for="turn in turns" :key="turn.turn" class="turn-block">
      <div class="log-row turn-row" @click="toggleTurn(turn.turn)">
        <span class="caret">{{ collapsedTurns.has(turn.turn) ? '▶' : '▼' }}</span>
        <span class="turn-label">Turn {{ turn.turn }}</span>
      </div>
      <template v-if="!collapsedTurns.has(turn.turn)">
        <template v-for="(event, idx) in turn.events" :key="idx">
          <!-- Combat event -->
          <template v-if="event.combat">
            <div class="log-row event-row expandable" @click="toggleCombat(turn.turn, idx)">
              <span class="caret">{{ isCombatExpanded(turn.turn, idx) ? '▼' : '▶' }}</span>
              <span class="event-label">
                Encountered {{ pluralMonster(event.combat.monster_type, event.combat.monster_count ?? 1) }}
              </span>
              <span :class="['outcome-badge', outcomeClass(event.combat.outcome)]">{{ event.combat.outcome }}</span>
              <span v-if="isCurrentEvent(turn, idx)" class="current-badge">This event</span>
              <span class="row-meta" :class="{ 'meta-danger': isCurrentEvent(turn, idx) }">{{ combatMeta(turn, idx) }}</span>
            </div>
            <template v-if="isCombatExpanded(turn.turn, idx)">
              <template v-if="event.combat.round_log?.length">
                <template v-for="(r, ri) in event.combat.round_log" :key="ri">
                  <div class="log-row round-row expandable" @click="toggleRound(turn.turn, idx, ri, $event)">
                    <span class="caret">{{ isRoundExpanded(turn.turn, idx, ri) ? '▼' : '▶' }}</span>
                    <span class="round-label">{{ roundLabel(r) }}</span>
                    <span class="row-meta">{{ roundMeta(r) }}</span>
                    <template v-if="r.morale_checks?.length">
                      <span
                        v-for="(mc, mi) in r.morale_checks"
                        :key="mi"
                        :class="['morale-tag', mc.passed ? '' : 'morale-break']"
                      >
                        {{ mc.side }} morale {{ mc.passed ? 'holds' : 'breaks' }}
                      </span>
                    </template>
                  </div>
                  <template v-if="isRoundExpanded(turn.turn, idx, ri)">
                    <div v-if="r.event === 'spell'" class="log-row attack-row">
                      {{ r.caster }} casts {{ r.spell }} — {{ r.monsters_destroyed }} destroyed
                    </div>
                    <template v-else>
                      <div v-for="(sc, si) in (r.spell_casts ?? [])" :key="'sc' + si" class="log-row attack-row">
                        {{ sc.caster }} casts {{ sc.spell }}<template v-if="sc.scroll_used"> from a scroll</template> · {{ sc.monsters_destroyed }} destroyed
                      </div>
                      <template v-for="(ct, cti) in (r.cleric_turns ?? [])" :key="'ct' + cti">
                        <div
                          v-for="(tl, tli) in ct.turn_log"
                          :key="'tl' + tli"
                          class="log-row attack-row"
                        >
                          {{ ct.cleric }} → {{ tl.monster }} · {{ tl.result }}<template v-if="tl.roll"> · roll {{ tl.roll }} vs {{ tl.needed }}</template>
                        </div>
                      </template>
                      <div
                        v-for="(atk, ai) in (r.halfling_pre_round ?? r.attacks ?? [])"
                        :key="'a' + ai"
                        class="log-row attack-row"
                      >
                        {{ attackLine(atk) }}
                      </div>
                    </template>
                  </template>
                </template>
              </template>
              <div v-else class="log-row attack-row">{{ event.combat.rounds_fought ?? 0 }} round(s) fought</div>
              <div
                v-for="(h, hi) in (event.combat.healed_adventurers ?? [])"
                :key="'h' + hi"
                class="log-row attack-row heal-line"
              >
                ✚ {{ h.name }} healed for {{ h.hp }} HP<template v-if="h.healer"> by {{ h.healer }}</template>
              </div>
              <div
                v-for="(rv, rvi) in (event.combat.revivals ?? [])"
                :key="'rv' + rvi"
                class="log-row attack-row heal-line"
              >
                ✚ {{ rv.name }} {{ rv.source === 'potion' ? 'drinks a Cure Light Wounds potion and gets back up' : `is revived by ${rv.healer}` }} · {{ rv.hp }} HP
              </div>
            </template>
          </template>
          <!-- Trap event -->
          <div v-else-if="event.trap_damage" class="log-row event-row">
            <span class="caret">·</span>
            <span class="event-label">
              Trap — {{ (event.trap_victims ?? []).filter(v => v.damage > 0).map(v => `${v.name} −${v.damage}`).join(', ') || `${event.trap_damage} damage` }}
            </span>
            <span v-if="isCurrentEvent(turn, idx)" class="current-badge">This event</span>
            <span class="row-meta" :class="{ 'meta-danger': isCurrentEvent(turn, idx) }">{{ trapMeta(turn, idx) }}</span>
          </div>
          <!-- Treasure event -->
          <div v-else-if="event.treasure" class="log-row event-row">
            <span class="caret">·</span>
            <span class="event-label">Found treasure</span>
            <span v-if="isCurrentEvent(turn, idx)" class="current-badge">This event</span>
            <span class="row-meta meta-gold">
              {{ formatCurrency(event.treasure.gold, event.treasure.silver ?? 0, event.treasure.copper ?? 0) }}
            </span>
          </div>
          <!-- Anything else -->
          <div v-else class="log-row event-row">
            <span class="caret">·</span>
            <span class="event-label">{{ event.type }}</span>
            <span v-if="isCurrentEvent(turn, idx)" class="current-badge">This event</span>
          </div>
        </template>
        <div v-for="dead in (turn.deaths ?? [])" :key="dead" class="log-row event-row death-row">
          <span class="caret">·</span>
          <span class="event-label"><strong>{{ dead }}</strong> has fallen</span>
        </div>
      </template>
    </div>
  </div>
</template>

<style scoped>
.log-tree {
  border: 1px solid #374151;
  border-radius: 6px;
  background: #1a1a1a;
  padding: 8px 10px;
  font-family: var(--font-mono);
}

.log-row {
  display: flex;
  align-items: baseline;
  gap: 8px;
  padding: 3px 4px;
  border-radius: 3px;
}

.log-row.expandable {
  cursor: pointer;
}

.log-row:hover {
  background: rgba(74, 222, 128, 0.04);
}

.caret {
  width: 10px;
  flex-shrink: 0;
  font-size: 9px;
  color: #6b7280;
}

.turn-label {
  font-size: 11px;
  font-weight: 700;
  color: #4ade80;
}

.event-row {
  padding-left: 14px;
}

.event-label {
  font-size: 11.5px;
  color: #e5e7eb;
}

.round-row {
  padding-left: 32px;
  flex-wrap: wrap; /* the summary and morale tags drop to a second line rather than squeezing the label */
}

.round-label {
  font-size: 11px;
  color: #d1d5db;
  white-space: nowrap;
}

.attack-row {
  padding-left: 50px;
  font-size: 10.5px;
  color: #6b7280;
}

.row-meta {
  margin-left: auto;
  font-size: 10.5px;
  color: #6b7280;
  white-space: nowrap;
}

.meta-danger {
  color: #ef4444;
}

.meta-gold {
  color: #fbbf24;
}

.outcome-badge {
  font-size: 9.5px;
  font-weight: 700;
  letter-spacing: 0.06em;
  padding: 1px 6px;
  border-radius: 4px;
  white-space: nowrap;
}

.outcome-success {
  background: rgba(74, 222, 128, 0.15);
  color: #4ade80;
}

.outcome-warning {
  background: rgba(251, 191, 36, 0.15);
  color: #fbbf24;
}

.outcome-danger {
  background: rgba(239, 68, 68, 0.15);
  color: #ef4444;
}

.current-badge {
  font-size: 9.5px;
  font-weight: 700;
  letter-spacing: 0.06em;
  padding: 1px 6px;
  border-radius: 4px;
  background: rgba(251, 191, 36, 0.15);
  color: #fbbf24;
  border: 1px solid rgba(251, 191, 36, 0.3);
  white-space: nowrap;
}

.morale-tag {
  font-size: 10px;
  color: #6b7280;
}

.morale-break {
  color: #fbbf24;
}

.heal-line {
  color: #4ade80;
}

.death-row .event-label {
  color: #ef4444;
}

.death-row strong {
  text-decoration: line-through;
  opacity: 0.7;
}
</style>
