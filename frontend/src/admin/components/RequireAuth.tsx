import { Navigate, Outlet } from 'react-router-dom'
import { useAdminAuth } from '../context/AdminAuthContext'

export default function RequireAuth() {
  const { status } = useAdminAuth()

  if (status === 'loading') {
    return <p className="admin-status">Cargando…</p>
  }

  if (status === 'unauthenticated') {
    return <Navigate to="/admin/login" replace />
  }

  return <Outlet />
}
