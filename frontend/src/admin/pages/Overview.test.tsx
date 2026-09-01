import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import Overview from './Overview'
import { getOverview } from '../api/dashboard'
import type { DashboardOverview } from '../types'

vi.mock('../api/dashboard')

const mockedGetOverview = vi.mocked(getOverview)

const OVERVIEW: DashboardOverview = {
  appointments_today: 3,
  upcoming_appointments_next_7_days: 5,
  revenue_this_month: '4250.00',
  completed_appointments_this_month: 12,
  cancellations_this_month: 2,
  pending_payments: 1,
  refund_pending_payments: 0,
}

describe('Admin Overview page', () => {
  it('renders stat tiles from the API', async () => {
    mockedGetOverview.mockResolvedValue(OVERVIEW)

    render(<Overview />)

    expect(await screen.findByText('L 4,250')).toBeInTheDocument()
    expect(screen.getByText('3')).toBeInTheDocument()
    expect(screen.getByText('5')).toBeInTheDocument()
    expect(screen.getByText('12')).toBeInTheDocument()
  })

  it('shows an error message when the request fails', async () => {
    mockedGetOverview.mockRejectedValue(new Error('network error'))

    render(<Overview />)

    expect(await screen.findByText(/error inesperado/i)).toBeInTheDocument()
  })
})
