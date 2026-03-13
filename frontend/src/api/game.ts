import { get, post, put } from './client'
import type { GameTimeInfo, AdvanceDayResult, DashboardStats } from '../types'

export function getTime(): Promise<GameTimeInfo> {
  return get<GameTimeInfo>('/time/')
}

export function advanceDay(): Promise<AdvanceDayResult> {
  return post<AdvanceDayResult>('/time/advance-day')
}

export function runUpkeep(): Promise<unknown> {
  return put('/upkeep')
}

export function getDashboardStats(): Promise<DashboardStats> {
  return get<DashboardStats>('/dashboard/stats')
}
