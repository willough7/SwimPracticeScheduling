import { useState } from 'react'
import type { FormEvent } from 'react'
import { createPractice, errorMessage, updatePractice } from '../api'
import { DAY_NAMES } from '../labels'
import { formatDuration, formatTime, toMinutes, toTimeString } from '../time'
import type { Day, Practice } from '../types'
import LengthPicker from './LengthPicker'
import TimePicker from './TimePicker'

// One-click practice lengths, in minutes: 1h to 2h in 15-minute steps.
// Anything else can be set with the length picker next to them.
const LENGTH_CHOICES = [60, 75, 90, 105, 120]

const MIDNIGHT = 24 * 60

type PracticeFormProps = {
  // Leave out to add a new practice; pass one to edit it
  practice?: Practice
  defaultDay: Day // for a new practice: the day tab that's open
  onSaved: (practice: Practice) => void
  onCancel: () => void
}

// One form for both adding and editing. When editing, every field starts
// filled in with the practice's current values.
function PracticeForm({ practice, defaultDay, onSaved, onCancel }: PracticeFormProps) {
  const isEditing = practice !== undefined
  const [day, setDay] = useState<Day>(practice?.day ?? defaultDay)
  const [title, setTitle] = useState(practice?.practice_title ?? '')
  // The coach picks a start time and a length, both in minutes.
  // The end time is worked out from those two.
  const [startMinutes, setStartMinutes] = useState(
    practice ? toMinutes(practice.start_time) : 6 * 60, // new practices start at 6:00 AM
  )
  const [lengthMinutes, setLengthMinutes] = useState(
    practice ? toMinutes(practice.end_time) - toMinutes(practice.start_time) : 90,
  )
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const endMinutes = startMinutes + lengthMinutes
  const endsByMidnight = endMinutes <= MIDNIGHT

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()

    if (lengthMinutes === 0) {
      setError('The practice needs a length.')
      return
    }
    if (!endsByMidnight) {
      setError('The practice has to end by midnight.')
      return
    }

    setSubmitting(true)
    setError(null)
    try {
      const data = {
        day,
        start_time: toTimeString(startMinutes),
        end_time: toTimeString(endMinutes % MIDNIGHT),
        practice_title: title.trim(),
      }
      const saved = isEditing
        ? await updatePractice(practice.practice_id, data)
        : await createPractice(data)
      onSaved(saved)
    } catch (err) {
      setError(errorMessage(err))
      setSubmitting(false)
    }
  }

  return (
    <form className="form" onSubmit={handleSubmit}>
      <label>
        Title
        <input
          placeholder="e.g. Morning Swim"
          value={title}
          onChange={(event) => setTitle(event.target.value)}
          required
        />
      </label>

      <label>
        Day
        <select value={day} onChange={(event) => setDay(Number(event.target.value) as Day)}>
          {Object.entries(DAY_NAMES).map(([value, name]) => (
            <option key={value} value={value}>
              {name}
            </option>
          ))}
        </select>
      </label>

      <div className="field">
        <span className="field-label">Starts</span>
        <TimePicker label="Start" value={startMinutes} onChange={setStartMinutes} />
      </div>

      <div className="field">
        <span className="field-label">Length</span>
        <div className="tag-filters">
          {LENGTH_CHOICES.map((minutes) => (
            <button
              key={minutes}
              type="button"
              // Highlighted whenever the current length matches, however it got there
              className={minutes === lengthMinutes ? 'tag-filter selected' : 'tag-filter'}
              aria-pressed={minutes === lengthMinutes}
              onClick={() => setLengthMinutes(minutes)}
            >
              {formatDuration(minutes)}
            </button>
          ))}
        </div>
        {/* Always shows the current length, whether it came from a button or from here */}
        <LengthPicker value={lengthMinutes} onChange={setLengthMinutes} />
      </div>

      {lengthMinutes > 0 && endsByMidnight && (
        <p className="time-summary">
          {DAY_NAMES[day]}, {formatTime(startMinutes)} – {formatTime(endMinutes % MIDNIGHT)} (
          {formatDuration(lengthMinutes)})
        </p>
      )}

      {error && <p className="form-error">{error}</p>}

      <div className="form-actions">
        <button type="button" className="button" onClick={onCancel}>
          Cancel
        </button>
        <button type="submit" className="button primary" disabled={submitting}>
          {submitting ? 'Saving…' : isEditing ? 'Save changes' : 'Add practice'}
        </button>
      </div>
    </form>
  )
}

export default PracticeForm
