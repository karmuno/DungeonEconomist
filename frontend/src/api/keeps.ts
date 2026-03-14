import { get, post, del } from './client'
import type { KeepOut } from '../types'

export function list(): Promise<KeepOut[]> {
  return get<KeepOut[]>('/keeps/')
}

export function create(name: string): Promise<KeepOut> {
  return post<KeepOut>('/keeps/', { name })
}

export function deleteKeep(id: number): Promise<{ ok: boolean }> {
  return del<{ ok: boolean }>(`/keeps/${id}`)
}
