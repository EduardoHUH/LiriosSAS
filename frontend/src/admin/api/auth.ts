import { adminClient, clearStoredTokens, getStoredTokens, setStoredTokens } from './adminClient'
import type { AdminUser } from '../types'

export async function login(username: string, password: string): Promise<void> {
  const response = await adminClient.post<{ access: string; refresh: string }>('/auth/login/', {
    username,
    password,
  })
  setStoredTokens(response.data)
}

export async function getMe(): Promise<AdminUser> {
  const response = await adminClient.get<AdminUser>('/auth/me/')
  return response.data
}

export async function logout(): Promise<void> {
  const tokens = getStoredTokens()
  if (tokens) {
    try {
      await adminClient.post('/auth/logout/', { refresh: tokens.refresh })
    } catch {
      /* best-effort blacklist -- clear local session regardless */
    }
  }
  clearStoredTokens()
}
