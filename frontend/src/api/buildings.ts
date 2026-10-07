import { get, post } from './client'

export interface BuildingAssignedAdventurer {
  id: number
  name: string
  adventurer_class: string
  level: number
}

export interface BuildingStatLine {
  /** What the building delivers now, e.g. "+2"; null when it is not built. */
  value: string | null
  /** The words after the value, e.g. "to-hit in combat". */
  phrase: string
  /** What one more assigned adventurer adds, e.g. "+1"; null for the standing XP line. */
  rate: string | null
  /** Whether anyone currently counts toward it. */
  active: boolean
}

export interface BuildingTierSlot {
  tier: number
  slots: number
  min_level: number
}

export interface BuildingData {
  id: number | null
  building_type: string
  name: string
  level: number
  max_level: number
  adventurer_class: string
  allowed_classes?: string[]
  description: string
  assigned_bonus_desc: string
  effects?: string[]
  max_assigned: number
  min_adventurer_level: number
  tier_slots?: BuildingTierSlot[]
  assigned_adventurers: BuildingAssignedAdventurer[]
  buy_cost?: number
  upgrade_cost: number | null
  next_name: string | null
  slots_total?: number
  slots_free?: number
  current_stats: BuildingStatLine[]
  next_stats: BuildingStatLine[] | null
}

export function list(): Promise<BuildingData[]> {
  return get<BuildingData[]>('/buildings/')
}

export function buy(building_type: string): Promise<BuildingData> {
  return post<BuildingData>('/buildings/buy', { building_type })
}

export function upgrade(buildingId: number): Promise<BuildingData> {
  return post<BuildingData>(`/buildings/${buildingId}/upgrade`)
}

export function assign(buildingId: number, adventurerId: number): Promise<BuildingData> {
  return post<BuildingData>(`/buildings/${buildingId}/assign`, { adventurer_id: adventurerId })
}

export function unassign(buildingId: number, adventurerId: number): Promise<BuildingData> {
  return post<BuildingData>(`/buildings/${buildingId}/unassign`, { adventurer_id: adventurerId })
}
