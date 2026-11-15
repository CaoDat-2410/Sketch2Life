import { authService } from './authService'
import { organizationId } from './be1Client'
import type {
  TeacherSvgIllustrationDraftRequestV1,
  TeacherSvgIllustrationDraftV1,
} from '../domain/svgGuide'

export class SvgIllustrationServiceError extends Error {
  readonly status: number
  readonly code: string

  constructor(status: number, code: string, message: string) {
    super(message)
    this.name = 'SvgIllustrationServiceError'
    this.status = status
    this.code = code
  }
}

export class SvgIllustrationService {
  async generateDraft(
    input: Omit<TeacherSvgIllustrationDraftRequestV1, 'contract'>,
  ): Promise<TeacherSvgIllustrationDraftV1> {
    const baseUrl = import.meta.env.VITE_BE1_BASE_URL?.trim()
    if (!baseUrl) throw new Error('Thiếu VITE_BE1_BASE_URL để kết nối Teacher API.')
    const token = await authService.getIdToken()
    const response = await fetch(
      `${baseUrl.replace(/\/+$/, '')}/api/teacher/v1/organizations/${encodeURIComponent(organizationId())}/ai/svg-illustrations`,
      {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
          Accept: 'application/json',
          'Content-Type': 'application/json',
          'X-Request-ID': crypto.randomUUID(),
        },
        body: JSON.stringify({ contract: 'TeacherSvgIllustrationDraftRequestV1', ...input }),
        signal: AbortSignal.timeout(1_850_000),
      },
    )
    const body: unknown = await response.json().catch(() => null)
    if (!response.ok) {
      const outer = body && typeof body === 'object' ? body as Record<string, unknown> : {}
      const detail = outer.detail && typeof outer.detail === 'object' ? outer.detail as Record<string, unknown> : outer
      throw new SvgIllustrationServiceError(
        response.status,
        typeof detail.code === 'string' ? detail.code : `HTTP_${response.status}`,
        typeof detail.message === 'string' ? detail.message : 'Không tạo được bản nháp SVG.',
      )
    }
    if (!body || typeof body !== 'object') throw new Error('Backend trả về bản nháp SVG không hợp lệ.')
    return body as TeacherSvgIllustrationDraftV1
  }
}

export const svgIllustrationService = new SvgIllustrationService()
