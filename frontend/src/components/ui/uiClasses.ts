export type UiTone = 'neutral' | 'accent' | 'confirmed' | 'tentative' | 'warning' | 'danger' | 'subtle'
export type UiSize = 'sm' | 'md'
export type UiButtonVariant = 'primary' | 'secondary' | 'ghost' | 'state' | 'confirm' | 'tentative'
export type UiPanelDensity = 'normal' | 'compact'

function compactClasses(classes: Array<string | false | null | undefined>): string[] {
  return classes.filter((className): className is string => Boolean(className))
}

export function uiButtonClasses({
  variant = 'ghost',
  size = 'md',
}: {
  variant?: UiButtonVariant
  size?: UiSize
} = {}): string[] {
  return compactClasses(['ui-button', `ui-button--${variant}`, `ui-button--${size}`])
}

export function uiBadgeClasses({
  tone = 'neutral',
  size = 'md',
}: {
  tone?: UiTone
  size?: UiSize
} = {}): string[] {
  return ['ui-badge', `ui-badge--${tone}`, `ui-badge--${size}`]
}

export function uiChipClasses({
  tone = 'neutral',
  size = 'md',
  active = false,
}: {
  tone?: UiTone
  size?: UiSize
  active?: boolean
} = {}): string[] {
  return compactClasses(['ui-chip', `ui-chip--${tone}`, `ui-chip--${size}`, active && 'ui-chip--active'])
}

export function uiPanelClasses({
  tone = 'neutral',
  density = 'normal',
}: {
  tone?: Extract<UiTone, 'neutral' | 'subtle' | 'accent' | 'warning'>
  density?: UiPanelDensity
} = {}): string[] {
  return ['ui-panel', `ui-panel--${tone}`, `ui-panel--${density}`]
}
