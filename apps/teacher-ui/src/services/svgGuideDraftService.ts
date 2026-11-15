import { authService } from './authService'
import { organizationId } from './be1Client'
import type { SvgTopicStrokeGuideDraftV1 } from '../domain/svgGuide'

export class SvgGuideDraftServiceError extends Error {
  readonly status: number
  readonly code: string

  constructor(status: number, code: string, message: string) {
    super(message)
    this.name = 'SvgGuideDraftServiceError'
    this.status = status
    this.code = code
  }
}

export class SvgGuideDraftService {
  async generate(topic: string): Promise<SvgTopicStrokeGuideDraftV1> {
    const baseUrl = import.meta.env.VITE_BE1_BASE_URL?.trim()
    if (!baseUrl) throw new Error('Thiếu VITE_BE1_BASE_URL để kết nối Teacher API.')
    const token = await authService.getIdToken()
    const response = await fetch(
      `${baseUrl.replace(/\/+$/, '')}/api/teacher/v1/organizations/${encodeURIComponent(organizationId())}/ai/svg-stroke-guides`,
      {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
          Accept: 'application/json',
          'Content-Type': 'application/json',
          'X-Request-ID': crypto.randomUUID(),
        },
        body: JSON.stringify({ contract: 'SvgTopicStrokeGuideRequestV1', topic, difficulty: 'beginner' }),
        signal: AbortSignal.timeout(1_800_000),
      },
    )
    const body: unknown = await response.json().catch(() => null)
    if (!response.ok) {
      const outer = body && typeof body === 'object' ? body as Record<string, unknown> : {}
      const detail = outer.detail && typeof outer.detail === 'object' ? outer.detail as Record<string, unknown> : outer
      throw new SvgGuideDraftServiceError(
        response.status,
        typeof detail.code === 'string' ? detail.code : `HTTP_${response.status}`,
        typeof detail.reason_code === 'string' ? `${detail.code}: ${detail.reason_code}` : 'Không tạo được hướng dẫn nét SVG.',
      )
    }
    if (!body || typeof body !== 'object') throw new Error('Backend trả về hướng dẫn nét SVG không hợp lệ.')
    return body as SvgTopicStrokeGuideDraftV1
  }
}

export const svgGuideDraftService = new SvgGuideDraftService()
