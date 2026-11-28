// These mirror the Pydantic schemas in backend/app/schemas.py.
// If a schema changes there, change it here too.

export type WeightsGroup = 'THREE_DAY_A' | 'THREE_DAY_B' | 'FOUR_DAY'

// Matches the backend's Day IntEnum (isoweekday): 1 = Monday ... 7 = Sunday
export type Day = 1 | 2 | 3 | 4 | 5 | 6 | 7

export interface SwimmerCreate {
  first_name: string
  last_name: string
  weights_group: WeightsGroup
  tags?: string[]
}

export interface Swimmer extends SwimmerCreate {
  swimmer_id: number
  tags: string[]
  has_schedule: boolean
}

export interface PracticeCreate {
  day: Day
  start_time: string // "HH:MM" or "HH:MM:SS"
  end_time: string
  practice_title?: string
}

export interface Practice extends PracticeCreate {
  practice_id: number
  practice_title: string
}

export interface PracticeConflicts {
  practice_id: number
  week_start: string // "YYYY-MM-DD", always a Monday
  available: number[]
  conflict: number[]
  unknown: number[]
}
// Where a swimmer stands for the selected practice (from the conflicts endpoint)
export type SwimmerStatus = 'available' | 'conflict' | 'unknown'

// One swimmer's spot in a practice's pool lanes
export interface LanePlacement {
  swimmer_id: number
  lane: number // 1-8
}

// What the panels show for the selected practice:
//   browse = no practice selected; clicking a swimmer opens their details
//   assign = practice clicked once; the full roster, click to assign
//   lanes  = practice double-clicked; its lanes, drag swimmers into them
export type PanelMode = 'browse' | 'assign' | 'lanes'
