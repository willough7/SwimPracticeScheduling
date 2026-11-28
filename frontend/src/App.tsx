import { useEffect, useState } from 'react'
import { getPracticeConflicts, getPractices, getSwimmers } from './api'
import DayTabs from './components/DayTabs'
import ScheduleView from './components/ScheduleView'
import SwimmerPanel from './components/SwimmerPanel'
import { toDateString } from './time'
import type { Day, Practice, PracticeConflicts, Swimmer, SwimmerStatus } from './types'
import './App.css'

// JavaScript's getDay() is 0 = Sunday ... 6 = Saturday.
// The backend uses isoweekday(): 1 = Monday ... 7 = Sunday.
function today(): Day {
  const jsDay = new Date().getDay()
  return (jsDay === 0 ? 7 : jsDay) as Day
}

function errorMessage(err: unknown): string {
  return err instanceof Error ? err.message : String(err)
}

// Turns the endpoint's three id lists into one lookup: swimmer_id -> status
function toStatusMap(conflicts: PracticeConflicts): Map<number, SwimmerStatus> {
  const statuses = new Map<number, SwimmerStatus>()
  for (const id of conflicts.available) {
    statuses.set(id, 'available')
  }
  for (const id of conflicts.conflict) {
    statuses.set(id, 'conflict')
  }
  for (const id of conflicts.unknown) {
    statuses.set(id, 'unknown')
  }
  return statuses
}

function App() {
  const [selectedDay, setSelectedDay] = useState<Day>(today())
  const [practices, setPractices] = useState<Practice[]>([])
  const [selectedPracticeId, setSelectedPracticeId] = useState<number | null>(null)
  const [conflicts, setConflicts] = useState<PracticeConflicts | null>(null)
  const [swimmers, setSwimmers] = useState<Swimmer[]>([])
  const [error, setError] = useState<string | null>(null)

  // Load the roster once, when the page opens.
  useEffect(() => {
    async function loadSwimmers() {
      try {
        setSwimmers(await getSwimmers())
      } catch (err) {
        setError(errorMessage(err))
      }
    }

    loadSwimmers()
  }, [])

  // Load the selected day's practices, and again whenever the day changes.
  useEffect(() => {
    // If the coach clicks another day before this request finishes, the cleanup
    // below sets ignore = true, so this older response can't overwrite the newer day.
    let ignore = false

    async function loadPractices() {
      try {
        const dayPractices = await getPractices(selectedDay)
        if (!ignore) {
          setPractices(dayPractices)
        }
      } catch (err) {
        if (!ignore) {
          setError(errorMessage(err))
        }
      }
    }

    loadPractices()
    return () => {
      ignore = true
    }
  }, [selectedDay])

  // Ask the backend who can make the selected practice, whenever the selection changes.
  useEffect(() => {
    if (selectedPracticeId === null) {
      return
    }
    let ignore = false // same race-condition guard as the practices effect

    async function loadConflicts(practiceId: number) {
      try {
        // Any date in the week works; the backend rounds it back to Monday.
        // For now that's always the current week.
        const result = await getPracticeConflicts(practiceId, toDateString(new Date()))
        if (!ignore) {
          setConflicts(result)
        }
      } catch (err) {
        if (!ignore) {
          setError(errorMessage(err))
        }
      }
    }

    loadConflicts(selectedPracticeId)
    return () => {
      ignore = true
    }
  }, [selectedPracticeId])

  const selectedPractice =
    practices.find((practice) => practice.practice_id === selectedPracticeId) ?? null

  // Only use conflict results that belong to the practice selected right now.
  // Just after a click, `conflicts` still holds the previous practice's results
  // until the new ones arrive, and those must not be shown.
  const statuses =
    conflicts !== null && conflicts.practice_id === selectedPracticeId
      ? toStatusMap(conflicts)
      : null

  function handleSelectDay(day: Day) {
    setSelectedDay(day)
    setSelectedPracticeId(null) // a selected practice belongs to the old day
  }

  function handleSelectPractice(practiceId: number) {
    // Clicking the selected practice again deselects it.
    setSelectedPracticeId((current) => (current === practiceId ? null : practiceId))
  }

  return (
    <div className="app">
      <DayTabs selectedDay={selectedDay} onSelectDay={handleSelectDay} />

      {error && <p className="error">Something went wrong: {error}</p>}

      <ScheduleView
        practices={practices}
        selectedPracticeId={selectedPracticeId}
        onSelectPractice={handleSelectPractice}
      />

      <SwimmerPanel
        swimmers={swimmers}
        statuses={statuses}
        selectedPractice={selectedPractice}
      />
    </div>
  )
}

export default App
