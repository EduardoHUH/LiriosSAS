import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { getService } from '../api/services'
import ServiceStep from '../components/booking/ServiceStep'
import DateTimeStep from '../components/booking/DateTimeStep'
import CustomerStep from '../components/booking/CustomerStep'
import ReviewStep from '../components/booking/ReviewStep'
import ConfirmationStep from '../components/booking/ConfirmationStep'
import type { Appointment, CustomerInput, Service } from '../types/api'
import './Booking.css'

type Step = 'service' | 'datetime' | 'customer' | 'review' | 'confirmation'

const EMPTY_CUSTOMER: CustomerInput = { full_name: '', email: '', phone: '' }

export default function Booking() {
  const [searchParams] = useSearchParams()
  const preselectedSlug = searchParams.get('service')

  const [step, setStep] = useState<Step>('service')
  const [service, setService] = useState<Service | null>(null)
  const [startDatetime, setStartDatetime] = useState('')
  const [customer, setCustomer] = useState<CustomerInput>(EMPTY_CUSTOMER)
  const [notes, setNotes] = useState('')
  const [appointment, setAppointment] = useState<Appointment | null>(null)
  const [conflictMessage, setConflictMessage] = useState('')

  useEffect(() => {
    if (!preselectedSlug) return
    getService(preselectedSlug)
      .then((data) => {
        setService(data)
        setStep('datetime')
      })
      .catch(() => {
        /* fall back to letting the customer pick a service manually */
      })
  }, [preselectedSlug])

  return (
    <main className="booking-page">
      {step === 'service' && (
        <ServiceStep
          onSelect={(selected) => {
            setService(selected)
            setStep('datetime')
          }}
        />
      )}

      {step === 'datetime' && service && (
        <>
          {conflictMessage && (
            <p className="booking-page__conflict">{conflictMessage}</p>
          )}
          <DateTimeStep
            service={service}
            onSelect={(slot) => {
              setStartDatetime(slot)
              setConflictMessage('')
              setStep('customer')
            }}
            onBack={() => setStep('service')}
          />
        </>
      )}

      {step === 'customer' && (
        <CustomerStep
          initialCustomer={customer}
          initialNotes={notes}
          onSubmit={(newCustomer, newNotes) => {
            setCustomer(newCustomer)
            setNotes(newNotes)
            setStep('review')
          }}
          onBack={() => setStep('datetime')}
        />
      )}

      {step === 'review' && service && (
        <ReviewStep
          service={service}
          startDatetime={startDatetime}
          customer={customer}
          notes={notes}
          onConfirmed={(created) => {
            setAppointment(created)
            setStep('confirmation')
          }}
          onBack={() => setStep('customer')}
          onSlotConflict={(message) => {
            setConflictMessage(message)
            setStep('datetime')
          }}
        />
      )}

      {step === 'confirmation' && appointment && <ConfirmationStep appointment={appointment} />}
    </main>
  )
}
