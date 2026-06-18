import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { sanitizeRecommendationCriterionOrder, useSettingsStore } from '@/stores/settings'

function stubLocalStorage(initial: Record<string, string> = {}) {
  const storage = new Map(Object.entries(initial))
  vi.stubGlobal('window', {
    localStorage: {
      getItem: vi.fn((key: string) => storage.get(key) ?? null),
      setItem: vi.fn((key: string, value: string) => storage.set(key, value)),
      removeItem: vi.fn((key: string) => storage.delete(key)),
    },
  })
  return storage
}

describe('settings store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.restoreAllMocks()
    vi.clearAllMocks()
  })

  it('sanitizes recommendation criterion order without duplicates', () => {
    expect(sanitizeRecommendationCriterionOrder(['score', 'score', 'options'])).toEqual(['score', 'options', 'conflicts'])
  })

  it('moves a selected recommendation criterion and persists the order', () => {
    const storage = stubLocalStorage()
    const store = useSettingsStore()

    store.setRecommendationCriterionOrder(0, 'score')

    expect(store.recommendationSettings.criterionOrder).toEqual(['score', 'options', 'conflicts'])
    expect(JSON.parse(storage.get('potential-spork-settings') ?? '{}')).toMatchObject({
      recommendationSettings: {
        criterionOrder: ['score', 'options', 'conflicts'],
      },
    })
  })
})
