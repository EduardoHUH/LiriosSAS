import axios from 'axios'
import type { InternalAxiosRequestConfig } from 'axios'

const STORAGE_KEY = 'lirios:staffAuth'
const BASE_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000/api/v1'

export interface StoredTokens {
  access: string
  refresh: string
}

interface RetriableConfig extends InternalAxiosRequestConfig {
  _retry?: boolean
}

export function getStoredTokens(): StoredTokens | null {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    return raw ? (JSON.parse(raw) as StoredTokens) : null
  } catch {
    return null
  }
}

export function setStoredTokens(tokens: StoredTokens): void {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(tokens))
  } catch {
    /* localStorage can be unavailable (private mode, disabled) -- non-critical */
  }
}

export function clearStoredTokens(): void {
  try {
    localStorage.removeItem(STORAGE_KEY)
  } catch {
    /* ignore */
  }
}

export const adminClient = axios.create({ baseURL: BASE_URL })

adminClient.interceptors.request.use((config) => {
  const tokens = getStoredTokens()
  if (tokens) {
    config.headers.set('Authorization', `Bearer ${tokens.access}`)
  }
  return config
})

let refreshPromise: Promise<string | null> | null = null

async function refreshAccessToken(): Promise<string | null> {
  const tokens = getStoredTokens()
  if (!tokens) return null
  try {
    const response = await axios.post<{ access: string; refresh: string }>(
      `${BASE_URL}/auth/refresh/`,
      { refresh: tokens.refresh },
    )
    setStoredTokens(response.data)
    return response.data.access
  } catch {
    clearStoredTokens()
    return null
  }
}

adminClient.interceptors.response.use(
  (response) => response,
  async (error: unknown) => {
    if (!axios.isAxiosError(error) || !error.config) {
      return Promise.reject(error)
    }
    const originalRequest = error.config as RetriableConfig

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true
      refreshPromise ??= refreshAccessToken().finally(() => {
        refreshPromise = null
      })
      const newAccess = await refreshPromise
      if (newAccess) {
        originalRequest.headers.set('Authorization', `Bearer ${newAccess}`)
        return adminClient(originalRequest)
      }
    }

    return Promise.reject(error)
  },
)
