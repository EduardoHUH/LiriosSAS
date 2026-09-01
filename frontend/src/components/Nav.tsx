import { useState } from 'react'
import { useMotionValueEvent, useScroll } from 'motion/react'
import { Link } from 'react-router-dom'
import Button from './Button'
import './Nav.css'

interface NavProps {
  variant?: 'transparent' | 'solid'
}

export default function Nav({ variant = 'solid' }: NavProps) {
  const [scrolled, setScrolled] = useState(false)
  const { scrollY } = useScroll()

  useMotionValueEvent(scrollY, 'change', (latest) => {
    setScrolled(latest > 80)
  })

  const isTransparent = variant === 'transparent'
  const classes = ['nav', `nav--${variant}`, isTransparent && scrolled ? 'nav--scrolled' : '']
    .filter(Boolean)
    .join(' ')

  return (
    <header className={classes}>
      <Link className="nav__logo" to="/">
        Lirios
      </Link>
      <nav className="nav__links">
        <Link to="/servicios">Servicios</Link>
        <Link to="/#galeria">Galería</Link>
        <Button variant={isTransparent ? 'glass' : 'solid'} to="/reservar">
          Reservar cita
        </Button>
      </nav>
    </header>
  )
}
