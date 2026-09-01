import { isAxiosError } from 'axios'

const DEFAULT_MESSAGE = 'Ocurrió un error inesperado. Intenta de nuevo.'

/** Extracts a displayable message from a DRF error response ({"detail": "..."} or
 * {"field": ["..."]}), falling back to a generic message for network/unknown errors. */
export function getErrorMessage(error: unknown): string {
  if (!isAxiosError(error)) {
    return DEFAULT_MESSAGE
  }

  const data: unknown = error.response?.data
  if (!data || typeof data !== 'object') {
    return DEFAULT_MESSAGE
  }

  const payload = data as Record<string, unknown>

  if (typeof payload.detail === 'string') {
    return payload.detail
  }

  for (const value of Object.values(payload)) {
    if (typeof value === 'string') {
      return value
    }
    if (Array.isArray(value) && typeof value[0] === 'string') {
      return value[0]
    }
  }

  return DEFAULT_MESSAGE
}
