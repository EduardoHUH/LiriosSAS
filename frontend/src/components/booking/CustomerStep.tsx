import { useState } from 'react'
import type { FormEvent } from 'react'
import Button from '../Button'
import type { CustomerInput } from '../../types/api'
import './BookingSteps.css'

interface CustomerStepProps {
  initialCustomer: CustomerInput
  initialNotes: string
  onSubmit: (customer: CustomerInput, notes: string) => void
  onBack: () => void
}

export default function CustomerStep({
  initialCustomer,
  initialNotes,
  onSubmit,
  onBack,
}: CustomerStepProps) {
  const [fullName, setFullName] = useState(initialCustomer.full_name)
  const [email, setEmail] = useState(initialCustomer.email)
  const [phone, setPhone] = useState(initialCustomer.phone)
  const [notes, setNotes] = useState(initialNotes)

  function handleSubmit(event: FormEvent) {
    event.preventDefault()
    onSubmit({ full_name: fullName, email, phone }, notes)
  }

  return (
    <form className="booking-step" onSubmit={handleSubmit}>
      <span className="booking-step__eyebrow">Paso 3 de 4</span>
      <h1 className="booking-step__title">Tus datos</h1>

      <div className="booking-step__field">
        <label htmlFor="full_name">Nombre completo</label>
        <input
          id="full_name"
          name="full_name"
          type="text"
          autoComplete="name"
          required
          value={fullName}
          onChange={(e) => setFullName(e.target.value)}
        />
      </div>

      <div className="booking-step__field">
        <label htmlFor="email">Correo electrónico</label>
        <input
          id="email"
          name="email"
          type="email"
          autoComplete="email"
          required
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />
      </div>

      <div className="booking-step__field">
        <label htmlFor="phone">Teléfono</label>
        <input
          id="phone"
          name="phone"
          type="tel"
          autoComplete="tel"
          required
          value={phone}
          onChange={(e) => setPhone(e.target.value)}
        />
      </div>

      <div className="booking-step__field">
        <label htmlFor="notes">Notas para el salón (opcional)</label>
        <textarea id="notes" name="notes" rows={3} value={notes} onChange={(e) => setNotes(e.target.value)} />
      </div>

      <div className="booking-step__actions">
        <Button variant="text" type="button" onClick={onBack}>
          Volver
        </Button>
        <Button variant="solid" type="submit">
          Continuar
        </Button>
      </div>
    </form>
  )
}
