// Shared shapes for the expedition events_log payload, used by the
// Expedition Event modal and the Expedition Summary view.

export interface AttackEntry {
  attacker: string
  target: string
  roll: number
  needed: number
  /** d20-style view of the same check (newer logs only): roll + attack_bonus >= target_ac */
  attack_bonus?: number
  target_ac?: number
  hit: boolean
  damage: number
  target_died: boolean
}

export interface TurnUndeadEntry {
  monster: string
  result: 'destroyed' | 'turned' | 'resisted'
  roll?: number
  needed?: number
}

export interface SpellCastEntry {
  caster: string
  spell: string
  monsters_destroyed: number
  /** True when the cast consumed a scroll rather than a memorised spell */
  scroll_used?: boolean
}

/** A fallen adventurer brought back after a fight, by a potion they held or by a Cleric */
export interface RevivalEntry {
  name: string
  hp: number
  healer: string
  source: 'potion' | 'cleric'
}

export interface MoraleCheck {
  side: string
  roll: number
  morale: number
  passed: boolean
}

/** One thing that happened in a round, in the order it resolved. */
export type RoundEvent =
  | ({ kind: 'turn_undead'; cleric: string; turn_log: TurnUndeadEntry[]; message?: string })
  | ({ kind: 'spell' } & SpellCastEntry)
  | { kind: 'attacks'; side: 'party' | 'monsters'; label?: string; attacks: AttackEntry[] }
  | ({ kind: 'morale' } & MoraleCheck)
  | ({ kind: 'revival' } & RevivalEntry)
  | { kind: 'heal'; name: string; hp: number; healer?: string }

export interface RoundEntry {
  round: number
  initiative?: string
  initiative_winner?: string
  /**
   * The round as one ordered list. Rounds recorded before this existed carry the
   * `attacks` / `spell_casts` / `cleric_turns` buckets below instead, whose order
   * the renderer had to reconstruct — and got wrong. Read `events` when present.
   */
  events?: RoundEvent[]
  // --- buckets, for expeditions stored before the ordered log ---
  event?: string
  caster?: string
  spell?: string
  monsters_destroyed?: number
  halfling_pre_round?: AttackEntry[]
  attacks?: AttackEntry[]
  morale_checks?: MoraleCheck[]
  cleric_turn?: { cleric: string; turn_log: TurnUndeadEntry[] }
  cleric_turns?: Array<{ cleric: string; turn_log: TurnUndeadEntry[] }>
  spell_casts?: SpellCastEntry[]
}

export interface CombatEvent {
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
  healed_adventurers?: Array<{ name: string; hp: number; healer?: string }>
  revivals?: RevivalEntry[]
  round_log?: RoundEntry[]
}

export interface TurnEvent {
  type: string
  combat?: CombatEvent
  treasure?: { gold: number; silver: number; copper: number; xp_value: number; name: string }
  trap_damage?: number
  trap_victims?: Array<{ name: string; damage: number }>
}

export interface TurnLog {
  turn: number
  deaths?: string[]
  events: TurnEvent[]
}

export function pluralMonster(name: string, count: number): string {
  if (count <= 1) return name
  if (name.endsWith('f')) return `${count} ${name.slice(0, -1)}ves`
  if (name.endsWith('fe')) return `${count} ${name.slice(0, -2)}ves`
  return `${count} ${name}s`
}


/** Every attack in a round, ordered log or old buckets alike. */
export function roundAttacks(r: RoundEntry): AttackEntry[] {
  if (r.events) {
    return r.events.flatMap(ev => (ev.kind === 'attacks' ? ev.attacks : []))
  }
  return r.halfling_pre_round ?? r.attacks ?? []
}

/** Every spell cast in a round, ordered log or old buckets alike. */
export function roundSpellCasts(r: RoundEntry): SpellCastEntry[] {
  if (r.events) {
    return r.events.filter(ev => ev.kind === 'spell') as SpellCastEntry[]
  }
  const casts = [...(r.spell_casts ?? [])]
  if (r.event === 'spell' && r.caster && r.spell) {
    casts.push({ caster: r.caster, spell: r.spell, monsters_destroyed: r.monsters_destroyed ?? 0 })
  }
  return casts
}

/** Morale checks for a round, ordered log or old buckets alike. */
export function roundMoraleChecks(r: RoundEntry): MoraleCheck[] {
  if (r.events) {
    return r.events.filter(ev => ev.kind === 'morale') as MoraleCheck[]
  }
  return r.morale_checks ?? []
}
