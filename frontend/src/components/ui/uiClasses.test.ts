import { describe, expect, it } from 'vitest'

import { uiBadgeClasses, uiButtonClasses, uiChipClasses, uiPanelClasses } from './uiClasses'

describe('uiClasses', () => {
  it('builds BEM classes for button variants', () => {
    expect(
      uiButtonClasses({
        variant: 'confirm',
        size: 'sm',
      }),
    ).toEqual([
      'ui-button',
      'ui-button--confirm',
      'ui-button--sm',
    ])
  })

  it('builds compact badge and chip classes', () => {
    expect(uiBadgeClasses({ tone: 'warning', size: 'sm' })).toEqual([
      'ui-badge',
      'ui-badge--warning',
      'ui-badge--sm',
    ])

    expect(uiChipClasses({ tone: 'accent', active: true })).toEqual([
      'ui-chip',
      'ui-chip--accent',
      'ui-chip--md',
      'ui-chip--active',
    ])
  })

  it('builds panel classes with density', () => {
    expect(uiPanelClasses({ tone: 'subtle', density: 'compact' })).toEqual([
      'ui-panel',
      'ui-panel--subtle',
      'ui-panel--compact',
    ])
  })
})
