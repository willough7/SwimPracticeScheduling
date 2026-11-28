import type { MouseEvent, ReactNode } from 'react'
import { startSwimmerDrag } from '../dragDrop'
import { WEIGHTS_GROUP_LABELS } from '../labels'
import type { PanelMode, Swimmer, SwimmerStatus } from '../types'

const STATUS_LABELS: Record<SwimmerStatus, string> = {
  available: 'Available',
  conflict: 'Class conflict',
  unknown: 'No calendar',
}

type SwimmerCardProps = {
  swimmer: Swimmer
  mode: PanelMode
  status?: SwimmerStatus // only set while a practice is selected
  assigned: boolean // assigned to the selected practice
  disabled: boolean // a request for this swimmer is in flight
  onClick: () => void
  onContextMenu: (x: number, y: number) => void
}

function SwimmerCard({
  swimmer,
  mode,
  status,
  assigned,
  disabled,
  onClick,
  onContextMenu,
}: SwimmerCardProps) {
  const classNames = ['swimmer-card']
  if (status !== undefined) {
    classNames.push(status)
  }
  if (assigned && mode === 'assign') {
    classNames.push('assigned')
  }

  function handleContextMenu(event: MouseEvent) {
    event.preventDefault() // don't show the browser's own menu
    onContextMenu(event.clientX, event.clientY)
  }

  const content: ReactNode = (
    <>
      <span className="swimmer-name">
        {swimmer.first_name} {swimmer.last_name}
        {assigned && mode === 'assign' && <span className="assigned-mark">✓ Assigned</span>}
      </span>
      <span className="swimmer-details">
        <span>Weights: {WEIGHTS_GROUP_LABELS[swimmer.weights_group]}</span>
        {status !== undefined ? (
          <span className={`badge status-${status}`}>{STATUS_LABELS[status]}</span>
        ) : (
          !swimmer.has_schedule && <span className="badge status-unknown">No calendar</span>
        )}
      </span>
      {swimmer.tags.length > 0 && (
        <span className="swimmer-tags">
          {swimmer.tags.map((tag) => (
            <span key={tag} className="badge">
              {tag}
            </span>
          ))}
        </span>
      )}
    </>
  )

  // In lanes mode the card is something to drag, not to click. It's a <div>
  // rather than a <button> because some browsers (Firefox) won't drag buttons.
  if (mode === 'lanes') {
    return (
      <div
        className={`${classNames.join(' ')} draggable`}
        draggable={!disabled}
        tabIndex={0} // still reachable with Tab, so the right-click menu works from the keyboard
        onDragStart={(event) => startSwimmerDrag(event, swimmer.swimmer_id)}
        onContextMenu={handleContextMenu}
      >
        {content}
      </div>
    )
  }

  // A <button> (not a clickable <div>) so it works with the keyboard and screen
  // readers. In assign mode, aria-pressed tells assistive tech it's an on/off
  // toggle; otherwise it's a plain button that opens the swimmer's details.
  return (
    <button
      className={classNames.join(' ')}
      disabled={disabled}
      aria-pressed={mode === 'assign' ? assigned : undefined}
      onClick={onClick}
      onContextMenu={handleContextMenu}
    >
      {content}
    </button>
  )
}

export default SwimmerCard
