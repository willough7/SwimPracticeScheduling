import type { Practice, Swimmer, SwimmerStatus } from '../types'
import PracticeHeader from './PracticeHeader'

type PracticeSummaryProps = {
  practice: Practice
  assignedSwimmers: Swimmer[]
  statuses: Map<number, SwimmerStatus> | null // null while the conflict check is loading
  canEdit: boolean
  onOpenLanes: () => void
  onEdit: () => void
  onDelete: () => void
}

// Shown on the right when a practice is clicked once: who's in it, and how
// many of the whole roster can make it. Assigning happens in the bottom panel.
function PracticeSummary({
  practice,
  assignedSwimmers,
  statuses,
  canEdit,
  onOpenLanes,
  onEdit,
  onDelete,
}: PracticeSummaryProps) {
  // How many of the whole roster are in each group for this practice
  const counts = { available: 0, conflict: 0, unknown: 0 }
  if (statuses !== null) {
    for (const status of statuses.values()) {
      counts[status] += 1
    }
  }

  return (
    <div className="detail-view">
      <PracticeHeader
        practice={practice}
        summary={
          statuses === null
            ? 'Checking schedules…'
            : `${counts.available} available · ${counts.conflict} class conflict · ${counts.unknown} no calendar`
        }
      >
        <button className="button primary" onClick={onOpenLanes}>
          Open lanes
        </button>
        {canEdit && (
          <>
            <button className="button" onClick={onEdit}>
              Edit
            </button>
            <button className="button danger" onClick={onDelete}>
              Delete
            </button>
          </>
        )}
      </PracticeHeader>

      <h3 className="detail-subheading">
        Assigned ({assignedSwimmers.length})
      </h3>
      {assignedSwimmers.length === 0 ? (
        <p className="detail-hint">
          {canEdit
            ? 'No one yet. Click swimmers in the panel below to assign them, then double-click the practice (or press Open lanes) to arrange lanes.'
            : 'No one is assigned to this practice yet.'}
        </p>
      ) : (
        <div className="swimmer-chips">
          {assignedSwimmers.map((swimmer) => {
            const status = statuses?.get(swimmer.swimmer_id)
            return (
              <span
                key={swimmer.swimmer_id}
                className={status ? `swimmer-chip ${status}` : 'swimmer-chip'}
              >
                {swimmer.first_name} {swimmer.last_name}
              </span>
            )
          })}
        </div>
      )}
    </div>
  )
}

export default PracticeSummary
