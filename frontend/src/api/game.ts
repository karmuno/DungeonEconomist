import { get, post, put } from './client'
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

export function runUpkeep(): Promise<unknown> {
  return put('/upkeep')
}

export function getDashboardStats(): Promise<DashboardStats> {
  return get<DashboardStats>('/dashboard/stats')
}

export interface GameStatus {
  exists: boolean
  keep_name: string | null
}

export function getGameStatus(): Promise<GameStatus> {
  return get<GameStatus>('/game/status')
}

export function newGame(keepName?: string): Promise<{ current_day: number; keep_name: string }> {
  return post('/game/new', keepName ? { keep_name: keepName } : {})
}
