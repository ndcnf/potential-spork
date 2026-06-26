import type { Screening } from '@/types'
import type { UiButtonVariant } from '@/components/ui/uiClasses'

export type ScreeningActionContext = 'timeline' | 'detail'
export type ScreeningActionSelectionStatus = 'tentative' | 'confirmed' | 'rejected'

export type ScreeningActionScreening = Pick<Screening, 'selection_status' | 'derived_state'> & {
  isAlternative?: boolean
}

export type ScreeningAction =
  | {
      kind: 'select'
      status: ScreeningActionSelectionStatus
      label: string
      variant: UiButtonVariant
    }
  | {
      kind: 'clear'
      label: string
      variant: UiButtonVariant
    }
  | {
      kind: 'state'
      label: string
      variant: Extract<UiButtonVariant, 'state'>
    }

export function getScreeningActions(
  screening: ScreeningActionScreening,
  { context = 'detail' }: { context?: ScreeningActionContext } = {},
): ScreeningAction[] {
  if (screening.selection_status === 'rejected') {
    return [
      { kind: 'state', label: 'Ignoré', variant: 'state' },
      { kind: 'clear', label: 'Annuler', variant: 'ghost' },
    ]
  }

  if (screening.selection_status === 'confirmed') {
    if (context === 'timeline') {
      return [{ kind: 'select', status: 'rejected', label: 'Ignorer', variant: 'ghost' }]
    }

    return [
      { kind: 'select', status: 'tentative', label: 'Repasser en tentative', variant: 'secondary' },
      { kind: 'clear', label: 'Retirer du planning', variant: 'ghost' },
    ]
  }

  if (screening.selection_status === 'tentative') {
    return [
      { kind: 'select', status: 'confirmed', label: 'Confirmer cette séance', variant: 'confirm' },
      context === 'timeline'
        ? { kind: 'select', status: 'rejected', label: 'Ignorer', variant: 'ghost' }
        : { kind: 'clear', label: 'Retirer du planning', variant: 'ghost' },
    ]
  }

  return [
    {
      kind: 'select',
      status: 'tentative',
      label: screening.isAlternative || screening.derived_state === 'disabled' ? 'Remplacer par cette séance' : 'Mettre une option',
      variant: 'tentative',
    },
    { kind: 'select', status: 'rejected', label: context === 'timeline' ? 'Ignorer' : 'Ignorer cette séance', variant: 'ghost' },
  ]
}
