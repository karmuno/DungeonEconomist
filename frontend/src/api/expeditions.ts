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
  dungeon_level?: number
  member_results: ExpeditionMemberResult[]
  total_loot: number
  total_xp: number
  events_log: unknown[]
  estimated_readiness_day: number | null
  pending_event?: PendingEvent | null
  turn_summaries?: string[]
}

export function getSummary(id: number): Promise<ExpeditionSummaryDetail> {
  return get<ExpeditionSummaryDetail>(`/expeditions/${id}/summary`)
}

export interface PendingEvent {
  type: string
  message: string
  options: string[]
  dead_member?: string
  loot_so_far?: number
  new_level?: number
  new_level_name?: string
}

export interface PendingEventResponse {
  pending: boolean
  expedition_id?: number
  party_name?: string
  pending_event?: PendingEvent
}

export interface ChoiceResponse {
  status: string
  retreated?: boolean
  auto_choice?: string | null
  pending_event?: PendingEvent
  events?: Array<{ type: string; message: string }>
}

export function getPending(id: number): Promise<PendingEventResponse> {
  return get<PendingEventResponse>(`/expeditions/${id}/pending`)
}

export function choose(id: number, choice: string): Promise<ChoiceResponse> {
  return post<ChoiceResponse>(`/expeditions/${id}/choose`, { choice })
}
