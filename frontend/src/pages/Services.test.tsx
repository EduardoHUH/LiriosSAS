import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'
import Services from './Services'
import { getServices } from '../api/services'
import type { Service } from '../types/api'

vi.mock('../api/services')

const mockedGetServices = vi.mocked(getServices)

const SERVICE: Service = {
  id: 1,
  name: 'Maquillaje social',
  slug: 'maquillaje-social',
  description: 'Un look para cualquier ocasión.',
  price: '850.00',
  duration_minutes: 60,
  image: '',
  preparation_instructions: '',
  cancellation_policy_notes: '',
  is_bookable: true,
  display_order: 0,
  category: { id: 1, name: 'Maquillaje', slug: 'maquillaje', description: '', display_order: 0 },
}

describe('Services page', () => {
  it('renders services returned by the API', async () => {
    mockedGetServices.mockResolvedValue([SERVICE])

    render(
      <MemoryRouter>
        <Services />
      </MemoryRouter>,
    )

    expect(await screen.findByText('Maquillaje social')).toBeInTheDocument()
    expect(screen.getByText('L 850')).toBeInTheDocument()
  })

  it('shows an empty state when there are no services yet', async () => {
    mockedGetServices.mockResolvedValue([])

    render(
      <MemoryRouter>
        <Services />
      </MemoryRouter>,
    )

    expect(await screen.findByText(/aún no hay servicios/i)).toBeInTheDocument()
  })

  it('shows an error message when the request fails', async () => {
    mockedGetServices.mockRejectedValue(new Error('network error'))

    render(
      <MemoryRouter>
        <Services />
      </MemoryRouter>,
    )

    expect(await screen.findByText(/error inesperado/i)).toBeInTheDocument()
  })
})
