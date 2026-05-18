import { defineStore } from 'pinia'

import { buildPreviewDataset } from '@/mock/nifff2025Preview'
import { api } from '@/services/api'
import type { Cycle, Film, Priority, Screening } from '@/types'

const previewDataset = buildPreviewDataset()
const mockCycles: Cycle[] = previewDataset.cycles
const mockFilms: Film[] = previewDataset.films
const mockScreenings: Screening[] = previewDataset.screenings

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
    selectedScreenings(state) {
      const screenings = state.screenings.length ? state.screenings : mockScreenings
      return screenings.filter(
        (screening) => screening.selection_status === 'tentative' || screening.selection_status === 'confirmed',
      )
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

        const hasRealData = cycles.length > 0 || films.length > 0 || screenings.length > 0
        if (!hasRealData) {
          this.cycles = mockCycles
          this.films = mockFilms
          this.screenings = mockScreenings
          this.usingMocks = true
          return
        }

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
    updateFilmPriority(filmId: number, priority: Priority) {
      const target = this.films.find((film) => film.id === filmId)
      if (target) {
        target.priority = priority
      }
    },
    updateCyclePriority(cycleId: number, priority: Priority) {
      const target = this.cycles.find((cycle) => cycle.id === cycleId)
      if (target) {
        target.priority = priority
      }
    },
  },
})
