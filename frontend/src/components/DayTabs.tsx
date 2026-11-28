import type { Day } from '../types'

const DAYS: { day: Day; label: string }[] = [
  { day: 1, label: 'Mon' },
  { day: 2, label: 'Tue' },
  { day: 3, label: 'Wed' },
  { day: 4, label: 'Thu' },
  { day: 5, label: 'Fri' },
  { day: 6, label: 'Sat' },
  { day: 7, label: 'Sun' },
]

type DayTabsProps = {
  selectedDay: Day
  onSelectDay: (day: Day) => void
}

function DayTabs({ selectedDay, onSelectDay }: DayTabsProps) {
  return (
    <nav className="day-tabs">
      {DAYS.map(({ day, label }) => (
        <button
          key={day}
          className={day === selectedDay ? 'day-tab selected' : 'day-tab'}
          onClick={() => onSelectDay(day)}
        >
          {label}
        </button>
      ))}
    </nav>
  )
}

export default DayTabs