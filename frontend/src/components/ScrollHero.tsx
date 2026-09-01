import { useRef, useState } from 'react'
import {
  motion,
  useMotionValueEvent,
  useReducedMotion,
  useScroll,
  useTransform,
} from 'motion/react'
import Button from './Button'
import './ScrollHero.css'

const HERO_GRADIENT =
  'linear-gradient(155deg, oklch(30% 0.035 100) 0%, oklch(38% 0.05 70) 38%, oklch(46% 0.06 40) 68%, oklch(58% 0.05 30) 100%)'

export default function ScrollHero() {
  const sectionRef = useRef<HTMLDivElement>(null)
  const prefersReducedMotion = useReducedMotion()
  const { scrollYProgress } = useScroll({
    target: sectionRef,
    offset: ['start start', 'end end'],
  })
  const [cueVisible, setCueVisible] = useState(true)

  useMotionValueEvent(scrollYProgress, 'change', (progress) => {
    setCueVisible(progress < 0.06)
  })

  const scrimOpacity = useTransform(scrollYProgress, [0, 0.5], [0, 1])
  const wordmarkOpacity = useTransform(scrollYProgress, [0, 0.16, 0.3], [1, 1, 0])
  const wordmarkY = useTransform(scrollYProgress, [0, 0.3], [0, -60])
  const ghostWordmarkOpacity = useTransform(scrollYProgress, [0.28, 0.42], [0, 1])
  const philosophyOpacity = useTransform(scrollYProgress, [0.32, 0.48, 0.72, 0.86], [0, 1, 1, 0])
  const philosophyY = useTransform(scrollYProgress, [0.32, 0.48], [40, 0])

  if (prefersReducedMotion) {
    return (
      <section className="scroll-hero scroll-hero--static">
        <div className="scroll-hero__frame" style={{ background: HERO_GRADIENT }}>
          <div className="scroll-hero__scrim" style={{ opacity: 1 }} />
          <HeroContent />
        </div>
        <div className="scroll-hero__philosophy-static">
          <PhilosophyContent />
        </div>
      </section>
    )
  }

  return (
    <section ref={sectionRef} className="scroll-hero">
      <div className="scroll-hero__pin">
        <div className="scroll-hero__frame" style={{ background: HERO_GRADIENT }}>
          <motion.div className="scroll-hero__scrim" style={{ opacity: scrimOpacity }} />

          <motion.div style={{ opacity: wordmarkOpacity, y: wordmarkY }}>
            <HeroContent />
          </motion.div>

          <motion.span className="scroll-hero__ghost-wordmark" style={{ opacity: ghostWordmarkOpacity }}>
            Lirios
          </motion.span>

          <motion.div
            className="scroll-hero__philosophy"
            style={{ opacity: philosophyOpacity, y: philosophyY }}
          >
            <PhilosophyContent />
          </motion.div>

          <div
            className={`scroll-hero__scroll-cue${cueVisible ? '' : ' scroll-hero__scroll-cue--hidden'}`}
          >
            <span className="scroll-hero__scroll-cue-line" />
            <span className="scroll-hero__scroll-cue-label">Desplázate</span>
          </div>
        </div>
      </div>
    </section>
  )
}

function HeroContent() {
  return (
    <div className="scroll-hero__content">
      <span className="scroll-hero__eyebrow">Maquillaje · Uñas · Pestañas</span>
      <h1 className="scroll-hero__wordmark">Lirios</h1>
      <p className="scroll-hero__tagline">
        Belleza que florece en calma. Un espacio para que cada detalle tenga tiempo de existir.
      </p>
      <Button variant="solid" href="#reservar" className="scroll-hero__cta">
        Reservar cita
      </Button>
    </div>
  )
}

function PhilosophyContent() {
  return (
    <div className="scroll-hero__philosophy-inner">
      <span className="scroll-hero__eyebrow scroll-hero__eyebrow--center">Nuestra filosofía</span>
      <h2 className="scroll-hero__philosophy-headline">
        Creemos en la belleza sin prisa — donde cada cita es un espacio para respirar, no una fila
        más en la agenda.
      </h2>
      <div className="scroll-hero__divider" />
      <p className="scroll-hero__philosophy-body">
        Maquillaje, uñas y pestañas, con la misma calma en cada cita.
      </p>
    </div>
  )
}
