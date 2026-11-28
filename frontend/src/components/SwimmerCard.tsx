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
}

function SwimmerCard({ swimmer, status }: SwimmerCardProps) {
  return (
    <div className={status === undefined ? 'swimmer-card' : `swimmer-card ${status}`}>
      <div className="swimmer-name">
        {swimmer.first_name} {swimmer.last_name}
      </div>
      <div className="swimmer-details">
        <span>Weights: {WEIGHTS_GROUP_LABELS[swimmer.weights_group]}</span>
        {status !== undefined ? (
          <span className={`badge status-${status}`}>{STATUS_LABELS[status]}</span>
        ) : (
          !swimmer.has_schedule && <span className="badge status-unknown">No calendar</span>
        )}
      </div>
      {swimmer.tags.length > 0 && (
        <div className="swimmer-tags">
          {swimmer.tags.map((tag) => (
            <span key={tag} className="badge">
              {tag}
            </span>
          ))}
        </div>
      )}
    </div>
  )
}

export default SwimmerCard
