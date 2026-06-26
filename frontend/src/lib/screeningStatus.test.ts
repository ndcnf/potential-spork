import { describe, expect, it } from 'vitest'

import { getScreeningStatusPresentation } from './screeningStatus'
import type { Screening } from '@/types'

function screening(
  overrides: Partial<Screening> & {
    isSelected?: boolean
    isConflict?: boolean
    isSingleScreening?: boolean
    isMustLock?: boolean
    isRecommended?: boolean
    isAlternative?: boolean
  } = {},
) {
  return {
    id: 1,
    film_id: 1,
    film_title: 'Film',
    venue_id: 1,
    venue_name: 'Rex',
    starts_at: '2025-07-05T18:00:00+02:00',
    ends_at: '2025-07-05T19:30:00+02:00',
    selection_status: 'none',
    derived_state: 'available',
    isSelected: false,
    isConflict: false,
    isSingleScreening: false,
    isMustLock: false,
    isRecommended: false,
    isAlternative: false,
    ...overrides,
  } satisfies Screening & {
    isSelected: boolean
    isConflict: boolean
    isSingleScreening: boolean
    isMustLock: boolean
    isRecommended: boolean
    isAlternative: boolean
  }
}

describe('getScreeningStatusPresentation', () => {
  it('returns timeline label and tone for selected states', () => {
    expect(getScreeningStatusPresentation(screening({ selection_status: 'confirmed' }))).toEqual({
      label: 'Confirmée',
      tone: 'confirmed',
    })

    expect(getScreeningStatusPresentation(screening({ selection_status: 'tentative' }))).toEqual({
      label: 'Tentative',
      tone: 'tentative',
    })
  })

  it('gives conflicts precedence over confirmed and tentative labels', () => {
    expect(
      getScreeningStatusPresentation(
        screening({
          selection_status: 'confirmed',
          isSelected: true,
          isConflict: true,
        }),
      ),
    ).toEqual({
      label: 'Conflit',
      tone: 'conflict',
    })
  })

  it('uses comparison wording for disabled alternatives', () => {
    const alternative = screening({ isAlternative: true })

    expect(getScreeningStatusPresentation(alternative)).toEqual({
      label: 'Autre séance choisie',
      tone: 'disabled',
    })

    expect(getScreeningStatusPresentation(alternative, { context: 'comparison' })).toEqual({
      label: 'Autre séance du film déjà prévue',
      tone: 'disabled',
    })
  })

  it('returns system recommendation and availability states', () => {
    expect(getScreeningStatusPresentation(screening({ isMustLock: true }))).toEqual({
      label: 'À sécuriser',
      tone: 'must-lock',
    })

    expect(getScreeningStatusPresentation(screening({ isRecommended: true }))).toEqual({
      label: 'Recommandée',
      tone: 'recommended',
    })

    expect(getScreeningStatusPresentation(screening())).toEqual({
      label: 'Disponible',
      tone: 'available',
    })
  })
})
