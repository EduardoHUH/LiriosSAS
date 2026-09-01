import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'
import Login from './Login'
import { AdminAuthProvider } from '../context/AdminAuthContext'
import * as authApi from '../api/auth'
import { getStoredTokens } from '../api/adminClient'

vi.mock('../api/auth')

const mockedLogin = vi.mocked(authApi.login)
const mockedGetMe = vi.mocked(authApi.getMe)

function renderLogin() {
  return render(
    <MemoryRouter initialEntries={['/admin/login']}>
      <AdminAuthProvider>
        <Routes>
          <Route path="/admin/login" element={<Login />} />
          <Route path="/admin" element={<p>Panel</p>} />
        </Routes>
      </AdminAuthProvider>
    </MemoryRouter>,
  )
}

describe('Admin Login page', () => {
  it('logs in and navigates to the dashboard on success', async () => {
    const user = userEvent.setup()
    mockedLogin.mockResolvedValue(undefined)
    mockedGetMe.mockResolvedValue({ id: 1, username: 'admin', email: '', is_staff: true })

    renderLogin()

    await user.type(screen.getByLabelText('Usuario'), 'admin')
    await user.type(screen.getByLabelText('Contraseña'), 'secret')
    await user.click(screen.getByRole('button', { name: 'Ingresar' }))

    expect(await screen.findByText('Panel')).toBeInTheDocument()
    expect(mockedLogin).toHaveBeenCalledWith('admin', 'secret')
  })

  it('shows an error message on invalid credentials', async () => {
    const user = userEvent.setup()
    mockedLogin.mockRejectedValue({
      isAxiosError: true,
      response: { status: 401, data: { detail: 'No se encontró una cuenta activa con las credenciales proporcionadas.' } },
    })

    renderLogin()

    await user.type(screen.getByLabelText('Usuario'), 'admin')
    await user.type(screen.getByLabelText('Contraseña'), 'wrong')
    await user.click(screen.getByRole('button', { name: 'Ingresar' }))

    expect(
      await screen.findByText('No se encontró una cuenta activa con las credenciales proporcionadas.'),
    ).toBeInTheDocument()
    expect(getStoredTokens()).toBeNull()
  })
})
