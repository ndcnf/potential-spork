import { describe, expect, it } from 'vitest'

import { getScreeningActions } from './screeningActions'
import type { Screening } from '@/types'

function screening(overrides: Partial<Screening> & { isAlternative?: boolean } = {}) {
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
    ...overrides,
  } satisfies Screening & { isAlternative?: boolean }
}

describe('getScreeningActions', () => {
  it('returns the tentative and reject actions for an available screening', () => {
    expect(getScreeningActions(screening())).toEqual([
      { kind: 'select', status: 'tentative', label: 'Mettre une option', variant: 'tentative' },
      { kind: 'select', status: 'rejected', label: 'Ignorer cette séance', variant: 'ghost' },
    ])
  })

  it('uses the replacement label for an alternative screening', () => {
    expect(getScreeningActions(screening({ isAlternative: true }))[0]).toEqual({
      kind: 'select',
      status: 'tentative',
      label: 'Remplacer par cette séance',
      variant: 'tentative',
    })
  })

  it('promotes tentative screenings to confirmation', () => {
    expect(getScreeningActions(screening({ selection_status: 'tentative' }))).toEqual([
      { kind: 'select', status: 'confirmed', label: 'Confirmer cette séance', variant: 'confirm' },
      { kind: 'clear', label: 'Retirer du planning', variant: 'ghost' },
    ])
  })

  it('keeps the current timeline behavior for confirmed screenings', () => {
    expect(getScreeningActions(screening({ selection_status: 'confirmed' }), { context: 'timeline' })).toEqual([
      { kind: 'select', status: 'rejected', label: 'Ignorer', variant: 'ghost' },
    ])
  })

  it('returns detail actions for confirmed screenings', () => {
    expect(getScreeningActions(screening({ selection_status: 'confirmed' }), { context: 'detail' })).toEqual([
      { kind: 'select', status: 'tentative', label: 'Repasser en tentative', variant: 'secondary' },
      { kind: 'clear', label: 'Retirer du planning', variant: 'ghost' },
    ])
  })

  it('shows ignored state and undo action for rejected screenings', () => {
    expect(getScreeningActions(screening({ selection_status: 'rejected' }))).toEqual([
      { kind: 'state', label: 'Ignoré', variant: 'state' },
      { kind: 'clear', label: 'Annuler', variant: 'ghost' },
    ])
  })
})
