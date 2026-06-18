import { describe, expect, it } from 'vitest'

import {
  isHighPriority,
  isPlanningPriority,
  normalizePriority,
  priorityDotCount,
  priorityLabel,
  priorityRank,
  sanitizePriority,
} from '@/lib/priorities'

describe('priority helpers', () => {
  it('maps legacy and product priorities to display buckets', () => {
    expect(normalizePriority('low')).toBe('pending')
    expect(normalizePriority('unreviewed')).toBe('pending')
    expect(normalizePriority('must-see')).toBe('high')
    expect(normalizePriority('high')).toBe('high')
    expect(normalizePriority('medium')).toBe('medium')
    expect(normalizePriority('ignore')).toBe('ignore')
  })

  it('sanitizes backend default priority for the frontend workflow', () => {
    expect(sanitizePriority(null)).toBe('unreviewed')
    expect(sanitizePriority(undefined)).toBe('unreviewed')
    expect(sanitizePriority('low')).toBe('unreviewed')
    expect(sanitizePriority('must-see')).toBe('must-see')
  })

  it('keeps planning and high priority rules compatible with legacy values', () => {
    expect(isPlanningPriority('medium')).toBe(true)
    expect(isPlanningPriority('high')).toBe(true)
    expect(isPlanningPriority('must-see')).toBe(true)
    expect(isPlanningPriority('low')).toBe(false)
    expect(isHighPriority('must-see')).toBe(true)
    expect(isHighPriority('medium')).toBe(false)
  })

  it('returns labels, ranks, and dots from the normalized priority', () => {
    expect(priorityLabel('low')).toBe('À traiter')
    expect(priorityLabel('must-see')).toBe('Immanquable')
    expect(priorityRank('ignore')).toBe(0)
    expect(priorityRank('low')).toBe(1)
    expect(priorityRank('medium')).toBe(2)
    expect(priorityRank('high')).toBe(3)
    expect(priorityDotCount('must-see')).toBe(2)
    expect(priorityDotCount('medium')).toBe(1)
    expect(priorityDotCount('low')).toBe(0)
  })
})
