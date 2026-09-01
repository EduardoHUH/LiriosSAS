const TIME_ZONE = 'America/Tegucigalpa'

/** All formatting pins to the salon's own timezone, not the visitor's
 * browser timezone -- a slot's displayed time must match business hours
 * regardless of where the customer is browsing from. */

export function formatDayChip(date: Date): { weekday: string; day: string; month: string } {
  const weekday = new Intl.DateTimeFormat('es-HN', { weekday: 'short', timeZone: TIME_ZONE }).format(date)
  const day = new Intl.DateTimeFormat('es-HN', { day: 'numeric', timeZone: TIME_ZONE }).format(date)
  const month = new Intl.DateTimeFormat('es-HN', { month: 'short', timeZone: TIME_ZONE }).format(date)
  return { weekday, day, month }
}

export function formatSlotTime(isoDatetime: string): string {
  return new Intl.DateTimeFormat('es-HN', {
    hour: 'numeric',
    minute: '2-digit',
    timeZone: TIME_ZONE,
  }).format(new Date(isoDatetime))
}

export function formatFullDateTime(isoDatetime: string): string {
  return new Intl.DateTimeFormat('es-HN', {
    weekday: 'long',
    day: 'numeric',
    month: 'long',
    hour: 'numeric',
    minute: '2-digit',
    timeZone: TIME_ZONE,
  }).format(new Date(isoDatetime))
}

export function toDateParam(date: Date): string {
  return new Intl.DateTimeFormat('en-CA', { timeZone: TIME_ZONE }).format(date)
}
