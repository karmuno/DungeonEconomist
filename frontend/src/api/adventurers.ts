import { get, post } from './client'
import type { AdventurerOut, AdventurerCreate, LevelUpResult } from '../types'

export function list(): Promise<AdventurerOut[]> {
  return get<AdventurerOut[]>('/adventurers/')
}

export function getById(id: number): Promise<AdventurerOut> {
  return get<AdventurerOut>(`/adventurers/${id}`)
}

export function create(data: AdventurerCreate): Promise<AdventurerOut> {
  return post<AdventurerOut>('/adventurers/', data)
}

export function levelUp(id: number): Promise<LevelUpResult> {
  return post<LevelUpResult>(`/adventurers/${id}/level-up`)
}

export interface GraveyardEntry {
  id: number
  name: string
  class: string
  level: number
  death_day: number
}

export interface DebtorEntry {
  id: number
  name: string
  class: string
  level: number
  bankruptcy_day: number
}

export function getGraveyard(): Promise<GraveyardEntry[]> {
  return get<GraveyardEntry[]>('/adventurers/graveyard')
}

export function getDebtorsPrison(): Promise<DebtorEntry[]> {
  return get<DebtorEntry[]>('/adventurers/debtors-prison')
}
