import { createIdempotencyKey } from '../../../../shared/api/backendApi'
import { AdminBe1Error, adminBe1Request, adminOrganizationId } from './be1Client'

export interface Be1Class {
  class_id: string
  display_name: string
  state: 'active' | 'inactive'
  /** FEAT-066 M9-B: class assignment revision, sent as If-Match (absent from older servers). */
  assignment_revision?: number
  has_active_teacher?: boolean
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
  state: 'active' | 'inactive'
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
  listClasses: async () => {
    const organization = adminOrganizationId()
    const result = await adminBe1Request<{ items: Be1Class[] }>(
      `/organizations/${encodeURIComponent(organization)}/classes`,
    )
    return result.items
  },
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
