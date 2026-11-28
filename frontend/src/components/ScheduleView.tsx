import { formatTime, toMinutes } from '../time'
import type { Practice } from '../types'

// 1 pixel per minute = 60 pixels per hour
const PIXELS_PER_MINUTE = 1

// The grid always shows at least this range, and grows if a practice falls outside it.
const DEFAULT_FIRST_HOUR = 6
const DEFAULT_LAST_HOUR = 20

type ScheduleViewProps = {
  practices: Practice[]
  selectedPracticeId: number | null
  assignedCounts: Map<number, number> // practice_id -> number of swimmers assigned
  onSelectPractice: (practiceId: number) => void
  onOpenLanes: (practiceId: number) => void
  onPracticeContextMenu: (practiceId: number, x: number, y: number) => void
}

// Puts overlapping practices in separate columns so they sit side by side
// (e.g. Saturday's lift 8-9 and swim 7-8:45). Each practice goes in the
// first column that is free by the time it starts.
function assignColumns(practices: Practice[]) {
  const sorted = [...practices].sort(
    (a, b) => toMinutes(a.start_time) - toMinutes(b.start_time),
  )
  const columnEnds: number[] = [] // columnEnds[i] = when the last practice in column i ends
  const columnOf = new Map<number, number>() // practice_id -> column

  for (const practice of sorted) {
    const start = toMinutes(practice.start_time)
    let column = columnEnds.findIndex((end) => end <= start)
    if (column === -1) {
      column = columnEnds.length
      columnEnds.push(0)
    }
    columnEnds[column] = toMinutes(practice.end_time)
    columnOf.set(practice.practice_id, column)
  }

  return { columnOf, columnCount: Math.max(columnEnds.length, 1) }
}

function ScheduleView({
  practices,
  selectedPracticeId,
  assignedCounts,
  onSelectPractice,
  onOpenLanes,
  onPracticeContextMenu,
}: ScheduleViewProps) {
  const startHours = practices.map((p) => Math.floor(toMinutes(p.start_time) / 60))
  const endHours = practices.map((p) => Math.ceil(toMinutes(p.end_time) / 60))
  const firstHour = Math.min(DEFAULT_FIRST_HOUR, ...startHours)
  const lastHour = Math.max(DEFAULT_LAST_HOUR, ...endHours)

  // [firstHour, firstHour + 1, ..., lastHour], one line per hour
  const hours = Array.from({ length: lastHour - firstHour + 1 }, (_, i) => firstHour + i)
  const { columnOf, columnCount } = assignColumns(practices)

  // How far down the grid a time of day is drawn
  function topFor(minutes: number) {
    return (minutes - firstHour * 60) * PIXELS_PER_MINUTE
  }

  return (
    <div className="schedule">
      {practices.length === 0 && <p className="schedule-empty">No practices on this day.</p>}

      <div
        className="schedule-grid"
        style={{ height: (lastHour - firstHour) * 60 * PIXELS_PER_MINUTE }}
      >
        {hours.map((hour) => (
          <div key={hour} className="hour-line" style={{ top: topFor(hour * 60) }}>
            <span className="hour-label">{formatTime(hour * 60)}</span>
          </div>
        ))}

        <div className="practice-area">
          {practices.map((practice) => {
            const start = toMinutes(practice.start_time)
            const end = toMinutes(practice.end_time)
            const column = columnOf.get(practice.practice_id) ?? 0
            const isSelected = practice.practice_id === selectedPracticeId
            const count = assignedCounts.get(practice.practice_id) ?? 0

            return (
              <button
                key={practice.practice_id}
                className={isSelected ? 'practice selected' : 'practice'}
                style={{
                  top: topFor(start),
                  height: (end - start) * PIXELS_PER_MINUTE,
                  left: `${(column / columnCount) * 100}%`,
                  width: `calc(${100 / columnCount}% - 4px)`,
                }}
                onClick={(event) => {
                  // A double-click also fires two clicks first. event.detail counts
                  // the clicks in a row, so ignore the second one; the double-click
                  // handler below takes over from there.
                  if (event.detail < 2) {
                    onSelectPractice(practice.practice_id)
                  }
                }}
                onDoubleClick={() => onOpenLanes(practice.practice_id)}
                onContextMenu={(event) => {
                  event.preventDefault() // don't show the browser's own menu
                  onPracticeContextMenu(practice.practice_id, event.clientX, event.clientY)
                }}
              >
                <span className="practice-title">{practice.practice_title}</span>
                <span className="practice-time">
                  {formatTime(start)} – {formatTime(end)}
                </span>
                <span className="practice-count">
                  {count} {count === 1 ? 'swimmer' : 'swimmers'}
                </span>
              </button>
            )
          })}
        </div>
      </div>
    </div>
  )
}

export default ScheduleView
