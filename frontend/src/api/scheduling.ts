import { apiClient } from './client'
import type { AvailabilityResponse, BusinessHours } from '../types/api'

export async function getAvailability(
  serviceSlug: string,
  date: string,
): Promise<AvailabilityResponse> {
  const response = await apiClient.get<AvailabilityResponse>('/availability/', {
    params: { service: serviceSlug, date },
  })
  return response.data
}

export async function getBusinessHours(): Promise<BusinessHours[]> {
  const response = await apiClient.get<BusinessHours[]>('/business-hours/')
  return response.data
}
