import { useEffect } from 'react'
import Button from '../Button'
import { saveLastAccessToken } from '../../utils/bookingStorage'
import { formatFullDateTime } from '../../utils/formatDateTime'
import { formatMoney } from '../../utils/formatMoney'
import type { Appointment } from '../../types/api'
import './BookingSteps.css'

interface ConfirmationStepProps {
  appointment: Appointment
}

export default function ConfirmationStep({ appointment }: ConfirmationStepProps) {
  useEffect(() => {
    saveLastAccessToken(appointment.access_token)
  }, [appointment.access_token])

  return (
    <div className="booking-step">
      <span className="booking-step__eyebrow">Reserva creada</span>
      <h1 className="booking-step__title">¡Gracias por tu reserva!</h1>
      <p className="booking-step__subtitle">
        Te enviamos un correo con los detalles de tu cita en Lirios. Nuestro equipo confirmará tu
        cita pronto.
      </p>

      <dl className="booking-step__summary">
        <div>
          <dt>Servicio</dt>
          <dd>{appointment.service.name}</dd>
        </div>
        <div>
          <dt>Fecha y hora</dt>
          <dd>{formatFullDateTime(appointment.start_datetime)}</dd>
        </div>
        <div>
          <dt>Precio</dt>
          <dd>{formatMoney(appointment.price_snapshot)}</dd>
        </div>
        <div>
          <dt>Estado</dt>
          <dd>{appointment.status_display}</dd>
        </div>
      </dl>

      <Button variant="solid" to={`/citas/${appointment.access_token}`}>
        Ver mi cita
      </Button>
    </div>
  )
}
