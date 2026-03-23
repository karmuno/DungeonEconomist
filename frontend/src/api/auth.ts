import { post, get } from './client'
import type { TokenResponse, AccountOut } from '../types'

export function register(username: string, password: string): Promise<TokenResponse> {
  return post<TokenResponse>('/auth/register', { username, password })
}

export function login(username: string, password: string): Promise<TokenResponse> {
  return post<TokenResponse>('/auth/login', { username, password })
}

export function refresh(refreshToken: string): Promise<TokenResponse> {
  return post<TokenResponse>('/auth/refresh', { refresh_token: refreshToken })
}

export function logout(): Promise<unknown> {
  return post('/auth/logout')
}

export function changePassword(currentPassword: string, newPassword: string): Promise<TokenResponse> {
  return post<TokenResponse>('/auth/change-password', {
    current_password: currentPassword,
    new_password: newPassword,
  })
}

export function getMe(): Promise<AccountOut> {
  return get<AccountOut>('/auth/me')
}
