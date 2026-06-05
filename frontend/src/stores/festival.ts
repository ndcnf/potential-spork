import { defineStore } from 'pinia'

import { screeningsOverlapWithBuffer } from '@/lib/planning'
import { buildPreviewDataset } from '@/mock/nifff2025Preview'
import { api } from '@/services/api'
import type { Cycle, Film, Priority, Screening } from '@/types'

const previewDataset = buildPreviewDataset()
const mockCycles: Cycle[] = previewDataset.cycles
const mockFilms: Film[] = previewDataset.films
const mockScreenings: Screening[] = previewDataset.screenings

function normalizePriority(priority: Priority): 'pending' | 'ignore' | 'medium' | 'high' {
  if (priority === 'must-see' || priority === 'high') {
    return 'high'
  }

  if (priority === 'medium') {
    return 'medium'
  }

  if (priority === 'unreviewed' || priority === 'low') {
    return 'pending'
  }

  return 'ignore'
}

function sanitizePriority(priority: Priority | null | undefined): Priority {
  if (!priority || priority === 'low') {
    return 'unreviewed'
  }

  return priority
}

function sanitizeFilms(films: Film[]): Film[] {
  return films.map((film) => ({
    ...film,
    priority: sanitizePriority(film.priority),
  }))
}

function sanitizeCycles(cycles: Cycle[]): Cycle[] {
  return cycles.map((cycle) => ({
    ...cycle,
    priority: sanitizePriority(cycle.priority),
  }))
}

function recomputeScreeningStates(screenings: Screening[]): Screening[] {
  return screenings.map((screening) => {
    if (screening.selection_status === 'tentative' || screening.selection_status === 'confirmed') {
      return { ...screening, derived_state: 'selected' }
    }

    if (screening.selection_status === 'rejected') {
      return { ...screening, derived_state: 'rejected' }
    }

    const siblingConfirmed = screenings.find(
      (other) =>
        other.film_id === screening.film_id &&
        other.id !== screening.id &&
        other.selection_status === 'confirmed',
    )

    if (siblingConfirmed) {
      return { ...screening, derived_state: 'disabled' }
    }

    const conflictSelected = screenings.find(
      (other) =>
        other.id !== screening.id &&
        (other.selection_status === 'tentative' || other.selection_status === 'confirmed') &&
        screeningsOverlapWithBuffer(screening, other),
    )

    if (conflictSelected) {
      return { ...screening, derived_state: 'conflict' }
    }

    return { ...screening, derived_state: 'available' }
  })
}

export const useFestivalStore = defineStore('festival', {
  state: () => ({
    cycles: [] as Cycle[],
    films: [] as Film[],
    screenings: [] as Screening[],
    loading: false,
    loadError: null as string | null,
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
      return films.filter((film) => normalizePriority(film.priority) === 'high')
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
    ensureWorkingData() {
      if (!this.cycles.length) {
        this.cycles = sanitizeCycles(structuredClone(mockCycles))
      }
      if (!this.films.length) {
        this.films = sanitizeFilms(structuredClone(mockFilms))
      }
      if (!this.screenings.length) {
        this.screenings = structuredClone(mockScreenings)
        this.usingMocks = true
      }
    },
    async bootstrap() {
      this.loading = true
      this.loadError = null
      try {
        const [cycles, films, screenings] = await Promise.all([
          api.listCycles(),
          api.listFilms(),
          api.listScreenings(),
        ])

        const hasRealData = cycles.length > 0 || films.length > 0 || screenings.length > 0
        if (!hasRealData) {
          this.cycles = sanitizeCycles(mockCycles)
          this.films = sanitizeFilms(mockFilms)
          this.screenings = mockScreenings
          this.usingMocks = true
          return
        }

        this.cycles = sanitizeCycles(cycles)
        this.films = sanitizeFilms(films)
        this.screenings = screenings
        this.usingMocks = false
      } catch {
        this.cycles = sanitizeCycles(mockCycles)
        this.films = sanitizeFilms(mockFilms)
        this.screenings = mockScreenings
        this.usingMocks = true
        this.loadError = 'Impossible de charger les données réelles. Mode démo activé.'
      } finally {
        this.loading = false
      }
    },
    updateFilmPriority(filmId: number, priority: Priority) {
      this.ensureWorkingData()
      const target = this.films.find((film) => film.id === filmId)
      if (target) {
        target.priority = priority
      }
    },
    updateCyclePriority(cycleId: number, priority: Priority) {
      this.ensureWorkingData()
      const target = this.cycles.find((cycle) => cycle.id === cycleId)
      if (target) {
        target.priority = priority
      }
    },
    async setScreeningSelection(screeningId: number, status: Screening['selection_status']) {
      this.ensureWorkingData()

      const target = this.screenings.find((screening) => screening.id === screeningId)
      if (!target) {
        return
      }

      if (!this.usingMocks) {
        await api.updateScreeningSelection(screeningId, status)
        const screenings = await api.listScreenings()
        this.screenings = screenings
        return
      }

      if (status === 'none' || status === 'rejected') {
        target.selection_status = 'none'
        if (status === 'rejected') {
          target.selection_status = 'rejected'
        }
      } else {
        target.selection_status = status
        if (status === 'confirmed') {
          for (const sibling of this.screenings) {
            if (sibling.film_id === target.film_id && sibling.id !== target.id && sibling.selection_status !== 'rejected') {
              sibling.selection_status = 'none'
            }
          }
        }
      }

      this.screenings = recomputeScreeningStates(this.screenings)
    },
  },
})
