import { useEffect, useState } from 'react'
import { getGalleryItems } from '../api/gallery'
import { getCategories } from '../api/services'
import { getErrorMessage } from '../api/errors'
import Button from '../components/Button'
import type { Category, GalleryItem } from '../types/api'
import './Gallery.css'

type LoadState = 'loading' | 'loaded' | 'error'

// Every 5th tile (0-indexed, skipping the first) gets a larger footprint,
// giving the grid a staggered, editorial rhythm instead of a uniform card
// grid -- the brief explicitly warns against "a grid of small generic
// cards."
function isFeatureTile(index: number): boolean {
  return index > 0 && index % 5 === 0
}

export default function Gallery() {
  const [items, setItems] = useState<GalleryItem[]>([])
  const [categories, setCategories] = useState<Category[]>([])
  const [activeCategory, setActiveCategory] = useState<string | null>(null)
  const [state, setState] = useState<LoadState>('loading')
  const [error, setError] = useState('')

  useEffect(() => {
    getCategories()
      .then(setCategories)
      .catch(() => {
        /* category pills are a nice-to-have; the gallery still works without them */
      })
  }, [])

  useEffect(() => {
    let cancelled = false
    setState('loading')

    getGalleryItems(activeCategory ?? undefined)
      .then((data) => {
        if (cancelled) return
        setItems(data)
        setState('loaded')
      })
      .catch((err: unknown) => {
        if (cancelled) return
        setError(getErrorMessage(err))
        setState('error')
      })

    return () => {
      cancelled = true
    }
  }, [activeCategory])

  return (
    <main className="gallery-page">
      <header className="gallery-page__header">
        <span className="gallery-page__eyebrow">Galería</span>
        <h1 className="gallery-page__headline">Nuestro trabajo, de cerca.</h1>
      </header>

      {categories.length > 0 && (
        <div className="gallery-page__filters">
          <Button
            variant={activeCategory === null ? 'solid' : 'outline'}
            type="button"
            onClick={() => setActiveCategory(null)}
          >
            Todo
          </Button>
          {categories.map((category) => (
            <Button
              key={category.id}
              variant={activeCategory === category.slug ? 'solid' : 'outline'}
              type="button"
              onClick={() => setActiveCategory(category.slug)}
            >
              {category.name}
            </Button>
          ))}
        </div>
      )}

      {state === 'loading' && <p className="gallery-page__status">Cargando…</p>}
      {state === 'error' && <p className="gallery-page__status gallery-page__status--error">{error}</p>}
      {state === 'loaded' && items.length === 0 && (
        <p className="gallery-page__status">Aún no hay fotos publicadas. Vuelve pronto.</p>
      )}

      {state === 'loaded' && items.length > 0 && (
        <div className="gallery-page__grid">
          {items.map((item, index) => (
            <figure
              key={item.id}
              className={`gallery-page__tile${isFeatureTile(index) ? ' gallery-page__tile--feature' : ''}`}
            >
              <img className="gallery-page__image" src={item.image} alt={item.caption || 'Trabajo de Lirios'} />
              {item.caption && <figcaption className="gallery-page__caption">{item.caption}</figcaption>}
            </figure>
          ))}
        </div>
      )}
    </main>
  )
}
