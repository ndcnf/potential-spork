import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { usePlanningModel } from '@/composables/usePlanningModel'
import { useFestivalStore } from '@/stores/festival'
import { useSettingsStore } from '@/stores/settings'
import type { Film, Screening } from '@/types'

function film(overrides: Partial<Film>): Film {
  return {
    id: 1,
    title: 'Film',
    slug: 'film',
    directors: null,
    year: 2025,
    countries: null,
    duration_minutes: 90,
    tagline: null,
    cast: null,
    synopsis: null,
    language: null,
    age_rating: null,
    priority: 'medium',
    planning_type: 'standalone',
    cycle_id: null,
    cycle_name: null,
    cycle_color: null,
    ...overrides,
  }
}

function screening(overrides: Partial<Screening>): Screening {
  return {
    id: 1,
    film_id: 1,
    film_title: 'Film',
    venue_id: 1,
    venue_name: 'Rex',
    starts_at: '2025-07-05T18:00:00+02:00',
    ends_at: '2025-07-05T19:30:00+02:00',
    selection_status: 'none',
    derived_state: 'available',
    ...overrides,
  }
}

function stubLocalStorage() {
  const storage = new Map<string, string>()
  vi.stubGlobal('window', {
    localStorage: {
      getItem: vi.fn((key: string) => storage.get(key) ?? null),
      setItem: vi.fn((key: string, value: string) => storage.set(key, value)),
      removeItem: vi.fn((key: string) => storage.delete(key)),
    },
    innerWidth: 1200,
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
  })
}

describe('usePlanningModel recommendations', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.restoreAllMocks()
    vi.clearAllMocks()
    stubLocalStorage()
  })

  it('recommends immanquable films before peut-être films when sessions compete', () => {
    const festivalStore = useFestivalStore()
    const settingsStore = useSettingsStore()

    settingsStore.setRecommendationEnabled(true)
    settingsStore.setVenueScore('Rex', 1)
    festivalStore.films = [
      film({ id: 1, title: 'Maybe Film', priority: 'medium' }),
      film({ id: 2, title: 'Must Film', priority: 'high' }),
    ]
    festivalStore.screenings = [
      screening({ id: 101, film_id: 1, film_title: 'Maybe Film', starts_at: '2025-07-05T18:00:00+02:00', ends_at: '2025-07-05T19:30:00+02:00' }),
      screening({ id: 201, film_id: 2, film_title: 'Must Film', starts_at: '2025-07-05T18:15:00+02:00', ends_at: '2025-07-05T19:45:00+02:00' }),
      screening({ id: 202, film_id: 2, film_title: 'Must Film', starts_at: '2025-07-06T18:15:00+02:00', ends_at: '2025-07-06T19:45:00+02:00' }),
    ]

    const model = usePlanningModel()

    expect(model.planningScreenings.value.find((item) => item.id === 101)?.isRecommended).toBe(false)
    expect(model.planningScreenings.value.find((item) => item.id === 201)?.isRecommended).toBe(true)
  })
})
