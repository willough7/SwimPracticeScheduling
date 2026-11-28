import { useState } from 'react'
import type { FormEvent, KeyboardEvent } from 'react'
import { createSwimmer, errorMessage, updateSwimmer, uploadSchedule } from '../api'
import { WEIGHTS_GROUP_LABELS } from '../labels'
import type { Swimmer, WeightsGroup } from '../types'

type SwimmerFormProps = {
  // Leave out to add a new swimmer; pass one to edit them
  swimmer?: Swimmer
  knownTags: string[] // tags already used by other swimmers, offered as choices
  // uploadError is set when a new swimmer was created but their calendar was rejected
  onSaved: (swimmer: Swimmer, uploadError: string | null) => void
  onCancel: () => void
}

// One form for both adding and editing. When editing, every field starts
// filled in, and the calendar upload is left out (that's in the swimmer's
// details dialog, so a details edit can never replace their calendar by accident).
function SwimmerForm({ swimmer, knownTags, onSaved, onCancel }: SwimmerFormProps) {
  const isEditing = swimmer !== undefined
  const [firstName, setFirstName] = useState(swimmer?.first_name ?? '')
  const [lastName, setLastName] = useState(swimmer?.last_name ?? '')
  const [weightsGroup, setWeightsGroup] = useState<WeightsGroup>(
    swimmer?.weights_group ?? 'THREE_DAY_A',
  )
  const [tags, setTags] = useState<string[]>(swimmer?.tags ?? [])
  const [newTag, setNewTag] = useState('')
  const [calendarFile, setCalendarFile] = useState<File | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Existing tags plus any new ones typed for this swimmer
  const tagChoices = [...new Set([...knownTags, ...tags])].sort()

  function toggleTag(tag: string) {
    setTags((current) =>
      current.includes(tag) ? current.filter((t) => t !== tag) : [...current, tag],
    )
  }

  function addNewTag() {
    const tag = newTag.trim()
    if (tag !== '' && !tags.includes(tag)) {
      setTags([...tags, tag])
    }
    setNewTag('')
  }

  function handleNewTagKeyDown(event: KeyboardEvent<HTMLInputElement>) {
    // Enter in a form field normally submits the whole form. Here it should
    // just add the tag, so we cancel that default.
    if (event.key === 'Enter') {
      event.preventDefault()
      addNewTag()
    }
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    // Without this, the browser does an old-style form submission and reloads the page.
    event.preventDefault()
    setSubmitting(true)
    setError(null)

    // Include a tag that was typed but never added with Enter or the Add button.
    const pendingTag = newTag.trim()
    const finalTags = pendingTag !== '' && !tags.includes(pendingTag) ? [...tags, pendingTag] : tags

    const data = {
      first_name: firstName.trim(),
      last_name: lastName.trim(),
      weights_group: weightsGroup,
      tags: finalTags,
    }

    let saved: Swimmer
    try {
      saved = isEditing
        ? await updateSwimmer(swimmer.swimmer_id, data)
        : await createSwimmer(data)
    } catch (err) {
      // Nothing was created, so keep the form open to fix and try again.
      setError(errorMessage(err))
      setSubmitting(false)
      return
    }

    // The swimmer exists now. If their calendar is rejected, submitting the form
    // again would create a duplicate swimmer, so report the problem instead.
    let uploadError: string | null = null
    if (calendarFile !== null) {
      try {
        saved = await uploadSchedule(saved.swimmer_id, calendarFile)
      } catch (err) {
        uploadError = errorMessage(err)
      }
    }
    onSaved(saved, uploadError)
  }

  return (
    <form className="form" onSubmit={handleSubmit}>
      <div className="form-row">
        <label>
          First name
          <input
            value={firstName}
            onChange={(event) => setFirstName(event.target.value)}
            required
          />
        </label>
        <label>
          Last name
          <input
            value={lastName}
            onChange={(event) => setLastName(event.target.value)}
            required
          />
        </label>
      </div>

      <label>
        Weights group
        <select
          value={weightsGroup}
          onChange={(event) => setWeightsGroup(event.target.value as WeightsGroup)}
        >
          {Object.entries(WEIGHTS_GROUP_LABELS).map(([value, label]) => (
            <option key={value} value={value}>
              {label}
            </option>
          ))}
        </select>
      </label>

      <fieldset>
        <legend>Tags</legend>
        {tagChoices.length > 0 && (
          <div className="tag-filters">
            {tagChoices.map((tag) => (
              // type="button": a plain <button> inside a form is a submit button by default
              <button
                key={tag}
                type="button"
                className={tags.includes(tag) ? 'tag-filter selected' : 'tag-filter'}
                onClick={() => toggleTag(tag)}
              >
                {tag}
              </button>
            ))}
          </div>
        )}
        <div className="new-tag-row">
          <input
            placeholder="New tag, e.g. Distance"
            value={newTag}
            onChange={(event) => setNewTag(event.target.value)}
            onKeyDown={handleNewTagKeyDown}
          />
          <button type="button" className="button" onClick={addNewTag}>
            Add
          </button>
        </div>
      </fieldset>

      {!isEditing && (
        <label>
          Class calendar (.ics, optional)
          <input
            type="file"
            accept=".ics,text/calendar"
            onChange={(event) => setCalendarFile(event.target.files?.[0] ?? null)}
          />
        </label>
      )}

      {error && <p className="form-error">{error}</p>}

      <div className="form-actions">
        <button type="button" className="button" onClick={onCancel}>
          Cancel
        </button>
        <button type="submit" className="button primary" disabled={submitting}>
          {submitting ? 'Saving…' : isEditing ? 'Save changes' : 'Add swimmer'}
        </button>
      </div>
    </form>
  )
}

export default SwimmerForm
