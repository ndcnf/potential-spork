import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { useFestivalStore } from '@/stores/festival'
import type { Screening } from '@/types'

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
    store.films = [
      {
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
      },
    ]
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
})
