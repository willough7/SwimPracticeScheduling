import { useEffect, useState } from 'react'
import {
  assignSwimmer,
  deletePractice,
  deleteSwimmer,
  errorMessage,
  getPracticeConflicts,
  getPracticeLanes,
  getPractices,
  getPracticeSwimmers,
  getSwimmers,
  setSwimmerLane,
  unassignSwimmer,
} from './api'
import ContextMenu from './components/ContextMenu'
import type { MenuItem } from './components/ContextMenu'
import DayTabs from './components/DayTabs'
import LanesView from './components/LanesView'
import Modal from './components/Modal'
import PracticeForm from './components/PracticeForm'
import PracticeSummary from './components/PracticeSummary'
import ScheduleView from './components/ScheduleView'
import SwimmerDetails from './components/SwimmerDetails'
import SwimmerForm from './components/SwimmerForm'
import SwimmerPanel from './components/SwimmerPanel'
import { LANES } from './labels'
import { toDateString } from './time'
import type { Day, PanelMode, Practice, PracticeConflicts, Swimmer, SwimmerStatus } from './types'
import './App.css'

// Which pop-up is open, if any. Each kind carries only the data it needs:
// the edit forms and the swimmer dialog need to know which one, the add forms need nothing.
type DialogState =
  | { kind: 'add-swimmer' }
  | { kind: 'add-practice' }
  | { kind: 'swimmer'; swimmerId: number }
  | { kind: 'edit-swimmer'; swimmerId: number }
  | { kind: 'edit-practice'; practiceId: number }
  | null

// An open right-click menu: where it is and what's in it
type ContextMenuState = { x: number; y: number; items: MenuItem[] } | null

// JavaScript's getDay() is 0 = Sunday ... 6 = Saturday.
// The backend uses isoweekday(): 1 = Monday ... 7 = Sunday.
function today(): Day {
  const jsDay = new Date().getDay()
  return (jsDay === 0 ? 7 : jsDay) as Day
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
  // Clicked once = 'assign', double-clicked = 'lanes'
  const [practiceView, setPracticeView] = useState<'assign' | 'lanes'>('assign')
  // Lane spots for one practice (swimmer_id -> lane), loaded when its lanes open.
  // practiceId says which practice they belong to, like the conflicts check.
  const [lanePlacements, setLanePlacements] = useState<{
    practiceId: number
    lanes: Map<number, number>
  } | null>(null)
  // practice_id -> ids of the swimmers assigned to it, for the selected day's practices
  const [assignments, setAssignments] = useState<Map<number, number[]>>(new Map())
  // Swimmers with an assign/unassign request still in flight (their cards are disabled)
  const [pendingSwimmerIds, setPendingSwimmerIds] = useState<Set<number>>(new Set())
  const [conflicts, setConflicts] = useState<PracticeConflicts | null>(null)
  // Bumped whenever swimmers change, so the conflicts effect runs again
  const [conflictsVersion, setConflictsVersion] = useState(0)
  const [swimmers, setSwimmers] = useState<Swimmer[]>([])
  const [dialog, setDialog] = useState<DialogState>(null)
  const [contextMenu, setContextMenu] = useState<ContextMenuState>(null)
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

  // Ask the backend who can make the selected practice, whenever the selection
  // changes or a swimmer is added, deleted, or gets a new calendar.
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
  }, [selectedPracticeId, conflictsVersion])

  // Load the selected practice's lanes whenever its lanes view opens.
  useEffect(() => {
    if (selectedPracticeId === null || practiceView !== 'lanes') {
      return
    }
    let ignore = false

    async function loadLanes(practiceId: number) {
      try {
        const placements = await getPracticeLanes(practiceId)
        if (!ignore) {
          setLanePlacements({
            practiceId,
            lanes: new Map(placements.map((p) => [p.swimmer_id, p.lane])),
          })
        }
      } catch (err) {
        if (!ignore) {
          setError(errorMessage(err))
        }
      }
    }

    loadLanes(selectedPracticeId)
    return () => {
      ignore = true
    }
  }, [selectedPracticeId, practiceView])

  const selectedPractice =
    practices.find((practice) => practice.practice_id === selectedPracticeId) ?? null

  // What the right side and the bottom panel are showing right now
  const mode: PanelMode =
    selectedPractice === null ? 'browse' : practiceView === 'lanes' ? 'lanes' : 'assign'

  // Lane spots for the selected practice, or null if they're not loaded (yet)
  const lanesForSelected =
    lanePlacements !== null && lanePlacements.practiceId === selectedPracticeId
      ? lanePlacements.lanes
      : null

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

  // The selected practice's swimmers, in roster order
  const assignedSwimmers =
    assignedToSelected === null
      ? []
      : swimmers.filter((swimmer) => assignedToSelected.has(swimmer.swimmer_id))

  // The bottom panel shows the whole roster, except in lanes mode, where it
  // shows the practice's swimmers who aren't in a lane yet
  const panelSwimmers =
    mode === 'lanes'
      ? assignedSwimmers.filter((swimmer) => !lanesForSelected?.has(swimmer.swimmer_id))
      : swimmers

  // Every tag in use, offered as choices in the Add swimmer form
  const knownTags = [...new Set(swimmers.flatMap((swimmer) => swimmer.tags))]

  // The swimmer or practice a dialog is about, looked up fresh on every render
  // so the dialog shows changes (like a new calendar) as soon as they happen.
  const dialogSwimmer =
    dialog?.kind === 'swimmer' || dialog?.kind === 'edit-swimmer'
      ? (swimmers.find((swimmer) => swimmer.swimmer_id === dialog.swimmerId) ?? null)
      : null
  const dialogPractice =
    dialog?.kind === 'edit-practice'
      ? (practices.find((practice) => practice.practice_id === dialog.practiceId) ?? null)
      : null

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
      if (isAssigned) {
        removeFromLanes(swimmerId) // the backend dropped their lane spot too
      }
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

  // With a practice selected, clicking a swimmer assigns or unassigns them.
  // Without one, it opens their details so the coach can upload a calendar.
  // Puts a swimmer in a lane (1-8), or takes them out of their lane (null).
  // Like assigning, the screen changes once the backend confirms.
  async function handleMoveToLane(swimmerId: number, lane: number | null) {
    if (selectedPracticeId === null || lanesForSelected === null) {
      return
    }
    const practiceId = selectedPracticeId
    if ((lanesForSelected.get(swimmerId) ?? null) === lane) {
      return // dropped back where it started
    }

    setPendingSwimmerIds((current) => new Set(current).add(swimmerId))
    try {
      await setSwimmerLane(practiceId, swimmerId, lane)
      setLanePlacements((current) => {
        if (current === null || current.practiceId !== practiceId) {
          return current
        }
        const next = new Map(current.lanes)
        if (lane === null) {
          next.delete(swimmerId)
        } else {
          next.set(swimmerId, lane)
        }
        return { practiceId, lanes: next }
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

  function removeFromLanes(swimmerId: number) {
    setLanePlacements((current) => {
      if (current === null || !current.lanes.has(swimmerId)) {
        return current
      }
      const next = new Map(current.lanes)
      next.delete(swimmerId)
      return { ...current, lanes: next }
    })
  }

  // Clicking a swimmer card: assigns/unassigns in assign mode, opens their
  // details when no practice is selected, and does nothing in lanes mode
  // (there, cards are dragged instead).
  function handleSwimmerClick(swimmerId: number) {
    if (mode === 'assign') {
      handleToggleAssignment(swimmerId)
    } else if (mode === 'browse') {
      setDialog({ kind: 'swimmer', swimmerId })
    }
  }

  function handleSwimmerCreated(swimmer: Swimmer, uploadError: string | null) {
    setSwimmers((current) => [...current, swimmer])
    setConflictsVersion((version) => version + 1)
    setDialog(null)
    if (uploadError !== null) {
      setError(
        `${swimmer.first_name} ${swimmer.last_name} was added, but their calendar wasn't ` +
          `(${uploadError}). Click their card to try another file.`,
      )
    }
  }

  function handleSwimmerEdited(updated: Swimmer) {
    handleSwimmerUpdated(updated)
    setDialog(null)
  }

  function handleSwimmerUpdated(updated: Swimmer) {
    setSwimmers((current) =>
      current.map((swimmer) => (swimmer.swimmer_id === updated.swimmer_id ? updated : swimmer)),
    )
    setConflictsVersion((version) => version + 1)
  }

  function handleSwimmerDeleted(swimmerId: number) {
    setSwimmers((current) => current.filter((swimmer) => swimmer.swimmer_id !== swimmerId))
    // The backend removed their assignments too, so match that here.
    setAssignments(
      (current) =>
        new Map(
          [...current].map(([practiceId, ids]) => [practiceId, ids.filter((id) => id !== swimmerId)]),
        ),
    )
    removeFromLanes(swimmerId)
    setConflictsVersion((version) => version + 1)
    setDialog(null)
  }

  function handlePracticeCreated(practice: Practice) {
    setDialog(null)
    if (practice.day === selectedDay) {
      setPractices((current) => [...current, practice])
      setAssignments((current) => new Map(current).set(practice.practice_id, []))
    } else {
      // Switch to the new practice's day; the practices effect will load it.
      setSelectedDay(practice.day)
    }
    // Select it, so the coach can start assigning swimmers right away.
    setSelectedPracticeId(practice.practice_id)
  }

  function handlePracticeEdited(practice: Practice) {
    setDialog(null)
    if (practice.day === selectedDay) {
      setPractices((current) =>
        current.map((p) => (p.practice_id === practice.practice_id ? practice : p)),
      )
    } else {
      // It moved to another day: follow it there. The practices effect loads
      // that day, and the assignments come along because the id didn't change.
      setSelectedDay(practice.day)
    }
    setSelectedPracticeId(practice.practice_id)
    // New times can mean different conflicts
    setConflictsVersion((version) => version + 1)
  }

  async function handleDeletePractice(practiceId: number) {
    const practice = practices.find((p) => p.practice_id === practiceId)
    if (practice === undefined) {
      return
    }
    if (
      !window.confirm(`Delete ${practice.practice_title}? Its swimmer assignments are removed too.`)
    ) {
      return
    }
    try {
      await deletePractice(practiceId)
      setPractices((current) => current.filter((practice) => practice.practice_id !== practiceId))
      setAssignments((current) => {
        const next = new Map(current)
        next.delete(practiceId)
        return next
      })
      setSelectedPracticeId((current) => (current === practiceId ? null : current))
    } catch (err) {
      setError(errorMessage(err))
    }
  }

  async function handleDeleteSwimmer(swimmerId: number) {
    const swimmer = swimmers.find((s) => s.swimmer_id === swimmerId)
    if (swimmer === undefined) {
      return
    }
    const fullName = `${swimmer.first_name} ${swimmer.last_name}`
    if (!window.confirm(`Delete ${fullName}? This also removes them from every practice.`)) {
      return
    }
    try {
      await deleteSwimmer(swimmerId)
      handleSwimmerDeleted(swimmerId)
    } catch (err) {
      setError(errorMessage(err))
    }
  }

  // Right-clicking a practice selects it and opens its menu
  function handlePracticeContextMenu(practiceId: number, x: number, y: number) {
    if (practiceId !== selectedPracticeId) {
      setSelectedPracticeId(practiceId)
      setPracticeView('assign')
    }
    setContextMenu({
      x,
      y,
      items: [
        { label: 'Open lanes', onSelect: () => handleOpenLanes(practiceId) },
        { label: 'Edit practice', onSelect: () => setDialog({ kind: 'edit-practice', practiceId }) },
        { label: 'Delete practice', danger: true, onSelect: () => handleDeletePractice(practiceId) },
      ],
    })
  }

  function handleSwimmerContextMenu(swimmerId: number, x: number, y: number) {
    // In lanes mode the menu can also move the swimmer, so lanes work
    // without dragging (for the keyboard, or a trackpad that makes dragging awkward)
    const laneItems: MenuItem[] = []
    if (mode === 'lanes' && lanesForSelected !== null) {
      const currentLane = lanesForSelected.get(swimmerId) ?? null
      for (const lane of LANES) {
        if (lane !== currentLane) {
          laneItems.push({ label: `Move to lane ${lane}`, onSelect: () => handleMoveToLane(swimmerId, lane) })
        }
      }
      if (currentLane !== null) {
        laneItems.push({ label: 'Take out of lane', onSelect: () => handleMoveToLane(swimmerId, null) })
      }
    }

    setContextMenu({
      x,
      y,
      items: [
        ...laneItems,
        { label: 'Edit swimmer', onSelect: () => setDialog({ kind: 'edit-swimmer', swimmerId }) },
        { label: 'Class calendar…', onSelect: () => setDialog({ kind: 'swimmer', swimmerId }) },
        { label: 'Delete swimmer', danger: true, onSelect: () => handleDeleteSwimmer(swimmerId) },
      ],
    })
  }

  function closeContextMenu() {
    setContextMenu(null)
  }

  function handleSelectDay(day: Day) {
    setSelectedDay(day)
    setSelectedPracticeId(null) // a selected practice belongs to the old day
    setPracticeView('assign')
  }

  // One click: select the practice for assigning. Clicking it again while
  // assigning deselects it; clicking it while its lanes are open goes back to assigning.
  function handleSelectPractice(practiceId: number) {
    if (practiceId === selectedPracticeId && practiceView === 'assign') {
      setSelectedPracticeId(null)
    } else {
      setSelectedPracticeId(practiceId)
      setPracticeView('assign')
    }
  }

  // Double-click: select the practice and open its lanes
  function handleOpenLanes(practiceId: number) {
    setSelectedPracticeId(practiceId)
    setPracticeView('lanes')
  }

  function closeDialog() {
    setDialog(null)
  }

  return (
    <div className="app">
      <div className="top-bar">
        <DayTabs selectedDay={selectedDay} onSelectDay={handleSelectDay} />
        <div className="top-bar-actions">
          <button
            className="button"
            disabled={selectedPractice === null}
            title={selectedPractice === null ? 'Select a practice to edit it' : undefined}
            onClick={() =>
              selectedPractice !== null &&
              setDialog({ kind: 'edit-practice', practiceId: selectedPractice.practice_id })
            }
          >
            Edit practice
          </button>
          <button className="button" onClick={() => setDialog({ kind: 'add-practice' })}>
            + Practice
          </button>
        </div>
      </div>

      {error && (
        <div className="error">
          <span>Something went wrong: {error}</span>
          <button onClick={() => setError(null)} aria-label="Dismiss error">
            ×
          </button>
        </div>
      )}

      {/* Calendar on the left quarter, the selected practice on the other three quarters */}
      <div className="workspace">
        <div className="schedule-column">
          <ScheduleView
            practices={practices}
            selectedPracticeId={selectedPracticeId}
            assignedCounts={assignedCounts}
            onSelectPractice={handleSelectPractice}
            onOpenLanes={handleOpenLanes}
            onPracticeContextMenu={handlePracticeContextMenu}
          />
        </div>

        <div className="detail-area">
          {selectedPractice === null && (
            <div className="detail-empty">
              <p>Select a practice to see who can make it and assign swimmers.</p>
              <p>Double-click a practice to arrange its lanes.</p>
            </div>
          )}

          {selectedPractice !== null && mode === 'assign' && (
            <PracticeSummary
              practice={selectedPractice}
              assignedSwimmers={assignedSwimmers}
              statuses={statuses}
              onOpenLanes={() => handleOpenLanes(selectedPractice.practice_id)}
              onEdit={() =>
                setDialog({ kind: 'edit-practice', practiceId: selectedPractice.practice_id })
              }
              onDelete={() => handleDeletePractice(selectedPractice.practice_id)}
            />
          )}

          {selectedPractice !== null && mode === 'lanes' && (
            <LanesView
              practice={selectedPractice}
              assignedSwimmers={assignedSwimmers}
              lanes={lanesForSelected}
              statuses={statuses}
              pendingIds={pendingSwimmerIds}
              onMove={handleMoveToLane}
              onSwimmerContextMenu={handleSwimmerContextMenu}
              onBack={() => setPracticeView('assign')}
              onEdit={() =>
                setDialog({ kind: 'edit-practice', practiceId: selectedPractice.practice_id })
              }
              onDelete={() => handleDeletePractice(selectedPractice.practice_id)}
            />
          )}
        </div>
      </div>

      <SwimmerPanel
        title={mode === 'lanes' ? 'Not in a lane' : 'Swimmers'}
        mode={mode}
        swimmers={panelSwimmers}
        statuses={statuses}
        assignedIds={assignedToSelected}
        pendingIds={pendingSwimmerIds}
        onSwimmerClick={handleSwimmerClick}
        onSwimmerContextMenu={handleSwimmerContextMenu}
        onAddSwimmer={() => setDialog({ kind: 'add-swimmer' })}
        onDropOutOfLane={(swimmerId) => handleMoveToLane(swimmerId, null)}
      />

      {dialog?.kind === 'add-swimmer' && (
        <Modal title="Add swimmer" onClose={closeDialog}>
          <SwimmerForm knownTags={knownTags} onSaved={handleSwimmerCreated} onCancel={closeDialog} />
        </Modal>
      )}

      {dialog?.kind === 'add-practice' && (
        <Modal title="Add practice" onClose={closeDialog}>
          <PracticeForm
            defaultDay={selectedDay}
            onSaved={handlePracticeCreated}
            onCancel={closeDialog}
          />
        </Modal>
      )}

      {dialogPractice !== null && (
        <Modal title="Edit practice" onClose={closeDialog}>
          <PracticeForm
            practice={dialogPractice}
            defaultDay={selectedDay}
            onSaved={handlePracticeEdited}
            onCancel={closeDialog}
          />
        </Modal>
      )}

      {dialog?.kind === 'edit-swimmer' && dialogSwimmer !== null && (
        <Modal title="Edit swimmer" onClose={closeDialog}>
          <SwimmerForm
            swimmer={dialogSwimmer}
            knownTags={knownTags}
            onSaved={handleSwimmerEdited}
            onCancel={closeDialog}
          />
        </Modal>
      )}

      {dialog?.kind === 'swimmer' && dialogSwimmer !== null && (
        <Modal title={`${dialogSwimmer.first_name} ${dialogSwimmer.last_name}`} onClose={closeDialog}>
          <SwimmerDetails
            swimmer={dialogSwimmer}
            onUpdated={handleSwimmerUpdated}
            onDeleted={handleSwimmerDeleted}
            onEdit={() => setDialog({ kind: 'edit-swimmer', swimmerId: dialogSwimmer.swimmer_id })}
          />
        </Modal>
      )}

      {contextMenu !== null && (
        <ContextMenu
          x={contextMenu.x}
          y={contextMenu.y}
          items={contextMenu.items}
          onClose={closeContextMenu}
        />
      )}
    </div>
  )
}

export default App
