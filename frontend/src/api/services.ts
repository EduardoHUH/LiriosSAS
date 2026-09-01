import { apiClient } from './client'
import type { Category, Service } from '../types/api'

export async function getCategories(): Promise<Category[]> {
  const response = await apiClient.get<Category[]>('/categories/')
  return response.data
}

export async function getServices(categorySlug?: string): Promise<Service[]> {
  const response = await apiClient.get<Service[]>('/services/', {
    params: categorySlug ? { category: categorySlug } : undefined,
  })
  return response.data
}

export async function getService(slug: string): Promise<Service> {
  const response = await apiClient.get<Service>(`/services/${slug}/`)
  return response.data
}
