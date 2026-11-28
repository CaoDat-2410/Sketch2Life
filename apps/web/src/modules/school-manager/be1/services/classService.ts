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
  /** Masked by the server (the full address is never returned); absent from older servers. */
  email_masked?: string | null
  /** Only meaningful when the list was asked with a class: this Teacher already holds that class. */
  is_current?: boolean
}

/** One line that tells candidates apart: name and masked e-mail, whichever the account has. */
export function teacherCandidateLabel(candidate: Be1TeacherCandidate): string {
  const parts = [candidate.display_name, candidate.email_masked].filter(Boolean)
  return parts.length > 0 ? parts.join(' · ') : 'Giáo viên chưa có tên hiển thị'
}

/** Adds a stable ordinal only when a visible label is shared by multiple candidates. */
export function teacherCandidateLabels(candidates: readonly Be1TeacherCandidate[]): string[] {
  const baseLabels = candidates.map(teacherCandidateLabel)
  const totals = new Map<string, number>()
  baseLabels.forEach((label) => totals.set(label, (totals.get(label) ?? 0) + 1))

  const seen = new Map<string, number>()
  let labels = baseLabels.map((label) => {
    if (totals.get(label) === 1) return label
    const ordinal = (seen.get(label) ?? 0) + 1
    seen.set(label, ordinal)
    return `${label} (${ordinal})`
  })

  // A naturally suffixed name can collide with an ordinal added above. Resolve any such
  // collision with the stable list position, without exposing candidate references.
  for (let attempt = 0; new Set(labels).size < labels.length && attempt < labels.length; attempt++) {
    const counts = new Map<string, number>()
    labels.forEach((label) => counts.set(label, (counts.get(label) ?? 0) + 1))
    labels = labels.map((label, index) => counts.get(label) === 1 ? label : `${label} (${index + 1})`)
  }

  return labels
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

export type Be1TeacherAssignmentTransferAction = 'REASSIGN' | 'OFFBOARD'
export type Be1TeacherAssignmentTransferState =
  | 'TRANSFER_PENDING'
  | 'RECONCILE_REQUIRED'
  | 'COMPLETED'
  | 'OFFBOARDED'
  | 'COMPENSATED_CONFLICT'

export interface Be1TeacherAssignmentTransferAcceptedV1 {
  contract: 'Be1TeacherAssignmentTransferAcceptedV1'
  transfer_id: string
  class_id: string
  action: Be1TeacherAssignmentTransferAction
  state: 'TRANSFER_PENDING'
  assignment_revision: number
  status_url: string
}

function isTeacherAssignmentTransferAccepted<TAction extends Be1TeacherAssignmentTransferAction>(
  value: unknown,
  action: TAction,
): value is Be1TeacherAssignmentTransferAcceptedV1 & { action: TAction } {
  if (typeof value !== 'object' || value === null) return false
  const result = value as Record<string, unknown>
  return result.contract === 'Be1TeacherAssignmentTransferAcceptedV1' &&
    result.transfer_id !== '' && typeof result.transfer_id === 'string' &&
    typeof result.class_id === 'string' && result.class_id !== '' &&
    result.action === action && result.state === 'TRANSFER_PENDING' &&
    typeof result.assignment_revision === 'number' && Number.isInteger(result.assignment_revision) &&
    typeof result.status_url === 'string' && result.status_url !== ''
}

async function requestTeacherAssignmentTransfer<TAction extends Be1TeacherAssignmentTransferAction>(
  path: string,
  init: RequestInit,
  action: TAction,
): Promise<(Be1TeacherAssignmentTransferAcceptedV1 & { action: TAction }) | null> {
  let result: unknown
  try {
    result = await adminBe1Request<unknown>(path, init)
  } catch (cause) {
    if (cause instanceof Error && cause.message === 'BE1 returned an invalid response body.') return null
    throw cause
  }
  return isTeacherAssignmentTransferAccepted(result, action) ? result : null
}

export interface Be1TeacherAssignmentTransferStatusV1 {
  contract: 'Be1TeacherAssignmentTransferStatusV1'
  transfer_id: string
  class_id: string
  action: Be1TeacherAssignmentTransferAction
  state: Be1TeacherAssignmentTransferState
  assignment_revision: number
  created_at: string
  updated_at: string
  last_failure_code: string | null
  status_url: string
}

export type Be1TeacherAssignmentResult =
  | { kind: 'assigned'; assignment: Be1TeacherAssignment }
  | { kind: 'transfer_accepted'; transfer: Be1TeacherAssignmentTransferAcceptedV1 }

export const ASSIGNMENT_TRANSFER_STATE_LABELS: Record<Be1TeacherAssignmentTransferState, string> = {
  TRANSFER_PENDING: 'Đang chuyển giáo viên phụ trách.',
  RECONCILE_REQUIRED: 'Chuyển giáo viên cần được theo dõi thêm.',
  COMPLETED: 'Đã đổi giáo viên phụ trách.',
  OFFBOARDED: 'Đã gỡ giáo viên phụ trách.',
  COMPENSATED_CONFLICT: 'Đã hoàn tác thay đổi do xung đột.',
}

export function assignmentTransferStateLabel(state: string): string {
  return ASSIGNMENT_TRANSFER_STATE_LABELS[state as Be1TeacherAssignmentTransferState] ?? state
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
  listTeacherCandidates: async (cursor?: string, classId?: string) => {
    const organization = adminOrganizationId()
    const query = new URLSearchParams({ limit: '25' })
    if (cursor) query.set('cursor', cursor)
    if (classId) query.set('class_id', classId)
    return adminBe1Request<{ contract: 'Be1TeacherCandidatePageV1'; items: Be1TeacherCandidate[]; next_cursor: string | null }>(
      `/organizations/${encodeURIComponent(organization)}/teacher-candidates?${query.toString()}`,
    )
  },
  assignTeacher: async (classId: string, candidateRef: string, revision: number, idempotencyKey: string): Promise<Be1TeacherAssignmentResult> => {
    const result = await adminBe1Request<Be1TeacherAssignment | Be1TeacherAssignmentTransferAcceptedV1>(`/classes/${encodeURIComponent(classId)}/assignments`, {
      method: 'POST',
      headers: { 'If-Match': `"${revision}"`, 'Idempotency-Key': idempotencyKey },
      body: JSON.stringify({ candidate_ref: candidateRef }),
    })
    if (result.contract === 'Be1AdultAssignmentV1') return { kind: 'assigned', assignment: result }
    if (result.contract === 'Be1TeacherAssignmentTransferAcceptedV1') return { kind: 'transfer_accepted', transfer: result }
    throw new Error('BE1 returned an invalid assignment response.')
  },
  reassignTeacher: async (classId: string, candidateRef: string, revision: number, idempotencyKey: string) =>
    requestTeacherAssignmentTransfer(`/classes/${encodeURIComponent(classId)}/assignments`, {
      method: 'POST',
      headers: { 'If-Match': `"${revision}"`, 'Idempotency-Key': idempotencyKey },
      body: JSON.stringify({ candidate_ref: candidateRef }),
    }, 'REASSIGN'),
  offboardTeacher: async (classId: string, revision: number, idempotencyKey: string) =>
    requestTeacherAssignmentTransfer(`/classes/${encodeURIComponent(classId)}/assignments/current`, {
      method: 'DELETE',
      headers: { 'If-Match': `"${revision}"`, 'Idempotency-Key': idempotencyKey },
    }, 'OFFBOARD'),
  getAssignmentTransfer: async (classId: string, transferId: string, signal?: AbortSignal) =>
    adminBe1Request<Be1TeacherAssignmentTransferStatusV1>(
      `/classes/${encodeURIComponent(classId)}/assignment-transfers/${encodeURIComponent(transferId)}`,
      signal ? { signal } : {},
    ),
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
    if (cause.code === 'TEACHER_ASSIGNMENT_REQUIRED') {
      return { text: 'Lớp hiện không có Giáo viên phụ trách. Danh sách lớp đã được tải lại.', reload: true }
    }
    if (cause.status === 409) return { text: 'Lớp đã thay đổi hoặc đã có Giáo viên; đã tải lại.', reload: true }
    if (cause.status === 404) return { text: 'Không thể hoàn tất phân công; danh sách đã được tải lại.', reload: true }
    if (cause.status === 403) return { text: 'Tài khoản không có quyền phân công.', reload: false }
  }
  return { text: cause instanceof Error ? cause.message : 'Không thể phân công Giáo viên lúc này.', reload: false }
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
