// Enums

export enum AdventurerClass {
  FIGHTER = 'Fighter',
  CLERIC = 'Cleric',
  MAGIC_USER = 'Magic-User',
  ELF = 'Elf',
  DWARF = 'Dwarf',
  HOBBIT = 'Hobbit',
}

export enum EquipmentType {
  WEAPON = 'Weapon',
  ARMOR = 'Armor',
  SHIELD = 'Shield',
  MAGIC_ITEM = 'Magic Item',
  POTION = 'Potion',
  TOOL = 'Tool',
  MISCELLANEOUS = 'Miscellaneous',
}

export enum SupplyType {
  FOOD = 'Food',
  WATER = 'Water',
  LIGHT = 'Light',
  MEDICAL = 'Medical',
  TOOL = 'Tool',
  ADVENTURE = 'Adventure',
  MISCELLANEOUS = 'Miscellaneous',
}

// Equipment

export interface EquipmentOut {
  id: number
  name: string
  type: EquipmentType
  cost: number
  weight: number
  description?: string
}

export interface AdventurerEquipmentOut {
  equipment: EquipmentOut
  equipped: boolean
  quantity: number
}

// Supplies

export interface SupplyOut {
  id: number
  name: string
  type: SupplyType
  cost: number
  weight: number
  description?: string
}

export interface PartySupplyOut {
  supply: SupplyOut
  quantity: number
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
  is_available: boolean
  on_expedition: boolean
  expedition_status?: string | null
  healing_until_day?: number | null
  carry_capacity: number
  is_bankrupt: boolean
  equipment?: AdventurerEquipmentOut[] | null
  next_level_xp?: number | null
  xp_progress?: number | null
}

export interface AdventurerCreate {
  name: string
  adventurer_class: AdventurerClass
  level?: number
  hp_max?: number
  carry_capacity?: number | null
}

export interface AdventurerLevelUpInfo {
  id: number
  name: string
  current_level: number
  next_level: number
}

// Players

export interface PlayerOut {
  id: number
  name: string
  treasury: number
  total_score: number
}

export interface PlayerCreate {
  name: string
}

// Parties

export interface PartyCreate {
  name: string
  funds?: number
  player_id?: number | null
}

export interface PartyOut {
  id: number
  name: string
  created_at?: string | null
  on_expedition: boolean
  current_expedition_id?: number | null
  funds: number
  player_id?: number | null
  members: AdventurerOut[]
  supplies?: PartySupplyOut[] | null
}

export interface PartyMemberOperation {
  party_id: number
  adventurer_id: number
}

export interface PartyFundsUpdate {
  amount: number
}

export interface SupplyOperation {
  party_id: number
  supply_id: number
  quantity?: number
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

export interface GameTimeInfo {
  current_day: number
  day_started_at: string
  last_updated: string
}

// Expeditions

export interface ExpeditionCreate {
  party_id: number
  dungeon_level?: number
  duration_days?: number
  supplies_to_bring?: Array<Record<string, number>> | null
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
  supplies_consumed?: Record<string, number> | null
  equipment_lost?: Record<string, number[]> | null
  dead_members: string[]
  party_status: PartyStatus
  log: unknown[]
  party_members_ready_for_level_up?: AdventurerLevelUpInfo[] | null
}

// Dashboard

export interface DashboardStats {
  adventurer_count: number
  party_count: number
  expedition_count: number
  treasury: number
  total_score: number
  current_day: number
  active_expeditions: Array<{
    id: number
    party_id: number
    start_day: number
    return_day: number
    result: string
  }>
  recent_expeditions: Array<{
    id: number
    party_id: number
    start_day: number
    return_day: number
    duration_days: number
    result: string
    started_at: string | null
    finished_at: string | null
  }>
}
