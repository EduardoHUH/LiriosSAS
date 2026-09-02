import { apiClient } from './client'
import type { Appointment, CreateAppointmentInput, ReviewInput } from '../types/api'

export async function createAppointment(input: CreateAppointmentInput): Promise<Appointment> {
  const response = await apiClient.post<Appointment>('/appointments/', input)
  return response.data
}

export async function getAppointment(accessToken: string): Promise<Appointment> {
  const response = await apiClient.get<Appointment>(`/appointments/${accessToken}/`)
  return response.data
}

export async function cancelAppointment(
  accessToken: string,
  reason?: string,
): Promise<Appointment> {
  const response = await apiClient.post<Appointment>(`/appointments/${accessToken}/cancel/`, {
    reason: reason ?? '',
  })
  return response.data
}

export async function rescheduleAppointment(
  accessToken: string,
  startDatetime: string,
): Promise<Appointment> {
  const response = await apiClient.post<Appointment>(`/appointments/${accessToken}/reschedule/`, {
    start_datetime: startDatetime,
  })
  return response.data
}

export async function submitReview(
  accessToken: string,
  input: ReviewInput,
): Promise<Appointment> {
  const response = await apiClient.post<Appointment>(`/appointments/${accessToken}/review/`, input)
  return response.data
}
