const HOURS = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
const MINUTES = [0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55]

type TimePickerProps = {
  label: string // e.g. "Start", used to name the controls for screen readers
  value: number // minutes since midnight
  onChange: (minutes: number) => void
}

// A time of day as an hour dropdown, a minute dropdown, and an AM/PM switch.
// The parent only ever deals in "minutes since midnight"; this component
// handles converting to and from the 12-hour clock.
function TimePicker({ label, value, onChange }: TimePickerProps) {
  const hours24 = Math.floor(value / 60) % 24
  const minute = value % 60
  const isPm = hours24 >= 12
  const hour12 = hours24 % 12 === 0 ? 12 : hours24 % 12

  // Rebuild minutes since midnight from the three parts.
  // 12 AM is hour 0 and 12 PM is hour 12, which is what `% 12` takes care of.
  function update(newHour12: number, newMinute: number, newIsPm: boolean) {
    const newHours24 = (newHour12 % 12) + (newIsPm ? 12 : 0)
    onChange(newHours24 * 60 + newMinute)
  }

  return (
    <div className="time-picker" role="group" aria-label={label}>
      <select
        aria-label={`${label} hour`}
        value={hour12}
        onChange={(event) => update(Number(event.target.value), minute, isPm)}
      >
        {HOURS.map((hour) => (
          <option key={hour} value={hour}>
            {hour}
          </option>
        ))}
      </select>
      <span className="time-colon">:</span>
      <select
        aria-label={`${label} minute`}
        value={minute}
        onChange={(event) => update(hour12, Number(event.target.value), isPm)}
      >
        {MINUTES.map((m) => (
          <option key={m} value={m}>
            {String(m).padStart(2, '0')}
          </option>
        ))}
      </select>
      <div className="am-pm">
        <button
          type="button"
          className={isPm ? '' : 'selected'}
          aria-pressed={!isPm}
          onClick={() => update(hour12, minute, false)}
        >
          AM
        </button>
        <button
          type="button"
          className={isPm ? 'selected' : ''}
          aria-pressed={isPm}
          onClick={() => update(hour12, minute, true)}
        >
          PM
        </button>
      </div>
    </div>
  )
}

export default TimePicker
