import { apiClient } from './client'
import type { BusinessSettingsPublic } from '../types/api'

export async function getPublicBusinessSettings(): Promise<BusinessSettingsPublic> {
  const response = await apiClient.get<BusinessSettingsPublic>('/business-settings/')
  return response.data
}
