// The backend sends times of day as "HH:MM:SS" strings (e.g. "13:30:00").
// The schedule works in minutes since midnight, which makes the math simple.

export function toMinutes(time: string): number {
  const [hours, minutes] = time.split(':').map(Number)
  return hours * 60 + minutes
}

// 810 -> "1:30 PM"
export function formatTime(totalMinutes: number): string {
  const hours24 = Math.floor(totalMinutes / 60)
  const minutes = totalMinutes % 60
  const period = hours24 < 12 || hours24 === 24 ? 'AM' : 'PM'
  const hours12 = hours24 % 12 === 0 ? 12 : hours24 % 12
  return `${hours12}:${String(minutes).padStart(2, '0')} ${period}`
}

// A date as "YYYY-MM-DD" in the coach's own time zone.
// (date.toISOString() would give the UTC date, which on a US evening is already tomorrow.)
export function toDateString(date: Date): string {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0') // getMonth() counts from 0
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

// 390 -> "06:30", the format the backend accepts for a time of day
export function toTimeString(totalMinutes: number): string {
  const hours = String(Math.floor(totalMinutes / 60)).padStart(2, '0')
  const minutes = String(totalMinutes % 60).padStart(2, '0')
  return `${hours}:${minutes}`
}

// 90 -> "1h 30m", 60 -> "1h", 45 -> "45m"
export function formatDuration(totalMinutes: number): string {
  const hours = Math.floor(totalMinutes / 60)
  const minutes = totalMinutes % 60
  if (hours === 0) {
    return `${minutes}m`
  }
  return minutes === 0 ? `${hours}h` : `${hours}h ${minutes}m`
}
