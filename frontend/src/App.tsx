import { useEffect, useState } from 'react'
import {
  assignSwimmer,
  getPracticeConflicts,
  getPractices,
  getPracticeSwimmers,
  getSwimmers,
  unassignSwimmer,
} from './api'
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
  // practice_id -> ids of the swimmers assigned to it, for the selected day's practices
  const [assignments, setAssignments] = useState<Map<number, number[]>>(new Map())
  // Swimmers with an assign/unassign request still in flight (their cards are disabled)
  const [pendingSwimmerIds, setPendingSwimmerIds] = useState<Set<number>>(new Set())
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

  // Load the selected day's practices and who is assigned to each,
  // and again whenever the day changes.
  useEffect(() => {
    // If the coach clicks another day before this request finishes, the cleanup
    // below sets ignore = true, so this older response can't overwrite the newer day.
    let ignore = false

    async function loadPractices() {
      try {
        const dayPractices = await getPractices(selectedDay)
        // One request per practice, all sent at once. Promise.all waits until
        // every one has finished and gives back the results in the same order.
        const swimmerLists = await Promise.all(
          dayPractices.map((practice) => getPracticeSwimmers(practice.practice_id)),
        )
        if (!ignore) {
          setPractices(dayPractices)
          setAssignments(
            new Map(
              dayPractices.map((practice, i) => [
                practice.practice_id,
                swimmerLists[i].map((swimmer) => swimmer.swimmer_id),
              ]),
            ),
          )
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

  // How many swimmers each practice has, for the practice blocks
  const assignedCounts = new Map(
    [...assignments].map(([practiceId, swimmerIds]) => [practiceId, swimmerIds.length]),
  )

  // Who is assigned to the selected practice (null when nothing is selected)
  const assignedToSelected =
    selectedPracticeId === null ? null : new Set(assignments.get(selectedPracticeId) ?? [])

  async function handleToggleAssignment(swimmerId: number) {
    if (selectedPracticeId === null) {
      return
    }
    // Copy into a local constant: if the coach clicks another practice while the
    // request is in flight, this function still finishes the one it started.
    const practiceId = selectedPracticeId
    const isAssigned = (assignments.get(practiceId) ?? []).includes(swimmerId)

    setPendingSwimmerIds((current) => new Set(current).add(swimmerId))
    try {
      if (isAssigned) {
        await unassignSwimmer(practiceId, swimmerId)
      } else {
        await assignSwimmer(practiceId, swimmerId)
      }
      // Only update the screen once the backend has confirmed the change.
      setAssignments((current) => {
        const next = new Map(current)
        const ids = current.get(practiceId) ?? []
        next.set(practiceId, isAssigned ? ids.filter((id) => id !== swimmerId) : [...ids, swimmerId])
        return next
      })
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setPendingSwimmerIds((current) => {
        const next = new Set(current)
        next.delete(swimmerId)
        return next
      })
    }
  }

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

      {error && (
        <div className="error">
          <span>Something went wrong: {error}</span>
          <button onClick={() => setError(null)} aria-label="Dismiss error">
            ×
          </button>
        </div>
      )}

      <ScheduleView
        practices={practices}
        selectedPracticeId={selectedPracticeId}
        assignedCounts={assignedCounts}
        onSelectPractice={handleSelectPractice}
      />

      <SwimmerPanel
        swimmers={swimmers}
        statuses={statuses}
        selectedPractice={selectedPractice}
        assignedIds={assignedToSelected}
        pendingIds={pendingSwimmerIds}
        onToggleAssignment={handleToggleAssignment}
      />
    </div>
  )
}

export default App
