import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'

import { FESTIVAL_DAY_CUTOFF_HOUR, formatMinutes, formatTimeRange as formatTimeRangeValue, getFestivalDisplayInfo, screeningsOverlapWithBuffer, toMinutes } from '@/lib/planning'
import { useFestivalStore } from '@/stores/festival'
import { useSettingsStore } from '@/stores/settings'
import type { Film, Screening } from '@/types'

export type PlanningScreening = Screening & {
  film: Film | null
  dayKey: string
  startMinutes: number
  endMinutes: number
  isSelected: boolean
  isConflict: boolean
  isAlternative: boolean
  isSingleScreening: boolean
  isLastViableOption: boolean
  isMustLock: boolean
  isRecommended: boolean
  recommendationRank: number | null
  recommendationTotalOptions: number | null
  recommendationNote: string | null
  recommendationReasons: string[]
  recommendationDrawbacks: string[]
  recommendationBlockedBy: string | null
  visualRowStart?: number
  visualRowSpan?: number
}

export const FESTIVAL_VIEW_KEY = '__festival__'

export function usePlanningModel() {
  const store = useFestivalStore()
  const settingsStore = useSettingsStore()
  const activeDay = ref('')
  const planningMode = ref<'timeline' | 'visualization'>('timeline')
  const screeningFilter = ref<'all' | 'confirmed'>('all')
  const detailScreeningId = ref<number | null>(null)
  const isMobile = ref(false)
  let mobileMedia: MediaQueryList | null = null

  const syncMobileMode = () => {
    isMobile.value = mobileMedia?.matches ?? false
  }

  function isPlanningPriority(priority: Film['priority']): boolean {
    return priority === 'medium' || priority === 'high' || priority === 'must-see'
  }

  function isHighPriority(priority: Film['priority'] | undefined): boolean {
    return priority === 'high' || priority === 'must-see'
  }

  function toFestivalPreferenceMinutes(minutes: number | null): number | null {
    if (minutes === null) return null
    const hours = Math.floor(minutes / 60)
    return hours < FESTIVAL_DAY_CUTOFF_HOUR ? minutes + (24 * 60) : minutes
  }

  function classifyTimePreference(startMinutes: number, avoidBeforeMinutes: number | null, avoidAfterMinutes: number | null): 'early' | 'late' | null {
    const festivalAvoidBeforeMinutes = toFestivalPreferenceMinutes(avoidBeforeMinutes)
    const festivalAvoidAfterMinutes = toFestivalPreferenceMinutes(avoidAfterMinutes)

    if (festivalAvoidBeforeMinutes === null && festivalAvoidAfterMinutes === null) {
      return null
    }

    if (festivalAvoidBeforeMinutes !== null && festivalAvoidAfterMinutes === null) {
      return startMinutes < festivalAvoidBeforeMinutes ? 'early' : null
    }

    if (festivalAvoidBeforeMinutes === null && festivalAvoidAfterMinutes !== null) {
      return startMinutes >= festivalAvoidAfterMinutes ? 'late' : null
    }

    if (festivalAvoidBeforeMinutes === festivalAvoidAfterMinutes) {
      return null
    }

    if (festivalAvoidBeforeMinutes! < festivalAvoidAfterMinutes!) {
      if (startMinutes < festivalAvoidBeforeMinutes!) return 'early'
      if (startMinutes >= festivalAvoidAfterMinutes!) return 'late'
      return null
    }

    if (startMinutes < festivalAvoidBeforeMinutes! && startMinutes >= festivalAvoidAfterMinutes!) {
      const distanceToLateBoundary = startMinutes - festivalAvoidAfterMinutes!
      const distanceToEarlyBoundary = festivalAvoidBeforeMinutes! - startMinutes
      return distanceToLateBoundary <= distanceToEarlyBoundary ? 'late' : 'early'
    }

    return null
  }

  function screeningRecommendationScore(screening: Screening, selectedScreenings: Screening[]): { score: number; note: string; reasons: string[]; drawbacks: string[]; hasConflict: boolean } {
    const settings = settingsStore.recommendationSettings
    const reasons: string[] = []
    const drawbacks: string[] = []
    const hasConflict = selectedScreenings.some((other) => other.id !== screening.id && other.film_id !== screening.film_id && screeningsOverlapWithBuffer(screening, other))
    const conflictPenalty = hasConflict ? -100 : 0
    const comfortBonus = settings.preferredVenueScores[screening.venue_name ?? ''] ?? 0
    const startMinutes = toMinutes(screening.starts_at)
    const timePreference = classifyTimePreference(startMinutes, settings.avoidBeforeMinutes, settings.avoidAfterMinutes)
    const timePenalty = timePreference ? -1 : 0
    const total = conflictPenalty + comfortBonus + timePenalty

    if (conflictPenalty < 0) {
      drawbacks.push('conflit avec une autre séance déjà retenue')
    }

    if (comfortBonus > 0) {
      reasons.push(`salle ${screening.venue_name || 'inconnue'} marquée comme favorable`)
    } else if (comfortBonus < 0) {
      drawbacks.push(`salle ${screening.venue_name || 'inconnue'} marquée comme inconfortable`)
    }

    if (timePreference === 'early') {
      drawbacks.push('un peu tot')
    }

    if (timePreference === 'late') {
      drawbacks.push('un peu tard')
    }

    return {
      score: total,
      note: total > 0 ? 'option favorable selon tes préférences' : 'option neutre selon tes préférences',
      reasons,
      drawbacks,
      hasConflict,
    }
  }

  function countConflictPairs(screenings: Screening[]): number {
    let count = 0

    for (let index = 0; index < screenings.length; index += 1) {
      for (let otherIndex = index + 1; otherIndex < screenings.length; otherIndex += 1) {
        if (screeningsOverlapWithBuffer(screenings[index], screenings[otherIndex])) {
          count += 1
        }
      }
    }

    return count
  }

  onMounted(() => {
    if (typeof window !== 'undefined') {
      const breakpoint = getComputedStyle(document.documentElement).getPropertyValue('--breakpoint-mobile').trim() || '960px'
      mobileMedia = window.matchMedia(`(max-width: ${breakpoint})`)
      syncMobileMode()
      mobileMedia.addEventListener('change', syncMobileMode)
    }

    settingsStore.load()
    if (!store.cycles.length && !store.loading) {
      store.bootstrap()
    }
  })

  onBeforeUnmount(() => {
    mobileMedia?.removeEventListener('change', syncMobileMode)
  })

  const effectivePlanningMode = computed(() => (isMobile.value && planningMode.value === 'visualization' ? 'timeline' : planningMode.value))

  const filmById = computed(() => new Map(store.films.map((film) => [film.id, film])))

  const plannableFilmIds = computed(() => new Set(store.films.filter((film) => isPlanningPriority(film.priority)).map((film) => film.id)))

  const planningScreenings = computed<PlanningScreening[]>(() => {
    const baseScreenings = store.visibleScreenings.filter((screening) => screening.starts_at && screening.ends_at && plannableFilmIds.value.has(screening.film_id))
    const selectedScreenings = baseScreenings.filter((screening) => screening.selection_status === 'tentative' || screening.selection_status === 'confirmed')
    const selectedFilmIds = new Set(selectedScreenings.map((screening) => screening.film_id))
    const totalScreeningCountByFilmId = new Map<number, number>()
    const validScreeningCountByFilmId = new Map<number, number>()
    const lastViableScreeningIdByFilmId = new Map<number, number>()
    const recommendationByFilmId = new Map<number, number>()
    const recommendationRankByScreeningId = new Map<number, number>()
    const recommendationTotalByScreeningId = new Map<number, number>()
    const recommendationNoteByScreeningId = new Map<number, string>()
    const recommendationReasonsByScreeningId = new Map<number, string[]>()
    const recommendationDrawbacksByScreeningId = new Map<number, string[]>()
    const recommendationBlockedByScreeningId = new Map<number, string>()

    for (const screening of baseScreenings) {
      totalScreeningCountByFilmId.set(screening.film_id, (totalScreeningCountByFilmId.get(screening.film_id) ?? 0) + 1)

      if (screening.selection_status !== 'rejected') {
        validScreeningCountByFilmId.set(screening.film_id, (validScreeningCountByFilmId.get(screening.film_id) ?? 0) + 1)
        lastViableScreeningIdByFilmId.set(screening.film_id, screening.id)
      }
    }

    const candidatesByFilmId = new Map<number, Screening[]>()
    for (const screening of baseScreenings) {
      if (screening.selection_status === 'rejected') continue
      candidatesByFilmId.set(screening.film_id, [...(candidatesByFilmId.get(screening.film_id) ?? []), screening])
    }

    const scoredCandidatesByFilmId = new Map<number, Array<ReturnType<typeof screeningRecommendationScore> & { screening: Screening }>>()

    for (const [filmId, screenings] of candidatesByFilmId.entries()) {
      if (settingsStore.recommendationMode === 'personalized') {
        const hasSelected = screenings.some((screening) => screening.selection_status === 'tentative' || screening.selection_status === 'confirmed')
        const selectedOtherFilmScreenings = selectedScreenings.filter((screening) => screening.film_id !== filmId)
        const scored = [...screenings]
          .map((screening) => ({ screening, ...screeningRecommendationScore(screening, selectedOtherFilmScreenings) }))
          .sort((left, right) => right.score - left.score || (left.screening.starts_at ?? '').localeCompare(right.screening.starts_at ?? ''))

        scoredCandidatesByFilmId.set(filmId, scored)

        scored.forEach((entry, index) => {
          recommendationRankByScreeningId.set(entry.screening.id, index + 1)
          recommendationTotalByScreeningId.set(entry.screening.id, scored.length)
          recommendationNoteByScreeningId.set(entry.screening.id, entry.note)
          recommendationReasonsByScreeningId.set(entry.screening.id, entry.reasons)
          recommendationDrawbacksByScreeningId.set(entry.screening.id, entry.drawbacks)
        })

        if (hasSelected) continue
      }
    }

    const recommendedScreenings: Screening[] = []

    const filmIdsToRecommend = [...scoredCandidatesByFilmId.entries()]
      .filter(([filmId, scored]) => {
        const hasSelected = scored.some((entry) => entry.screening.selection_status === 'tentative' || entry.screening.selection_status === 'confirmed')
        return !hasSelected && scored.length > 0
      })
      .sort((left, right) => {
        const leftBestScore = left[1][0]?.score ?? Number.NEGATIVE_INFINITY
        const rightBestScore = right[1][0]?.score ?? Number.NEGATIVE_INFINITY
        return left[1].length - right[1].length || rightBestScore - leftBestScore
      })

    for (const [filmId, scored] of filmIdsToRecommend) {
      const recommendable = scored.find((entry) => !entry.hasConflict && !recommendedScreenings.some((other) => screeningsOverlapWithBuffer(entry.screening, other)))
      if (!recommendable) continue
      recommendationByFilmId.set(filmId, recommendable.screening.id)
      recommendedScreenings.push(recommendable.screening)

      for (const entry of scored) {
        if (entry.screening.id === recommendable.screening.id || entry.hasConflict) continue
        const blockingRecommendation = recommendedScreenings.find((other) => other.id !== entry.screening.id && screeningsOverlapWithBuffer(entry.screening, other))
        if (!blockingRecommendation) continue
        recommendationBlockedByScreeningId.set(
          entry.screening.id,
          `potentiel conflit avec ${blockingRecommendation.film_title}`,
        )
      }
    }

    return baseScreenings
      .map((screening) => {
        const startInfo = getFestivalDisplayInfo(screening.starts_at)
        const endInfo = getFestivalDisplayInfo(screening.ends_at)
        const isSelected = screening.selection_status === 'tentative' || screening.selection_status === 'confirmed'
        const film = filmById.value.get(screening.film_id) ?? null
        const totalScreeningCount = totalScreeningCountByFilmId.get(screening.film_id) ?? 0
        const validScreeningCount = validScreeningCountByFilmId.get(screening.film_id) ?? 0
        const lastViableScreeningId = lastViableScreeningIdByFilmId.get(screening.film_id) ?? null
        const isSingleScreening = totalScreeningCount === 1
        const isLastViableOption = totalScreeningCount > 1 && validScreeningCount === 1
        const isMustLock = isLastViableOption && lastViableScreeningId === screening.id && screening.selection_status !== 'rejected' && isHighPriority(film?.priority) && !isSelected
        const isRecommended = recommendationByFilmId.get(screening.film_id) === screening.id && !isSelected

        return {
          ...screening,
          film,
          dayKey: startInfo.displayDayKey,
          startMinutes: startInfo.displayMinutes,
          endMinutes: endInfo.displayMinutes,
          isSelected,
          isConflict: selectedScreenings.some((other) => screeningsOverlapWithBuffer(screening, other)),
          isAlternative: selectedFilmIds.has(screening.film_id) && screening.selection_status === 'none',
          isSingleScreening,
          isLastViableOption,
          isMustLock,
          isRecommended,
          recommendationRank: recommendationRankByScreeningId.get(screening.id) ?? null,
          recommendationTotalOptions: recommendationTotalByScreeningId.get(screening.id) ?? null,
          recommendationNote: recommendationNoteByScreeningId.get(screening.id) ?? null,
          recommendationReasons: recommendationReasonsByScreeningId.get(screening.id) ?? [],
          recommendationDrawbacks: recommendationDrawbacksByScreeningId.get(screening.id) ?? [],
          recommendationBlockedBy: recommendationBlockedByScreeningId.get(screening.id) ?? null,
        }
      })
      .sort((left, right) => left.dayKey.localeCompare(right.dayKey) || left.startMinutes - right.startMinutes || left.film_title.localeCompare(right.film_title))
  })

  const dayKeys = computed(() => [...new Set(planningScreenings.value.map((screening) => screening.dayKey))])
  const dayOptions = computed(() => [FESTIVAL_VIEW_KEY, ...dayKeys.value])

  watch(dayKeys, (days) => {
    if (!days.length) {
      activeDay.value = ''
      return
    }
    if (!activeDay.value || (activeDay.value !== FESTIVAL_VIEW_KEY && !days.includes(activeDay.value))) {
      activeDay.value = FESTIVAL_VIEW_KEY
    }
  }, { immediate: true })

  const filteredScreenings = computed(() => {
    if (screeningFilter.value === 'confirmed') {
      return planningScreenings.value.filter((screening) => screening.selection_status === 'confirmed')
    }

    return planningScreenings.value
  })

  const dayScreenings = computed(() => activeDay.value === FESTIVAL_VIEW_KEY ? filteredScreenings.value : filteredScreenings.value.filter((screening) => screening.dayKey === activeDay.value))

  const timelineGroups = computed(() => {
    if (activeDay.value !== FESTIVAL_VIEW_KEY) {
      return [{ dayKey: activeDay.value, screenings: dayScreenings.value }]
    }

    const grouped = new Map<string, PlanningScreening[]>()
    for (const screening of dayScreenings.value) {
      grouped.set(screening.dayKey, [...(grouped.get(screening.dayKey) ?? []), screening])
    }

    return [...grouped.entries()].map(([dayKey, screenings]) => ({ dayKey, screenings }))
  })

  const detailScreening = computed(() => planningScreenings.value.find((screening) => screening.id === detailScreeningId.value) ?? null)

  const relatedFilmScreenings = computed(() => {
    if (!detailScreening.value) {
      return [] as PlanningScreening[]
    }

    return filteredScreenings.value
      .filter((screening) => screening.film_id === detailScreening.value?.film_id)
      .sort((left, right) => left.dayKey.localeCompare(right.dayKey) || left.startMinutes - right.startMinutes)
  })

  const conflictingSelectedScreenings = computed(() => planningScreenings.value.filter((screening) => screening.isSelected && screening.isConflict))

  const arbitrableScreenings = computed(() => planningScreenings.value.filter((screening) => !screening.isSelected && !screening.isAlternative && screening.selection_status !== 'rejected'))

  const selectedConflictCount = computed(() => {
    const selected = planningScreenings.value.filter((screening) => screening.selection_status === 'tentative' || screening.selection_status === 'confirmed')
    return countConflictPairs(selected)
  })

  const summary = computed(() => ({
    films: store.films.filter((film) => isPlanningPriority(film.priority)).length,
    selected: planningScreenings.value.filter((screening) => screening.isSelected).length,
    conflicts: selectedConflictCount.value,
    toPlace: planningScreenings.value.filter((screening) => !screening.isSelected && !screening.isAlternative && screening.selection_status !== 'rejected').length,
  }))

  const daySummary = computed(() => ({
    total: dayScreenings.value.length,
    selected: dayScreenings.value.filter((screening) => screening.isSelected).length,
    conflicts: countConflictPairs(dayScreenings.value.filter((screening) => screening.selection_status === 'tentative' || screening.selection_status === 'confirmed')),
  }))

  const visualizationGroups = computed(() => {
    const sourceGroups = activeDay.value === FESTIVAL_VIEW_KEY ? timelineGroups.value : [{ dayKey: activeDay.value, screenings: dayScreenings.value }]

    return sourceGroups.map((group) => {
      const allScreenings = group.screenings
      if (!allScreenings.length) {
        return { dayKey: group.dayKey, bucketLabels: [] as string[], lanes: [] as Array<{ venueName: string; blocks: PlanningScreening[] }> }
      }

      const minMinutes = Math.min(...allScreenings.map((screening) => screening.startMinutes))
      const maxMinutes = Math.max(...allScreenings.map((screening) => screening.endMinutes))
      const dayStart = Math.floor(minMinutes / 15) * 15
      const dayEnd = Math.ceil(maxMinutes / 15) * 15
      const bucketCount = Math.max(1, (dayEnd - dayStart) / 15)

      const bucketLabels = Array.from({ length: bucketCount + 1 }, (_, index) => {
        const totalMinutes = dayStart + index * 15
        const hours = Math.floor(totalMinutes / 60) % 24
        const minutes = totalMinutes % 60
        return `${String(hours).padStart(2, '0')}h${String(minutes).padStart(2, '0')}`
      })

      const venueNames = [...new Set(allScreenings.map((screening) => screening.venue_name || 'Salle inconnue'))].sort((left, right) => left.localeCompare(right))

      return {
        dayKey: group.dayKey,
        bucketLabels,
        bucketCount,
        dayStart,
        lanes: venueNames.map((venueName) => ({
          venueName,
          blocks: allScreenings
            .filter((screening) => (screening.venue_name || 'Salle inconnue') === venueName)
            .map((screening) => ({
              ...screening,
              visualRowStart: Math.floor((screening.startMinutes - dayStart) / 15) + 1,
              visualRowSpan: Math.max(1, Math.ceil((screening.endMinutes - screening.startMinutes) / 15)),
            })),
        })),
      }
    })
  })

  watch([activeDay, detailScreening], ([day, screening]) => {
    if (!screening) return
    if (day !== FESTIVAL_VIEW_KEY && screening.dayKey !== day) {
      detailScreeningId.value = null
    }
  })

  function formatDayLabel(dayKey: string): string {
    const date = new Date(`${dayKey}T12:00:00`)
    return new Intl.DateTimeFormat('fr-CH', { weekday: 'short', day: '2-digit', month: '2-digit' }).format(date)
  }

  function formatDayChipLabel(dayKey: string): string {
    const date = new Date(`${dayKey}T12:00:00`)
    const weekday = new Intl.DateTimeFormat('fr-CH', { weekday: 'short' }).format(date).replace('.', '').toLowerCase()
    const day = new Intl.DateTimeFormat('fr-CH', { day: '2-digit' }).format(date)
    return `${weekday} ${day}`
  }

  function formatTimeRange(screening: PlanningScreening): string {
    return formatTimeRangeValue(screening.starts_at, screening.ends_at)
  }

  function filmPriorityDots(priority: Film['priority'] | undefined): number {
    if (priority === 'must-see' || priority === 'high') return 2
    if (priority === 'medium') return 1
    return 0
  }

  function filmMeta(screening: PlanningScreening): string {
    const countries = screening.film?.countries ?? 'Pays ?'
    const duration = screening.film?.duration_minutes
    return `${countries} · ${formatMinutes(duration)}`
  }

  function findSelectedSibling(screening: PlanningScreening): PlanningScreening | undefined {
    return planningScreenings.value.find(
      (other) =>
        other.film_id === screening.film_id &&
        other.id !== screening.id &&
        (other.selection_status === 'tentative' || other.selection_status === 'confirmed'),
    )
  }

  function findConflictingSelectedOtherFilm(screening: PlanningScreening): PlanningScreening | undefined {
    return planningScreenings.value.find(
      (other) =>
        other.id !== screening.id &&
        other.film_id !== screening.film_id &&
        (other.selection_status === 'tentative' || other.selection_status === 'confirmed') &&
        screeningsOverlapWithBuffer(screening, other),
    )
  }

  function screeningReason(screening: PlanningScreening): string {
    if (screening.selection_status === 'rejected') return 'Ignorée'
    if (screening.isSelected && screening.isConflict) return 'Conflit'
    if (screening.derived_state === 'conflict') return 'Conflit potentiel'
    if (screening.selection_status === 'confirmed') return 'Confirmée'
    if (screening.selection_status === 'tentative') return 'Tentative'
    if (screening.isSingleScreening) return 'Séance unique'
    if (screening.isMustLock) return 'À sécuriser'
    if (screening.isRecommended) return 'Recommandée'
    if (screening.isAlternative || screening.derived_state === 'disabled') {
      return 'Autre séance choisie'
    }
    return 'Disponible'
  }

  function screeningComparisonStatus(screening: PlanningScreening): string {
    if (screening.selection_status === 'rejected') return 'Ignorée'
    if (screening.isSelected && screening.isConflict) return 'Conflit'
    if (screening.derived_state === 'conflict') return 'Conflit potentiel'
    if (screening.selection_status === 'confirmed') return 'Confirmée'
    if (screening.selection_status === 'tentative') return 'Tentative'
    if (screening.isSingleScreening) return 'Séance unique'
    if (screening.isMustLock) return 'À sécuriser'
    if (screening.isRecommended) return 'Recommandée'
    if (screening.isAlternative || screening.derived_state === 'disabled') return 'Autre séance du film déjà prévue'
    return 'Disponible'
  }

  function screeningStateClass(screening: PlanningScreening): string {
    if (screening.isSelected && screening.isConflict) return 'planning__timeline-item--conflict'
    if (screening.isMustLock) return 'planning__timeline-item--must-lock'
    if (screening.selection_status === 'confirmed') return 'planning__timeline-item--confirmed'
    if (screening.selection_status === 'tentative') return 'planning__timeline-item--tentative'
    if (screening.selection_status === 'rejected') return 'planning__timeline-item--rejected'
    if (screening.isAlternative || screening.derived_state === 'disabled') return 'planning__timeline-item--disabled'
    if (screening.derived_state === 'conflict') return 'planning__timeline-item--blocked'
    if (screening.isRecommended) return 'planning__timeline-item--recommended'
    return 'planning__timeline-item--available'
  }

  function screeningComparisonHints(screening: PlanningScreening): string[] {
    const hints: string[] = []
    const conflictingSelected = findConflictingSelectedOtherFilm(screening)

    if (screening.isAlternative || screening.derived_state === 'disabled') {
      const selectedSibling = findSelectedSibling(screening)
      if (selectedSibling?.starts_at) {
        hints.push(`Tu as déjà retenu ${formatDayChipLabel(selectedSibling.dayKey)} à ${selectedSibling.starts_at.slice(11, 16).replace(':', 'h')}`)
      }
    } else if (conflictingSelected?.starts_at) {
      hints.push(`Potentiel conflit avec ${conflictingSelected.film_title}, ${formatDayChipLabel(conflictingSelected.dayKey)} ${conflictingSelected.starts_at.slice(11, 16).replace(':', 'h')}`)
    }

    return hints.slice(0, 2)
  }

  function screeningDecisionNote(screening: PlanningScreening): string {
    const selectedSibling = findSelectedSibling(screening)
    const conflictingSelected = findConflictingSelectedOtherFilm(screening)

    if (screening.selection_status === 'confirmed') {
      return 'Cette séance est déjà confirmée dans votre planning.'
    }

    if (screening.selection_status === 'tentative') {
      return 'Cette séance est déjà retenue provisoirement.'
    }

    if ((screening.isAlternative || screening.derived_state === 'disabled') && selectedSibling?.starts_at) {
      return `Choisir cette séance remplacera votre autre choix du ${formatDayChipLabel(selectedSibling.dayKey)} à ${selectedSibling.starts_at.slice(11, 16).replace(':', 'h')}.`
    }

    if (conflictingSelected?.starts_at) {
      return `Choisir cette séance créerait un conflit avec ${conflictingSelected.film_title}, ${formatDayChipLabel(conflictingSelected.dayKey)} ${conflictingSelected.starts_at.slice(11, 16).replace(':', 'h')}.`
    }

    if (screening.isMustLock) {
      return 'C’est la dernière option viable pour ce film prioritaire.'
    }

    if (screening.isSingleScreening) {
      return 'C’est la seule séance disponible pour ce film.'
    }

    return 'Cette séance reste disponible sans collision immédiate.'
  }

  function screeningPrimaryActionLabel(screening: PlanningScreening): string {
    if (screening.isAlternative || screening.derived_state === 'disabled') {
      return 'Remplacer par cette séance'
    }

    return 'Choisir cette séance'
  }

  function screeningStatusTone(screening: PlanningScreening): string {
    if (screening.selection_status === 'rejected') return 'rejected'
    if (screening.isSelected && screening.isConflict) return 'conflict'
    if (screening.derived_state === 'conflict') return 'warning'
    if (screening.selection_status === 'confirmed') return 'confirmed'
    if (screening.selection_status === 'tentative') return 'tentative'
    if (screening.isSingleScreening) return 'single'
    if (screening.isMustLock) return 'must-lock'
    if (screening.isAlternative || screening.derived_state === 'disabled') return 'disabled'
    if (screening.isRecommended) return 'recommended'
    return 'available'
  }

  function visualizationBlockClass(screening: PlanningScreening): string {
    if (screening.isSelected && screening.isConflict) {
      return screening.selection_status === 'confirmed' ? 'planning__visual-block--confirmed-conflict' : 'planning__visual-block--tentative-conflict'
    }
    if (screening.selection_status === 'confirmed') return 'planning__visual-block--confirmed'
    if (screening.selection_status === 'tentative') return 'planning__visual-block--tentative'
    if (screening.selection_status === 'rejected') return 'planning__visual-block--rejected'
    if (screening.isAlternative || screening.derived_state === 'disabled') return 'planning__visual-block--disabled'
    if (screening.isMustLock) return 'planning__visual-block--must-lock'
    if (screening.isRecommended) return 'planning__visual-block--recommended'
    if (screening.derived_state === 'conflict' || screening.isConflict) return 'planning__visual-block--conflict'
    return 'planning__visual-block--available'
  }

  function selectedCountForDay(dayKey: string): number {
    if (dayKey === FESTIVAL_VIEW_KEY) {
      return planningScreenings.value.filter((screening) => screening.isSelected).length
    }
    return planningScreenings.value.filter((screening) => screening.dayKey === dayKey && screening.isSelected).length
  }

  function dayChipLabel(dayKey: string): string {
    return dayKey === FESTIVAL_VIEW_KEY ? 'Festival entier' : formatDayChipLabel(dayKey)
  }

  async function setScreeningSelection(screeningId: number, nextStatus: Screening['selection_status']): Promise<void> {
    await store.setScreeningSelection(screeningId, nextStatus)
  }

  async function clearScreeningSelection(screeningId: number): Promise<void> {
    await store.setScreeningSelection(screeningId, 'none')
  }

  function jumpToDay(dayKey: string): void {
    activeDay.value = dayKey
  }

  function focusScreening(screening: PlanningScreening | null | undefined): void {
    if (!screening) return
    planningMode.value = 'timeline'
    activeDay.value = screening.dayKey
    detailScreeningId.value = screening.id
  }

  function focusFirstConflict(): void {
    focusScreening(conflictingSelectedScreenings.value[0])
  }

  function focusFirstArbitration(): void {
    focusScreening(arbitrableScreenings.value[0])
  }

  function openDetailPanel(screeningId: number): void {
    detailScreeningId.value = screeningId
  }

  function closeDetailPanel(): void {
    detailScreeningId.value = null
  }

  return {
    store,
    settingsStore,
    activeDay,
    planningMode,
    screeningFilter,
    detailScreeningId,
    isMobile,
    effectivePlanningMode,
    planningScreenings,
    dayKeys,
    dayOptions,
    dayScreenings,
    timelineGroups,
    detailScreening,
    relatedFilmScreenings,
    conflictingSelectedScreenings,
    arbitrableScreenings,
    summary,
    daySummary,
    visualizationGroups,
    formatDayLabel,
    formatTimeRange,
    filmPriorityDots,
    filmMeta,
    screeningReason,
    screeningStatusTone,
    screeningComparisonStatus,
    screeningStateClass,
    screeningComparisonHints,
    screeningDecisionNote,
    screeningPrimaryActionLabel,
    visualizationBlockClass,
    selectedCountForDay,
    dayChipLabel,
    setScreeningSelection,
    clearScreeningSelection,
    jumpToDay,
    focusFirstConflict,
    focusFirstArbitration,
    openDetailPanel,
    closeDetailPanel,
    FESTIVAL_VIEW_KEY,
  }
}
