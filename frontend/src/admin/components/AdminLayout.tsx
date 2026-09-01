import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { useAdminAuth } from '../context/AdminAuthContext'
import '../admin-shared.css'
import './AdminLayout.css'

function navLinkClass({ isActive }: { isActive: boolean }): string {
  return `admin-layout__link${isActive ? ' admin-layout__link--active' : ''}`
}

export default function AdminLayout() {
  const { user, logout } = useAdminAuth()
  const navigate = useNavigate()

  async function handleLogout() {
    await logout()
    navigate('/admin/login', { replace: true })
  }

  return (
    <div className="admin-layout">
      <aside className="admin-layout__sidebar">
        <span className="admin-layout__brand">Lirios</span>
        <nav className="admin-layout__nav">
          <NavLink to="/admin" end className={navLinkClass}>
            Resumen
          </NavLink>
          <NavLink to="/admin/analytics" className={navLinkClass}>
            Analítica
          </NavLink>
        </nav>
        <button type="button" className="admin-layout__logout" onClick={handleLogout}>
          Cerrar sesión
        </button>
      </aside>
      <div className="admin-layout__content">
        <header className="admin-layout__topbar">
          <span className="admin-layout__user">{user?.username}</span>
        </header>
        <main className="admin-layout__main">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
