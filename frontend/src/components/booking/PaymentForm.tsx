import { useState } from 'react'
import type { FormEvent } from 'react'
import { payAppointment } from '../../api/appointments'
import { getErrorMessage } from '../../api/errors'
import Button from '../Button'
import type { Appointment } from '../../types/api'
import './BookingSteps.css'

interface PaymentFormProps {
  accessToken: string
  onSuccess: (appointment: Appointment) => void
  onCancel: () => void
}

const CURRENT_YEAR = new Date().getFullYear()
const EXPIRY_YEARS = Array.from({ length: 15 }, (_, i) => CURRENT_YEAR + i)
const MONTHS = Array.from({ length: 12 }, (_, i) => i + 1)

export default function PaymentForm({ accessToken, onSuccess, onCancel }: PaymentFormProps) {
  const [cardNumber, setCardNumber] = useState('')
  const [cardCvv, setCardCvv] = useState('')
  const [expireMonth, setExpireMonth] = useState(MONTHS[0])
  const [expireYear, setExpireYear] = useState(CURRENT_YEAR)
  const [cardholder, setCardholder] = useState('')
  const [billingAddress, setBillingAddress] = useState('')
  const [billingCountry, setBillingCountry] = useState('HN')
  const [billingState, setBillingState] = useState('')
  const [billingCity, setBillingCity] = useState('')
  const [billingZip, setBillingZip] = useState('')
  const [billingPhone, setBillingPhone] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setSubmitting(true)
    setError('')
    try {
      const appointment = await payAppointment(accessToken, {
        card_number: cardNumber,
        card_cvv: cardCvv,
        card_expire_month: expireMonth,
        card_expire_year: expireYear,
        cardholder,
        billing_address: billingAddress,
        billing_country: billingCountry,
        billing_state: billingState,
        billing_city: billingCity,
        billing_zip: billingZip,
        billing_phone: billingPhone,
      })
      onSuccess(appointment)
    } catch (err: unknown) {
      setError(getErrorMessage(err))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <form className="payment-form" onSubmit={handleSubmit}>
      <p className="payment-form__notice">
        El pago se procesa de forma segura al confirmar. Tu tarjeta nunca se guarda en nuestros
        servidores.
      </p>

      <div className="booking-step__field">
        <label htmlFor="card_number">Número de tarjeta</label>
        <input
          id="card_number"
          type="text"
          inputMode="numeric"
          autoComplete="cc-number"
          maxLength={19}
          required
          value={cardNumber}
          onChange={(e) => setCardNumber(e.target.value)}
        />
      </div>

      <div className="payment-form__row">
        <div className="booking-step__field">
          <label htmlFor="expire_month">Mes</label>
          <select
            id="expire_month"
            autoComplete="cc-exp-month"
            value={expireMonth}
            onChange={(e) => setExpireMonth(Number(e.target.value))}
          >
            {MONTHS.map((month) => (
              <option key={month} value={month}>
                {String(month).padStart(2, '0')}
              </option>
            ))}
          </select>
        </div>

        <div className="booking-step__field">
          <label htmlFor="expire_year">Año</label>
          <select
            id="expire_year"
            autoComplete="cc-exp-year"
            value={expireYear}
            onChange={(e) => setExpireYear(Number(e.target.value))}
          >
            {EXPIRY_YEARS.map((year) => (
              <option key={year} value={year}>
                {year}
              </option>
            ))}
          </select>
        </div>

        <div className="booking-step__field">
          <label htmlFor="card_cvv">CVV</label>
          <input
            id="card_cvv"
            type="text"
            inputMode="numeric"
            autoComplete="cc-csc"
            maxLength={4}
            required
            value={cardCvv}
            onChange={(e) => setCardCvv(e.target.value)}
          />
        </div>
      </div>

      <div className="booking-step__field">
        <label htmlFor="cardholder">Nombre en la tarjeta</label>
        <input
          id="cardholder"
          type="text"
          autoComplete="cc-name"
          required
          value={cardholder}
          onChange={(e) => setCardholder(e.target.value)}
        />
      </div>

      <div className="booking-step__field">
        <label htmlFor="billing_address">Dirección de facturación</label>
        <input
          id="billing_address"
          type="text"
          autoComplete="address-line1"
          required
          value={billingAddress}
          onChange={(e) => setBillingAddress(e.target.value)}
        />
      </div>

      <div className="payment-form__row">
        <div className="booking-step__field">
          <label htmlFor="billing_city">Ciudad</label>
          <input
            id="billing_city"
            type="text"
            autoComplete="address-level2"
            required
            value={billingCity}
            onChange={(e) => setBillingCity(e.target.value)}
          />
        </div>

        <div className="booking-step__field">
          <label htmlFor="billing_state">Departamento</label>
          <input
            id="billing_state"
            type="text"
            maxLength={10}
            required
            value={billingState}
            onChange={(e) => setBillingState(e.target.value)}
          />
        </div>

        <div className="booking-step__field">
          <label htmlFor="billing_zip">Código postal</label>
          <input
            id="billing_zip"
            type="text"
            autoComplete="postal-code"
            required
            value={billingZip}
            onChange={(e) => setBillingZip(e.target.value)}
          />
        </div>
      </div>

      <div className="payment-form__row">
        <div className="booking-step__field">
          <label htmlFor="billing_country">País (código de 2 letras)</label>
          <input
            id="billing_country"
            type="text"
            maxLength={2}
            required
            value={billingCountry}
            onChange={(e) => setBillingCountry(e.target.value.toUpperCase())}
          />
        </div>

        <div className="booking-step__field">
          <label htmlFor="billing_phone">Teléfono de facturación</label>
          <input
            id="billing_phone"
            type="tel"
            autoComplete="tel"
            required
            value={billingPhone}
            onChange={(e) => setBillingPhone(e.target.value)}
          />
        </div>
      </div>

      {error && <p className="booking-step__status booking-step__status--error">{error}</p>}

      <div className="booking-step__actions">
        <Button variant="text" type="button" onClick={onCancel} disabled={submitting}>
          Cancelar
        </Button>
        <Button variant="solid" type="submit" disabled={submitting}>
          {submitting ? 'Procesando…' : 'Pagar'}
        </Button>
      </div>
    </form>
  )
}
