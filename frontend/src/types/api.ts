export interface Category {
  id: number
  name: string
  slug: string
  description: string
  display_order: number
}

export interface Service {
  id: number
  name: string
  slug: string
  description: string
  price: string
  duration_minutes: number
  image: string | null
  preparation_instructions: string
  cancellation_policy_notes: string
  is_bookable: boolean
  display_order: number
  category: Category
}

export interface BusinessHours {
  id: number
  weekday: number
  start_time: string
  end_time: string
}

export interface AvailabilityResponse {
  service: string
  date: string
  slots: string[]
}

export interface BusinessSettingsPublic {
  business_name: string
  contact_email: string
  contact_phone: string
  address: string
  social_links: Record<string, string>
  min_booking_notice_hours: number
  max_booking_window_days: number
  cancellation_deadline_hours: number
  unpaid_hold_minutes: number
  default_buffer_minutes: number
  is_accepting_bookings: boolean
}

export type AppointmentStatus =
  | 'pending'
  | 'awaiting_payment'
  | 'confirmed'
  | 'cancelled'
  | 'completed'
  | 'no_show'
  | 'reschedule_requested'

export interface Appointment {
  id: number
  access_token: string
  service: Service
  status: AppointmentStatus
  status_display: string
  start_datetime: string
  end_datetime: string
  price_snapshot: string
  customer_notes: string
  reschedule_count: number
  cancelled_at: string | null
  cancellation_reason: string
  created_at: string
}

export interface CustomerInput {
  full_name: string
  email: string
  phone: string
}

export interface CreateAppointmentInput {
  service: string
  start_datetime: string
  customer: CustomerInput
  customer_notes?: string
}

export interface PaymentInput {
  card_number: string
  card_cvv: string
  card_expire_month: number
  card_expire_year: number
  cardholder: string
  billing_address: string
  billing_country: string
  billing_state: string
  billing_city: string
  billing_zip: string
  billing_phone: string
}
