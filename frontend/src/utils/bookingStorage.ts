const STORAGE_KEY = 'lirios:lastAccessToken'

export function saveLastAccessToken(token: string): void {
  try {
    localStorage.setItem(STORAGE_KEY, token)
  } catch {
    /* localStorage can be unavailable (private mode, disabled) -- non-critical */
  }
}

export function getLastAccessToken(): string | null {
  try {
    return localStorage.getItem(STORAGE_KEY)
  } catch {
    return null
  }
}
