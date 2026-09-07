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

export interface RoundEntry {
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
