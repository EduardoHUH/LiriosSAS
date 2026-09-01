import { useState } from 'react'
import { isAxiosError } from 'axios'
import { createAppointment } from '../../api/appointments'
import { getErrorMessage } from '../../api/errors'
import { formatFullDateTime } from '../../utils/formatDateTime'
import { formatMoney } from '../../utils/formatMoney'
import Button from '../Button'
import type { Appointment, CustomerInput, Service } from '../../types/api'
import './BookingSteps.css'

interface ReviewStepProps {
  service: Service
  startDatetime: string
  customer: CustomerInput
  notes: string
  onConfirmed: (appointment: Appointment) => void
  onBack: () => void
  onSlotConflict: (message: string) => void
}

export default function ReviewStep({
  service,
  startDatetime,
  customer,
  notes,
  onConfirmed,
  onBack,
  onSlotConflict,
}: ReviewStepProps) {
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')

  async function handleConfirm() {
    setSubmitting(true)
    setError('')
    try {
      const appointment = await createAppointment({
        service: service.slug,
        start_datetime: startDatetime,
        customer,
        customer_notes: notes,
      })
      onConfirmed(appointment)
    } catch (err: unknown) {
      if (isAxiosError(err) && err.response?.status === 409) {
        onSlotConflict(getErrorMessage(err))
        return
      }
      setError(getErrorMessage(err))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="booking-step">
      <span className="booking-step__eyebrow">Paso 4 de 4</span>
      <h1 className="booking-step__title">Revisa tu cita</h1>

      <dl className="booking-step__summary">
        <div>
          <dt>Servicio</dt>
          <dd>{service.name}</dd>
        </div>
        <div>
          <dt>Fecha y hora</dt>
          <dd>{formatFullDateTime(startDatetime)}</dd>
        </div>
        <div>
          <dt>Precio</dt>
          <dd>{formatMoney(service.price)}</dd>
        </div>
        <div>
          <dt>Nombre</dt>
          <dd>{customer.full_name}</dd>
        </div>
        <div>
          <dt>Correo</dt>
          <dd>{customer.email}</dd>
        </div>
        <div>
          <dt>Teléfono</dt>
          <dd>{customer.phone}</dd>
        </div>
      </dl>

      {error && <p className="booking-step__status booking-step__status--error">{error}</p>}

      <div className="booking-step__actions">
        <Button variant="text" type="button" onClick={onBack} disabled={submitting}>
          Volver
        </Button>
        <Button variant="solid" type="button" onClick={handleConfirm} disabled={submitting}>
          {submitting ? 'Confirmando…' : 'Confirmar cita'}
        </Button>
      </div>
    </div>
  )
}
