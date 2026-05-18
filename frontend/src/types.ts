export type Priority = 'ignore' | 'low' | 'medium' | 'high' | 'must-see'

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
  cast: string | null
  synopsis: string | null
  language: string | null
  age_rating: string | null
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
  selection_status: 'none' | 'tentative' | 'confirmed'
  derived_state: 'available' | 'selected' | 'disabled' | 'conflict' | 'past'
}
