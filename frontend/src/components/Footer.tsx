import { Link } from 'react-router-dom'
import Button from './Button'
import './Footer.css'

export default function Footer() {
  return (
    <footer className="footer">
      <div className="footer__brand">
        <span className="footer__wordmark">Lirios</span>
        <p className="footer__tagline">Belleza que florece en calma.</p>
      </div>
      <Button variant="outline" to="/reservar">
        Reservar cita
      </Button>
      <div className="footer__meta">
        <nav className="footer__links">
          <Link to="/servicios">Servicios</Link>
          <Link to="/galeria">Galería</Link>
        </nav>
        <span className="footer__copyright">© {new Date().getFullYear()} Lirios</span>
      </div>
    </footer>
  )
}
