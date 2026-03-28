import { get, post } from './client'
import type { AdventurerOut, AdventurerCreate, LevelUpResult } from '../types'

export function list(includeAll = false): Promise<AdventurerOut[]> {
  const params = includeAll ? '?include_all=true' : ''
  return get<AdventurerOut[]>(`/adventurers/${params}`)
}

export function getById(id: number): Promise<AdventurerOut> {
  return get<AdventurerOut>(`/adventurers/${id}`)
}

export function getByName(name: string): Promise<AdventurerOut> {
  return get<AdventurerOut>(`/adventurers/by-name/${encodeURIComponent(name)}`)
}

export function create(data: AdventurerCreate): Promise<AdventurerOut> {
  return post<AdventurerOut>('/adventurers/', data)
}

export function levelUp(id: number): Promise<LevelUpResult> {
  return post<LevelUpResult>(`/adventurers/${id}/level-up`)
}

export function getGraveyard(): Promise<AdventurerOut[]> {
  return get<AdventurerOut[]>('/adventurers/graveyard')
}

export function getDebtorsPrison(): Promise<AdventurerOut[]> {
  return get<AdventurerOut[]>('/adventurers/debtors-prison')
}
