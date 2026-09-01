import Button from './Button'
import './Footer.css'

export default function Footer() {
  return (
    <footer className="footer" id="reservar">
      <div className="footer__brand">
        <span className="footer__wordmark">Lirios</span>
        <p className="footer__tagline">Belleza que florece en calma.</p>
      </div>
      <Button variant="outline" href="#reservar">
        Reservar cita
      </Button>
      <div className="footer__meta">
        <nav className="footer__links">
          <a href="#servicios">Servicios</a>
          <a href="#galeria">Galería</a>
        </nav>
        <span className="footer__copyright">© {new Date().getFullYear()} Lirios</span>
      </div>
    </footer>
  )
}
