import { useState } from 'react'
import type { DragEvent } from 'react'
import { droppedSwimmerId, isSwimmerDrag, startSwimmerDrag } from '../dragDrop'
import { LANES } from '../labels'
import type { Practice, Swimmer, SwimmerStatus } from '../types'
import PracticeHeader from './PracticeHeader'

type LanesViewProps = {
  practice: Practice
  assignedSwimmers: Swimmer[]
  lanes: Map<number, number> | null // swimmer_id -> lane; null while loading
  statuses: Map<number, SwimmerStatus> | null
  pendingIds: Set<number> // swimmers with a request in flight
  onMove: (swimmerId: number, lane: number | null) => void
  onSwimmerContextMenu: (swimmerId: number, x: number, y: number) => void
  onBack: () => void
  onEdit: () => void
  onDelete: () => void
}

// Shown on the right when a practice is double-clicked: the pool's 8 lanes.
// Swimmers are dragged in from the bottom panel, between lanes, or back out.
function LanesView({
  practice,
  assignedSwimmers,
  lanes,
  statuses,
  pendingIds,
  onMove,
  onSwimmerContextMenu,
  onBack,
  onEdit,
  onDelete,
}: LanesViewProps) {
  // Which lane a swimmer is being dragged over, so it can be highlighted
  const [dragOverLane, setDragOverLane] = useState<number | null>(null)

  const placedCount = lanes === null ? 0 : lanes.size

  function handleDragOver(event: DragEvent<HTMLDivElement>, lane: number) {
    if (isSwimmerDrag(event)) {
      event.preventDefault() // this is what allows dropping here
      event.dataTransfer.dropEffect = 'move'
      setDragOverLane(lane)
    }
  }

  function handleDragLeave(event: DragEvent<HTMLDivElement>) {
    // dragleave also fires when moving onto a swimmer inside the lane;
    // only clear the highlight when the pointer has really left the lane
    if (!event.currentTarget.contains(event.relatedTarget as Node | null)) {
      setDragOverLane(null)
    }
  }

  function handleDrop(event: DragEvent<HTMLDivElement>, lane: number) {
    event.preventDefault()
    setDragOverLane(null)
    const swimmerId = droppedSwimmerId(event)
    if (swimmerId !== null) {
      onMove(swimmerId, lane)
    }
  }

  return (
    <div className="detail-view lanes-view">
      <PracticeHeader
        practice={practice}
        summary={`${placedCount} of ${assignedSwimmers.length} assigned swimmers in a lane`}
      >
        <button className="button" onClick={onBack}>
          Back to assigning
        </button>
        <button className="button" onClick={onEdit}>
          Edit
        </button>
        <button className="button danger" onClick={onDelete}>
          Delete
        </button>
      </PracticeHeader>

      {lanes === null ? (
        <p className="detail-hint">Loading lanes…</p>
      ) : (
        <div className="lanes">
          {LANES.map((lane) => {
            const inLane = assignedSwimmers.filter((s) => lanes.get(s.swimmer_id) === lane)
            return (
              <div
                key={lane}
                className={dragOverLane === lane ? 'lane drag-over' : 'lane'}
                onDragOver={(event) => handleDragOver(event, lane)}
                onDragLeave={handleDragLeave}
                onDrop={(event) => handleDrop(event, lane)}
              >
                <div className="lane-header">
                  <span className="lane-number" aria-label={`Lane ${lane}`}>
                    {lane}
                  </span>
                  <span className="lane-count">{inLane.length}</span>
                </div>
                <div className="lane-swimmers">
                  {inLane.length === 0 && <span className="lane-empty">Drop swimmers here</span>}
                  {inLane.map((swimmer) => {
                    const status = statuses?.get(swimmer.swimmer_id)
                    const classNames = ['swimmer-chip', 'draggable']
                    if (status) {
                      classNames.push(status)
                    }
                    return (
                      <span
                        key={swimmer.swimmer_id}
                        className={classNames.join(' ')}
                        draggable={!pendingIds.has(swimmer.swimmer_id)}
                        tabIndex={0}
                        onDragStart={(event) => startSwimmerDrag(event, swimmer.swimmer_id)}
                        onDragEnd={() => setDragOverLane(null)}
                        onContextMenu={(event) => {
                          event.preventDefault()
                          onSwimmerContextMenu(swimmer.swimmer_id, event.clientX, event.clientY)
                        }}
                      >
                        {swimmer.first_name} {swimmer.last_name}
                      </span>
                    )
                  })}
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}

export default LanesView
