import { useState } from 'react'
import type { PointerEvent } from 'react'
import type { Swimmer } from '../types'
import SwimmerCard from './SwimmerCard'

const MIN_PANEL_HEIGHT = 120 // enough for the header and one row of cards
const MIN_SCHEDULE_HEIGHT = 150 // never let the panel cover the whole schedule
const DEFAULT_PANEL_HEIGHT = 280

type SwimmerPanelProps = {
  swimmers: Swimmer[]
}

function SwimmerPanel({ swimmers }: SwimmerPanelProps) {
  const [height, setHeight] = useState(DEFAULT_PANEL_HEIGHT)
  const [search, setSearch] = useState('')
  const [selectedTags, setSelectedTags] = useState<string[]>([])

  // Every tag used by at least one swimmer, sorted, with no duplicates.
  // Worked out from the swimmers on every render rather than kept in state,
  // so it can never get out of sync with them.
  const allTags = [...new Set(swimmers.flatMap((swimmer) => swimmer.tags))].sort()

  // A swimmer is shown if their name contains the search text AND they have
  // every selected tag (so "Breast" + "100s" shows only 100 breaststrokers).
  const query = search.trim().toLowerCase()
  const visibleSwimmers = swimmers.filter((swimmer) => {
    const fullName = `${swimmer.first_name} ${swimmer.last_name}`.toLowerCase()
    const matchesSearch = fullName.includes(query)
    const hasAllTags = selectedTags.every((tag) => swimmer.tags.includes(tag))
    return matchesSearch && hasAllTags
  })

  function toggleTag(tag: string) {
    setSelectedTags((current) =>
      current.includes(tag) ? current.filter((t) => t !== tag) : [...current, tag],
    )
  }

  function clearFilters() {
    setSearch('')
    setSelectedTags([])
  }

  // Resizing: while the mouse button is held on the handle, the panel's top
  // edge follows the pointer. The panel sits at the bottom of the window, so
  // its height is the distance from the pointer to the bottom of the window.
  function handlePointerDown(event: PointerEvent<HTMLDivElement>) {
    event.preventDefault() // stop the drag from selecting text on the page
    // Pointer capture keeps sending move events to the handle even when the
    // pointer moves off it, which it will, since the handle is only a few pixels tall.
    event.currentTarget.setPointerCapture(event.pointerId)
  }

  function handlePointerMove(event: PointerEvent<HTMLDivElement>) {
    if (!event.currentTarget.hasPointerCapture(event.pointerId)) {
      return // the button isn't held down, so the mouse is just passing over
    }
    const maxHeight = window.innerHeight - MIN_SCHEDULE_HEIGHT
    const newHeight = window.innerHeight - event.clientY
    setHeight(Math.min(Math.max(newHeight, MIN_PANEL_HEIGHT), maxHeight))
  }

  const filtersActive = search !== '' || selectedTags.length > 0

  return (
    <section className="swimmer-panel" style={{ height }}>
      <div
        className="resize-handle"
        onPointerDown={handlePointerDown}
        onPointerMove={handlePointerMove}
      />

      <div className="panel-header">
        <h2>Swimmers</h2>
        <input
          type="search"
          className="swimmer-search"
          placeholder="Search by name"
          value={search}
          onChange={(event) => setSearch(event.target.value)}
        />
        <div className="tag-filters">
          {allTags.map((tag) => (
            <button
              key={tag}
              className={selectedTags.includes(tag) ? 'tag-filter selected' : 'tag-filter'}
              onClick={() => toggleTag(tag)}
            >
              {tag}
            </button>
          ))}
        </div>
        <span className="swimmer-count">
          {visibleSwimmers.length} of {swimmers.length}
        </span>
        {filtersActive && (
          <button className="clear-filters" onClick={clearFilters}>
            Clear
          </button>
        )}
      </div>

      <div className="panel-body">
        {swimmers.length === 0 && <p>No swimmers yet.</p>}
        {swimmers.length > 0 && visibleSwimmers.length === 0 && (
          <p>No swimmers match these filters.</p>
        )}
        <div className="swimmer-grid">
          {visibleSwimmers.map((swimmer) => (
            <SwimmerCard key={swimmer.swimmer_id} swimmer={swimmer} />
          ))}
        </div>
      </div>
    </section>
  )
}

export default SwimmerPanel
