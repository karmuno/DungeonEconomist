import { get, post } from './client'
import type { GameTimeInfo, AdvanceDayResult, DashboardStats } from '../types'

export function getTime(): Promise<GameTimeInfo> {
  return get<GameTimeInfo>('/time/')
}

export function advanceDay(): Promise<AdvanceDayResult> {
  return post<AdvanceDayResult>('/time/advance-day')
}

export function skipToEvent(): Promise<AdvanceDayResult> {
  return post<AdvanceDayResult>('/time/skip-to-event')
}

export function getDashboardStats(): Promise<DashboardStats> {
  return get<DashboardStats>('/dashboard/stats')
}
