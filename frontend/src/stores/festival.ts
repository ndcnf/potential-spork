import { defineStore } from 'pinia'

import { screeningsOverlapWithBuffer } from '@/lib/planning'
import { buildPreviewDataset } from '@/mock/nifff2025Preview'
import { api } from '@/services/api'
import { useSettingsStore } from '@/stores/settings'
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

function sanitizePlanningType(planningType: Film['planning_type'] | null | undefined): Film['planning_type'] {
  return planningType ?? 'standalone'
}

function isPlannableFilm(film: Film): boolean {
  return film.planning_type !== 'package_member'
}

function sanitizeFilms(films: Film[]): Film[] {
  return films.map((film) => ({
    ...film,
    priority: sanitizePriority(film.priority),
    planning_type: sanitizePlanningType(film.planning_type),
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

function clearPersistedUiState() {
  if (typeof window === 'undefined') {
    return
  }

  window.localStorage.removeItem(STORAGE_KEY)
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

function shouldIgnoreLegacyAllMediumPriorities(persisted: PersistedFestivalUiState, films: Film[]): boolean {
  const entries = Object.entries(persisted.filmPriorities)
  if (!entries.length || !films.length) {
    return false
  }

  const filmIds = new Set(films.map((film) => String(film.id)))
  const knownEntries = entries.filter(([filmId]) => filmIds.has(filmId))

  return knownEntries.length === films.length && knownEntries.every(([, priority]) => priority === 'medium')
}

function applyPersistedUiState(films: Film[], screenings: Screening[]): { films: Film[]; screenings: Screening[] } {
  const persisted = readPersistedUiState()
  if (!persisted) {
    return {
      films,
      screenings: recomputeScreeningStates(screenings),
    }
  }

  const ignorePersistedFilmPriorities = shouldIgnoreLegacyAllMediumPriorities(persisted, films)
  const nextFilms = films.map((film) => {
    if (ignorePersistedFilmPriorities) {
      return film
    }

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

function resetLocalUserChoices(films: Film[], screenings: Screening[]): { films: Film[]; screenings: Screening[] } {
  return {
    films: films.map((film) => ({
      ...film,
      priority: 'unreviewed',
    })),
    screenings: recomputeScreeningStates(
      screenings.map((screening) => ({
        ...screening,
        selection_status: 'none',
      })),
    ),
  }
}

function demoDataset() {
  return {
    cycles: sanitizeCycles(structuredClone(mockCycles)),
    films: sanitizeFilms(structuredClone(mockFilms)),
    screenings: structuredClone(mockScreenings),
  }
}

async function loadBackendCatalog() {
  const [cycles, films, screenings] = await Promise.all([
    api.listCycles(),
    api.listFilms(),
    api.listScreenings(),
  ])

  return {
    cycles,
    films,
    screenings,
    hasData: cycles.length > 0 || films.length > 0 || screenings.length > 0,
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
        films: films.filter((film) => film.cycle_id === cycle.id && isPlannableFilm(film)),
      }))
    },
    highlightedFilms(state) {
      return state.films.filter((film) => isPlannableFilm(film) && normalizePriority(film.priority) === 'high')
    },
    visibleScreenings(state) {
      return state.screenings
    },
    selectedScreenings(state) {
      return state.screenings.filter(
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

      if (state.usingMocks) {
        return {
          label: 'Démo',
          tone: 'subtle' as const,
          description:
            state.sourceFallbackReason ?? 'La démonstration locale est utilisée car la DB démo n’est pas disponible.',
          showBadge: true,
        }
      }

      if (state.effectiveSourceMode === 'demo') {
        return {
          label: 'Démo',
          tone: 'subtle' as const,
          description: state.sourceFallbackReason ?? 'La DB démo issue de l’archive Wayback est actuellement utilisée.',
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
    loadDemoData(reason: string | null = null) {
      const demo = demoDataset()
      const hydrated = applyPersistedUiState(demo.films, demo.screenings)
      this.cycles = demo.cycles
      this.films = hydrated.films
      this.screenings = hydrated.screenings
      this.usingMocks = true
      this.effectiveSourceMode = 'demo'
      this.sourceFallbackReason = reason
    },
    ensureWorkingData() {
      if (!this.cycles.length && !this.films.length && !this.screenings.length) {
        this.loadDemoData('Aucune donnée disponible : démonstration locale activée.')
      }

      const hydrated = applyPersistedUiState(this.films, this.screenings)
      this.films = hydrated.films
      this.screenings = hydrated.screenings
    },
    async bootstrap(sourceMode?: DataSourceMode) {
      const settingsStore = useSettingsStore()
      settingsStore.load()
      const requestedMode = sourceMode ?? settingsStore.dataSourceMode

      this.loading = true
      this.loadError = null
      try {
        if (requestedMode === 'demo') {
          try {
            const { cycles, films, screenings, hasData } = await loadBackendCatalog()

            if (!hasData) {
              this.loadDemoData('Aucune donnée en DB démo : démonstration locale activée.')
              return
            }

            this.cycles = sanitizeCycles(cycles)
            const hydrated = applyPersistedUiState(sanitizeFilms(films), screenings)
            this.films = hydrated.films
            this.screenings = hydrated.screenings
            this.usingMocks = false
            this.effectiveSourceMode = 'demo'
            this.sourceFallbackReason = screenings.length
              ? null
              : 'La DB démo est chargée, mais aucune séance exploitable n’est encore disponible.'
          } catch {
            this.loadDemoData('Backend indisponible : démonstration locale activée.')
            this.loadError = 'Backend indisponible : démonstration locale activée.'
          }
          return
        }

        const { cycles, films, screenings, hasData } = await loadBackendCatalog()

        if (!hasData) {
          this.loadDemoData('Le backend a répondu sans catalogue exploitable. Démonstration locale activée.')
          return
        }

        this.cycles = sanitizeCycles(cycles)
        const hydrated = applyPersistedUiState(sanitizeFilms(films), screenings)
        this.films = hydrated.films
        this.screenings = hydrated.screenings
        this.usingMocks = false
        this.effectiveSourceMode = 'prod'
        this.sourceFallbackReason = screenings.length
          ? null
          : 'Le catalogue live est chargé, mais aucune séance exploitable n’est encore disponible.'
      } catch {
        this.loadDemoData('Impossible de charger les données réelles. Démonstration locale activée.')
        this.loadError = 'Impossible de charger les données réelles. Démonstration locale activée.'
      } finally {
        this.loading = false
      }
    },
    async switchSource(mode: DataSourceMode) {
      this.sourceSwitchPending = true
      this.loadError = null
      try {
        if (mode === 'demo') {
          this.lastImportSummary = null
          await this.bootstrap('demo')
          return
        }

        const summary = await api.importCatalog(2025, mode)
        this.lastImportSummary = summary
        this.effectiveSourceMode = mode
        await this.bootstrap(mode)
      } finally {
        this.sourceSwitchPending = false
      }
    },
    async resetUserChoices() {
      clearPersistedUiState()

      if (!this.usingMocks) {
        await api.resetUserChoices()
        await this.bootstrap()
        return
      }

      const reset = resetLocalUserChoices(this.films, this.screenings)
      this.films = reset.films
      this.screenings = reset.screenings
    },
    async reimportCurrentSource(mode: DataSourceMode) {
      this.sourceSwitchPending = true
      this.loadError = null
      try {
        clearPersistedUiState()
        const summary = await api.importCatalog(2025, mode)
        this.lastImportSummary = summary
        this.effectiveSourceMode = mode
        await api.resetUserChoices()
        await this.bootstrap(mode)
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
        this.screenings = recomputeScreeningStates(screenings)
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
