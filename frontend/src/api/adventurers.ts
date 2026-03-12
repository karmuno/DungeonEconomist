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
