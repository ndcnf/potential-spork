import { defineStore } from 'pinia'

import type { DataSourceMode, RecommendationSettings } from '@/types'

const STORAGE_KEY = 'potential-spork-settings'

type PersistedSettings = {
  recommendationSettings: RecommendationSettings
  dataSourceMode: DataSourceMode
}

const defaultSettings = (): RecommendationSettings => ({
  enabled: false,
  preferredVenueScores: {},
  avoidBeforeMinutes: null,
  avoidAfterMinutes: null,
})

export const useSettingsStore = defineStore('settings', {
  state: () => ({
    recommendationSettings: defaultSettings() as RecommendationSettings,
    dataSourceMode: 'demo' as DataSourceMode,
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
          }
          this.dataSourceMode = parsed.dataSourceMode === 'prod' ? 'prod' : 'demo'
        } catch {
          this.recommendationSettings = defaultSettings()
          this.dataSourceMode = 'demo'
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
    setDataSourceMode(mode: DataSourceMode) {
      this.dataSourceMode = mode
      this.persist()
    },
    resetRecommendationSettings() {
      this.recommendationSettings = defaultSettings()
      this.persist()
    },
  },
})
