import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'
import Gallery from './Gallery'
import { getGalleryItems } from '../api/gallery'
import { getCategories } from '../api/services'
import type { Category, GalleryItem } from '../types/api'

vi.mock('../api/gallery')
vi.mock('../api/services')

const mockedGetGalleryItems = vi.mocked(getGalleryItems)
const mockedGetCategories = vi.mocked(getCategories)

const CATEGORY: Category = { id: 1, name: 'Maquillaje', slug: 'maquillaje', description: '', display_order: 0 }

const ITEM: GalleryItem = {
  id: 1,
  image: 'https://example.com/foto.jpg',
  category: CATEGORY,
  caption: 'Look editorial',
  display_order: 0,
}

function renderGallery() {
  return render(
    <MemoryRouter>
      <Gallery />
    </MemoryRouter>,
  )
}

describe('Gallery page', () => {
  it('renders items returned by the API', async () => {
    mockedGetCategories.mockResolvedValue([CATEGORY])
    mockedGetGalleryItems.mockResolvedValue([ITEM])

    renderGallery()

    expect(await screen.findByAltText('Look editorial')).toBeInTheDocument()
    expect(screen.getByText('Look editorial')).toBeInTheDocument()
  })

  it('shows an empty state when there are no items yet', async () => {
    mockedGetCategories.mockResolvedValue([])
    mockedGetGalleryItems.mockResolvedValue([])

    renderGallery()

    expect(await screen.findByText(/aún no hay fotos/i)).toBeInTheDocument()
  })

  it('refetches with the category filter when a pill is clicked', async () => {
    const user = userEvent.setup()
    mockedGetCategories.mockResolvedValue([CATEGORY])
    mockedGetGalleryItems.mockResolvedValue([ITEM])

    renderGallery()

    await screen.findByAltText('Look editorial')
    await user.click(screen.getByRole('button', { name: 'Maquillaje' }))

    expect(mockedGetGalleryItems).toHaveBeenCalledWith('maquillaje')
  })
})
