import { apiClient } from './client'
import type { Review } from '../types/api'

export async function getReviews(): Promise<Review[]> {
  const response = await apiClient.get<Review[]>('/reviews/')
  return response.data
}
