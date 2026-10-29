import { authService } from './authService'

export class AdminBe1Error extends Error {
  readonly status: number
  readonly code: string

  constructor(message: string, status: number, code: string) {
    super(message)
    this.name = 'AdminBe1Error'
    this.status = status
    this.code = code
  }
}

export function adminOrganizationId() {
  const value = import.meta.env.VITE_BE1_ORGANIZATION_ID?.trim()
  if (!value) throw new Error('Set VITE_BE1_ORGANIZATION_ID for the assigned school.')
  return value
}

export async function adminBe1Request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const baseUrl = import.meta.env.VITE_BE1_BASE_URL?.trim()
  if (!baseUrl) throw new Error('Set VITE_BE1_BASE_URL before connecting Admin to BE1.')
  const headers = new Headers(init.headers)
  headers.set('Authorization', `Bearer ${await authService.getIdToken()}`)
  headers.set('Accept', 'application/json')
  headers.set('X-Request-ID', crypto.randomUUID())
  if (init.body && !headers.has('Content-Type')) headers.set('Content-Type', 'application/json')

  const response = await fetch(`${baseUrl.replace(/\/+$/, '')}/api/be1/v1${path}`, {
    ...init,
    headers,
    signal: init.signal ?? AbortSignal.timeout(15_000),
  })
  const body: unknown = await response.json().catch(() => null)
  if (!response.ok) {
    const error = body && typeof body === 'object' ? body as Record<string, unknown> : {}
    throw new AdminBe1Error(
      typeof error.message === 'string' ? error.message : `BE1 request failed (${response.status}).`,
      response.status,
      typeof error.code === 'string' ? error.code : 'HTTP_ERROR',
    )
  }
  if (!body || typeof body !== 'object') throw new Error('BE1 returned an invalid response body.')
  return body as T
}
