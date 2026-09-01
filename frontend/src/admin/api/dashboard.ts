import { adminClient } from './adminClient'
import type { DashboardOverview, RevenueTrendPoint, ServicePopularity, TrendGroupBy } from '../types'

export async function getOverview(): Promise<DashboardOverview> {
  const response = await adminClient.get<DashboardOverview>('/admin/dashboard/overview/')
  return response.data
}

export interface DateRangeParams {
  date_from?: string
  date_to?: string
}

export async function getRevenueTrend(
  params: DateRangeParams & { group_by?: TrendGroupBy },
): Promise<RevenueTrendPoint[]> {
  const response = await adminClient.get<RevenueTrendPoint[]>('/admin/analytics/revenue/', { params })
  return response.data
}

export async function getServicePopularity(params: DateRangeParams): Promise<ServicePopularity[]> {
  const response = await adminClient.get<ServicePopularity[]>('/admin/analytics/services/', { params })
  return response.data
}
