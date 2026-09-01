import { Outlet, useLocation } from 'react-router-dom'
import Nav from './Nav'
import Footer from './Footer'

export default function Layout() {
  const { pathname } = useLocation()
  const navVariant = pathname === '/' ? 'transparent' : 'solid'

  return (
    <>
      <Nav variant={navVariant} />
      <Outlet />
      <Footer />
    </>
  )
}
