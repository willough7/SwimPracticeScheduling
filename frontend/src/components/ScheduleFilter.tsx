import { useState } from 'react'
import type { KeyboardEvent } from 'react'
import type { Swimmer } from '../types'

// The most names the drop-down list shows at once
const MAX_MATCHES = 8

type ScheduleFilterProps = {
  swimmers: Swimmer[]
  // The swimmer whose practices the schedule is showing, or null for everyone's
  selectedSwimmer: Swimmer | null
  onSelect: (swimmerId: number | null) => void
}

function fullName(swimmer: Swimmer) {
  return `${swimmer.first_name} ${swimmer.last_name}`
}

// The search box under the schedule. Picking a swimmer filters the schedule
// down to the practices they're assigned to, on every day tab.
function ScheduleFilter({ swimmers, selectedSwimmer, onSelect }: ScheduleFilterProps) {
  const [search, setSearch] = useState('')
  // Which name in the drop-down the arrow keys are on
  const [highlighted, setHighlighted] = useState(0)

  // Once a swimmer is picked, show who it is with a button to clear it
  if (selectedSwimmer !== null) {
    return (
      <div className="schedule-filter">
        <span className="schedule-filter-label">
          Showing practices for <strong>{fullName(selectedSwimmer)}</strong>
        </span>
        <button className="button small" onClick={() => onSelect(null)}>
          Show all
        </button>
      </div>
    )
  }

  const query = search.trim().toLowerCase()
  const matches =
    query === ''
      ? []
      : swimmers
          .filter((swimmer) => fullName(swimmer).toLowerCase().includes(query))
          .slice(0, MAX_MATCHES)

  function pick(swimmer: Swimmer) {
    onSelect(swimmer.swimmer_id)
    setSearch('')
    setHighlighted(0)
  }

  // Arrow keys move through the list, Enter picks, Escape clears the box
  function handleKeyDown(event: KeyboardEvent<HTMLInputElement>) {
    if (event.key === 'ArrowDown' && matches.length > 0) {
      event.preventDefault() // don't move the cursor to the end of the text
      setHighlighted((i) => (i + 1) % matches.length)
    } else if (event.key === 'ArrowUp' && matches.length > 0) {
      event.preventDefault()
      setHighlighted((i) => (i - 1 + matches.length) % matches.length)
    } else if (event.key === 'Enter' && matches.length > 0) {
      pick(matches[Math.min(highlighted, matches.length - 1)])
    } else if (event.key === 'Escape') {
      setSearch('')
    }
  }

  return (
    <div className="schedule-filter">
      {/* The list opens upward, because the box sits at the bottom of the column */}
      {query !== '' && (
        <ul className="schedule-filter-matches" role="listbox">
          {matches.length === 0 && <li className="schedule-filter-none">No swimmer by that name</li>}
          {matches.map((swimmer, i) => (
            <li key={swimmer.swimmer_id} role="option" aria-selected={i === highlighted}>
              <button
                className={i === highlighted ? 'highlighted' : undefined}
                // onMouseDown, not onClick: the input loses focus on mouse down,
                // and this way the pick happens first
                onMouseDown={(event) => {
                  event.preventDefault()
                  pick(swimmer)
                }}
                onMouseEnter={() => setHighlighted(i)}
              >
                {fullName(swimmer)}
              </button>
            </li>
          ))}
        </ul>
      )}
      <input
        type="search"
        className="swimmer-search schedule-filter-input"
        placeholder="Filter schedule for one swimmer by name"
        aria-label="Filter schedule for one swimmer by name"
        value={search}
        onChange={(event) => {
          setSearch(event.target.value)
          setHighlighted(0)
        }}
        onKeyDown={handleKeyDown}
      />
    </div>
  )
}

export default ScheduleFilter
