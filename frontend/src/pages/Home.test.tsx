import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it } from 'vitest'
import Home from './Home'

function renderHome() {
  return render(
    <MemoryRouter>
      <Home />
    </MemoryRouter>,
  )
}

describe('Home', () => {
  it('renders the Lirios wordmark and primary booking calls to action', () => {
    renderHome()

    expect(screen.getAllByText('Lirios').length).toBeGreaterThan(0)
    expect(screen.getAllByText('Reservar cita').length).toBeGreaterThan(0)
  })

  it('renders all three services', () => {
    renderHome()

    expect(screen.getByText('Un rostro, redefinido con delicadeza.')).toBeInTheDocument()
    expect(screen.getByText('El detalle final, perfeccionado.')).toBeInTheDocument()
    expect(screen.getByText('Una mirada que dice más.')).toBeInTheDocument()
  })
})
