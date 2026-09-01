import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { cancelAppointment, getAppointment, rescheduleAppointment } from '../api/appointments'
import { getErrorMessage } from '../api/errors'
import { formatFullDateTime } from '../utils/formatDateTime'
import { formatMoney } from '../utils/formatMoney'
import Button from '../components/Button'
import DateTimeStep from '../components/booking/DateTimeStep'
import PaymentForm from '../components/booking/PaymentForm'
import type { Appointment } from '../types/api'
import './ManageBooking.css'

type LoadState = 'loading' | 'loaded' | 'error'
type View = 'details' | 'cancel' | 'reschedule' | 'pay'

const ACTIONABLE_STATUSES = new Set(['pending', 'awaiting_payment', 'confirmed', 'reschedule_requested'])
const PAYABLE_STATUSES = new Set(['pending', 'awaiting_payment'])

export default function ManageBooking() {
  const { accessToken } = useParams<{ accessToken: string }>()
  const [appointment, setAppointment] = useState<Appointment | null>(null)
  const [state, setState] = useState<LoadState>('loading')
  const [loadError, setLoadError] = useState('')
  const [view, setView] = useState<View>('details')
  const [cancelReason, setCancelReason] = useState('')
  const [actionError, setActionError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    if (!accessToken) return
    getAppointment(accessToken)
      .then((data) => {
        setAppointment(data)
        setState('loaded')
      })
      .catch((err: unknown) => {
        setLoadError(getErrorMessage(err))
        setState('error')
      })
  }, [accessToken])

  if (state === 'loading') {
    return (
      <main className="manage-booking">
        <p className="manage-booking__status">Cargando…</p>
      </main>
    )
  }

  if (state === 'error' || !appointment || !accessToken) {
    return (
      <main className="manage-booking">
        <p className="manage-booking__status manage-booking__status--error">
          {loadError || 'No encontramos esta cita.'}
        </p>
      </main>
    )
  }

  async function handleCancel() {
    setSubmitting(true)
    setActionError('')
    try {
      const updated = await cancelAppointment(accessToken!, cancelReason)
      setAppointment(updated)
      setView('details')
    } catch (err: unknown) {
      setActionError(getErrorMessage(err))
    } finally {
      setSubmitting(false)
    }
  }

  const canAct = ACTIONABLE_STATUSES.has(appointment.status)
  const canPay = PAYABLE_STATUSES.has(appointment.status)

  return (
    <main className="manage-booking">
      <span className="manage-booking__eyebrow">Tu cita en Lirios</span>
      <h1 className="manage-booking__title">{appointment.service.name}</h1>

      <dl className="manage-booking__summary">
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
        {appointment.cancellation_reason && (
          <div>
            <dt>Motivo de cancelación</dt>
            <dd>{appointment.cancellation_reason}</dd>
          </div>
        )}
      </dl>

      {view === 'details' && canAct && (
        <div className="manage-booking__actions">
          {canPay && (
            <Button variant="solid" type="button" onClick={() => setView('pay')}>
              Pagar
            </Button>
          )}
          <Button variant="outline" type="button" onClick={() => setView('reschedule')}>
            Reprogramar
          </Button>
          <Button variant="text" type="button" onClick={() => setView('cancel')}>
            Cancelar cita
          </Button>
        </div>
      )}

      {view === 'pay' && (
        <PaymentForm
          accessToken={accessToken}
          onCancel={() => setView('details')}
          onSuccess={(updated) => {
            setAppointment(updated)
            setView('details')
          }}
        />
      )}

      {view === 'reschedule' && (
        <DateTimeStep
          service={appointment.service}
          onBack={() => setView('details')}
          onSelect={(slot) => {
            setSubmitting(true)
            setActionError('')
            rescheduleAppointment(accessToken, slot)
              .then((updated) => {
                setAppointment(updated)
                setView('details')
              })
              .catch((err: unknown) => setActionError(getErrorMessage(err)))
              .finally(() => setSubmitting(false))
          }}
        />
      )}

      {view === 'cancel' && (
        <div className="manage-booking__cancel">
          <label htmlFor="cancel_reason">Motivo (opcional)</label>
          <textarea
            id="cancel_reason"
            rows={3}
            value={cancelReason}
            onChange={(e) => setCancelReason(e.target.value)}
          />
          <div className="manage-booking__actions">
            <Button variant="text" type="button" onClick={() => setView('details')} disabled={submitting}>
              Volver
            </Button>
            <Button variant="solid" type="button" onClick={handleCancel} disabled={submitting}>
              {submitting ? 'Cancelando…' : 'Confirmar cancelación'}
            </Button>
          </div>
        </div>
      )}

      {actionError && <p className="manage-booking__status manage-booking__status--error">{actionError}</p>}
    </main>
  )
}
