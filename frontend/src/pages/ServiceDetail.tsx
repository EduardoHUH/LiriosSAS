import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { getService } from '../api/services'
import { getErrorMessage } from '../api/errors'
import Button from '../components/Button'
import PlaceholderImage from '../components/PlaceholderImage'
import { getPlaceholderGradient } from '../utils/placeholderGradients'
import { formatMoney } from '../utils/formatMoney'
import type { Service } from '../types/api'
import './ServiceDetail.css'

type LoadState = 'loading' | 'loaded' | 'error'

export default function ServiceDetail() {
  const { slug } = useParams<{ slug: string }>()
  const [service, setService] = useState<Service | null>(null)
  const [state, setState] = useState<LoadState>('loading')
  const [error, setError] = useState('')

  useEffect(() => {
    if (!slug) return
    let cancelled = false
    setState('loading')

    getService(slug)
      .then((data) => {
        if (cancelled) return
        setService(data)
        setState('loaded')
      })
      .catch((err: unknown) => {
        if (cancelled) return
        setError(getErrorMessage(err))
        setState('error')
      })

    return () => {
      cancelled = true
    }
  }, [slug])

  if (state === 'loading') {
    return (
      <main className="service-detail">
        <p className="service-detail__status">Cargando…</p>
      </main>
    )
  }

  if (state === 'error' || !service) {
    return (
      <main className="service-detail">
        <p className="service-detail__status service-detail__status--error">
          {error || 'No encontramos este servicio.'}
        </p>
        <Link to="/servicios" className="service-detail__back">
          Ver todos los servicios
        </Link>
      </main>
    )
  }

  return (
    <main className="service-detail">
      <div className="service-detail__media">
        {service.image ? (
          <img className="service-detail__image" src={service.image} alt={service.name} />
        ) : (
          <PlaceholderImage
            label={`Marcador — ${service.name.toLowerCase()}`}
            gradient={getPlaceholderGradient(service.id)}
            className="service-detail__image"
          />
        )}
      </div>
      <div className="service-detail__body">
        <span className="service-detail__category">{service.category.name}</span>
        <h1 className="service-detail__name">{service.name}</h1>
        <div className="service-detail__meta">
          <span>{formatMoney(service.price)}</span>
          <span>{service.duration_minutes} min</span>
        </div>
        {service.description && <p className="service-detail__description">{service.description}</p>}
        {service.preparation_instructions && (
          <div className="service-detail__note">
            <h2>Antes de tu cita</h2>
            <p>{service.preparation_instructions}</p>
          </div>
        )}
        {service.cancellation_policy_notes && (
          <div className="service-detail__note">
            <h2>Política de cancelación</h2>
            <p>{service.cancellation_policy_notes}</p>
          </div>
        )}
        {service.is_bookable ? (
          <Button variant="solid" to={`/reservar?service=${service.slug}`}>
            Reservar
          </Button>
        ) : (
          <p className="service-detail__unavailable">Este servicio no está disponible para reservar en línea.</p>
        )}
      </div>
    </main>
  )
}
