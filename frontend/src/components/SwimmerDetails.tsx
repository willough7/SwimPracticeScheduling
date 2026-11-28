import { useState } from 'react'
import { deleteSwimmer, errorMessage, uploadSchedule } from '../api'
import { WEIGHTS_GROUP_LABELS } from '../labels'
import type { Swimmer } from '../types'

type SwimmerDetailsProps = {
  swimmer: Swimmer
  onUpdated: (swimmer: Swimmer) => void
  onDeleted: (swimmerId: number) => void
  canEdit: boolean // only admins can edit or delete; anyone can upload a calendar
  onEdit: () => void
}

// Shown in a Modal when the coach clicks a swimmer while no practice is selected.
function SwimmerDetails({ swimmer, onUpdated, onDeleted, canEdit, onEdit }: SwimmerDetailsProps) {
  const [calendarFile, setCalendarFile] = useState<File | null>(null)
  const [busy, setBusy] = useState(false)
  const [message, setMessage] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  const fullName = `${swimmer.first_name} ${swimmer.last_name}`

  async function handleUpload() {
    if (calendarFile === null) {
      return
    }
    setBusy(true)
    setError(null)
    setMessage(null)
    try {
      onUpdated(await uploadSchedule(swimmer.swimmer_id, calendarFile))
      setMessage('Calendar uploaded.')
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setBusy(false)
    }
  }

  async function handleDelete() {
    // window.confirm shows the browser's built-in OK/Cancel box and returns true for OK.
    if (!window.confirm(`Delete ${fullName}? This also removes them from every practice.`)) {
      return
    }
    setBusy(true)
    setError(null)
    try {
      await deleteSwimmer(swimmer.swimmer_id)
      onDeleted(swimmer.swimmer_id)
    } catch (err) {
      setError(errorMessage(err))
      setBusy(false)
    }
  }

  return (
    <div className="form">
      <p className="form-hint">
        Weights: {WEIGHTS_GROUP_LABELS[swimmer.weights_group]}
        {swimmer.tags.length > 0 && <> · Tags: {swimmer.tags.join(', ')}</>}
      </p>

      <fieldset>
        <legend>Class calendar</legend>
        <p className="form-hint">
          {swimmer.has_schedule
            ? 'Uploaded. Uploading a new file replaces it.'
            : 'Not uploaded yet, so this swimmer shows as "No calendar".'}
        </p>
        <div className="new-tag-row">
          <input
            type="file"
            accept=".ics,text/calendar"
            onChange={(event) => setCalendarFile(event.target.files?.[0] ?? null)}
          />
          <button
            type="button"
            className="button primary"
            disabled={calendarFile === null || busy}
            onClick={handleUpload}
          >
            Upload
          </button>
        </div>
      </fieldset>

      {message && <p className="form-success">{message}</p>}
      {error && <p className="form-error">{error}</p>}

      {canEdit && (
        <div className="form-actions">
          <button type="button" className="button danger" disabled={busy} onClick={handleDelete}>
            Delete swimmer
          </button>
          <button type="button" className="button" disabled={busy} onClick={onEdit}>
            Edit details
          </button>
        </div>
      )}
    </div>
  )
}

export default SwimmerDetails
