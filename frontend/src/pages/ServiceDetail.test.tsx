import { render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'
import ServiceDetail from './ServiceDetail'
import { getService } from '../api/services'
import type { Service } from '../types/api'

vi.mock('../api/services')

const mockedGetService = vi.mocked(getService)

const SERVICE: Service = {
  id: 1,
  name: 'Manicure en gel',
  slug: 'manicure-gel',
  description: 'Manicure de larga duración.',
  price: '650.00',
  duration_minutes: 45,
  image: '',
  preparation_instructions: 'Llega con las uñas limpias, sin esmalte previo.',
  cancellation_policy_notes: '',
  is_bookable: true,
  display_order: 0,
  category: { id: 2, name: 'Uñas', slug: 'unas', description: '', display_order: 0 },
}

function renderAt(slug: string) {
  return render(
    <MemoryRouter initialEntries={[`/servicios/${slug}`]}>
      <Routes>
        <Route path="/servicios/:slug" element={<ServiceDetail />} />
      </Routes>
    </MemoryRouter>,
  )
}

describe('ServiceDetail page', () => {
  it('renders the service returned by the API with a booking CTA', async () => {
    mockedGetService.mockResolvedValue(SERVICE)

    renderAt('manicure-gel')

    expect(await screen.findByText('Manicure en gel')).toBeInTheDocument()
    expect(screen.getByText('L 650')).toBeInTheDocument()
    expect(screen.getByText('Llega con las uñas limpias, sin esmalte previo.')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Reservar' })).toHaveAttribute(
      'href',
      '/reservar?service=manicure-gel',
    )
  })

  it('shows a not-found message when the service does not exist', async () => {
    mockedGetService.mockRejectedValue({
      isAxiosError: true,
      response: { status: 404, data: { detail: 'Servicio no encontrado.' } },
    })

    renderAt('no-existe')

    expect(await screen.findByText('Servicio no encontrado.')).toBeInTheDocument()
  })
})
