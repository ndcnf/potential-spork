import type { Cycle, DataSourceMode, Film, ImportSummary, ResetUserChoicesSummary, Screening } from '@/types'

const API_BASE = 'http://localhost:8000/api'

function formatApiDetail(detail: unknown): string | null {
  if (typeof detail === 'string' && detail.trim()) {
    return detail
  }

  if (Array.isArray(detail) && detail.length > 0) {
    return detail
      .map((item) => {
        if (typeof item === 'string') return item
        if (item && typeof item === 'object' && 'msg' in item && typeof item.msg === 'string') return item.msg
        return JSON.stringify(item)
      })
      .join(' · ')
  }

  return null
}

async function readJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...init,
  })

  if (!response.ok) {
    let apiMessage: string | null = null
    try {
      const payload = (await response.json()) as { detail?: unknown }
      apiMessage = formatApiDetail(payload.detail)
    } catch {
      apiMessage = null
    }

    throw new Error(apiMessage ?? `API error ${response.status} on ${path}`)
  }

  return response.json() as Promise<T>
}

export const api = {
  listCycles: () => readJson<Cycle[]>('/cycles'),
  listFilms: () => readJson<Film[]>('/films'),
  listScreenings: () => readJson<Screening[]>('/screenings'),
  updateScreeningSelection: (screeningId: number, selection_status: Screening['selection_status']) =>
    readJson<Screening>(`/screenings/${screeningId}`, {
      method: 'PATCH',
      body: JSON.stringify({ selection_status }),
    }),
  resetUserChoices: () =>
    readJson<ResetUserChoicesSummary>('/user-choices/reset', {
      method: 'POST',
    }),
  importCatalog: (year = 2025, source_mode: DataSourceMode = 'demo', schedule_url?: string) =>
    readJson<ImportSummary>('/imports/nifff/catalog', {
      method: 'POST',
      body: JSON.stringify({ year, source_mode, schedule_url: schedule_url || null }),
    }),
}
