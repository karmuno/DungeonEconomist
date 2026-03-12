import { get, post } from './client'
import type { EquipmentOut } from '../types'

export function list(): Promise<EquipmentOut[]> {
  return get<EquipmentOut[]>('/equipment/')
}

export function assign(data: {
  adventurer_id: number
  equipment_id: number
  quantity?: number
}): Promise<unknown> {
  return post('/equipment/assign', data)
}
