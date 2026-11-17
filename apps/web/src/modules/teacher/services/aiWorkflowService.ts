import {
  apiBaseUrl,
  configuredOrganizationId,
  hasFirebaseAuthBridge,
} from '../../../shared/api/backendApi'

export type TeacherLessonSuggestionInput = Readonly<{
  topic: string
  target_age_months: number
  objectives: string[]
  drawing_subject: string
  activity_count: number
  activity_kind: 'outdoor' | 'indoor' | 'mixed'
  script_following_allowed: boolean
  script_direction: string | null
}>

export type TeacherReviewedPlanInput = Readonly<{
  review_confirmed: true
  plan_revision_ref: string
  topic: string
  target_age_months: number
  objectives: string[]
  drawing_steps: Array<{ action: string; placement: string }>
  subject_knowledge: string[]
  activities: Array<{
    activity_ref: string
    title: string
    goal: string
    materials: string
    preparation: string
    instructions: string
    safety_notes: string
  }>
}>

type AiResponse<T> = Readonly<{
  request_id: string
  modal_call_id: string
  model: { id: string; revision: string } | null
  status?: string
  review_required?: boolean
  suggestion?: T
  deck?: Record<string, unknown>
  image_base64?: string
  asset?: Record<string, unknown>
}>

function organizationId() {
  const value = configuredOrganizationId()
  if (!value) throw new Error('Thiếu organization_id để gọi dịch vụ giáo án.')
  return encodeURIComponent(value)
}

async function post<T>(path: string, body: unknown): Promise<T> {
  const auth = window.sketch2lifeAuth
  if (!hasFirebaseAuthBridge() || !auth?.getIdToken) {
    throw new Error('Chưa có Firebase ID token để gọi dịch vụ giáo án.')
  }
  const token = await auth.getIdToken()
  if (!token) throw new Error('Phiên đăng nhập đã hết hạn. Hãy đăng nhập lại.')

  const response = await fetch(`${apiBaseUrl()}${path}`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
      Accept: 'application/json',
      'Content-Type': 'application/json',
      'X-Request-ID': globalThis.crypto?.randomUUID?.() ?? `teacher-${Date.now()}`,
    },
    body: JSON.stringify(body),
    signal: AbortSignal.timeout(1_900_000),
  })
  const payload = await response.json().catch(() => null) as Record<string, unknown> | null
  if (!response.ok) {
    const detail = payload?.detail
    const code = detail && typeof detail === 'object' && 'code' in detail
      ? String((detail as { code: unknown }).code)
      : `HTTP_${response.status}`
    throw new Error(`Yêu cầu AI thất bại (${code}).`)
  }
  if (!payload || typeof payload !== 'object') throw new Error('Backend trả về contract không hợp lệ.')
  return payload as T
}

const prefix = () => `/api/teacher/v1/organizations/${organizationId()}/ai`

export const aiWorkflowService = {
  suggestLessonPlan: (input: TeacherLessonSuggestionInput) =>
    post<AiResponse<Record<string, unknown>>>(`${prefix()}/lesson-plan-suggestions`, input),
  generateSketchDeck: (input: TeacherReviewedPlanInput) =>
    post<AiResponse<Record<string, unknown>>>(`${prefix()}/sketch-decks`, input),
  generateLessonVisual: (input: TeacherReviewedPlanInput) =>
    post<AiResponse<Record<string, unknown>>>(`${prefix()}/lesson-visuals`, input),
}
