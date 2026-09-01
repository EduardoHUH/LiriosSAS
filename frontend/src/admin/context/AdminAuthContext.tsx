import { createContext, useContext, useEffect, useState } from 'react'
import type { ReactNode } from 'react'
import { clearStoredTokens, getStoredTokens } from '../api/adminClient'
import { getMe, login as loginRequest, logout as logoutRequest } from '../api/auth'
import type { AdminUser } from '../types'

type AuthStatus = 'loading' | 'authenticated' | 'unauthenticated'

interface AdminAuthContextValue {
  user: AdminUser | null
  status: AuthStatus
  login: (username: string, password: string) => Promise<void>
  logout: () => Promise<void>
}

const AdminAuthContext = createContext<AdminAuthContextValue | null>(null)

export function AdminAuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AdminUser | null>(null)
  const [status, setStatus] = useState<AuthStatus>('loading')

  useEffect(() => {
    if (!getStoredTokens()) {
      setStatus('unauthenticated')
      return
    }
    getMe()
      .then((me) => {
        setUser(me)
        setStatus('authenticated')
      })
      .catch(() => {
        clearStoredTokens()
        setStatus('unauthenticated')
      })
  }, [])

  async function login(username: string, password: string) {
    await loginRequest(username, password)
    const me = await getMe()
    setUser(me)
    setStatus('authenticated')
  }

  async function logout() {
    await logoutRequest()
    setUser(null)
    setStatus('unauthenticated')
  }

  return (
    <AdminAuthContext.Provider value={{ user, status, login, logout }}>
      {children}
    </AdminAuthContext.Provider>
  )
}

export function useAdminAuth(): AdminAuthContextValue {
  const ctx = useContext(AdminAuthContext)
  if (!ctx) {
    throw new Error('useAdminAuth must be used within AdminAuthProvider')
  }
  return ctx
}
