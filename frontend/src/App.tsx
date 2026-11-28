import { useEffect, useState } from 'react'
import { getPractices, getSwimmers } from './api'
import DayTabs from './components/DayTabs'
import ScheduleView from './components/ScheduleView'
import type { Day, Practice, Swimmer } from './types'
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

function App() {
  const [selectedDay, setSelectedDay] = useState<Day>(today())
  const [practices, setPractices] = useState<Practice[]>([])
  const [selectedPracticeId, setSelectedPracticeId] = useState<number | null>(null)
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

      {/* Temporary: this becomes the resizable swimmer panel in step 4. */}
      <section className="swimmer-list">
        <h2>Swimmers</h2>
        {swimmers.length === 0 && <p>No swimmers yet.</p>}
        <ul>
          {swimmers.map((swimmer) => (
            <li key={swimmer.swimmer_id}>
              {swimmer.first_name} {swimmer.last_name}
            </li>
          ))}
        </ul>
      </section>
    </div>
  )
}

export default App
