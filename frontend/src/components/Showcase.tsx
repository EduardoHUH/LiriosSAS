import { motion, useReducedMotion } from 'motion/react'
import { Link } from 'react-router-dom'
import PlaceholderImage from './PlaceholderImage'
import './Showcase.css'

const fadeUp = (reduced: boolean | null) => ({
  initial: reduced ? {} : { opacity: 0, y: 32 },
  whileInView: reduced ? {} : { opacity: 1, y: 0 },
  viewport: { once: true, amount: 0.3 },
  transition: { duration: 0.6, ease: [0.16, 1, 0.3, 1] as const },
})

export default function Showcase() {
  const reducedMotion = useReducedMotion()

  return (
    <section className="showcase">
      <motion.div className="showcase__header" {...fadeUp(reducedMotion)}>
        <div className="showcase__intro">
          <span className="showcase__eyebrow">Nuestro trabajo</span>
          <h2 className="showcase__headline">Cada trazo, con intención.</h2>
        </div>
        <Link to="/galeria" className="showcase__link">
          Ver galería completa
        </Link>
      </motion.div>

      <div className="showcase__composition">
        <motion.div className="showcase__image showcase__image--square" {...fadeUp(reducedMotion)}>
          <PlaceholderImage
            label="Marcador — trabajo de maquillaje, retrato 1:1"
            gradient="linear-gradient(170deg, oklch(85% 0.03 95) 0%, oklch(68% 0.05 55) 55%, oklch(48% 0.06 30) 100%)"
            className="showcase__placeholder"
          />
        </motion.div>

        <motion.div
          className="showcase__image showcase__image--tall"
          {...fadeUp(reducedMotion)}
          transition={{ ...fadeUp(reducedMotion).transition, delay: 0.1 }}
        >
          <PlaceholderImage
            label="Marcador — detalle de uñas, 4:5"
            gradient="linear-gradient(175deg, oklch(90% 0.02 90) 0%, oklch(72% 0.05 145) 60%, oklch(50% 0.05 150) 100%)"
            className="showcase__placeholder"
          />
        </motion.div>

        <motion.div
          className="showcase__note"
          {...fadeUp(reducedMotion)}
          transition={{ ...fadeUp(reducedMotion).transition, delay: 0.2 }}
        >
          <p className="showcase__note-text">
            Maquillaje, uñas y pestañas — documentados como los vemos nosotros: de cerca, con
            calma, sin filtros de más.
          </p>
          <div className="showcase__note-divider" />
          <span className="showcase__note-quote">Precisión con alma.</span>
        </motion.div>
      </div>
    </section>
  )
}
