import type { Priority } from '@/types'

export type NormalizedPriority = 'pending' | 'ignore' | 'medium' | 'high'
export type SelectablePriority = 'ignore' | 'medium' | 'high'

export const priorityOptions: Array<{ value: SelectablePriority; label: string }> = [
  { value: 'high', label: 'Immanquable' },
  { value: 'medium', label: 'Peut-être' },
  { value: 'ignore', label: 'Non merci' },
]

export const priorityLabels: Record<NormalizedPriority, string> = {
  pending: 'À traiter',
  ignore: 'Non merci',
  medium: 'Peut-être',
  high: 'Immanquable',
}

export function normalizePriority(priority: Priority | null | undefined): NormalizedPriority {
  if (priority === 'must-see' || priority === 'high') {
    return 'high'
  }

  if (priority === 'medium') {
    return 'medium'
  }

  if (priority === 'unreviewed' || priority === 'low' || !priority) {
    return 'pending'
  }

  return 'ignore'
}

export function sanitizePriority(priority: Priority | null | undefined): Priority {
  if (!priority || priority === 'low') {
    return 'unreviewed'
  }

  return priority
}

export function isPrioritySelected(priority: Priority | null | undefined): boolean {
  const normalized = normalizePriority(priority)
  return normalized === 'high' || normalized === 'medium' || normalized === 'ignore'
}

export function isPlanningPriority(priority: Priority | null | undefined): boolean {
  const normalized = normalizePriority(priority)
  return normalized === 'medium' || normalized === 'high'
}

export function isHighPriority(priority: Priority | null | undefined): boolean {
  return normalizePriority(priority) === 'high'
}

export function priorityRank(priority: Priority | null | undefined): number {
  return {
    ignore: 0,
    pending: 1,
    medium: 2,
    high: 3,
  }[normalizePriority(priority)]
}

export function priorityLabel(priority: Priority | null | undefined): string {
  return priorityLabels[normalizePriority(priority)]
}

export function priorityDotCount(priority: Priority | null | undefined): number {
  const normalized = normalizePriority(priority)
  if (normalized === 'high') return 2
  if (normalized === 'medium') return 1
  return 0
}
