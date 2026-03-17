// Enums

export enum AdventurerClass {
  FIGHTER = 'Fighter',
  CLERIC = 'Cleric',
  MAGIC_USER = 'Magic-User',
  ELF = 'Elf',
  DWARF = 'Dwarf',
  HOBBIT = 'Hobbit',
}

// Auth

export interface TokenResponse {
  access_token: string
  token_type: string
}

export interface AccountOut {
  id: number
  username: string
  is_admin: boolean
}

// Keeps

export interface KeepOut {
  id: number
  name: string
  treasury_gold: number
  treasury_silver: number
  treasury_copper: number
  total_score: number
  current_day: number
  day_started_at: string
  last_updated: string
  created_at: string
}

// Adventurers

export interface LevelUpResult {
  old_level: number
  new_level: number
  hp_gained: number
  next_level_xp?: number | null
  class_bonuses: Record<string, unknown>
}

export interface AdventurerOut {
  id: number
  name: string
  adventurer_class: AdventurerClass
  level: number
  xp: number
  hp_current: number
  hp_max: number
  gold: number
  silver: number
  copper: number
  is_available: boolean
  on_expedition: boolean
  is_assigned: boolean
  is_bankrupt: boolean
  is_dead: boolean
  death_day?: number | null
  death_party_name?: string | null
  bankruptcy_day?: number | null
  magic_items: Array<{ id: number; name: string; item_type: string; bonus: number }>
  next_level_xp?: number | null
  xp_progress?: number | null
}

export interface AdventurerCreate {
  name: string
  adventurer_class: AdventurerClass
  level?: number
  hp_max?: number
}

export interface AdventurerLevelUpInfo {
  id: number
  name: string
  current_level: number
  next_level: number
}

// Parties

export interface PartyCreate {
  name: string
}

export interface PartyOut {
  id: number
  name: string
  created_at?: string | null
  on_expedition: boolean
  current_expedition_id?: number | null
  keep_id?: number | null
  auto_delve_healed: boolean
  auto_delve_full: boolean
  auto_decide_events: boolean
  members: AdventurerOut[]
}

export interface PartyMemberOperation {
  party_id: number
  adventurer_id: number
}

export interface PartyStatus {
  members_total: number
  members_alive: number
  members_dead: number
  hp_current: number
  hp_max: number
  hp_percentage: number
}

// Game Time

export interface GameEvent {
  type: 'recruitment' | 'healing' | 'expedition_complete' | 'auto_start' | 'upkeep' | string
  message: string
  expedition_id?: number | null
}

export interface GameTimeInfo {
  current_day: number
  day_started_at: string
  last_updated: string
}

export interface AdvanceDayResult {
  current_day: number
  day_started_at: string
  last_updated: string
  events: GameEvent[]
}

// Expeditions

export interface ExpeditionSummary {
  id: number
  party_id: number
  party_name: string
  dungeon_level: number
  start_day: number
  duration_days: number
  return_day: number
  result: string
  treasure_total: number
  xp_earned: number
  started_at: string | null
  finished_at: string | null
}

export interface ExpeditionCreate {
  party_id: number
  dungeon_level?: number
}

export interface ExpeditionResult {
  expedition_id: number
  party_id: number
  dungeon_level: number
  turns: number
  start_day: number
  duration_days: number
  return_day: number
  start_time: string
  end_time?: string | null
  treasure_total: number
  special_items: string[]
  xp_earned: number
  xp_per_party_member: number
  resources_used: Record<string, unknown>
  dead_members: string[]
  party_status: PartyStatus
  log: unknown[]
  party_members_ready_for_level_up?: AdventurerLevelUpInfo[] | null
}

// Dashboard

export interface DashboardStats {
  adventurer_count: number
  graveyard_count: number
  debtors_prison_count: number
  party_count: number
  expedition_count: number
  treasury_gold: number
  treasury_silver: number
  treasury_copper: number
  total_score: number
  current_day: number
  dungeon_name: string | null
  max_dungeon_level: number
  buildings: Array<{
    id: number
    building_type: string
    name: string
    level: number
    adventurer_class: string
    assigned_count: number
    effects: string[]
    assigned_adventurers: Array<{
      id: number
      name: string
      adventurer_class: string
      level: number
      hp_current: number
      hp_max: number
      xp: number
      next_level_xp: number | null
      gold: number
      silver: number
      copper: number
      magic_items: Array<{ id: number; name: string; item_type: string; bonus: number }>
    }>
  }>
  parties: Array<{
    id: number
    name: string
    member_count: number
    status: string
    expedition_id: number | null
    auto_delve_healed: boolean
    auto_delve_full: boolean
    auto_decide_events: boolean
    members: Array<{
      id: number
      name: string
      adventurer_class: string
      level: number
      hp_current: number
      hp_max: number
      xp: number
      next_level_xp: number | null
      gold: number
      silver: number
      copper: number
      magic_items: Array<{ id: number; name: string; item_type: string; bonus: number }>
    }>
  }>
  unassigned_adventurers: Array<{
    id: number
    name: string
    adventurer_class: string
    level: number
    hp_current: number
    hp_max: number
    xp: number
    next_level_xp: number | null
    gold: number
    silver: number
    copper: number
    magic_items: Array<{ id: number; name: string; item_type: string; bonus: number }>
  }>
  hint: string | null
  active_expeditions: Array<{
    id: number
    party_name: string
    dungeon_level: number
    start_day: number
    return_day: number
    duration_days: number
    days_elapsed: number
    result: string
  }>
  recent_expeditions: Array<{
    id: number
    party_name: string
    dungeon_level: number
    start_day: number
    return_day: number
    duration_days: number
    result: string
    treasure_total: number
    xp_earned: number
  }>
}
