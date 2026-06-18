import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { useFestivalStore } from '@/stores/festival'
import type { Cycle, Film, Screening } from '@/types'

const apiMock = vi.hoisted(() => ({
  listCycles: vi.fn(),
  listFilms: vi.fn(),
  listScreenings: vi.fn(),
  updateScreeningSelection: vi.fn(),
  resetUserChoices: vi.fn(),
  importCatalog: vi.fn(),
}))

vi.mock('@/services/api', () => ({
  api: apiMock,
}))

function screening(overrides: Partial<Screening> = {}): Screening {
  return {
    id: 42,
    film_id: 7,
    film_title: 'After Darkness',
    venue_id: 3,
    venue_name: 'Rex',
    starts_at: '2025-07-05T18:00:00+02:00',
    ends_at: '2025-07-05T20:00:00+02:00',
    selection_status: 'tentative',
    derived_state: 'selected',
    ...overrides,
  }
}

function cycle(overrides: Partial<Cycle> = {}): Cycle {
  return {
    id: 1,
    name: 'Demo Cycle',
    slug: 'demo-cycle',
    color: null,
    priority: 'unreviewed',
    ...overrides,
  }
}

function film(overrides: Partial<Film> = {}): Film {
  return {
    id: 7,
    title: 'After Darkness',
    slug: 'after-darkness',
    directors: null,
    year: 1985,
    countries: 'CH/UK',
    duration_minutes: 110,
    tagline: null,
    cast: null,
    synopsis: null,
    language: null,
    age_rating: null,
    priority: 'high',
    planning_type: 'standalone',
    cycle_id: null,
    cycle_name: null,
    cycle_color: null,
    ...overrides,
  }
}

function stubLocalStorage(initial: Record<string, string> = {}) {
  const storage = new Map(Object.entries(initial))
  const localStorage = {
    getItem: vi.fn((key: string) => storage.get(key) ?? null),
    setItem: vi.fn((key: string, value: string) => {
      storage.set(key, value)
    }),
    removeItem: vi.fn((key: string) => {
      storage.delete(key)
    }),
  }

  vi.stubGlobal('window', { localStorage })

  return { localStorage, storage }
}

describe('festival store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.restoreAllMocks()
    vi.clearAllMocks()
  })

  it('keeps the fresh backend screening status over a stale localStorage selection', async () => {
    const staleUiState = {
      version: 1,
      filmPriorities: {},
      screeningSelections: {
        42: 'tentative',
      },
    }
    const { storage } = stubLocalStorage({
      'potential-spork-festival-ui-state': JSON.stringify(staleUiState),
    })
    const store = useFestivalStore()

    store.usingMocks = false
    store.films = [film()]
    store.screenings = [screening()]
    apiMock.updateScreeningSelection.mockResolvedValue(screening({ selection_status: 'confirmed' }))
    apiMock.listScreenings.mockResolvedValue([screening({ selection_status: 'confirmed' })])

    await store.setScreeningSelection(42, 'confirmed')

    expect(store.screenings[0].selection_status).toBe('confirmed')
    expect(JSON.parse(storage.get('potential-spork-festival-ui-state') ?? '{}')).toMatchObject({
      screeningSelections: {
        42: 'confirmed',
      },
    })
  })

  it('replaces an existing demo catalog with the live catalog as one dataset', async () => {
    stubLocalStorage()
    const store = useFestivalStore()

    store.usingMocks = true
    store.effectiveSourceMode = 'demo'
    store.cycles = [cycle({ id: 1, name: 'Demo Cycle' })]
    store.films = [film({ id: 10, title: 'Demo Film', cycle_id: 1 })]
    store.screenings = [screening({ id: 100, film_id: 10 })]

    apiMock.listCycles.mockResolvedValue([cycle({ id: 101, name: 'Live Cycle' })])
    apiMock.listFilms.mockResolvedValue([film({ id: 202, title: 'Live Film', cycle_id: 101 })])
    apiMock.listScreenings.mockResolvedValue([screening({ id: 303, film_id: 202 })])

    await store.bootstrap('prod')

    expect(store.usingMocks).toBe(false)
    expect(store.effectiveSourceMode).toBe('prod')
    expect(store.cycles.map((item) => item.name)).toEqual(['Live Cycle'])
    expect(store.films.map((item) => item.title)).toEqual(['Live Film'])
    expect(store.screenings.map((item) => item.id)).toEqual([303])
  })

  it('does not mix mock films into grouped films when a live catalog is partial', () => {
    const store = useFestivalStore()

    store.usingMocks = false
    store.effectiveSourceMode = 'prod'
    store.cycles = [cycle({ id: 1, name: 'Live Cycle' })]
    store.films = []
    store.screenings = []

    expect(store.groupedFilms).toEqual([
      {
        cycle: store.cycles[0],
        films: [],
      },
    ])
  })

  it('keeps live mode empty and reports an error when live loading fails', async () => {
    stubLocalStorage()
    const store = useFestivalStore()

    store.usingMocks = true
    store.effectiveSourceMode = 'demo'
    store.cycles = [cycle({ id: 1, name: 'Demo Cycle' })]
    store.films = [film({ id: 10, title: 'Demo Film', cycle_id: 1 })]
    store.screenings = [screening({ id: 100, film_id: 10 })]
    apiMock.listCycles.mockRejectedValue(new Error('live unavailable'))

    await store.bootstrap('prod')

    expect(store.usingMocks).toBe(false)
    expect(store.effectiveSourceMode).toBe('prod')
    expect(store.cycles).toEqual([])
    expect(store.films).toEqual([])
    expect(store.screenings).toEqual([])
    expect(store.groupedFilms).toEqual([])
    expect(store.loadError).toBe('Impossible de charger les données live pour le moment.')
    expect(store.sourceStatus).toMatchObject({
      label: 'Live indisponible',
      tone: 'warning',
    })
  })

  it('keeps live mode empty and reports an error when live returns no catalog', async () => {
    stubLocalStorage()
    const store = useFestivalStore()

    apiMock.listCycles.mockResolvedValue([])
    apiMock.listFilms.mockResolvedValue([])
    apiMock.listScreenings.mockResolvedValue([])

    await store.bootstrap('prod')

    expect(store.usingMocks).toBe(false)
    expect(store.effectiveSourceMode).toBe('prod')
    expect(store.cycles).toEqual([])
    expect(store.films).toEqual([])
    expect(store.screenings).toEqual([])
    expect(store.groupedFilms).toEqual([])
    expect(store.loadError).toBe('Aucun catalogue live exploitable n’est disponible pour le moment.')
  })

  it('keeps live mode selected when live import fails before catalog loading', async () => {
    stubLocalStorage()
    const store = useFestivalStore()

    store.usingMocks = true
    store.effectiveSourceMode = 'demo'
    store.cycles = [cycle({ id: 1, name: 'Demo Cycle' })]
    store.films = [film({ id: 10, title: 'Demo Film', cycle_id: 1 })]
    store.screenings = [screening({ id: 100, film_id: 10 })]
    apiMock.importCatalog.mockRejectedValue(new Error('nifff.ch unavailable'))

    await store.switchSource('prod')

    expect(store.usingMocks).toBe(false)
    expect(store.effectiveSourceMode).toBe('prod')
    expect(store.cycles).toEqual([])
    expect(store.films).toEqual([])
    expect(store.screenings).toEqual([])
    expect(store.loadError).toBe('Impossible de récupérer les données live depuis nifff.ch pour le moment.')
    expect(store.sourceStatus).toMatchObject({
      label: 'Live indisponible',
      tone: 'warning',
    })
  })

  it('passes the selected live source URL to the import request', async () => {
    stubLocalStorage()
    const store = useFestivalStore()

    apiMock.importCatalog.mockResolvedValue({
      cycles_created: 0,
      films_created: 0,
      films_updated: 0,
      venues_created: 0,
      venues_updated: 0,
      screenings_created: 0,
      screenings_updated: 0,
      warnings_count: 0,
      errors_count: 0,
      warnings: [],
      errors: [],
    })
    apiMock.listCycles.mockResolvedValue([cycle({ id: 101, name: 'Live Cycle' })])
    apiMock.listFilms.mockResolvedValue([film({ id: 202, title: 'Live Film', cycle_id: 101 })])
    apiMock.listScreenings.mockResolvedValue([screening({ id: 303, film_id: 202 })])

    await store.switchSource('prod', 'https://nifff.ch/programme/')

    expect(apiMock.importCatalog).toHaveBeenCalledWith(2025, 'prod', 'https://nifff.ch/programme/')
    expect(store.films.map((item) => item.title)).toEqual(['Live Film'])
  })
})
