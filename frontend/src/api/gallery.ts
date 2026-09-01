import { apiClient } from './client'
import type { GalleryItem } from '../types/api'

export async function getGalleryItems(categorySlug?: string): Promise<GalleryItem[]> {
  const response = await apiClient.get<GalleryItem[]>('/gallery/', {
    params: categorySlug ? { category: categorySlug } : undefined,
  })
  return response.data
}
