import { get, post } from './client'
import type { ExpeditionResult, ExpeditionSummary, ExpeditionCreate } from '../types'

export function list(): Promise<ExpeditionSummary[]> {
  return get<ExpeditionSummary[]>('/expeditions/')
}

export function getById(id: number): Promise<ExpeditionResult> {
  return get<ExpeditionResult>(`/expeditions/${id}`)
}

export function launch(data: ExpeditionCreate): Promise<ExpeditionSummary> {
  return post<ExpeditionSummary>('/expeditions/', data)
}

export interface ExpeditionMemberResult {
  name: string
  adventurer_class: string
  level: number
  alive: boolean
  hp_current: number
  hp_max: number
  xp_gained: number
  gold: number
  silver: number
  copper: number
}

export interface ExpeditionSummaryDetail {
  expedition_id: number
  party_id: number
  party_name: string
  start_day: number
  return_day: number
  duration_days: number
  result: string
  member_results: ExpeditionMemberResult[]
  total_loot: number
  total_xp: number
  events_log: unknown[]
  estimated_readiness_day: number
}

export function getSummary(id: number): Promise<ExpeditionSummaryDetail> {
  return get<ExpeditionSummaryDetail>(`/expeditions/${id}/summary`)
}
