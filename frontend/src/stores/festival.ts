import { defineStore } from 'pinia'

import { api } from '@/services/api'
import type { Cycle, Film, Screening } from '@/types'

const mockCycles: Cycle[] = [
  { id: 1, name: 'International Competition', slug: 'international-competition', color: '#ff5b57', priority: 'must-see' },
  { id: 2, name: 'Take Care', slug: 'take-care', color: '#8d6bff', priority: 'high' },
  { id: 3, name: 'NIFFF Invasion', slug: 'nifff-invasion', color: '#4d5868', priority: 'ignore' },
]

const mockFilms: Film[] = [
  {
    id: 1,
    title: 'Alpha',
    slug: 'alpha',
    directors: 'Julia Ducournau',
    year: 2025,
    countries: 'FR/BE',
    duration_minutes: 128,
    tagline: 'Marble-skin Allegory',
    cast: 'Tahar Rahim, Golshifteh Farahani, Mélissa Boros',
    synopsis: null,
    language: 'français / ov sub en',
    age_rating: '16',
    priority: 'must-see',
    cycle_id: 1,
    cycle_name: 'International Competition',
    cycle_color: '#ff5b57',
  },
  {
    id: 2,
    title: 'A Cure for Wellness',
    slug: 'a-cure-for-wellness',
    directors: 'Gore Verbinski',
    year: 2016,
    countries: 'DE/LU/US',
    duration_minutes: 146,
    tagline: 'Eurotrash Wellness Horror',
    cast: 'Dane DeHaan, Jason Isaacs, Mia Goth',
    synopsis: null,
    language: null,
    age_rating: null,
    priority: 'high',
    cycle_id: 2,
    cycle_name: 'Take Care',
    cycle_color: '#8d6bff',
  },
  {
    id: 3,
    title: 'Fantastic Shorts',
    slug: 'fantastic-shorts',
    directors: null,
    year: 2025,
    countries: 'CH',
    duration_minutes: 60,
    tagline: 'Shorts package',
    cast: null,
    synopsis: null,
    language: null,
    age_rating: null,
    priority: 'ignore',
    cycle_id: 3,
    cycle_name: 'NIFFF Invasion',
    cycle_color: '#4d5868',
  },
]

const mockScreenings: Screening[] = [
  {
    id: 1,
    film_id: 1,
    film_title: 'Alpha',
    venue_id: 1,
    venue_name: 'Théâtre du Passage',
    starts_at: '2026-07-04T19:00:00',
    ends_at: '2026-07-04T21:08:00',
    selection_status: 'tentative',
    derived_state: 'selected',
  },
  {
    id: 2,
    film_id: 2,
    film_title: 'A Cure for Wellness',
    venue_id: 2,
    venue_name: 'Rex',
    starts_at: '2026-07-04T21:45:00',
    ends_at: '2026-07-05T00:11:00',
    selection_status: 'none',
    derived_state: 'available',
  },
]

export const useFestivalStore = defineStore('festival', {
  state: () => ({
    cycles: [] as Cycle[],
    films: [] as Film[],
    screenings: [] as Screening[],
    loading: false,
    usingMocks: false,
  }),
  getters: {
    groupedFilms(state) {
      const cycles = state.cycles.length ? state.cycles : mockCycles
      const films = state.films.length ? state.films : mockFilms

      return cycles.map((cycle) => ({
        cycle,
        films: films.filter((film) => film.cycle_id === cycle.id),
      }))
    },
    highlightedFilms(state) {
      const films = state.films.length ? state.films : mockFilms
      return films.filter((film) => film.priority === 'must-see' || film.priority === 'high')
    },
    visibleScreenings(state) {
      return state.screenings.length ? state.screenings : mockScreenings
    },
  },
  actions: {
    async bootstrap() {
      this.loading = true
      try {
        const [cycles, films, screenings] = await Promise.all([
          api.listCycles(),
          api.listFilms(),
          api.listScreenings(),
        ])
        this.cycles = cycles
        this.films = films
        this.screenings = screenings
        this.usingMocks = false
      } catch {
        this.cycles = mockCycles
        this.films = mockFilms
        this.screenings = mockScreenings
        this.usingMocks = true
      } finally {
        this.loading = false
      }
    },
  },
})
