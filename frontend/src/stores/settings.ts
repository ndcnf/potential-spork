import { defineStore } from 'pinia'

import type { DataSourceMode, RecommendationSettings, RecommendationSortCriterion } from '@/types'

const STORAGE_KEY = 'potential-spork-settings'

type PersistedSettings = {
  recommendationSettings: RecommendationSettings
  dataSourceMode: DataSourceMode
  liveSourceUrl: string
}

export const defaultRecommendationCriterionOrder: RecommendationSortCriterion[] = ['options', 'score', 'conflicts']

export function sanitizeRecommendationCriterionOrder(
  value: RecommendationSortCriterion[] | undefined,
): RecommendationSortCriterion[] {
  const validCriteria = new Set<RecommendationSortCriterion>(defaultRecommendationCriterionOrder)
  const ordered = (value ?? []).filter(
    (item, index, items): item is RecommendationSortCriterion => validCriteria.has(item) && items.indexOf(item) === index,
  )
  return [...ordered, ...defaultRecommendationCriterionOrder.filter((item) => !ordered.includes(item))].slice(
    0,
    defaultRecommendationCriterionOrder.length,
  )
}

const defaultSettings = (): RecommendationSettings => ({
  enabled: false,
  preferredVenueScores: {},
  avoidBeforeMinutes: null,
  avoidAfterMinutes: null,
  criterionOrder: [...defaultRecommendationCriterionOrder],
})

export const useSettingsStore = defineStore('settings', {
  state: () => ({
    recommendationSettings: defaultSettings() as RecommendationSettings,
    dataSourceMode: 'demo' as DataSourceMode,
    liveSourceUrl: '',
    loaded: false,
  }),
  getters: {
    hasRecommendationPreferences(state): boolean {
      return (
        Object.keys(state.recommendationSettings.preferredVenueScores).length > 0 ||
        state.recommendationSettings.avoidBeforeMinutes !== null ||
        state.recommendationSettings.avoidAfterMinutes !== null
      )
    },
    recommendationMode(): 'off' | 'neutral' | 'personalized' {
      if (!this.recommendationSettings.enabled) {
        return 'off'
      }
      if (!this.hasRecommendationPreferences) {
        return 'neutral'
      }
      return 'personalized'
    },
  },
  actions: {
    load() {
      if (this.loaded || typeof window === 'undefined') {
        return
      }

      const raw = window.localStorage.getItem(STORAGE_KEY)
      if (raw) {
        try {
          const parsed = JSON.parse(raw) as Partial<PersistedSettings>
          const persistedRecommendationSettings = parsed.recommendationSettings ?? (parsed as Partial<RecommendationSettings>)
          this.recommendationSettings = {
            ...defaultSettings(),
            ...persistedRecommendationSettings,
            preferredVenueScores: persistedRecommendationSettings?.preferredVenueScores ?? {},
            avoidBeforeMinutes: persistedRecommendationSettings?.avoidBeforeMinutes ?? null,
            avoidAfterMinutes: persistedRecommendationSettings?.avoidAfterMinutes ?? null,
            criterionOrder: sanitizeRecommendationCriterionOrder(persistedRecommendationSettings?.criterionOrder),
          }
          this.dataSourceMode = parsed.dataSourceMode === 'prod' ? 'prod' : 'demo'
          this.liveSourceUrl = parsed.liveSourceUrl ?? ''
        } catch {
          this.recommendationSettings = defaultSettings()
          this.dataSourceMode = 'demo'
          this.liveSourceUrl = ''
        }
      }

      this.loaded = true
    },
    persist() {
      if (typeof window === 'undefined') {
        return
      }
      const payload: PersistedSettings = {
        recommendationSettings: this.recommendationSettings,
        dataSourceMode: this.dataSourceMode,
        liveSourceUrl: this.liveSourceUrl,
      }
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(payload))
    },
    setRecommendationEnabled(enabled: boolean) {
      this.recommendationSettings.enabled = enabled
      this.persist()
    },
    setVenueScore(venueName: string, score: number | null) {
      if (score === null) {
        delete this.recommendationSettings.preferredVenueScores[venueName]
      } else {
        this.recommendationSettings.preferredVenueScores[venueName] = score > 0 ? 1 : -1
      }
      this.persist()
    },
    setAvoidBeforeMinutes(value: number | null) {
      this.recommendationSettings.avoidBeforeMinutes = value
      this.persist()
    },
    setAvoidAfterMinutes(value: number | null) {
      this.recommendationSettings.avoidAfterMinutes = value
      this.persist()
    },
    setRecommendationCriterionOrder(index: number, criterion: RecommendationSortCriterion) {
      const current = sanitizeRecommendationCriterionOrder(this.recommendationSettings.criterionOrder)
      const withoutSelected = current.filter((item) => item !== criterion)
      withoutSelected.splice(index, 0, criterion)
      this.recommendationSettings.criterionOrder = sanitizeRecommendationCriterionOrder(withoutSelected)
      this.persist()
    },
    setDataSourceMode(mode: DataSourceMode) {
      this.dataSourceMode = mode
      this.persist()
    },
    setLiveSourceUrl(url: string) {
      this.liveSourceUrl = url.trim()
      this.persist()
    },
    resetRecommendationSettings() {
      this.recommendationSettings = defaultSettings()
      this.persist()
    },
  },
})
