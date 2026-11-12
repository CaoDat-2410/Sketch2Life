import * as Crypto from 'expo-crypto'
import * as SecureStore from 'expo-secure-store'

const DEVICE_KEY_STORAGE = 'sketch2life.be1.device-context.v1'

export interface ChildDeviceContext {
  organizationId: string
  sessionId: string
  grantId: string
  deviceKey: string
}

export class ChildApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
    readonly code: string,
    readonly requestId?: string,
  ) {
    super(message)
    this.name = 'ChildApiError'
  }
}

function apiBaseUrl() {
  const value = process.env.EXPO_PUBLIC_BE1_BASE_URL?.trim()
  if (!value) throw new Error('Thiết bị chưa được cấu hình địa chỉ BE1.')
  return value.replace(/\/+$/, '')
}

export async function getSavedDeviceContext(): Promise<ChildDeviceContext | null> {
  const raw = await SecureStore.getItemAsync(DEVICE_KEY_STORAGE)
  if (!raw) return null
  try {
    const parsed: unknown = JSON.parse(raw)
    if (!parsed || typeof parsed !== 'object') return null
    const value = parsed as Record<string, unknown>
    const organizationId = value.organizationId
    const sessionId = value.sessionId
    const grantId = value.grantId
    const deviceKey = value.deviceKey
    if (
      typeof organizationId !== 'string' ||
      typeof sessionId !== 'string' ||
      typeof grantId !== 'string' ||
      typeof deviceKey !== 'string'
    ) return null
    return { organizationId, sessionId, grantId, deviceKey }
  } catch {
    return null
  }
}

export async function saveDeviceContext(context: ChildDeviceContext) {
  await SecureStore.setItemAsync(DEVICE_KEY_STORAGE, JSON.stringify(context))
}

export async function clearDeviceContext() {
  await SecureStore.deleteItemAsync(DEVICE_KEY_STORAGE)
}

export function newDeviceKey() {
  return Crypto.randomUUID()
}

export async function childApiFetch<T>(
  path: string,
  init: RequestInit = {},
  device?: Pick<ChildDeviceContext, 'grantId' | 'deviceKey'>,
): Promise<T> {
  const headers = new Headers(init.headers)
  headers.set('Accept', 'application/json')
  headers.set('X-Request-ID', Crypto.randomUUID())
  if (init.body && !headers.has('Content-Type')) headers.set('Content-Type', 'application/json')
  if (device) {
    headers.set('X-Be1-Grant', device.grantId)
    headers.set('X-Be1-Device-Key', device.deviceKey)
  }
  let response: Response
  try {
    response = await fetch(`${apiBaseUrl()}/api/be1/v1${path}`, {
      ...init,
      headers,
      signal: init.signal ?? AbortSignal.timeout(12_000),
    })
  } catch (cause) {
    if (cause instanceof Error && cause.name === 'AbortError') throw new Error('Mất kết nối tới BE1. Hãy thử lại.')
    throw new Error('Không kết nối được BE1. Kiểm tra mạng rồi thử lại.')
  }
  const body: unknown = await response.json().catch(() => null)
  if (!response.ok) {
    const error = body && typeof body === 'object' ? body as Record<string, unknown> : {}
    throw new ChildApiError(
      typeof error.message === 'string' ? error.message : 'BE1 chưa thể hoàn tất yêu cầu.',
      response.status,
      typeof error.code === 'string' ? error.code : 'HTTP_ERROR',
      typeof error.request_id === 'string' ? error.request_id : undefined,
    )
  }
  if (!body || typeof body !== 'object') throw new Error('BE1 returned an invalid response body.')
  return body as T
}
