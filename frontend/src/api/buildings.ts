import { get, post } from './client'

export interface BuildingAssignedAdventurer {
  id: number
  name: string
  adventurer_class: string
  level: number
}

export interface BuildingData {
  id: number | null
  building_type: string
  name: string
  level: number
  max_level: number
  adventurer_class: string
  description: string
  assigned_bonus_desc: string
  effects: string[]
  max_assigned: number
  min_adventurer_level: number
  assigned_adventurers: BuildingAssignedAdventurer[]
  buy_cost?: number
  upgrade_cost: number | null
  next_name: string | null
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
