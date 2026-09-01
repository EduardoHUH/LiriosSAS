import { useState } from 'react'
import { useMotionValueEvent, useScroll } from 'motion/react'
import Button from './Button'
import './Nav.css'

export default function Nav() {
  const [scrolled, setScrolled] = useState(false)
  const { scrollY } = useScroll()

  useMotionValueEvent(scrollY, 'change', (latest) => {
    setScrolled(latest > 80)
  })

  return (
    <header className={`nav${scrolled ? ' nav--scrolled' : ''}`}>
      <span className="nav__logo">Lirios</span>
      <nav className="nav__links">
        <a href="#servicios">Servicios</a>
        <a href="#galeria">Galería</a>
        <Button variant="glass" href="#reservar">
          Reservar cita
        </Button>
      </nav>
    </header>
  )
}
