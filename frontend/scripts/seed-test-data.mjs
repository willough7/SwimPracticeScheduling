// Fills the backend with made-up test data: 75 swimmers (most with a class
// calendar) and 3 practices on each day of the week. Nothing here is real
// student data.
//
// The backend keeps everything in memory for now, so every restart empties it.
// Run this again afterwards to get the test data back:
//
//   npm run seed                 (refuses if the backend already has data)
//   npm run seed -- --reset      (deletes all swimmers and practices first)
//
// The backend must be running. The data is the same every run, because the
// random choices come from a fixed seed.

const SWIMMER_COUNT = 75
const NO_CALENDAR_SHARE = 0.12 // about 1 in 8 swimmers hasn't uploaded a calendar yet

// ---------- Repeatable randomness ----------

// Math.random() gives different numbers every run. This small generator
// (mulberry32) gives the same sequence every time for the same seed.
function makeRandom(seed) {
  let state = seed
  return function random() {
    state = (state + 0x6d2b79f5) | 0
    let t = Math.imul(state ^ (state >>> 15), 1 | state)
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296
  }
}

const random = makeRandom(2026)

function pick(list) {
  return list[Math.floor(random() * list.length)]
}

function shuffled(list) {
  const copy = [...list]
  for (let i = copy.length - 1; i > 0; i--) {
    const j = Math.floor(random() * (i + 1))
    ;[copy[i], copy[j]] = [copy[j], copy[i]]
  }
  return copy
}

// ---------- Practices: 3 a day ----------

const PRACTICES = [
  // Monday, Wednesday, Friday
  ...[1, 3, 5].flatMap((day) => [
    { day, practice_title: 'Morning Swim', start_time: '06:00', end_time: '07:30' },
    { day, practice_title: 'Afternoon Swim', start_time: '14:30', end_time: '16:30' },
    { day, practice_title: 'Lift', start_time: '16:45', end_time: '17:45' },
  ]),
  // Tuesday, Thursday
  ...[2, 4].flatMap((day) => [
    { day, practice_title: 'Morning Swim', start_time: '05:45', end_time: '07:15' },
    { day, practice_title: 'Lift', start_time: '07:30', end_time: '08:30' },
    { day, practice_title: 'Afternoon Swim', start_time: '15:00', end_time: '17:00' },
  ]),
  // Saturday: the two groups overlap, swimming and lifting in opposite orders
  { day: 6, practice_title: 'Swim (Group B)', start_time: '07:00', end_time: '08:45' },
  { day: 6, practice_title: 'Lift (Group A)', start_time: '08:00', end_time: '09:00' },
  { day: 6, practice_title: 'Swim (Group A)', start_time: '09:15', end_time: '11:00' },
  // Sunday
  { day: 7, practice_title: 'Recovery Swim', start_time: '09:00', end_time: '10:00' },
  { day: 7, practice_title: 'Mobility', start_time: '10:15', end_time: '11:00' },
  { day: 7, practice_title: 'Evening Swim', start_time: '16:00', end_time: '17:30' },
]

// ---------- Swimmers ----------

const FIRST_NAMES = [
  'Ava', 'Ben', 'Caleb', 'Chloe', 'Dylan', 'Ella', 'Ethan', 'Grace', 'Hannah', 'Isaac',
  'Jack', 'Jada', 'Kai', 'Kylie', 'Leah', 'Liam', 'Lucas', 'Maya', 'Mia', 'Noah',
  'Nora', 'Owen', 'Paige', 'Quinn', 'Riley', 'Ryan', 'Sam', 'Sofia', 'Tyler', 'Zoe',
  'Aiden', 'Brooke', 'Carter', 'Delaney', 'Evan', 'Faith', 'Gavin', 'Ivy', 'Jonah', 'Lila',
]

const LAST_NAMES = [
  'Adams', 'Baker', 'Brooks', 'Carter', 'Chen', 'Collins', 'Diaz', 'Evans', 'Foster', 'Garcia',
  'Gray', 'Hayes', 'Hughes', 'Jensen', 'Kim', 'Lopez', 'Mason', 'Meyer', 'Nguyen', 'Ortiz',
  'Patel', 'Perry', 'Price', 'Reed', 'Rivera', 'Ross', 'Shaw', 'Stone', 'Tran', 'Turner',
  'Walsh', 'Ward', 'Webb', 'Wells', 'West', 'Wood', 'Young', 'Zimmer', 'Bishop', 'Coleman',
]

const WEIGHTS_GROUPS = ['THREE_DAY_A', 'THREE_DAY_B', 'FOUR_DAY']

// Event group: each swimmer gets exactly one, weighted like a typical roster
const EVENT_GROUPS = ['100s', '100s', '100s', '200s', '200s', '200s', 'Distance', 'Distance', 'IM', 'IM']

// Strokes: Free shows up most often
const STROKES = ['Free', 'Free', 'Back', 'Breast', 'Fly']

function makeSwimmers() {
  const names = new Set()
  const swimmers = []
  while (swimmers.length < SWIMMER_COUNT) {
    const first = pick(FIRST_NAMES)
    const last = pick(LAST_NAMES)
    if (names.has(`${first} ${last}`)) {
      continue // keep every full name unique, so search results aren't confusing
    }
    names.add(`${first} ${last}`)

    const strokeCount = random() < 0.6 ? 1 : 2
    const strokes = [...new Set(Array.from({ length: strokeCount }, () => pick(STROKES)))]

    swimmers.push({
      first_name: first,
      last_name: last,
      weights_group: pick(WEIGHTS_GROUPS),
      tags: [pick(EVENT_GROUPS), ...strokes],
      calendar: random() < NO_CALENDAR_SHARE ? null : makeCalendar(swimmers.length + 1),
    })
  }
  return swimmers
}

// ---------- Class calendars (.ics) ----------

// Standard class times: 50-minute classes on Mon/Wed/Fri, 75-minute classes on Tue/Thu.
// The first dates are the first week of the fall 2026 semester.
const MWF_SLOTS = ['0800', '0900', '1000', '1100', '1200', '1300', '1400', '1500']
const TR_SLOTS = ['0800', '0930', '1100', '1230', '1400', '1530']

const COURSES = [
  'CSCI 155', 'CSCI 250', 'SWEN 200', 'MATH 210', 'MATH 305', 'ENGL 101', 'BIOL 120', 'CHEM 150',
  'PSYC 105', 'HIST 112', 'SPAN 101', 'ECON 201', 'COMM 101', 'PHYS 150', 'KINS 210', 'ART 110',
]

// Build one calendar of 4-6 weekly classes that don't overlap each other.
function makeCalendar(swimmerNumber) {
  const classCount = 4 + Math.floor(random() * 3)
  const mwfCount = Math.floor(random() * (classCount + 1))
  const mwfTimes = shuffled(MWF_SLOTS).slice(0, mwfCount)
  const trTimes = shuffled(TR_SLOTS).slice(0, classCount - mwfCount)
  const courses = shuffled(COURSES)

  const events = [
    ...mwfTimes.map((start) => ({ start, minutes: 50, days: 'MO,WE,FR', firstDate: '20260824' })),
    ...trTimes.map((start) => ({ start, minutes: 75, days: 'TU,TH', firstDate: '20260825' })),
  ].map((event, i) =>
    [
      'BEGIN:VEVENT',
      `UID:seed-${swimmerNumber}-${i}@test`,
      `SUMMARY:${courses[i]}`,
      `DTSTART;TZID=America/Indiana/Indianapolis:${event.firstDate}T${event.start}00`,
      `DURATION:PT${event.minutes}M`,
      `RRULE:FREQ=WEEKLY;UNTIL=20261211T235959Z;BYDAY=${event.days}`,
      'END:VEVENT',
    ].join('\r\n'),
  )

  return [
    'BEGIN:VCALENDAR',
    'VERSION:2.0',
    'PRODID:-//SwimPracticeScheduling//Seed Data//EN',
    'COMMENT:Made-up schedule for testing. Contains no real student data.',
    ...events,
    'END:VCALENDAR',
    '',
  ].join('\r\n')
}

// ---------- Sending it to the backend ----------

async function call(baseUrl, method, path, body) {
  const options = { method }
  if (body instanceof FormData) {
    options.body = body
  } else if (body !== undefined) {
    options.headers = { 'Content-Type': 'application/json' }
    options.body = JSON.stringify(body)
  }
  const response = await fetch(baseUrl + path, options)
  if (!response.ok) {
    throw new Error(`${method} ${path} failed with ${response.status}: ${await response.text()}`)
  }
  return response.status === 204 ? null : response.json()
}

// baseUrl: 'http://127.0.0.1:8000' from the command line, or '/api' in the browser
export async function seed(baseUrl, { reset = false } = {}) {
  const existingSwimmers = await call(baseUrl, 'GET', '/swimmers')
  const existingPractices = await call(baseUrl, 'GET', '/practices')
  const hasData = existingSwimmers.length > 0 || existingPractices.length > 0

  if (hasData && !reset) {
    throw new Error(
      `The backend already has ${existingSwimmers.length} swimmers and ` +
        `${existingPractices.length} practices. Run with --reset to delete them first.`,
    )
  }
  for (const swimmer of existingSwimmers) {
    await call(baseUrl, 'DELETE', `/swimmers/${swimmer.swimmer_id}`)
  }
  for (const practice of existingPractices) {
    await call(baseUrl, 'DELETE', `/practices/${practice.practice_id}`)
  }

  for (const practice of PRACTICES) {
    await call(baseUrl, 'POST', '/practices', practice)
  }

  let withCalendar = 0
  for (const { calendar, ...swimmer } of makeSwimmers()) {
    const created = await call(baseUrl, 'POST', '/swimmers', swimmer)
    if (calendar !== null) {
      const form = new FormData()
      form.append('file', new Blob([calendar], { type: 'text/calendar' }), 'schedule.ics')
      await call(baseUrl, 'PUT', `/swimmers/${created.swimmer_id}/schedule`, form)
      withCalendar += 1
    }
  }

  return {
    practices: PRACTICES.length,
    swimmers: SWIMMER_COUNT,
    withCalendar,
    withoutCalendar: SWIMMER_COUNT - withCalendar,
  }
}

// Run automatically from the command line (Node has no `window`), but not
// when a browser imports this file.
if (typeof window === 'undefined') {
  const reset = process.argv.includes('--reset')
  seed('http://127.0.0.1:8000', { reset })
    .then((summary) => {
      console.log(
        `Added ${summary.practices} practices and ${summary.swimmers} swimmers ` +
          `(${summary.withCalendar} with a calendar, ${summary.withoutCalendar} without).`,
      )
    })
    .catch((err) => {
      console.error(err.message)
      process.exit(1)
    })
}
