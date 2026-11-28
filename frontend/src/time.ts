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
