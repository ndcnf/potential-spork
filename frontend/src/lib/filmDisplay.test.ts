import { describe, expect, it } from 'vitest'

import {
  filmDirectorLabel,
  filmMetaLabel,
  filmTaglineLabel,
  hasFilmCardCopy,
  isFilmCardMetaOnly,
} from '@/lib/filmDisplay'
import type { Film } from '@/types'

type FilmDisplayFixture = Pick<Film, 'cast' | 'countries' | 'directors' | 'duration_minutes' | 'tagline' | 'year'>

function film(overrides: Partial<FilmDisplayFixture>): FilmDisplayFixture {
  return {
    cast: null,
    countries: null,
    directors: null,
    duration_minutes: null,
    tagline: null,
    year: null,
    ...overrides,
  }
}

describe('filmDisplay', () => {
  it('formats available metadata without adding missing placeholders or stray separators', () => {
    expect(filmMetaLabel(film({ countries: 'CH', duration_minutes: 60 }))).toBe('CH · 1h')
    expect(filmMetaLabel(film({ countries: null, duration_minutes: 54 }))).toBe('54 min')
    expect(filmMetaLabel(film({ countries: 'CH', duration_minutes: null }))).toBe('CH')
    expect(filmMetaLabel(film({ countries: null, duration_minutes: null }))).toBeNull()
  })

  it('filters directors when the imported value is metadata instead of a person name', () => {
    expect(filmDirectorLabel(film({ directors: "54'", tagline: null }))).toBeNull()
    expect(filmDirectorLabel(film({ directors: "CH, 2025, 60'", tagline: null }))).toBeNull()
    expect(filmDirectorLabel(film({ directors: 'Eric San (Kid Koala)', tagline: "CA, 2025, 86'" }))).toBe('Eric San (Kid Koala)')
  })

  it('filters taglines when the imported value is a screening slot instead of editorial copy', () => {
    expect(filmTaglineLabel(film({ tagline: '07.07, Rex, 11:00' }))).toBeNull()
    expect(filmTaglineLabel(film({ tagline: 'Helvetic Psycho-Gothic' }))).toBe('Helvetic Psycho-Gothic')
  })

  it('detects cards that only have compact metadata to attach that line to the title', () => {
    expect(isFilmCardMetaOnly(film({ countries: null, duration_minutes: 54, directors: "54'", tagline: '04.07, Rex, 16:15', cast: null }))).toBe(true)
    expect(isFilmCardMetaOnly(film({ countries: 'CA', duration_minutes: 86, directors: 'Eric San (Kid Koala)', tagline: "CA, 2025, 86'", cast: null }))).toBe(false)
  })

  it('does not render a card copy container when no displayable metadata remains', () => {
    expect(hasFilmCardCopy(film({ countries: null, duration_minutes: null, directors: "54'", tagline: '04.07, Rex, 16:15', cast: null }))).toBe(false)
  })
})
