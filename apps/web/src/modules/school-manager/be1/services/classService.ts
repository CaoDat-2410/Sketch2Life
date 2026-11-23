import { createIdempotencyKey } from '../../../../shared/api/backendApi'
import { CURSOR_PAGE_LIMIT, collectCursorPages, pageQuery } from '../../../../shared/api/cursorPages'
import { AdminBe1Error, adminBe1Request, adminOrganizationId } from './be1Client'

export type Be1ClassState = 'active' | 'suspended' | 'archived'
/** T-7b: the A07 state filter; a School Manager may list every state. */
export type Be1ClassFilter = Be1ClassState | 'all'

export interface Be1Class {
  class_id: string
  display_name: string
  state: Be1ClassState
  /** T-7b: class revision, the strong If-Match of suspend/archive (not the assignment revision). */
  class_revision?: number
  /** FEAT-066 M9-B: class assignment revision, sent as If-Match (absent from older servers). */
  assignment_revision?: number
  has_active_teacher?: boolean
}

/** T-7b: 200 body of suspend/archive. */
export interface Be1ClassStateResult {
  contract: 'Be1ClassStateV1'
  class_id: string
  state: Be1ClassState
  class_revision: number
}

export type ClassStateCommand = 'suspend' | 'archive'

export const CLASS_STATE_LABELS: Record<Be1ClassState, string> = {
  active: 'Đang hoạt động',
  suspended: 'Tạm ngưng',
  archived: 'Đã lưu trữ',
}

export function classStateLabel(state: string): string {
  return CLASS_STATE_LABELS[state as Be1ClassState] ?? state
}

/** The transitions of the backend state machine: archived is terminal, there is no restore. */
export function allowedClassCommands(state: string): ClassStateCommand[] {
  if (state === 'active') return ['suspend', 'archive']
  if (state === 'suspended') return ['archive']
  return []
}

/** FEAT-066 M9-B (O-3b): minimum candidate fields; no email or provider id. */
export interface Be1TeacherCandidate {
  candidate_ref: string
  display_name: string | null
}

export interface Be1TeacherAssignment {
  contract: 'Be1AdultAssignmentV1'
  assignment_id: string
  candidate_ref: string
  role: 'teacher'
  class_id: string
  active: boolean
  assignment_revision: number
}

/** 201 body of create class; `state` and `assignment_revision` are additive. */
export interface Be1CreatedClassResponse {
  contract: 'Be1ClassV1'
  class_id: string
  display_name: string
  state: Be1ClassState
  assignment_revision: number
}

export interface AdminAssignment {
  role: 'school_admin' | 'teacher' | 'guide' | 'observer'
  class_id: string | null
}

export const classService = {
  currentAssignments: async () => {
    const organization = adminOrganizationId()
    return adminBe1Request<{ contract: 'Be1AdultAssignmentsV1'; assignments: AdminAssignment[] }>(
      `/organizations/${encodeURIComponent(organization)}/me`,
    )
  },
  /** T-7a/T-7b (SRS l.1640): every page of A07 for one state filter. */
  listClasses: async (state: Be1ClassFilter = 'all') => {
    const organization = adminOrganizationId()
    const { items } = await collectCursorPages<Be1Class>((cursor) =>
      adminBe1Request<{ items: Be1Class[]; next_cursor: string | null }>(
        `/organizations/${encodeURIComponent(organization)}/classes${pageQuery({ state, limit: CURSOR_PAGE_LIMIT, cursor })}`,
      ),
    )
    return items
  },
  /** T-7b: suspend or archive; no body, one key per exact command, strong class-revision If-Match. */
  changeClassState: async (classId: string, command: ClassStateCommand, classRevision: number, idempotencyKey: string) =>
    adminBe1Request<Be1ClassStateResult>(`/classes/${encodeURIComponent(classId)}/${command}`, {
      method: 'POST',
      headers: { 'If-Match': `"${classRevision}"`, 'Idempotency-Key': idempotencyKey },
    }),
  listTeacherCandidates: async (cursor?: string) => {
    const organization = adminOrganizationId()
    const query = new URLSearchParams({ limit: '25' })
    if (cursor) query.set('cursor', cursor)
    return adminBe1Request<{ contract: 'Be1TeacherCandidatePageV1'; items: Be1TeacherCandidate[]; next_cursor: string | null }>(
      `/organizations/${encodeURIComponent(organization)}/teacher-candidates?${query.toString()}`,
    )
  },
  assignTeacher: async (classId: string, candidateRef: string, revision: number, idempotencyKey: string) =>
    adminBe1Request<Be1TeacherAssignment>(`/classes/${encodeURIComponent(classId)}/assignments`, {
      method: 'POST',
      headers: { 'If-Match': `"${revision}"`, 'Idempotency-Key': idempotencyKey },
      body: JSON.stringify({ candidate_ref: candidateRef }),
    }),
  /** One Idempotency-Key per user action: the caller passes the same key when it retries that action. */
  createClass: async (displayName: string, idempotencyKey: string = createIdempotencyKey()) => {
    const organization = adminOrganizationId()
    return adminBe1Request<Be1CreatedClassResponse>(
      `/organizations/${encodeURIComponent(organization)}/classes`,
      {
        method: 'POST',
        headers: { 'Idempotency-Key': idempotencyKey },
        body: JSON.stringify({ display_name: displayName }),
      },
    )
  },
}

/** FEAT-066 M9-B: page message for a failed assignment and whether the page reloads. */
export function assignmentOutcomeMessage(cause: unknown): { text: string; reload: boolean } {
  if (cause instanceof AdminBe1Error) {
    if (cause.status === 409) return { text: 'Lớp đã thay đổi hoặc đã có Teacher; đã tải lại.', reload: true }
    if (cause.status === 404) return { text: 'Không thể hoàn tất phân công; danh sách đã được tải lại.', reload: true }
    if (cause.status === 403) return { text: 'Tài khoản không có quyền phân công.', reload: false }
  }
  return { text: cause instanceof Error ? cause.message : 'Không thể phân công Teacher lúc này.', reload: false }
}

const NOT_FOUND_OR_NO_ACCESS = 'Không tìm thấy lớp hoặc bạn không có quyền truy cập. Danh sách lớp đã được tải lại.'

/** T-7b: page message for a failed suspend/archive, whether the list reloads, and whether the key is kept. */
export function classStateOutcomeMessage(cause: unknown): { text: string; reload: boolean; keepKey: boolean } {
  if (cause instanceof AdminBe1Error) {
    if (cause.code === 'STALE_REVISION') return { text: `${cause.message} Đã tải lại danh sách lớp; hãy kiểm tra rồi xác nhận lại.`, reload: true, keepKey: false }
    if (cause.code === 'INVALID_STATE_TRANSITION') return { text: 'Lớp không còn ở trạng thái cho phép thao tác này. Danh sách lớp đã được tải lại.', reload: true, keepKey: false }
    if (cause.status === 404) return { text: NOT_FOUND_OR_NO_ACCESS, reload: true, keepKey: false }
    if (cause.status === 403) return { text: 'Tài khoản không được phép thực hiện thao tác này.', reload: false, keepKey: false }
    if (cause.status === 429) return { text: cause.message, reload: false, keepKey: false }
    if (cause.status >= 400 && cause.status < 500) return { text: cause.message, reload: false, keepKey: false }
    return { text: `${cause.message} Hãy gửi lại cùng yêu cầu.`, reload: false, keepKey: true }
  }
  return { text: 'Chưa rõ kết quả. Hãy gửi lại cùng yêu cầu.', reload: false, keepKey: true }
}
