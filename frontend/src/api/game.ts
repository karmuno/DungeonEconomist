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

export interface DungeonLevel {
  level: number
  name: string
  duration_days: number
  unlocked: boolean
}

export interface DungeonInfo {
  dungeon_name: string
  max_dungeon_level: number
  total_levels: number
  levels: DungeonLevel[]
}

export function getDungeonInfo(): Promise<DungeonInfo> {
  return get<DungeonInfo>('/dungeon/')
}

export interface MetricsLevel {
  level: number
  expeditions: number
  avg_gold: number
  avg_xp: number
  total_deaths: number
  deaths_per_run: number
}

export interface MetricsData {
  levels: MetricsLevel[]
  total_expeditions: number
}

export function getMetrics(): Promise<MetricsData> {
  return get<MetricsData>('/metrics')
}
