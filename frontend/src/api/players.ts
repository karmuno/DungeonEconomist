import { get, post } from './client'
import type { PlayerOut, PlayerCreate } from '../types'

export function list(): Promise<PlayerOut[]> {
  return get<PlayerOut[]>('/players/')
}

export function create(data: PlayerCreate): Promise<PlayerOut> {
  return post<PlayerOut>('/players/', data)
}
