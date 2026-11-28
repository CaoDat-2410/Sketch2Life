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

type AiResponse<T> = Readonly<{
  request_id: string
  modal_call_id: string
  model: { id: string; revision: string } | null
  status?: string
  review_required?: boolean
  suggestion?: T
}>

function organizationId() {
  const value = configuredOrganizationId()
  if (!value) throw new Error('Chưa thể kết nối để tạo giáo án. Hãy tải lại trang hoặc liên hệ người quản lý.')
  return encodeURIComponent(value)
}

function messageForStatus(status: number): string {
  if (status === 401) return 'Phiên đăng nhập đã hết hạn. Hãy đăng nhập lại.'
  if (status === 403) return 'Bạn chưa thể thực hiện thao tác này. Hãy liên hệ người quản lý.'
  if (status === 404) return 'Không tìm thấy thông tin cần dùng. Hãy tải lại trang.'
  if (status === 409) return 'Thông tin đã thay đổi. Hãy tải lại trang rồi thử lại.'
  if (status === 422) return 'Thông tin chưa đầy đủ. Hãy kiểm tra lại các mục đã nhập.'
  if (status === 429) return 'Bạn đã gửi nhiều yêu cầu liên tiếp. Hãy thử lại sau ít phút.'
  if (status >= 500) return 'Chưa thể hoàn tất lúc này. Hãy thử lại sau.'
  return 'Yêu cầu chưa thể hoàn tất. Hãy kiểm tra thông tin rồi thử lại.'
}

async function post<T>(path: string, body: unknown): Promise<T> {
  const auth = window.sketch2lifeAuth
  if (!hasFirebaseAuthBridge() || !auth?.getIdToken) {
    throw new Error('Phiên đăng nhập chưa sẵn sàng. Hãy đăng nhập lại rồi thử lại.')
  }
  let idToken: string | null
  try {
    idToken = await auth.getIdToken()
  } catch {
    throw new Error('Không thể xác nhận phiên đăng nhập. Hãy đăng nhập lại rồi thử lại.')
  }
  if (!idToken) throw new Error('Phiên đăng nhập đã hết hạn. Hãy đăng nhập lại.')

  let response: Response
  try {
    response = await fetch(`${apiBaseUrl()}${path}`, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${idToken}`,
        Accept: 'application/json',
        'Content-Type': 'application/json',
        'X-Request-ID': globalThis.crypto?.randomUUID?.() ?? `teacher-${Date.now()}`,
      },
      body: JSON.stringify(body),
      signal: AbortSignal.timeout(1_900_000),
    })
  } catch {
    throw new Error('Không thể kết nối lúc này. Hãy kiểm tra mạng rồi thử lại.')
  }
  if (!response.ok) throw new Error(messageForStatus(response.status))
  const payload = await response.json().catch(() => null) as Record<string, unknown> | null
  if (!payload || typeof payload !== 'object') throw new Error('Chưa nhận được kết quả. Hãy thử lại.')
  return payload as T
}

const prefix = () => `/api/teacher/v1/organizations/${organizationId()}/ai`

export const aiWorkflowService = {
  suggestLessonPlan: (input: TeacherLessonSuggestionInput) =>
    post<AiResponse<Record<string, unknown>>>(`${prefix()}/lesson-plan-suggestions`, input),
}
