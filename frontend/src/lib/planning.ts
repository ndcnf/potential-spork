import type { Screening } from '@/types'

export const RESERVATION_BUFFER_MINUTES = 15
export const FESTIVAL_DAY_CUTOFF_HOUR = 6

function normalizeFestivalDate(value: string | null): Date | null {
  if (!value) return null

  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return null
  }

  if (date.getHours() < FESTIVAL_DAY_CUTOFF_HOUR) {
    date.setDate(date.getDate() + 1)
  }

  return date
}

function toTimestamp(value: string | null): number {
  if (!value) return 0
  return normalizeFestivalDate(value)?.getTime() ?? new Date(value).getTime()
}

export function toMinutes(value: string | null): number {
  if (!value) return 0
  const hours = Number(value.slice(11, 13))
  const minutes = Number(value.slice(14, 16))
  const normalizedHours = hours < FESTIVAL_DAY_CUTOFF_HOUR ? hours + 24 : hours
  return normalizedHours * 60 + minutes
}

export function getFestivalDayKey(value: string | null): string {
  return value?.slice(0, 10) ?? 'Sans date'
}

export function screeningsOverlapWithBuffer(
  left: Pick<Screening, 'id' | 'starts_at' | 'ends_at'>,
  right: Pick<Screening, 'id' | 'starts_at' | 'ends_at'>,
  bufferMinutes = RESERVATION_BUFFER_MINUTES,
): boolean {
  if (!left.starts_at || !left.ends_at || !right.starts_at || !right.ends_at || left.id === right.id) {
    return false
  }
  const bufferMs = bufferMinutes * 60 * 1000
  const leftStart = toTimestamp(left.starts_at)
  const leftEnd = toTimestamp(left.ends_at)
  const rightStart = toTimestamp(right.starts_at)
  const rightEnd = toTimestamp(right.ends_at)

  return leftStart < rightEnd + bufferMs && rightStart < leftEnd + bufferMs
}

export function formatMinutes(minutes: number | null | undefined): string {
  if (minutes == null) return '? min'
  if (minutes < 60) return `${minutes} min`

  const hours = Math.floor(minutes / 60)
  const remainder = minutes % 60
  if (remainder === 0) return `${hours}h`
  return `${hours}h${String(remainder).padStart(2, '0')}`
}

export function formatTimeRange(start: string | null, end: string | null): string {
  return `${start?.slice(11, 16) ?? '--:--'} - ${end?.slice(11, 16) ?? '--:--'}`
}
