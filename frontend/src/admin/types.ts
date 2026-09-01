export interface AdminUser {
  id: number
  username: string
  email: string
  is_staff: boolean
}

export interface DashboardOverview {
  appointments_today: number
  upcoming_appointments_next_7_days: number
  revenue_this_month: string
  completed_appointments_this_month: number
  cancellations_this_month: number
  pending_payments: number
  refund_pending_payments: number
}

export type TrendGroupBy = 'day' | 'week' | 'month'

export interface RevenueTrendPoint {
  period: string
  revenue: string
}

export interface ServicePopularity {
  service_name: string
  appointment_count: number
  revenue: string
}
