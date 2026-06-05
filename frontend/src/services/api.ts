import type { Cycle, DataSourceMode, Film, ImportSummary, Screening } from '@/types'

const API_BASE = 'http://localhost:8000/api'

async function readJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...init,
  })

  if (!response.ok) {
    throw new Error(`API error on ${path}`)
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
  importCatalog: (year = 2025, source_mode: DataSourceMode = 'demo') =>
    readJson<ImportSummary>('/imports/nifff/catalog', {
      method: 'POST',
      body: JSON.stringify({ year, source_mode }),
    }),
}
