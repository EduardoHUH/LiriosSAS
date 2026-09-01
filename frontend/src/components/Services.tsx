import { motion, useReducedMotion } from 'motion/react'
import Button from './Button'
import PlaceholderImage from './PlaceholderImage'
import './Services.css'

interface Service {
  index: string
  name: string
  headline: string
  description: string
  gradient: string
  placeholderLabel: string
}

const SERVICES: Service[] = [
  {
    index: '01',
    name: 'Maquillaje',
    headline: 'Un rostro, redefinido con delicadeza.',
    description:
      'Social, editorial o de novia — cada look parte de tu piel, no la cubre. Productos de alta gama, aplicación precisa.',
    gradient: 'linear-gradient(170deg, oklch(88% 0.03 95) 0%, oklch(70% 0.05 60) 60%, oklch(50% 0.06 35) 100%)',
    placeholderLabel: 'Marcador — maquillaje',
  },
  {
    index: '02',
    name: 'Uñas',
    headline: 'El detalle final, perfeccionado.',
    description:
      'Manicure y pedicure en gel o acrílico, con diseños tan sutiles o tan expresivos como los quieras.',
    gradient: 'linear-gradient(170deg, oklch(90% 0.02 90) 0%, oklch(74% 0.05 145) 55%, oklch(48% 0.05 150) 100%)',
    placeholderLabel: 'Marcador — uñas',
  },
  {
    index: '03',
    name: 'Pestañas',
    headline: 'Una mirada que dice más.',
    description:
      'Extensiones pelo a pelo o volumen ruso, adaptadas a la forma de tu ojo. Resultado natural, no artificial.',
    gradient: 'linear-gradient(170deg, oklch(87% 0.03 70) 0%, oklch(66% 0.05 35) 60%, oklch(44% 0.05 30) 100%)',
    placeholderLabel: 'Marcador — pestañas',
  },
]

export default function Services() {
  const reducedMotion = useReducedMotion()

  return (
    <section id="servicios" className="services">
      <motion.div
        className="services__header"
        initial={reducedMotion ? {} : { opacity: 0, y: 24 }}
        whileInView={reducedMotion ? {} : { opacity: 1, y: 0 }}
        viewport={{ once: true, amount: 0.4 }}
        transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
      >
        <span className="services__eyebrow">Servicios</span>
        <h2 className="services__headline">Tres oficios, un mismo cuidado.</h2>
      </motion.div>

      {SERVICES.map((service, i) => (
        <motion.article
          key={service.name}
          className={`services__row${i % 2 === 1 ? ' services__row--reverse' : ''}`}
          initial={reducedMotion ? {} : { opacity: 0, y: 32 }}
          whileInView={reducedMotion ? {} : { opacity: 1, y: 0 }}
          viewport={{ once: true, amount: 0.25 }}
          transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
        >
          <PlaceholderImage
            label={service.placeholderLabel}
            gradient={service.gradient}
            className="services__image"
          />
          <div className="services__copy">
            <span className="services__index">
              {service.index} — {service.name}
            </span>
            <h3 className="services__item-headline">{service.headline}</h3>
            <p className="services__item-description">{service.description}</p>
            <Button variant="text" to="/servicios">
              Ver detalles
            </Button>
          </div>
        </motion.article>
      ))}
    </section>
  )
}
