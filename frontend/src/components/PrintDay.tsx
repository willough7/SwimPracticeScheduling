import { DAY_NAMES, LANES } from '../labels'
import { formatTime, toMinutes } from '../time'
import type { Day, Practice, Swimmer } from '../types'

type PrintDayProps = {
  day: Day
  practices: Practice[]
  swimmers: Swimmer[]
  assignments: Map<number, number[]> // practice_id -> assigned swimmer ids
  lanes: Map<number, Map<number, number>> // practice_id -> (swimmer_id -> lane)
}

// A printer-friendly page with every practice of one day, laid out like the
// lanes view and the Excel export. It's hidden on screen (see .print-view in
// App.css) and only appears when printing, in place of the rest of the app.
function PrintDay({ day, practices, swimmers, assignments, lanes }: PrintDayProps) {
  const byStartTime = [...practices].sort(
    (a, b) => toMinutes(a.start_time) - toMinutes(b.start_time),
  )

  return (
    <div className="print-view">
      <h1>{DAY_NAMES[day]} practices</h1>
      {byStartTime.length === 0 && <p>No practices</p>}

      {byStartTime.map((practice) => {
        const assignedIds = new Set(assignments.get(practice.practice_id) ?? [])
        const practiceLanes = lanes.get(practice.practice_id) ?? new Map<number, number>()

        // Sorted by last name, like the Excel sheet, so the page is easy to scan
        const assigned = swimmers
          .filter((s) => assignedIds.has(s.swimmer_id))
          .sort(
            (a, b) =>
              a.last_name.localeCompare(b.last_name) || a.first_name.localeCompare(b.first_name),
          )

        // Columns: lanes 1-8, then assigned swimmers who aren't in a lane
        const columns: Swimmer[][] = [...LANES.map(() => []), []]
        for (const swimmer of assigned) {
          const lane = practiceLanes.get(swimmer.swimmer_id)
          columns[lane === undefined ? LANES.length : lane - 1].push(swimmer)
        }
        const rowCount = Math.max(1, ...columns.map((column) => column.length))

        return (
          <table key={practice.practice_id} className="print-practice">
            <caption>
              {practice.practice_title} · {formatTime(toMinutes(practice.start_time))} –{' '}
              {formatTime(toMinutes(practice.end_time))} · {assigned.length}{' '}
              {assigned.length === 1 ? 'swimmer' : 'swimmers'}
            </caption>
            <thead>
              <tr>
                {LANES.map((lane) => (
                  <th key={lane}>Lane {lane}</th>
                ))}
                <th>Not in a lane</th>
              </tr>
            </thead>
            <tbody>
              {Array.from({ length: rowCount }, (_, row) => (
                <tr key={row}>
                  {columns.map((column, i) => (
                    <td key={i}>
                      {column[row] ? `${column[row].first_name} ${column[row].last_name}` : ''}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        )
      })}
    </div>
  )
}

export default PrintDay
