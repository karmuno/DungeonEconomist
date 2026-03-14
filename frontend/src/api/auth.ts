import { post, get } from './client'
import type { TokenResponse, AccountOut } from '../types'

export function register(username: string, password: string): Promise<TokenResponse> {
  return post<TokenResponse>('/auth/register', { username, password })
}

export function login(username: string, password: string): Promise<TokenResponse> {
  return post<TokenResponse>('/auth/login', { username, password })
}

export function getMe(): Promise<AccountOut> {
  return get<AccountOut>('/auth/me')
}
