import { useEffect, useState } from 'react'
import { getServices } from '../../api/services'
import { getErrorMessage } from '../../api/errors'
import { formatMoney } from '../../utils/formatMoney'
import type { Service } from '../../types/api'
import './BookingSteps.css'

interface ServiceStepProps {
  onSelect: (service: Service) => void
}

type LoadState = 'loading' | 'loaded' | 'error'

export default function ServiceStep({ onSelect }: ServiceStepProps) {
  const [services, setServices] = useState<Service[]>([])
  const [state, setState] = useState<LoadState>('loading')
  const [error, setError] = useState('')

  useEffect(() => {
    let cancelled = false

    getServices()
      .then((data) => {
        if (cancelled) return
        setServices(data.filter((service) => service.is_bookable))
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
    <div className="booking-step">
      <span className="booking-step__eyebrow">Paso 1 de 4</span>
      <h1 className="booking-step__title">¿Qué servicio quieres reservar?</h1>

      {state === 'loading' && <p className="booking-step__status">Cargando servicios…</p>}
      {state === 'error' && <p className="booking-step__status booking-step__status--error">{error}</p>}
      {state === 'loaded' && services.length === 0 && (
        <p className="booking-step__status">Aún no hay servicios disponibles para reservar.</p>
      )}

      {state === 'loaded' && services.length > 0 && (
        <ul className="booking-step__service-list">
          {services.map((service) => (
            <li key={service.id}>
              <button
                type="button"
                className="booking-step__service-option"
                onClick={() => onSelect(service)}
              >
                <span className="booking-step__service-name">{service.name}</span>
                <span className="booking-step__service-meta">
                  {formatMoney(service.price)} · {service.duration_minutes} min
                </span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
