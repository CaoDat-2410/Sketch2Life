import { authService } from './authService'

export class Be1ApiError extends Error {
  readonly status: number
  readonly code: string
  readonly requestId?: string

  constructor(
    message: string,
    status: number,
    code: string,
    requestId?: string,
  ) {
    super(message)
    this.name = 'Be1ApiError'
    this.status = status
    this.code = code
    this.requestId = requestId
  }
}

function apiBaseUrl() {
  const value = import.meta.env.VITE_BE1_BASE_URL?.trim()
  if (!value) throw new Error('Set VITE_BE1_BASE_URL before connecting to the classroom backend.')
  return value.replace(/\/+$/, '')
}

export function organizationId() {
  const value = import.meta.env.VITE_BE1_ORGANIZATION_ID?.trim()
  if (!value) throw new Error('Set VITE_BE1_ORGANIZATION_ID to the assigned school organization.')
  return value
}

export function classroomPurposeRef() {
  const value = import.meta.env.VITE_BE1_CLASSROOM_PURPOSE_REF?.trim()
  if (!value) throw new Error('Set VITE_BE1_CLASSROOM_PURPOSE_REF to the approved consent purpose.')
  return value
}

export async function be1Request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const token = await authService.getIdToken()
  const headers = new Headers(init.headers)
  headers.set('Authorization', `Bearer ${token}`)
  headers.set('Accept', 'application/json')
  headers.set('X-Request-ID', crypto.randomUUID())
  if (init.body && !headers.has('Content-Type')) headers.set('Content-Type', 'application/json')

  const response = await fetch(`${apiBaseUrl()}/api/be1/v1${path}`, {
    ...init,
    headers,
    signal: init.signal ?? AbortSignal.timeout(15_000),
  })
  const body: unknown = await response.json().catch(() => null)
  if (!response.ok) {
    const error = body && typeof body === 'object' ? body as Record<string, unknown> : {}
    throw new Be1ApiError(
      typeof error.message === 'string' ? error.message : `BE1 request failed (${response.status}).`,
      response.status,
      typeof error.code === 'string' ? error.code : 'HTTP_ERROR',
      typeof error.request_id === 'string' ? error.request_id : undefined,
    )
  }
  if (!body || typeof body !== 'object') throw new Error('BE1 returned an invalid response body.')
  return body as T
}
