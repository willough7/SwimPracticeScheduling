import type { Swimmer, WeightsGroup } from '../types'

const WEIGHTS_GROUP_LABELS: Record<WeightsGroup, string> = {
  THREE_DAY_A: '3-day A',
  THREE_DAY_B: '3-day B',
  FOUR_DAY: '4-day',
}

type SwimmerCardProps = {
  swimmer: Swimmer
}

function SwimmerCard({ swimmer }: SwimmerCardProps) {
  return (
    <div className="swimmer-card">
      <div className="swimmer-name">
        {swimmer.first_name} {swimmer.last_name}
      </div>
      <div className="swimmer-details">
        <span>Weights: {WEIGHTS_GROUP_LABELS[swimmer.weights_group]}</span>
        {!swimmer.has_schedule && <span className="badge warning">No calendar</span>}
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
