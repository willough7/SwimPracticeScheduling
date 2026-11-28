import type { ReactNode } from 'react'
import { DAY_NAMES } from '../labels'
import { formatDuration, formatTime, toMinutes } from '../time'
import type { Practice } from '../types'

type PracticeHeaderProps = {
  practice: Practice
  summary: ReactNode // a line of counts under the time
  children: ReactNode // the action buttons on the right
}

// The title bar at the top of the practice summary and the lanes view
function PracticeHeader({ practice, summary, children }: PracticeHeaderProps) {
  const start = toMinutes(practice.start_time)
  const end = toMinutes(practice.end_time)

  return (
    <div className="practice-header">
      <div>
        <h2>{practice.practice_title}</h2>
        <p className="practice-header-time">
          {DAY_NAMES[practice.day]}, {formatTime(start)} – {formatTime(end)} (
          {formatDuration(end - start)})
        </p>
        <p className="practice-header-summary">{summary}</p>
      </div>
      <div className="practice-header-actions">{children}</div>
    </div>
  )
}

export default PracticeHeader
