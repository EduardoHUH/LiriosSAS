import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { apiClient } from '../api/client'
import Home from './Home'

vi.mock('../api/client', () => ({
  apiClient: { get: vi.fn().mockResolvedValue({}) },
}))

describe('Home', () => {
  it('shows the backend as online once the health check resolves', async () => {
    render(<Home />)

    expect(await screen.findByText('en línea')).toBeInTheDocument()
    expect(apiClient.get).toHaveBeenCalledWith('/health/')
  })
})
