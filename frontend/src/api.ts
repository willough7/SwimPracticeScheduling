import type {
  Day,
  LanePlacement,
  Practice,
  PracticeConflicts,
  PracticeCreate,
  Swimmer,
  SwimmerCreate,
} from './types'

// Every request goes through the Vite proxy, which forwards it to FastAPI.
const BASE_URL = '/api'

// The whole week as an Excel file, opening on the given day's sheet. Used as a
// plain link: the backend tells the browser to download it, so no fetch() is needed.
export function weekExportUrl(openOn: Day) {
  return `${BASE_URL}/export/week.xlsx?day=${openOn}`
}

// Thrown for any response that isn't 2xx, so callers can check err.status.
export class ApiError extends Error {
  status: number

  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

// Turns anything caught in a catch block into a message to show the user.
// (JavaScript lets you throw anything, so a caught value isn't always an Error.)
export function errorMessage(err: unknown): string {
  return err instanceof Error ? err.message : String(err)
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(BASE_URL + path, options)

  if (!response.ok) {
    let message = `Request failed with status ${response.status}`
    try {
      const body = await response.json()
      if (typeof body.detail === 'string') {
        // Our own HTTPExceptions, e.g. "Swimmer not found"
        message = body.detail
      } else if (Array.isArray(body.detail)) {
        // 422 validation errors: a list of problems, each with a msg
        message = body.detail.map((problem: { msg: string }) => problem.msg).join('; ')
      }
    } catch {
      // The body wasn't JSON, so keep the generic message.
    }
    throw new ApiError(response.status, message)
  }

  // 204 No Content has no body, so there's nothing to parse.
  if (response.status === 204) {
    return undefined as T
  }
  return response.json()
}

function jsonBody(method: string, data: unknown): RequestInit {
  return {
    method,
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  }
}

// Swimmers

export function getSwimmers() {
  return request<Swimmer[]>('/swimmers')
}

export function getSwimmer(swimmerId: number) {
  return request<Swimmer>(`/swimmers/${swimmerId}`)
}

export function createSwimmer(data: SwimmerCreate) {
  return request<Swimmer>('/swimmers', jsonBody('POST', data))
}

// Replaces the swimmer's details; their calendar and assignments are kept
export function updateSwimmer(swimmerId: number, data: SwimmerCreate) {
  return request<Swimmer>(`/swimmers/${swimmerId}`, jsonBody('PUT', data))
}

export function deleteSwimmer(swimmerId: number) {
  return request<void>(`/swimmers/${swimmerId}`, { method: 'DELETE' })
}

export function uploadSchedule(swimmerId: number, file: File) {
  const form = new FormData()
  form.append('file', file) // must match the backend's `file: UploadFile` parameter
  return request<Swimmer>(`/swimmers/${swimmerId}/schedule`, { method: 'PUT', body: form })
}

// Practices

export function getPractices(day?: Day) {
  const query = day === undefined ? '' : `?day=${day}`
  return request<Practice[]>(`/practices${query}`)
}

export function getPractice(practiceId: number) {
  return request<Practice>(`/practices/${practiceId}`)
}

export function createPractice(data: PracticeCreate) {
  return request<Practice>('/practices', jsonBody('POST', data))
}

// Replaces every field of the practice; its assignments are kept
export function updatePractice(practiceId: number, data: PracticeCreate) {
  return request<Practice>(`/practices/${practiceId}`, jsonBody('PUT', data))
}

export function deletePractice(practiceId: number) {
  return request<void>(`/practices/${practiceId}`, { method: 'DELETE' })
}

// week is any date in the week, as "YYYY-MM-DD"
export function getPracticeConflicts(practiceId: number, week: string) {
  return request<PracticeConflicts>(`/practices/${practiceId}/conflicts?week=${week}`)
}

// Assignments

export function assignSwimmer(practiceId: number, swimmerId: number) {
  return request<void>(`/practices/${practiceId}/swimmers/${swimmerId}`, { method: 'PUT' })
}

export function unassignSwimmer(practiceId: number, swimmerId: number) {
  return request<void>(`/practices/${practiceId}/swimmers/${swimmerId}`, { method: 'DELETE' })
}

export function getPracticeSwimmers(practiceId: number) {
  return request<Swimmer[]>(`/practices/${practiceId}/swimmers`)
}

export function getSwimmerPractices(swimmerId: number) {
  return request<Practice[]>(`/swimmers/${swimmerId}/practices`)
}

// Lanes

export function getPracticeLanes(practiceId: number) {
  return request<LanePlacement[]>(`/practices/${practiceId}/lanes`)
}

// lane is 1-8, or null to take the swimmer out of their lane (they stay assigned)
export function setSwimmerLane(practiceId: number, swimmerId: number, lane: number | null) {
  return request<void>(
    `/practices/${practiceId}/swimmers/${swimmerId}/lane`,
    jsonBody('PUT', { lane }),
  )
}

// Admin login. The backend keeps the login in an HttpOnly cookie, which the
// browser sends with every request by itself, so nothing here stores it.

type AdminResponse = { username: string | null }

// Who is logged in: a username, or null for everyone who isn't an admin
export function getCurrentAdmin() {
  return request<AdminResponse>('/auth/me')
}

export function login(username: string, password: string) {
  return request<AdminResponse>('/auth/login', jsonBody('POST', { username, password }))
}

export function logout() {
  return request<void>('/auth/logout', { method: 'POST' })
}
