import { useEffect, useState } from 'react'
import { getAvailability } from '../../api/scheduling'
import { getPublicBusinessSettings } from '../../api/businessSettings'
import { getErrorMessage } from '../../api/errors'
import { formatDayChip, formatSlotTime, toDateParam } from '../../utils/formatDateTime'
import Button from '../Button'
import type { Service } from '../../types/api'
import './BookingSteps.css'

interface DateTimeStepProps {
  service: Service
  onSelect: (startDatetime: string) => void
  onBack: () => void
}

const DEFAULT_WINDOW_DAYS = 30

function buildDayOptions(windowDays: number): Date[] {
  const today = new Date()
  return Array.from({ length: windowDays }, (_, i) => {
    const date = new Date(today)
    date.setDate(date.getDate() + i)
    return date
  })
}

export default function DateTimeStep({ service, onSelect, onBack }: DateTimeStepProps) {
  const [windowDays, setWindowDays] = useState(DEFAULT_WINDOW_DAYS)
  const [selectedDate, setSelectedDate] = useState<Date | null>(null)
  const [slots, setSlots] = useState<string[]>([])
  const [slotsLoading, setSlotsLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    getPublicBusinessSettings()
      .then((settings) => setWindowDays(settings.max_booking_window_days))
      .catch(() => {
        /* fall back to the default window; the date picker still works */
      })
  }, [])

  useEffect(() => {
    if (!selectedDate) return
    let cancelled = false
    setSlotsLoading(true)
    setError('')

    getAvailability(service.slug, toDateParam(selectedDate))
      .then((response) => {
        if (cancelled) return
        setSlots(response.slots)
        setSlotsLoading(false)
      })
      .catch((err: unknown) => {
        if (cancelled) return
        setError(getErrorMessage(err))
        setSlotsLoading(false)
      })

    return () => {
      cancelled = true
    }
  }, [service.slug, selectedDate])

  const days = buildDayOptions(windowDays)

  return (
    <div className="booking-step">
      <span className="booking-step__eyebrow">Paso 2 de 4</span>
      <h1 className="booking-step__title">Elige fecha y hora</h1>
      <p className="booking-step__subtitle">{service.name}</p>

      <div className="booking-step__day-list">
        {days.map((date) => {
          const { weekday, day, month } = formatDayChip(date)
          const isSelected = selectedDate !== null && toDateParam(date) === toDateParam(selectedDate)
          return (
            <button
              key={date.toISOString()}
              type="button"
              className={`booking-step__day-chip${isSelected ? ' booking-step__day-chip--selected' : ''}`}
              onClick={() => setSelectedDate(date)}
            >
              <span className="booking-step__day-chip-weekday">{weekday}</span>
              <span className="booking-step__day-chip-day">{day}</span>
              <span className="booking-step__day-chip-month">{month}</span>
            </button>
          )
        })}
      </div>

      {selectedDate && (
        <div className="booking-step__slots">
          {slotsLoading && <p className="booking-step__status">Buscando horarios…</p>}
          {!slotsLoading && error && <p className="booking-step__status booking-step__status--error">{error}</p>}
          {!slotsLoading && !error && slots.length === 0 && (
            <p className="booking-step__status">No hay horarios disponibles este día. Prueba otra fecha.</p>
          )}
          {!slotsLoading && slots.length > 0 && (
            <ul className="booking-step__slot-list">
              {slots.map((slot) => (
                <li key={slot}>
                  <button type="button" className="booking-step__slot" onClick={() => onSelect(slot)}>
                    {formatSlotTime(slot)}
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}

      <Button variant="text" type="button" onClick={onBack}>
        Volver
      </Button>
    </div>
  )
}
