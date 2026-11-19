import { authService } from './authService'
import { parseApiError } from '../../../../shared/api/errorEnvelope'

export class AdminBe1Error extends Error {
  readonly status: number
  readonly code: string
  readonly requestId?: string
  readonly retryable: boolean

  constructor(message: string, status: number, code: string, requestId?: string, retryable = false) {
    super(message)
    this.name = 'AdminBe1Error'
    this.status = status
    this.code = code
    this.requestId = requestId
    this.retryable = retryable
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
    const error = parseApiError(body, response.status, response.headers.get('X-Request-ID'))
    throw new AdminBe1Error(error.message, response.status, error.code, error.requestId, error.retryable)
  }
  if (!body || typeof body !== 'object') throw new Error('BE1 returned an invalid response body.')
  return body as T
}

export async function adminApiRequest<T>(path: string, init: RequestInit = {}): Promise<T> {
  const baseUrl = import.meta.env.VITE_BE1_BASE_URL?.trim()
  if (!baseUrl) throw new Error('Set VITE_BE1_BASE_URL before connecting Admin to the API.')
  const headers = new Headers(init.headers)
  headers.set('Authorization', `Bearer ${await authService.getIdToken()}`)
  headers.set('Accept', 'application/json')
  headers.set('X-Request-ID', crypto.randomUUID())
  if (init.body && !headers.has('Content-Type')) headers.set('Content-Type', 'application/json')

  const response = await fetch(`${baseUrl.replace(/\/+$/, '')}/api${path}`, {
    ...init,
    headers,
    signal: init.signal ?? AbortSignal.timeout(15_000),
  })
  const body: unknown = await response.json().catch(() => null)
  if (!response.ok) {
    const error = parseApiError(body, response.status, response.headers.get('X-Request-ID'))
    throw new AdminBe1Error(error.message, response.status, error.code, error.requestId, error.retryable)
  }
  if (!body || typeof body !== 'object') throw new Error('API returned an invalid response body.')
  return body as T
}
