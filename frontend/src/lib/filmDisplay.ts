import type { Film } from '@/types'

import { formatMinutes } from '@/lib/planning'

type FilmLike = Pick<Film, 'cast' | 'countries' | 'directors' | 'duration_minutes' | 'tagline' | 'year'> | null | undefined

function cleanText(value: string | null | undefined): string | null {
  const text = value?.trim()
  return text ? text : null
}

function normalizeText(value: string | null | undefined): string {
  return cleanText(value)?.toLocaleLowerCase() ?? ''
}

function isMetadataOnlyText(value: string | null | undefined): boolean {
  const text = cleanText(value)

  if (!text) {
    return false
  }

  const countryCode = '[A-Z]{2}(?:[/-][A-Z]{2})?'
  const countryYearDuration = new RegExp(`^(?:${countryCode})(?:\\s*,\\s*${countryCode})*\\s*,\\s*\\d{4}\\s*,\\s*\\d+\\s*'$`, 'i')
  const durationOnly = /^(\d+)\s*(?:'|min\.?|minutes?)$/i
  const screeningSlot = /^\d{2}\.\d{2}\s*,\s*[^,]+\s*,\s*\d{1,2}:\d{2}$/i

  return countryYearDuration.test(text) || durationOnly.test(text) || screeningSlot.test(text)
}

export function filmDirectorLabel(film: FilmLike): string | null {
  const directors = cleanText(film?.directors)

  if (!directors || isMetadataOnlyText(directors)) {
    return null
  }

  return normalizeText(directors) === normalizeText(film?.tagline) ? null : directors
}

export function filmTaglineLabel(film: FilmLike): string | null {
  const tagline = cleanText(film?.tagline)

  if (!tagline || isMetadataOnlyText(tagline)) {
    return null
  }

  return tagline
}

export function filmCastLabel(film: FilmLike): string | null {
  return cleanText(film?.cast)
}

export function filmYearLabel(film: FilmLike): string | null {
  return film?.year ? String(film.year) : null
}

export function filmMetaLabel(film: FilmLike): string | null {
  const parts = [
    cleanText(film?.countries),
    film?.duration_minutes == null ? null : formatMinutes(film.duration_minutes),
  ].filter(Boolean)

  return parts.length ? parts.join(' · ') : null
}

export function filmDetailMetaLabel(film: FilmLike): string | null {
  const parts = [
    filmMetaLabel(film),
    filmYearLabel(film),
  ].filter(Boolean)

  return parts.length ? parts.join(' · ') : null
}

export function hasFilmCardCopy(film: FilmLike): boolean {
  return Boolean(
    filmTaglineLabel(film) ||
    filmDirectorLabel(film) ||
    filmCastLabel(film) ||
    filmMetaLabel(film),
  )
}

export function isFilmCardMetaOnly(film: FilmLike): boolean {
  return Boolean(
    filmMetaLabel(film) &&
    !filmTaglineLabel(film) &&
    !filmDirectorLabel(film) &&
    !filmCastLabel(film),
  )
}

export function hasFilmDetailInfo(film: FilmLike): boolean {
  return Boolean(
    filmDirectorLabel(film) ||
    filmTaglineLabel(film) ||
    filmDetailMetaLabel(film),
  )
}
