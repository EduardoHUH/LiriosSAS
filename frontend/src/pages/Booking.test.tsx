import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'
import Booking from './Booking'
import { getServices } from '../api/services'
import { getAvailability } from '../api/scheduling'
import { getPublicBusinessSettings } from '../api/businessSettings'
import { createAppointment } from '../api/appointments'
import type { Appointment, BusinessSettingsPublic, Service } from '../types/api'

vi.mock('../api/services')
vi.mock('../api/scheduling')
vi.mock('../api/businessSettings')
vi.mock('../api/appointments')

const mockedGetServices = vi.mocked(getServices)
const mockedGetAvailability = vi.mocked(getAvailability)
const mockedGetBusinessSettings = vi.mocked(getPublicBusinessSettings)
const mockedCreateAppointment = vi.mocked(createAppointment)

const SERVICE: Service = {
  id: 1,
  name: 'Maquillaje social',
  slug: 'maquillaje-social',
  description: '',
  price: '850.00',
  duration_minutes: 60,
  image: '',
  preparation_instructions: '',
  cancellation_policy_notes: '',
  is_bookable: true,
  display_order: 0,
  category: { id: 1, name: 'Maquillaje', slug: 'maquillaje', description: '', display_order: 0 },
}

const SETTINGS: BusinessSettingsPublic = {
  business_name: 'Lirios',
  contact_email: '',
  contact_phone: '',
  address: '',
  social_links: {},
  min_booking_notice_hours: 2,
  max_booking_window_days: 5,
  cancellation_deadline_hours: 24,
  unpaid_hold_minutes: 20,
  default_buffer_minutes: 10,
  is_accepting_bookings: true,
}

const APPOINTMENT: Appointment = {
  id: 1,
  access_token: 'abc123',
  service: SERVICE,
  status: 'pending',
  status_display: 'Pendiente',
  start_datetime: '2026-09-02T15:00:00-06:00',
  end_datetime: '2026-09-02T16:00:00-06:00',
  price_snapshot: '850.00',
  customer_notes: '',
  reschedule_count: 0,
  cancelled_at: null,
  cancellation_reason: '',
  created_at: '2026-09-01T00:00:00-06:00',
  review: null,
}

function renderBooking() {
  return render(
    <MemoryRouter initialEntries={['/reservar']}>
      <Booking />
    </MemoryRouter>,
  )
}

describe('Booking wizard', () => {
  it('walks through service, date/time, customer, and review to confirmation', async () => {
    const user = userEvent.setup()
    mockedGetServices.mockResolvedValue([SERVICE])
    mockedGetBusinessSettings.mockResolvedValue(SETTINGS)
    mockedGetAvailability.mockResolvedValue({
      service: 'maquillaje-social',
      date: '2026-09-02',
      slots: ['2026-09-02T15:00:00-06:00'],
    })
    mockedCreateAppointment.mockResolvedValue(APPOINTMENT)

    renderBooking()

    await user.click(await screen.findByText('Maquillaje social'))

    const dayChips = await screen.findAllByText(/^\d+$/)
    await user.click(dayChips[0])

    const slotButton = await screen.findByRole('button', { name: /\d{1,2}:\d{2}/ })
    await user.click(slotButton)

    await user.type(screen.getByLabelText('Nombre completo'), 'Ana Pérez')
    await user.type(screen.getByLabelText('Correo electrónico'), 'ana@example.com')
    await user.type(screen.getByLabelText('Teléfono'), '99999999')
    await user.click(screen.getByRole('button', { name: 'Continuar' }))

    expect(await screen.findByText('Revisa tu cita')).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Confirmar cita' }))

    await waitFor(() => {
      expect(screen.getByText('¡Gracias por tu reserva!')).toBeInTheDocument()
    })
    expect(mockedCreateAppointment).toHaveBeenCalledWith({
      service: 'maquillaje-social',
      start_datetime: '2026-09-02T15:00:00-06:00',
      customer: { full_name: 'Ana Pérez', email: 'ana@example.com', phone: '99999999' },
      customer_notes: '',
    })
  })

  it('sends the customer back to date/time selection on a 409 slot conflict', async () => {
    const user = userEvent.setup()
    mockedGetServices.mockResolvedValue([SERVICE])
    mockedGetBusinessSettings.mockResolvedValue(SETTINGS)
    mockedGetAvailability.mockResolvedValue({
      service: 'maquillaje-social',
      date: '2026-09-02',
      slots: ['2026-09-02T15:00:00-06:00'],
    })
    mockedCreateAppointment.mockRejectedValue({
      isAxiosError: true,
      response: { status: 409, data: { detail: 'El horario ya no está disponible.' } },
    })

    renderBooking()

    await user.click(await screen.findByText('Maquillaje social'))
    const dayChips = await screen.findAllByText(/^\d+$/)
    await user.click(dayChips[0])
    const slotButton = await screen.findByRole('button', { name: /\d{1,2}:\d{2}/ })
    await user.click(slotButton)
    await user.type(screen.getByLabelText('Nombre completo'), 'Ana Pérez')
    await user.type(screen.getByLabelText('Correo electrónico'), 'ana@example.com')
    await user.type(screen.getByLabelText('Teléfono'), '99999999')
    await user.click(screen.getByRole('button', { name: 'Continuar' }))
    await user.click(await screen.findByRole('button', { name: 'Confirmar cita' }))

    expect(await screen.findByText('El horario ya no está disponible.')).toBeInTheDocument()
    expect(screen.getByText('Elige fecha y hora')).toBeInTheDocument()
  })
})
