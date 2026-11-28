import { useState } from 'react'
import type { DragEvent, PointerEvent } from 'react'
import { droppedSwimmerId, isSwimmerDrag } from '../dragDrop'
import { WEIGHTS_GROUP_LABELS } from '../labels'
import type { PanelMode, Swimmer, SwimmerStatus, WeightsGroup } from '../types'
import SwimmerCard from './SwimmerCard'

const MIN_PANEL_HEIGHT = 120 // enough for the header and one row of cards
const MIN_SCHEDULE_HEIGHT = 150 // never let the panel cover the whole schedule
const DEFAULT_PANEL_HEIGHT = 280

const WEIGHTS_GROUPS = Object.keys(WEIGHTS_GROUP_LABELS) as WeightsGroup[]

// When a practice is selected: available swimmers first, conflicts last
const STATUS_ORDER: Record<SwimmerStatus, number> = {
  available: 0,
  unknown: 1,
  conflict: 2,
}

type SwimmerPanelProps = {
  title: string
  mode: PanelMode
  canEdit: boolean // only admins can add swimmers, assign, or drag into lanes
  swimmers: Swimmer[] // the swimmers to show: everyone, or (in lanes mode) those not in a lane
  statuses: Map<number, SwimmerStatus> | null // null when no practice is selected
  assignedIds: Set<number> | null // who is assigned to the selected practice
  pendingIds: Set<number> // swimmers with a request in flight
  onSwimmerClick: (swimmerId: number) => void
  onSwimmerContextMenu: (swimmerId: number, x: number, y: number) => void
  onAddSwimmer: () => void
  onDropOutOfLane: (swimmerId: number) => void // a swimmer dragged from a lane back here
}

function SwimmerPanel({
  title,
  mode,
  canEdit,
  swimmers,
  statuses,
  assignedIds,
  pendingIds,
  onSwimmerClick,
  onSwimmerContextMenu,
  onAddSwimmer,
  onDropOutOfLane,
}: SwimmerPanelProps) {
  const [height, setHeight] = useState(DEFAULT_PANEL_HEIGHT)
  const [dragOver, setDragOver] = useState(false)
  const [search, setSearch] = useState('')
  const [selectedTags, setSelectedTags] = useState<string[]>([])
  const [selectedWeights, setSelectedWeights] = useState<WeightsGroup[]>([])

  // Every tag used by at least one swimmer, sorted, with no duplicates.
  // Worked out from the swimmers on every render rather than kept in state,
  // so it can never get out of sync with them.
  const allTags = [...new Set(swimmers.flatMap((swimmer) => swimmer.tags))].sort()

  // A swimmer is shown if all three hold:
  //  - their name contains the search text
  //  - they're in ANY of the selected weights groups (each swimmer has only one,
  //    so "3-day A" + "4-day" means either), or no weights group is selected
  //  - they have EVERY selected tag (so "Breast" + "100s" shows only 100 breaststrokers)
  const query = search.trim().toLowerCase()
  const visibleSwimmers = swimmers.filter((swimmer) => {
    const fullName = `${swimmer.first_name} ${swimmer.last_name}`.toLowerCase()
    const matchesSearch = fullName.includes(query)
    const matchesWeights =
      selectedWeights.length === 0 || selectedWeights.includes(swimmer.weights_group)
    const hasAllTags = selectedTags.every((tag) => swimmer.tags.includes(tag))
    return matchesSearch && matchesWeights && hasAllTags
  })

  // .sort() is stable, so swimmers with the same status keep their original order.
  // A swimmer missing from statuses (e.g. added after the check) sorts with unknown.
  const sortedSwimmers =
    statuses === null
      ? visibleSwimmers
      : [...visibleSwimmers].sort(
          (a, b) =>
            STATUS_ORDER[statuses.get(a.swimmer_id) ?? 'unknown'] -
            STATUS_ORDER[statuses.get(b.swimmer_id) ?? 'unknown'],
        )

  function toggleTag(tag: string) {
    setSelectedTags((current) =>
      current.includes(tag) ? current.filter((t) => t !== tag) : [...current, tag],
    )
  }

  function toggleWeights(group: WeightsGroup) {
    setSelectedWeights((current) =>
      current.includes(group) ? current.filter((g) => g !== group) : [...current, group],
    )
  }

  function clearFilters() {
    setSearch('')
    setSelectedTags([])
    setSelectedWeights([])
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

  const filtersActive = search !== '' || selectedTags.length > 0 || selectedWeights.length > 0

  // In lanes mode the panel is also a drop target: dropping a swimmer here
  // takes them out of their lane. preventDefault() in dragover is what tells
  // the browser "dropping is allowed here".
  function handleDragOver(event: DragEvent<HTMLDivElement>) {
    if (canEdit && mode === 'lanes' && isSwimmerDrag(event)) {
      event.preventDefault()
      event.dataTransfer.dropEffect = 'move'
      setDragOver(true)
    }
  }

  function handleDragLeave(event: DragEvent<HTMLDivElement>) {
    // dragleave also fires when moving onto a child element; only clear the
    // highlight when the pointer has really left the panel
    if (!event.currentTarget.contains(event.relatedTarget as Node | null)) {
      setDragOver(false)
    }
  }

  function handleDrop(event: DragEvent<HTMLDivElement>) {
    event.preventDefault()
    setDragOver(false)
    const swimmerId = droppedSwimmerId(event)
    if (swimmerId !== null) {
      onDropOutOfLane(swimmerId)
    }
  }

  return (
    <section className="swimmer-panel" style={{ height }}>
      <div
        className="resize-handle"
        onPointerDown={handlePointerDown}
        onPointerMove={handlePointerMove}
      />

      <div className="panel-header">
        <h2>{title}</h2>
        {canEdit && (
          <button className="button" onClick={onAddSwimmer}>
            + Swimmer
          </button>
        )}
        <input
          type="search"
          className="swimmer-search"
          placeholder="Search by name"
          value={search}
          onChange={(event) => setSearch(event.target.value)}
        />
        <div className="tag-filters" role="group" aria-label="Weights group">
          {WEIGHTS_GROUPS.map((group) => (
            <button
              key={group}
              className={selectedWeights.includes(group) ? 'tag-filter selected' : 'tag-filter'}
              aria-pressed={selectedWeights.includes(group)}
              onClick={() => toggleWeights(group)}
            >
              {WEIGHTS_GROUP_LABELS[group]}
            </button>
          ))}
        </div>
        <span className="filter-divider" />
        <div className="tag-filters" role="group" aria-label="Tags">
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

      <div
        className={dragOver ? 'panel-body drag-over' : 'panel-body'}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        {swimmers.length === 0 && (
          <p>
            {mode === 'lanes'
              ? canEdit
                ? 'Every assigned swimmer is in a lane. Drag one here to take them out.'
                : 'Every assigned swimmer is in a lane.'
              : 'No swimmers yet.'}
          </p>
        )}
        {swimmers.length > 0 && visibleSwimmers.length === 0 && (
          <p>No swimmers match these filters.</p>
        )}
        <div className="swimmer-grid">
          {sortedSwimmers.map((swimmer) => (
            <SwimmerCard
              key={swimmer.swimmer_id}
              swimmer={swimmer}
              mode={mode}
              canEdit={canEdit}
              status={statuses?.get(swimmer.swimmer_id)}
              assigned={assignedIds?.has(swimmer.swimmer_id) ?? false}
              disabled={pendingIds.has(swimmer.swimmer_id)}
              onClick={() => onSwimmerClick(swimmer.swimmer_id)}
              onContextMenu={(x, y) => onSwimmerContextMenu(swimmer.swimmer_id, x, y)}
            />
          ))}
        </div>
      </div>
    </section>
  )
}

export default SwimmerPanel
