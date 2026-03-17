import { get, post, put, del } from './client'
import type {
  PartyOut,
  PartyCreate,
  PartyMemberOperation,
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

export function deleteParty(id: number): Promise<{ ok: boolean }> {
  return del<{ ok: boolean }>(`/parties/${id}`)
}

export function getStatus(id: number): Promise<PartyStatus> {
  return get<PartyStatus>(`/parties/${id}/status`)
}

export function updateAutoDelve(id: number, healed: boolean, full: boolean, autoDecide?: boolean): Promise<{ ok: boolean }> {
  return put<{ ok: boolean }>(`/parties/${id}/auto-delve`, {
    auto_delve_healed: healed,
    auto_delve_full: full,
    auto_decide_events: autoDecide ?? false,
  })
}
