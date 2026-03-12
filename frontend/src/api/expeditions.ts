import { get, post } from './client'
import type { ExpeditionResult, ExpeditionCreate } from '../types'

export function list(): Promise<ExpeditionResult[]> {
  return get<ExpeditionResult[]>('/expeditions/')
}

export function getById(id: number): Promise<ExpeditionResult> {
  return get<ExpeditionResult>(`/expeditions/${id}`)
}

export function launch(data: ExpeditionCreate): Promise<ExpeditionResult> {
  return post<ExpeditionResult>('/expeditions/', data)
}
