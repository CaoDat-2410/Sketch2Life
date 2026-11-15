import { authService } from './authService'
import { organizationId } from './be1Client'
import type { LessonContentV1, LessonDetailV1, LessonSummaryV1, SketchStrokeGuideV3, SvgCatalogAssetV1, SvgGuideRevisionV1 } from '../domain/svgGuide'

export class SvgCatalogServiceError extends Error {
  readonly status: number
  readonly code: string

  constructor(status: number, code: string, message: string) {
    super(message)
    this.name = 'SvgCatalogServiceError'
    this.status = status
    this.code = code
  }
}

type LessonPage = { contract: string; items: LessonSummaryV1[]; next_cursor: string | null }
type SvgCatalogPage = { contract: string; items: SvgCatalogAssetV1[] }
type SvgGuideRevisionPage = { contract: 'SvgGuideRevisionPageV1'; items: SvgGuideRevisionV1[] }

export class SvgCatalogService {
  private get orgId(): string { return organizationId() }

  listLessons(): Promise<LessonPage> {
    return this.request(`/api/lesson-library/v1/organizations/${encodeURIComponent(this.orgId)}/lessons?state=ACTIVE&limit=100`)
  }

  getLesson(lessonId: string): Promise<LessonDetailV1> {
    return this.request(`/api/lesson-library/v1/organizations/${encodeURIComponent(this.orgId)}/lessons/${encodeURIComponent(lessonId)}`)
  }

  listAssets(): Promise<SvgCatalogPage> {
    return this.request(`/api/svg-catalog/v1/organizations/${encodeURIComponent(this.orgId)}/assets?limit=100`)
  }

  createAsset(input: {
    title_vi: string
    topic_key: string
    alt_text_vi: string
    source_uri: string
    license_id: string
    license_uri: string
    source_svg: string
  }): Promise<SvgCatalogAssetV1> {
    return this.request(`/api/svg-catalog/v1/organizations/${encodeURIComponent(this.orgId)}/assets`, {
      method: 'POST',
      body: JSON.stringify({ contract: 'SvgCatalogAssetCreateRequestV1', ...input }),
    })
  }

  listGuideRevisions(asset: SvgCatalogAssetV1): Promise<SvgGuideRevisionPage> {
    return this.request(
      `/api/svg-catalog/v1/organizations/${encodeURIComponent(this.orgId)}/assets/${encodeURIComponent(asset.catalog_entry_id)}/guide-revisions?limit=100`,
    )
  }

  createGuideRevision(asset: SvgCatalogAssetV1, guide: SketchStrokeGuideV3): Promise<SvgGuideRevisionV1> {
    return this.request(
      `/api/svg-catalog/v1/organizations/${encodeURIComponent(this.orgId)}/assets/${encodeURIComponent(asset.catalog_entry_id)}/guide-revisions`,
      { method: 'POST', body: JSON.stringify({ contract: 'CreateSvgGuideRevisionRequestV1', guide }) },
    )
  }

  reviewSource(asset: SvgCatalogAssetV1, decision: 'APPROVE' | 'REJECT', reason: string): Promise<unknown> {
    const path = asset.visibility_scope === 'PLATFORM'
      ? `/api/svg-catalog/v1/platform/assets/${encodeURIComponent(asset.catalog_entry_id)}/source-reviews`
      : `/api/svg-catalog/v1/organizations/${encodeURIComponent(this.orgId)}/assets/${encodeURIComponent(asset.catalog_entry_id)}/source-reviews`
    return this.request(path, {
      method: 'POST',
      body: JSON.stringify({ contract: 'SvgSourceReviewRequestV1', source_sha256: asset.source_sha256, decision, reason: reason.trim() || null }),
    })
  }

  reviewGuide(asset: SvgCatalogAssetV1, revision: SvgGuideRevisionV1, decision: 'APPROVE' | 'REJECT', reason: string): Promise<unknown> {
    const path = revision.visibility_scope === 'PLATFORM'
      ? `/api/svg-catalog/v1/platform/assets/${encodeURIComponent(asset.catalog_entry_id)}/guide-revisions/${encodeURIComponent(revision.guide_revision_id)}/educator-reviews`
      : `/api/svg-catalog/v1/organizations/${encodeURIComponent(this.orgId)}/assets/${encodeURIComponent(asset.catalog_entry_id)}/guide-revisions/${encodeURIComponent(revision.guide_revision_id)}/educator-reviews`
    return this.request(path, {
      method: 'POST',
      body: JSON.stringify({
        contract: 'SvgGuideReviewRequestV1',
        source_sha256: revision.source_sha256,
        guide_sha256: revision.guide_sha256,
        decision,
        reason: reason.trim() || null,
      }),
    })
  }

  updateLesson(lessonId: string, expectedRevision: number, content: LessonContentV1): Promise<LessonDetailV1> {
    return this.request(
      `/api/lesson-library/v1/organizations/${encodeURIComponent(this.orgId)}/lessons/${encodeURIComponent(lessonId)}`,
      {
        method: 'PATCH',
        headers: { 'If-Match': `"${expectedRevision}"` },
        body: JSON.stringify({ contract: 'UpdateLessonRequestV1', content }),
      },
    )
  }

  createSeparateLesson(content: LessonContentV1): Promise<LessonDetailV1> {
    return this.request(`/api/lesson-library/v1/organizations/${encodeURIComponent(this.orgId)}/lessons`, {
      method: 'POST',
      headers: { 'Idempotency-Key': crypto.randomUUID() },
      body: JSON.stringify({ contract: 'CreateLessonRequestV1', content, visibility: 'PRIVATE' }),
    })
  }

  private async request<T>(path: string, init: RequestInit = {}): Promise<T> {
    const baseUrl = import.meta.env.VITE_BE1_BASE_URL?.trim()
    if (!baseUrl) throw new Error('Thiếu VITE_BE1_BASE_URL để kết nối API giáo án và SVG.')
    const token = await authService.getIdToken()
    const headers = new Headers(init.headers)
    headers.set('Authorization', `Bearer ${token}`)
    headers.set('Accept', 'application/json')
    headers.set('X-Request-ID', crypto.randomUUID())
    if (init.body) headers.set('Content-Type', 'application/json')
    const response = await fetch(`${baseUrl.replace(/\/+$/, '')}${path}`, {
      ...init,
      headers,
      signal: init.signal ?? AbortSignal.timeout(30_000),
    })
    const body: unknown = await response.json().catch(() => null)
    if (!response.ok) {
      const outer = body && typeof body === 'object' ? body as Record<string, unknown> : {}
      const detail = outer.detail && typeof outer.detail === 'object' ? outer.detail as Record<string, unknown> : outer
      throw new SvgCatalogServiceError(
        response.status,
        typeof detail.code === 'string' ? detail.code : `HTTP_${response.status}`,
        typeof detail.message === 'string' ? detail.message : 'Không thực hiện được yêu cầu với thư viện SVG.',
      )
    }
    if (!body || typeof body !== 'object') throw new Error('Backend trả về phản hồi SVG không hợp lệ.')
    return body as T
  }
}

export const svgCatalogService = new SvgCatalogService()
