import { act } from 'react'
import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import Testimonials from './Testimonials'
import { getReviews } from '../api/reviews'
import type { Review } from '../types/api'

vi.mock('../api/reviews')

const mockedGetReviews = vi.mocked(getReviews)

const REVIEW: Review = {
  id: 1,
  reviewer_name: 'Ana López',
  rating: 5,
  comment: 'Una experiencia hermosa, con mucha calma.',
  created_at: '2026-09-01T00:00:00-06:00',
}

/** Renders and flushes the effect's fetch promise inside `act`, so the
 * resulting setState is applied before assertions run -- avoids the
 * common false-pass of asserting "empty" before the async work settles. */
async function renderAndFlush() {
  const result = render(<Testimonials />)
  await act(async () => {
    await mockedGetReviews.mock.results[0]!.value.catch(() => {})
  })
  return result
}

describe('Testimonials', () => {
  it('renders approved reviews with a comment', async () => {
    mockedGetReviews.mockResolvedValue([REVIEW])

    await renderAndFlush()

    expect(screen.getByText('— Ana López')).toBeInTheDocument()
    expect(screen.getByText('"Una experiencia hermosa, con mucha calma."')).toBeInTheDocument()
  })

  it('renders nothing when there are no reviews with a comment yet', async () => {
    mockedGetReviews.mockResolvedValue([{ ...REVIEW, comment: '' }])

    const { container } = await renderAndFlush()

    expect(container).toBeEmptyDOMElement()
  })

  it('renders nothing when the request fails', async () => {
    mockedGetReviews.mockRejectedValue(new Error('network error'))

    const { container } = await renderAndFlush()

    expect(container).toBeEmptyDOMElement()
  })
})
