import { authService } from './authService'

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

function apiBaseUrl() {
  const value = import.meta.env.VITE_BE1_BASE_URL?.trim()
  if (!value) throw new Error('Thiếu VITE_BE1_BASE_URL trong .env gốc.')
  return value.replace(/\/+$/, '')
}

function orgId() {
  const value = import.meta.env.VITE_BE1_ORGANIZATION_ID?.trim()
  if (!value) throw new Error('Thiếu VITE_BE1_ORGANIZATION_ID trong .env gốc.')
  return encodeURIComponent(value)
}

async function post<T>(path: string, body: unknown): Promise<T> {
  const token = await authService.getIdToken()
  const response = await fetch(`${apiBaseUrl()}${path}`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
      Accept: 'application/json',
      'Content-Type': 'application/json',
      'X-Request-ID': crypto.randomUUID(),
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

const prefix = () => `/api/teacher/v1/organizations/${orgId()}/ai`

export const aiWorkflowService = {
  suggestLessonPlan: (input: TeacherLessonSuggestionInput) =>
    post<AiResponse<Record<string, unknown>>>(`${prefix()}/lesson-plan-suggestions`, input),
  generateSketchDeck: (input: TeacherReviewedPlanInput) =>
    post<AiResponse<Record<string, unknown>>>(`${prefix()}/sketch-decks`, input),
  generateLessonVisual: (input: TeacherReviewedPlanInput) =>
    post<AiResponse<Record<string, unknown>>>(`${prefix()}/lesson-visuals`, input),
}
