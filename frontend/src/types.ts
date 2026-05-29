export type Priority = 'unreviewed' | 'ignore' | 'low' | 'medium' | 'high' | 'must-see'

export interface RecommendationSettings {
  enabled: boolean
  preferredVenueScores: Record<string, number>
  avoidBeforeMinutes: number | null
  avoidAfterMinutes: number | null
  minGapMinutes: number
}

export interface Cycle {
  id: number
  name: string
  slug: string
  color: string | null
  priority: Priority
}

export interface Film {
  id: number
  title: string
  slug: string
  directors: string | null
  year: number | null
  countries: string | null
  duration_minutes: number | null
  tagline: string | null
  premiere_label?: string | null
  short_description?: string | null
  cast: string | null
  synopsis: string | null
  language: string | null
  age_rating: string | null
  poster_url?: string | null
  festival_url?: string | null
  imdb_url?: string | null
  priority: Priority
  cycle_id: number | null
  cycle_name: string | null
  cycle_color: string | null
}

export interface Screening {
  id: number
  film_id: number
  film_title: string
  venue_id: number | null
  venue_name: string | null
  starts_at: string | null
  ends_at: string | null
  ticket_url?: string | null
  selection_status: 'none' | 'rejected' | 'tentative' | 'confirmed'
  derived_state: 'available' | 'selected' | 'disabled' | 'conflict' | 'rejected' | 'past'
}
