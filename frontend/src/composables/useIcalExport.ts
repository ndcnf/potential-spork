import { computed } from 'vue'

import { useFestivalStore } from '@/stores/festival'

const BACKEND_EXPORT_URL = 'http://localhost:8000/api/exports/confirmed.ics'

function escapeIcsText(value: string): string {
  return value.replace(/\\/g, '\\\\').replace(/;/g, '\\;').replace(/,/g, '\\,').replace(/\n/g, '\\n')
}

function toIcsDateTime(value: string | null): string | null {
  if (!value) return null
  const match = value.match(/^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})(?::(\d{2}))?/) 
  if (!match) return null
  const [, year, month, day, hours, minutes, seconds] = match
  return `${year}${month}${day}T${hours}${minutes}${seconds ?? '00'}`
}

function buildLocalCalendar(screenings: ReturnType<typeof useFestivalStore>['visibleScreenings']): string {
  const lines = ['BEGIN:VCALENDAR', 'VERSION:2.0', 'PRODID:-//Potential Spork//Festival Planner//FR']

  for (const screening of screenings) {
    if (screening.selection_status !== 'confirmed') continue
    const dtstart = toIcsDateTime(screening.starts_at)
    const dtend = toIcsDateTime(screening.ends_at)
    if (!dtstart || !dtend) continue

    lines.push('BEGIN:VEVENT')
    lines.push(`UID:screening-${screening.id}@potential-spork`)
    lines.push(`SUMMARY:${escapeIcsText(screening.film_title)}`)
    lines.push(`DTSTART:${dtstart}`)
    lines.push(`DTEND:${dtend}`)
    if (screening.venue_name) {
      lines.push(`LOCATION:${escapeIcsText(screening.venue_name)}`)
    }
    lines.push('END:VEVENT')
  }

  lines.push('END:VCALENDAR')
  return `${lines.join('\r\n')}\r\n`
}

export function useIcalExport() {
  const store = useFestivalStore()

  const exportHref = computed(() => (store.usingMocks ? '#' : BACKEND_EXPORT_URL))

  function exportIcal(event?: Event): void {
    if (!store.usingMocks) {
      return
    }

    event?.preventDefault()

    const calendar = buildLocalCalendar(store.visibleScreenings)
    const blob = new Blob([calendar], { type: 'text/calendar;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = 'potential-spork-confirmed.ics'
    link.click()
    URL.revokeObjectURL(url)
  }

  return {
    exportHref,
    exportIcal,
  }
}
