import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'
import ManageBooking from './ManageBooking'
import { cancelAppointment, getAppointment } from '../api/appointments'
import type { Appointment, Service } from '../types/api'

vi.mock('../api/appointments')
vi.mock('../api/scheduling')
vi.mock('../api/businessSettings')

const mockedGetAppointment = vi.mocked(getAppointment)
const mockedCancelAppointment = vi.mocked(cancelAppointment)

const SERVICE: Service = {
  id: 1,
  name: 'Manicure en gel',
  slug: 'manicure-gel',
  description: '',
  price: '650.00',
  duration_minutes: 45,
  image: '',
  preparation_instructions: '',
  cancellation_policy_notes: '',
  is_bookable: true,
  display_order: 0,
  category: { id: 2, name: 'Uñas', slug: 'unas', description: '', display_order: 0 },
}

const APPOINTMENT: Appointment = {
  id: 1,
  access_token: 'abc123',
  service: SERVICE,
  status: 'pending',
  status_display: 'Pendiente',
  start_datetime: '2026-09-02T15:00:00-06:00',
  end_datetime: '2026-09-02T15:45:00-06:00',
  price_snapshot: '650.00',
  customer_notes: '',
  reschedule_count: 0,
  cancelled_at: null,
  cancellation_reason: '',
  created_at: '2026-09-01T00:00:00-06:00',
}

function renderAt(token: string) {
  return render(
    <MemoryRouter initialEntries={[`/citas/${token}`]}>
      <Routes>
        <Route path="/citas/:accessToken" element={<ManageBooking />} />
      </Routes>
    </MemoryRouter>,
  )
}

describe('ManageBooking page', () => {
  it('renders appointment details and available actions', async () => {
    mockedGetAppointment.mockResolvedValue(APPOINTMENT)

    renderAt('abc123')

    expect(await screen.findByText('Manicure en gel')).toBeInTheDocument()
    expect(screen.getByText('L 650')).toBeInTheDocument()
    expect(screen.getByText('Pendiente')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Pagar' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Reprogramar' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Cancelar cita' })).toBeInTheDocument()
  })

  it('cancels the appointment and shows the updated status', async () => {
    const user = userEvent.setup()
    mockedGetAppointment.mockResolvedValue(APPOINTMENT)
    mockedCancelAppointment.mockResolvedValue({
      ...APPOINTMENT,
      status: 'cancelled',
      status_display: 'Cancelada',
      cancellation_reason: 'Cambio de planes',
    })

    renderAt('abc123')

    await user.click(await screen.findByRole('button', { name: 'Cancelar cita' }))
    await user.type(screen.getByLabelText('Motivo (opcional)'), 'Cambio de planes')
    await user.click(screen.getByRole('button', { name: 'Confirmar cancelación' }))

    expect(await screen.findByText('Cancelada')).toBeInTheDocument()
    expect(mockedCancelAppointment).toHaveBeenCalledWith('abc123', 'Cambio de planes')
  })

  it('shows an error when the appointment cannot be found', async () => {
    mockedGetAppointment.mockRejectedValue({
      isAxiosError: true,
      response: { status: 404, data: { detail: 'No encontrado.' } },
    })

    renderAt('does-not-exist')

    expect(await screen.findByText('No encontrado.')).toBeInTheDocument()
  })
})
