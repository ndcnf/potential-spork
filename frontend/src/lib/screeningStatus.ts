import type { Screening } from '@/types'

export type ScreeningStatusTone =
  | 'rejected'
  | 'conflict'
  | 'warning'
  | 'confirmed'
  | 'tentative'
  | 'single'
  | 'must-lock'
  | 'disabled'
  | 'recommended'
  | 'available'

export type ScreeningStatusContext = 'timeline' | 'comparison'

export type ScreeningStatusInput = Pick<Screening, 'selection_status' | 'derived_state'> & {
  isSelected?: boolean
  isConflict?: boolean
  isSingleScreening?: boolean
  isMustLock?: boolean
  isRecommended?: boolean
  isAlternative?: boolean
}

export type ScreeningStatusPresentation = {
  label: string
  tone: ScreeningStatusTone
}

export function getScreeningStatusPresentation(
  screening: ScreeningStatusInput,
  { context = 'timeline' }: { context?: ScreeningStatusContext } = {},
): ScreeningStatusPresentation {
  if (screening.selection_status === 'rejected') {
    return { label: 'Ignorée', tone: 'rejected' }
  }

  if (screening.isSelected && screening.isConflict) {
    return { label: 'Conflit', tone: 'conflict' }
  }

  if (screening.derived_state === 'conflict') {
    return { label: 'Conflit potentiel', tone: 'warning' }
  }

  if (screening.selection_status === 'confirmed') {
    return { label: 'Confirmée', tone: 'confirmed' }
  }

  if (screening.selection_status === 'tentative') {
    return { label: 'Tentative', tone: 'tentative' }
  }

  if (screening.isSingleScreening) {
    return { label: 'Séance unique', tone: 'single' }
  }

  if (screening.isMustLock) {
    return { label: 'À sécuriser', tone: 'must-lock' }
  }

  if (screening.isRecommended) {
    return { label: 'Recommandée', tone: 'recommended' }
  }

  if (screening.isAlternative || screening.derived_state === 'disabled') {
    return {
      label: context === 'comparison' ? 'Autre séance du film déjà prévue' : 'Autre séance choisie',
      tone: 'disabled',
    }
  }

  return { label: 'Disponible', tone: 'available' }
}
