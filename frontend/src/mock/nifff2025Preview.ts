import { screeningsOverlapWithBuffer } from '@/lib/planning'
import type { Cycle, Film, Priority, Screening } from '@/types'

type PreviewCycle = {
  slug: string
  name: string
  color: string | null
}

type PreviewFilm = {
  slug: string
  title: string
  cycle: string | null
  director: string | null
  tagline: string | null
  details: string | null
  status?: string
}

type PreviewScreening = {
  film_slug: string
  date: string
  venue_slug: string
  start_time: string
  ticket_url?: string | null
}

const cyclesSource: PreviewCycle[] = [
  { slug: 'international-competition', name: 'International competition', color: '#ff3b30' },
  { slug: 'third-kind', name: 'Third Kind', color: '#ffd60a' },
  { slug: 'ultra-movies', name: 'Ultra Movies', color: '#d7df01' },
  { slug: 'take-care', name: 'Take Care', color: '#007c73' },
  { slug: 'nifff-invasion', name: 'NIFFF Invasion', color: '#352c7a' },
]

const venues = {
  'passage-1': 'Passage 1',
  arcades: 'Arcades',
  rex: 'Rex',
  studio: 'Studio',
  'open-air': 'Open Air',
} as const

const filmSource: PreviewFilm[] = [
  { slug: 'alpha', title: 'Alpha', cycle: 'international-competition', director: 'Julia Ducournau', tagline: 'Marble-skin Allegory', details: "FR/BE, 2025, 128'" },
  { slug: 'a-cure-for-wellness', title: 'A Cure for Wellness', cycle: 'take-care', director: 'Gore Verbinski', tagline: 'Eurotrash Wellness Horror', details: "DE/LU/US, 2016, 146'" },
  { slug: 'dangerous-animals', title: 'Dangerous Animals', cycle: 'ultra-movies', director: 'Sean Byrne', tagline: 'Sharkcore', details: "AU/US/CA, 2025, 92'" },
  { slug: 'clown-in-a-cornfield', title: 'Clown in a Cornfield', cycle: 'ultra-movies', director: 'Eli Craig', tagline: 'Bozo goes Beserk', details: "US, 2025, 97'" },
  { slug: 'cloud', title: 'Cloud', cycle: 'third-kind', director: 'Kiyoshi Kurosawa', tagline: 'Dead End Digital Noir', details: "JP, 2024, 124'" },
  { slug: 'eddington', title: 'Eddington', cycle: 'third-kind', director: 'Ari Aster', tagline: 'Madness Always Grips America', details: "US/FI, 2025, 148'" },
  { slug: 'dead-talents-society', title: 'Dead Talents Society', cycle: 'ultra-movies', director: 'John Hsu', tagline: 'Feel Good Ghost Story', details: "TW, 2024, 111'" },
  { slug: 'dogtooth', title: 'Dogtooth', cycle: 'take-care', director: 'Yorgos Lanthimos', tagline: 'Kin Control Fable', details: "GR, 2009, 97'" },
  { slug: 'fantastic-shorts', title: 'Fantastic Shorts', cycle: 'nifff-invasion', director: null, tagline: null, details: "CH, 2025, 60'" },
  { slug: 'gatillero', title: 'Gatillero', cycle: 'third-kind', director: 'Cristian Tapia Marchiori', tagline: 'Revolt never truly dies', details: "AR, 2025, 80'" },
  { slug: 'hallow-road', title: 'Hallow Road', cycle: 'third-kind', director: 'Babak Anvari', tagline: 'Hit and run anxiety', details: "UK/IE/FI/US, 2025, 80'" },
  { slug: 'jimmy-and-stiggs', title: 'Jimmy and Stiggs', cycle: 'ultra-movies', director: 'Joe Begos', tagline: 'DIY Splatter Satire', details: "US, 2024, 80'" },
  { slug: 'monkey-shines', title: 'Monkey Shines', cycle: 'take-care', director: 'George A. Romero', tagline: 'Primate Psycho Thriller', details: "US, 1988, 113'" },
  { slug: 'the-home', title: 'The Home', cycle: 'international-competition', director: 'Mattias J. Skoglund', tagline: 'Old Age. New Fear', details: "SE/IS/EE, 2025, 87'" },
  { slug: 'the-rule-of-jenny-pen', title: 'The Rule of Jenny Pen', cycle: 'third-kind', director: 'James Ashcroft', tagline: 'Geriatric Terror', details: "NZ, 2024, 104'" },
  { slug: 'the-ugly-stepsister', title: 'The Ugly Stepsister', cycle: 'international-competition', director: 'Emilie Blichfeldt', tagline: 'Cinderella B Side goes Ballistic', details: "NO/SE/PL/DK/RO, 2025, 105'" },
  { slug: 'together', title: 'Together', cycle: null, director: null, tagline: null, details: null, status: 'not_found_in_wayback_capture' },
]

const screeningSource: PreviewScreening[] = [
  { film_slug: 'alpha', date: '2025-07-05', venue_slug: 'passage-1', start_time: '22:15' },
  { film_slug: 'alpha', date: '2025-07-09', venue_slug: 'passage-1', start_time: '19:15' },
  { film_slug: 'alpha', date: '2025-07-11', venue_slug: 'studio', start_time: '14:00' },
  { film_slug: 'a-cure-for-wellness', date: '2025-07-04', venue_slug: 'studio', start_time: '14:00' },
  { film_slug: 'dangerous-animals', date: '2025-07-05', venue_slug: 'studio', start_time: '22:15' },
  { film_slug: 'dangerous-animals', date: '2025-07-10', venue_slug: 'arcades', start_time: '22:00' },
  { film_slug: 'clown-in-a-cornfield', date: '2025-07-04', venue_slug: 'open-air', start_time: '00:45' },
  { film_slug: 'clown-in-a-cornfield', date: '2025-07-11', venue_slug: 'arcades', start_time: '00:30' },
  { film_slug: 'cloud', date: '2025-07-08', venue_slug: 'passage-1', start_time: '14:00' },
  { film_slug: 'cloud', date: '2025-07-11', venue_slug: 'passage-1', start_time: '11:00' },
  { film_slug: 'eddington', date: '2025-07-06', venue_slug: 'passage-1', start_time: '13:30' },
  { film_slug: 'eddington', date: '2025-07-11', venue_slug: 'passage-1', start_time: '19:45' },
  { film_slug: 'dead-talents-society', date: '2025-07-07', venue_slug: 'open-air', start_time: '21:45' },
  { film_slug: 'dead-talents-society', date: '2025-07-11', venue_slug: 'rex', start_time: '19:30' },
  { film_slug: 'dogtooth', date: '2025-07-11', venue_slug: 'rex', start_time: '11:00' },
  { film_slug: 'fantastic-shorts', date: '2025-07-07', venue_slug: 'rex', start_time: '11:00' },
  { film_slug: 'gatillero', date: '2025-07-05', venue_slug: 'arcades', start_time: '00:30' },
  { film_slug: 'gatillero', date: '2025-07-11', venue_slug: 'arcades', start_time: '14:15' },
  { film_slug: 'hallow-road', date: '2025-07-08', venue_slug: 'open-air', start_time: '00:15' },
  { film_slug: 'hallow-road', date: '2025-07-12', venue_slug: 'arcades', start_time: '17:00' },
  { film_slug: 'jimmy-and-stiggs', date: '2025-07-06', venue_slug: 'open-air', start_time: '00:15' },
  { film_slug: 'jimmy-and-stiggs', date: '2025-07-09', venue_slug: 'arcades', start_time: '00:30' },
  { film_slug: 'monkey-shines', date: '2025-07-12', venue_slug: 'arcades', start_time: '00:45' },
  { film_slug: 'the-home', date: '2025-07-06', venue_slug: 'arcades', start_time: '14:00' },
  { film_slug: 'the-home', date: '2025-07-08', venue_slug: 'arcades', start_time: '22:00' },
  { film_slug: 'the-home', date: '2025-07-11', venue_slug: 'studio', start_time: '17:00' },
  { film_slug: 'the-rule-of-jenny-pen', date: '2025-07-06', venue_slug: 'open-air', start_time: '21:45' },
  { film_slug: 'the-rule-of-jenny-pen', date: '2025-07-09', venue_slug: 'studio', start_time: '17:00' },
  { film_slug: 'the-ugly-stepsister', date: '2025-07-04', venue_slug: 'studio', start_time: '22:00' },
  { film_slug: 'the-ugly-stepsister', date: '2025-07-07', venue_slug: 'passage-1', start_time: '19:45' },
  { film_slug: 'the-ugly-stepsister', date: '2025-07-10', venue_slug: 'passage-1', start_time: '22:15' },
]

const cyclePriorities: Record<string, Priority> = {
  'international-competition': 'high',
  'third-kind': 'high',
  'ultra-movies': 'medium',
  'take-care': 'medium',
  'nifff-invasion': 'ignore',
}

const filmPriorities: Record<string, Priority> = {
  alpha: 'must-see',
  'the-ugly-stepsister': 'must-see',
  eddington: 'high',
  cloud: 'high',
  'dangerous-animals': 'high',
  'the-home': 'high',
  'the-rule-of-jenny-pen': 'high',
  'dead-talents-society': 'high',
  'a-cure-for-wellness': 'medium',
  'clown-in-a-cornfield': 'medium',
  dogtooth: 'medium',
  gatillero: 'medium',
  'hallow-road': 'medium',
  'jimmy-and-stiggs': 'medium',
  'monkey-shines': 'low',
  'fantastic-shorts': 'ignore',
  together: 'low',
}

const selectedScreenings = new Map<string, 'tentative' | 'confirmed'>([
  ['alpha|2025-07-09|19:15', 'confirmed'],
  ['dangerous-animals|2025-07-10|22:00', 'tentative'],
  ['the-home|2025-07-06|14:00', 'tentative'],
])

function parseDetails(details: string | null): { countries: string | null; year: number | null; duration: number | null } {
  if (!details) {
    return { countries: null, year: null, duration: null }
  }

  const match = details.match(/^(.*?),\s*(\d{4}),\s*(\d+)'$/)
  if (!match) {
    return { countries: details, year: null, duration: null }
  }

  return {
    countries: match[1],
    year: Number(match[2]),
    duration: Number(match[3]),
  }
}

function computeEnd(start: string, duration: number | null): string {
  const date = new Date(start)
  date.setMinutes(date.getMinutes() + (duration ?? 120))
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  const hours = String(date.getHours()).padStart(2, '0')
  const minutes = String(date.getMinutes()).padStart(2, '0')
  const seconds = String(date.getSeconds()).padStart(2, '0')
  return `${year}-${month}-${day}T${hours}:${minutes}:${seconds}`
}

function buildFestivalFilmUrl(slug: string): string {
  return `https://nifff.ch/prog/2025/film/${slug}`
}

export function buildPreviewDataset(): { cycles: Cycle[]; films: Film[]; screenings: Screening[] } {
  const cycles: Cycle[] = cyclesSource.map((cycle, index) => ({
    id: index + 1,
    name: cycle.name,
    slug: cycle.slug,
    color: cycle.color,
    priority: cyclePriorities[cycle.slug] ?? 'medium',
  }))

  const cycleBySlug = new Map(cycles.map((cycle) => [cycle.slug, cycle]))

  const films: Film[] = filmSource.map((film, index) => {
    const cycle = film.cycle ? cycleBySlug.get(film.cycle) ?? null : null
    const parsed = parseDetails(film.details)

    return {
      id: index + 1,
      title: film.title,
      slug: film.slug,
      directors: film.director,
      year: parsed.year,
      countries: parsed.countries,
      duration_minutes: parsed.duration,
      tagline: film.tagline,
      cast: film.status === 'not_found_in_wayback_capture' ? 'Absent de la capture Wayback croisee' : null,
      synopsis: null,
      language: null,
      age_rating: null,
      festival_url: film.status === 'not_found_in_wayback_capture' ? null : buildFestivalFilmUrl(film.slug),
      imdb_url: null,
      priority: filmPriorities[film.slug] ?? 'medium',
      cycle_id: cycle?.id ?? null,
      cycle_name: cycle?.name ?? null,
      cycle_color: cycle?.color ?? null,
    }
  })

  const filmBySlug = new Map(films.map((film) => [film.slug, film]))

  const screeningsBase: Screening[] = screeningSource.map((screening, index) => {
    const film = filmBySlug.get(screening.film_slug)
    const startsAt = `${screening.date}T${screening.start_time}:00`
    const status = selectedScreenings.get(`${screening.film_slug}|${screening.date}|${screening.start_time}`) ?? 'none'

    return {
      id: index + 1,
      film_id: film?.id ?? -1,
      film_title: film?.title ?? screening.film_slug,
      venue_id: index + 1,
      venue_name: venues[screening.venue_slug as keyof typeof venues] ?? screening.venue_slug,
      starts_at: startsAt,
      ends_at: computeEnd(startsAt, film?.duration_minutes ?? null),
      ticket_url: screening.ticket_url ?? null,
      selection_status: status,
      derived_state: 'available',
    }
  })

  const screenings = screeningsBase.map((screening) => {
    const selectedSibling = screeningsBase.find(
      (other) =>
        other.film_id === screening.film_id &&
        other.id !== screening.id &&
        (other.selection_status === 'tentative' || other.selection_status === 'confirmed'),
    )

    const conflictingSelected = screeningsBase.find(
      (other) =>
        other.id !== screening.id &&
        (other.selection_status === 'tentative' || other.selection_status === 'confirmed') &&
        screeningsOverlapWithBuffer(screening, other),
    )

    let derived: Screening['derived_state'] = 'available'
    if (screening.selection_status === 'tentative' || screening.selection_status === 'confirmed') {
      derived = 'selected'
    } else if (selectedSibling) {
      derived = 'disabled'
    } else if (conflictingSelected) {
      derived = 'conflict'
    }

    return { ...screening, derived_state: derived }
  })

  return { cycles, films, screenings }
}
