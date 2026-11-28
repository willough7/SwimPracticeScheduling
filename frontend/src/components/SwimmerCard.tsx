import type { Swimmer, SwimmerStatus, WeightsGroup } from '../types'

const WEIGHTS_GROUP_LABELS: Record<WeightsGroup, string> = {
  THREE_DAY_A: '3-day A',
  THREE_DAY_B: '3-day B',
  FOUR_DAY: '4-day',
}

const STATUS_LABELS: Record<SwimmerStatus, string> = {
  available: 'Available',
  conflict: 'Class conflict',
  unknown: 'No calendar',
}

type SwimmerCardProps = {
  swimmer: Swimmer
  status?: SwimmerStatus // only set while a practice is selected
  assigned: boolean // assigned to the selected practice
  disabled: boolean // no practice selected, or a request for this swimmer is in flight
  onToggle: () => void
}

function SwimmerCard({ swimmer, status, assigned, disabled, onToggle }: SwimmerCardProps) {
  const classNames = ['swimmer-card']
  if (status !== undefined) {
    classNames.push(status)
  }
  if (assigned) {
    classNames.push('assigned')
  }

  // A <button> (not a clickable <div>) so it works with the keyboard and screen
  // readers. aria-pressed tells assistive tech it's an on/off toggle.
  return (
    <button
      className={classNames.join(' ')}
      disabled={disabled}
      aria-pressed={assigned}
      onClick={onToggle}
    >
      <span className="swimmer-name">
        {swimmer.first_name} {swimmer.last_name}
        {assigned && <span className="assigned-mark">✓ Assigned</span>}
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
    </button>
  )
}

export default SwimmerCard
