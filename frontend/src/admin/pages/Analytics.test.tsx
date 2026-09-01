import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import Analytics from './Analytics'
import { getRevenueTrend, getServicePopularity } from '../api/dashboard'
import type { RevenueTrendPoint, ServicePopularity } from '../types'

vi.mock('../api/dashboard')

const mockedGetRevenueTrend = vi.mocked(getRevenueTrend)
const mockedGetServicePopularity = vi.mocked(getServicePopularity)

const REVENUE: RevenueTrendPoint[] = [
  { period: '2026-08-01', revenue: '500.00' },
  { period: '2026-08-02', revenue: '750.00' },
]

const POPULARITY: ServicePopularity[] = [
  { service_name: 'Maquillaje social', appointment_count: 4, revenue: '2000.00' },
  { service_name: 'Manicure en gel', appointment_count: 2, revenue: '1300.00' },
]

describe('Admin Analytics page', () => {
  it('renders both charts as tables with data from the API', async () => {
    mockedGetRevenueTrend.mockResolvedValue(REVENUE)
    mockedGetServicePopularity.mockResolvedValue(POPULARITY)

    render(<Analytics />)

    const tableToggles = await screen.findAllByRole('button', { name: 'Ver como tabla' })
    for (const toggle of tableToggles) {
      await userEvent.click(toggle)
    }

    expect(screen.getByText('L 500')).toBeInTheDocument()
    expect(screen.getAllByText('Maquillaje social').length).toBe(2)
    expect(screen.getAllByText('Manicure en gel').length).toBe(2)
  })

  it('refetches when the date range changes', async () => {
    const user = userEvent.setup()
    mockedGetRevenueTrend.mockResolvedValue(REVENUE)
    mockedGetServicePopularity.mockResolvedValue(POPULARITY)

    render(<Analytics />)

    await screen.findByText('Tendencia de ingresos')
    mockedGetRevenueTrend.mockClear()

    await user.selectOptions(screen.getByLabelText('Periodo'), '90')

    expect(mockedGetRevenueTrend).toHaveBeenCalled()
  })

  it('shows an error message when the request fails', async () => {
    mockedGetRevenueTrend.mockRejectedValue(new Error('network error'))
    mockedGetServicePopularity.mockResolvedValue([])

    render(<Analytics />)

    expect(await screen.findByText(/error inesperado/i)).toBeInTheDocument()
  })
})
