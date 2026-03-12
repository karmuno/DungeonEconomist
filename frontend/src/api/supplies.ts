import { get } from './client'
import type { SupplyOut } from '../types'

export function list(typeFilter?: string): Promise<SupplyOut[]> {
  const params = typeFilter ? `?type_filter=${encodeURIComponent(typeFilter)}` : ''
  return get<SupplyOut[]>(`/supplies/${params}`)
}

export function getById(id: number): Promise<SupplyOut> {
  return get<SupplyOut>(`/supplies/${id}`)
}
