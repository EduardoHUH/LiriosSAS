import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getServices } from '../api/services'
import { getErrorMessage } from '../api/errors'
import PlaceholderImage from '../components/PlaceholderImage'
import { getPlaceholderGradient } from '../utils/placeholderGradients'
import { formatMoney } from '../utils/formatMoney'
import type { Service } from '../types/api'
import './Services.css'

type LoadState = 'loading' | 'loaded' | 'error'

export default function Services() {
  const [services, setServices] = useState<Service[]>([])
  const [state, setState] = useState<LoadState>('loading')
  const [error, setError] = useState('')

  useEffect(() => {
    let cancelled = false

    getServices()
      .then((data) => {
        if (cancelled) return
        setServices(data)
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
  }, [])

  return (
    <main className="services-page">
      <header className="services-page__header">
        <span className="services-page__eyebrow">Servicios</span>
        <h1 className="services-page__headline">Tres oficios, un mismo cuidado.</h1>
      </header>

      {state === 'loading' && <p className="services-page__status">Cargando servicios…</p>}

      {state === 'error' && <p className="services-page__status services-page__status--error">{error}</p>}

      {state === 'loaded' && services.length === 0 && (
        <p className="services-page__status">Aún no hay servicios publicados. Vuelve pronto.</p>
      )}

      {state === 'loaded' && services.length > 0 && (
        <div className="services-page__grid">
          {services.map((service) => (
            <Link key={service.id} to={`/servicios/${service.slug}`} className="service-card">
              {service.image ? (
                <img className="service-card__image" src={service.image} alt={service.name} />
              ) : (
                <PlaceholderImage
                  label={`Marcador — ${service.name.toLowerCase()}`}
                  gradient={getPlaceholderGradient(service.id)}
                  className="service-card__image"
                />
              )}
              <div className="service-card__body">
                <span className="service-card__category">{service.category.name}</span>
                <h2 className="service-card__name">{service.name}</h2>
                <div className="service-card__meta">
                  <span>{formatMoney(service.price)}</span>
                  <span>{service.duration_minutes} min</span>
                </div>
              </div>
            </Link>
          ))}
        </div>
      )}
    </main>
  )
}
