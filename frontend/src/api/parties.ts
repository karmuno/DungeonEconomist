import { get, post, put } from './client'
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

export function getStatus(id: number): Promise<PartyStatus> {
  return get<PartyStatus>(`/parties/${id}/status`)
}
