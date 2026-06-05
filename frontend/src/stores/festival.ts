import { defineStore } from 'pinia'

import { screeningsOverlapWithBuffer } from '@/lib/planning'
import { buildPreviewDataset } from '@/mock/nifff2025Preview'
import { api } from '@/services/api'
import type { Cycle, DataSourceMode, Film, ImportSummary, Priority, Screening } from '@/types'

const STORAGE_KEY = 'potential-spork-festival-ui-state'
const previewDataset = buildPreviewDataset()
const mockCycles: Cycle[] = previewDataset.cycles
const mockFilms: Film[] = previewDataset.films
const mockScreenings: Screening[] = previewDataset.screenings

type PersistedFestivalUiState = {
  version: 1
  filmPriorities: Record<number, Priority>
  screeningSelections: Record<number, Screening['selection_status']>
}

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

function readPersistedUiState(): PersistedFestivalUiState | null {
  if (typeof window === 'undefined') {
    return null
  }

  const raw = window.localStorage.getItem(STORAGE_KEY)
  if (!raw) {
    return null
  }

  try {
    const parsed = JSON.parse(raw) as Partial<PersistedFestivalUiState>
    return {
      version: 1,
      filmPriorities: parsed.filmPriorities ?? {},
      screeningSelections: parsed.screeningSelections ?? {},
    }
  } catch {
    return null
  }
}

function persistUiState(films: Film[], screenings: Screening[]) {
  if (typeof window === 'undefined') {
    return
  }

  const filmPriorities = films.reduce<Record<number, Priority>>((result, film) => {
    if (film.priority !== 'unreviewed') {
      result[film.id] = film.priority
    }
    return result
  }, {})

  const screeningSelections = screenings.reduce<Record<number, Screening['selection_status']>>((result, screening) => {
    if (screening.selection_status !== 'none') {
      result[screening.id] = screening.selection_status
    }
    return result
  }, {})

  const payload: PersistedFestivalUiState = {
    version: 1,
    filmPriorities,
    screeningSelections,
  }

  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(payload))
}

function applyPersistedUiState(films: Film[], screenings: Screening[]): { films: Film[]; screenings: Screening[] } {
  const persisted = readPersistedUiState()
  if (!persisted) {
    return {
      films,
      screenings: recomputeScreeningStates(screenings),
    }
  }

  const nextFilms = films.map((film) => {
    const persistedPriority = persisted.filmPriorities[film.id]
    if (!persistedPriority) {
      return film
    }

    return {
      ...film,
      priority: sanitizePriority(persistedPriority),
    }
  })

  const nextScreenings = screenings.map((screening) => {
    const persistedSelection = persisted.screeningSelections[screening.id]
    if (!persistedSelection || persistedSelection === 'none') {
      return screening
    }

    return {
      ...screening,
      selection_status: persistedSelection,
    }
  })

  return {
    films: nextFilms,
    screenings: recomputeScreeningStates(nextScreenings),
  }
}

export const useFestivalStore = defineStore('festival', {
  state: () => ({
    cycles: [] as Cycle[],
    films: [] as Film[],
    screenings: [] as Screening[],
    loading: false,
    loadError: null as string | null,
    usingMocks: false,
    effectiveSourceMode: 'demo' as DataSourceMode,
    sourceFallbackReason: null as string | null,
    sourceSwitchPending: false,
    lastImportSummary: null as ImportSummary | null,
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
    sourceStatus(state) {
      if (state.sourceSwitchPending) {
        return {
          label: 'Sync…',
          tone: 'info' as const,
          description: 'Import en cours puis rechargement du catalogue.',
          showBadge: true,
        }
      }

      if (state.usingMocks && state.effectiveSourceMode === 'prod') {
        return {
          label: 'Fallback démo',
          tone: 'warning' as const,
          description:
            state.sourceFallbackReason ?? 'Les données live sont indisponibles pour le moment. L’application affiche une démonstration de secours.',
          showBadge: true,
        }
      }

      if (state.usingMocks || state.effectiveSourceMode === 'demo') {
        return {
          label: 'Démo',
          tone: 'subtle' as const,
          description: 'La source archive ou les données de démonstration sont actuellement utilisées.',
          showBadge: true,
        }
      }

      return {
        label: 'Live',
        tone: 'success' as const,
        description: 'Le programme courant est chargé depuis la source live.',
        showBadge: false,
      }
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
        this.sourceFallbackReason = 'Aucune donnée backend disponible : démonstration locale activée.'
      }

      const hydrated = applyPersistedUiState(this.films, this.screenings)
      this.films = hydrated.films
      this.screenings = hydrated.screenings
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
          const hydrated = applyPersistedUiState(sanitizeFilms(mockFilms), mockScreenings)
          this.films = hydrated.films
          this.screenings = hydrated.screenings
          this.usingMocks = true
          this.sourceFallbackReason = 'Le backend a répondu sans catalogue exploitable. Démonstration locale activée.'
          return
        }

        this.cycles = sanitizeCycles(cycles)
        const hydrated = applyPersistedUiState(sanitizeFilms(films), screenings)
        this.films = hydrated.films
        this.screenings = hydrated.screenings
        this.usingMocks = false
        this.sourceFallbackReason = null
      } catch {
        this.cycles = sanitizeCycles(mockCycles)
        const hydrated = applyPersistedUiState(sanitizeFilms(mockFilms), mockScreenings)
        this.films = hydrated.films
        this.screenings = hydrated.screenings
        this.usingMocks = true
        this.sourceFallbackReason = 'Impossible de charger les données réelles. Démonstration locale activée.'
        this.loadError = 'Impossible de charger les données réelles. Démonstration locale activée.'
      } finally {
        this.loading = false
      }
    },
    async switchSource(mode: DataSourceMode) {
      this.sourceSwitchPending = true
      this.loadError = null
      try {
        const summary = await api.importCatalog(2025, mode)
        this.lastImportSummary = summary
        this.effectiveSourceMode = mode
        await this.bootstrap()
      } finally {
        this.sourceSwitchPending = false
      }
    },
    updateFilmPriority(filmId: number, priority: Priority) {
      this.ensureWorkingData()
      const target = this.films.find((film) => film.id === filmId)
      if (target) {
        target.priority = priority
        persistUiState(this.films, this.screenings)
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
        const hydrated = applyPersistedUiState(this.films, screenings)
        this.screenings = hydrated.screenings
        persistUiState(this.films, this.screenings)
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
      persistUiState(this.films, this.screenings)
    },
  },
})
