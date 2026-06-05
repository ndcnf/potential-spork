import { defineStore } from 'pinia'

import type { RecommendationSettings } from '@/types'

const STORAGE_KEY = 'potential-spork-settings'

const defaultSettings = (): RecommendationSettings => ({
  enabled: false,
  preferredVenueScores: {},
  avoidBeforeMinutes: null,
  avoidAfterMinutes: null,
})

export const useSettingsStore = defineStore('settings', {
  state: () => ({
    recommendationSettings: defaultSettings() as RecommendationSettings,
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
          const parsed = JSON.parse(raw) as RecommendationSettings
          this.recommendationSettings = {
            ...defaultSettings(),
            ...parsed,
            preferredVenueScores: parsed.preferredVenueScores ?? {},
            avoidBeforeMinutes: parsed.avoidBeforeMinutes ?? null,
            avoidAfterMinutes: parsed.avoidAfterMinutes ?? null,
          }
        } catch {
          this.recommendationSettings = defaultSettings()
        }
      }

      this.loaded = true
    },
    persist() {
      if (typeof window === 'undefined') {
        return
      }
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(this.recommendationSettings))
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
    resetRecommendationSettings() {
      this.recommendationSettings = defaultSettings()
      this.persist()
    },
  },
})
