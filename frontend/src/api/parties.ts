import { get, post, put, del } from './client'
import type {
  PartyOut,
  PartyCreate,
  PartyMemberOperation,
  PartyFundsUpdate,
  SupplyOperation,
  PartyStatus,
} from '../types'

export function list(): Promise<PartyOut[]> {
  return get<PartyOut[]>('/parties/')
}

export function getById(id: number): Promise<PartyOut> {
  return get<PartyOut>(`/parties/${id}`)
}

export function create(data: PartyCreate): Promise<PartyOut> {
  return post<PartyOut>('/parties/', data)
}

export function update(id: number, data: PartyCreate): Promise<PartyOut> {
  return put<PartyOut>(`/parties/${id}`, data)
}

export function addMember(data: PartyMemberOperation): Promise<PartyOut> {
  return post<PartyOut>('/parties/add-member/', data)
}

export function removeMember(data: PartyMemberOperation): Promise<PartyOut> {
  return post<PartyOut>('/parties/remove-member/', data)
}

export function updateFunds(id: number, data: PartyFundsUpdate): Promise<PartyOut> {
  return put<PartyOut>(`/parties/${id}/funds`, data)
}

export function addSupply(id: number, data: SupplyOperation): Promise<PartyOut> {
  return post<PartyOut>(`/parties/${id}/supplies`, data)
}

export function removeSupply(
  partyId: number,
  supplyId: number,
  quantity?: number,
): Promise<PartyOut> {
  const params = quantity !== undefined ? `?quantity=${quantity}` : ''
  return del<PartyOut>(`/parties/${partyId}/supplies/${supplyId}${params}`)
}

export function getStatus(id: number): Promise<PartyStatus> {
  return get<PartyStatus>(`/parties/${id}/status`)
}
