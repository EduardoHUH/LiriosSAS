import { BrowserRouter, Route, Routes } from 'react-router-dom'
import Layout from './components/Layout'
import Home from './pages/Home'
import Services from './pages/Services'
import ServiceDetail from './pages/ServiceDetail'
import Booking from './pages/Booking'
import ManageBooking from './pages/ManageBooking'
import Gallery from './pages/Gallery'
import { AdminAuthProvider } from './admin/context/AdminAuthContext'
import RequireAuth from './admin/components/RequireAuth'
import AdminLayout from './admin/components/AdminLayout'
import AdminLogin from './admin/pages/Login'
import AdminOverview from './admin/pages/Overview'
import AdminAnalytics from './admin/pages/Analytics'

function AdminApp() {
  return (
    <AdminAuthProvider>
      <Routes>
        <Route path="login" element={<AdminLogin />} />
        <Route element={<RequireAuth />}>
          <Route element={<AdminLayout />}>
            <Route index element={<AdminOverview />} />
            <Route path="analytics" element={<AdminAnalytics />} />
          </Route>
        </Route>
      </Routes>
    </AdminAuthProvider>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<Home />} />
          <Route path="/servicios" element={<Services />} />
          <Route path="/servicios/:slug" element={<ServiceDetail />} />
          <Route path="/reservar" element={<Booking />} />
          <Route path="/citas/:accessToken" element={<ManageBooking />} />
          <Route path="/galeria" element={<Gallery />} />
        </Route>

        <Route path="/admin/*" element={<AdminApp />} />
      </Routes>
    </BrowserRouter>
  )
}
