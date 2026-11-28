import type { Day, WeightsGroup } from './types'

// Display names for backend values, shared by every component that shows them.

export const WEIGHTS_GROUP_LABELS: Record<WeightsGroup, string> = {
  THREE_DAY_A: '3-day A',
  THREE_DAY_B: '3-day B',
  FOUR_DAY: '4-day',
}

export const DAY_NAMES: Record<Day, string> = {
  1: 'Monday',
  2: 'Tuesday',
  3: 'Wednesday',
  4: 'Thursday',
  5: 'Friday',
  6: 'Saturday',
  7: 'Sunday',
}

// The pool's lanes, numbered like the lane markers (must match LANE_COUNT in backend/app/schemas.py)
export const LANES = [1, 2, 3, 4, 5, 6, 7, 8]
