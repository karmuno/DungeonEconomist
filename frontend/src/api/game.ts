import { get, post, put } from './client'
import type { GameTimeInfo, DashboardStats } from '../types'

export function getTime(): Promise<GameTimeInfo> {
  return get<GameTimeInfo>('/time/')
}

export function advanceDay(): Promise<GameTimeInfo> {
  return post<GameTimeInfo>('/time/advance-day')
}

export function runUpkeep(): Promise<unknown> {
  return put('/upkeep')
}

export function getDashboardStats(): Promise<DashboardStats> {
  return get<DashboardStats>('/dashboard/stats')
}
