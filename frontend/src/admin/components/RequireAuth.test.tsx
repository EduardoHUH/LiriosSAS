import { render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { describe, expect, it, vi, beforeEach } from 'vitest'
import RequireAuth from './RequireAuth'
import { AdminAuthProvider } from '../context/AdminAuthContext'
import * as authApi from '../api/auth'
import { clearStoredTokens, setStoredTokens } from '../api/adminClient'

vi.mock('../api/auth')

const mockedGetMe = vi.mocked(authApi.getMe)

function renderProtected() {
  return render(
    <MemoryRouter initialEntries={['/admin']}>
      <AdminAuthProvider>
        <Routes>
          <Route path="/admin/login" element={<p>Login page</p>} />
          <Route element={<RequireAuth />}>
            <Route path="/admin" element={<p>Protected content</p>} />
          </Route>
        </Routes>
      </AdminAuthProvider>
    </MemoryRouter>,
  )
}

describe('RequireAuth', () => {
  beforeEach(() => {
    clearStoredTokens()
  })

  it('redirects to login when there is no stored session', async () => {
    renderProtected()

    expect(await screen.findByText('Login page')).toBeInTheDocument()
  })

  it('renders the protected content when a session is valid', async () => {
    setStoredTokens({ access: 'a', refresh: 'r' })
    mockedGetMe.mockResolvedValue({ id: 1, username: 'admin', email: '', is_staff: true })

    renderProtected()

    expect(await screen.findByText('Protected content')).toBeInTheDocument()
  })

  it('redirects to login when the stored token is invalid', async () => {
    setStoredTokens({ access: 'bad', refresh: 'bad' })
    mockedGetMe.mockRejectedValue({ isAxiosError: true, response: { status: 401 } })

    renderProtected()

    expect(await screen.findByText('Login page')).toBeInTheDocument()
  })
})
