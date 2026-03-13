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
