const HOURS = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
const MINUTES = [0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55]

type LengthPickerProps = {
  value: number // length in minutes
  onChange: (minutes: number) => void
}

// A practice length as an hours dropdown and a minutes dropdown, styled to
// match TimePicker. Like TimePicker, the parent only deals in minutes.
function LengthPicker({ value, onChange }: LengthPickerProps) {
  const hours = Math.floor(value / 60)
  const minutes = value % 60

  return (
    <div className="time-picker" role="group" aria-label="Length">
      <select
        aria-label="Length hours"
        value={hours}
        onChange={(event) => onChange(Number(event.target.value) * 60 + minutes)}
      >
        {HOURS.map((h) => (
          <option key={h} value={h}>
            {h}
          </option>
        ))}
      </select>
      <span className="time-unit">h</span>
      <select
        aria-label="Length minutes"
        value={minutes}
        onChange={(event) => onChange(hours * 60 + Number(event.target.value))}
      >
        {MINUTES.map((m) => (
          <option key={m} value={m}>
            {String(m).padStart(2, '0')}
          </option>
        ))}
      </select>
      <span className="time-unit">m</span>
    </div>
  )
}

export default LengthPicker
