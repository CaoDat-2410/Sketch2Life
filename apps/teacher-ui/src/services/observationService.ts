import { be1Request, type Be1ApiError } from './be1Client'

export type TeacherObservationLevel = 'not_observed' | 'with_support' | 'during_activity' | 'extended_idea'

export interface TeacherObservationInput {
  organizationId: string
  classId: string
  sessionId: string
  childId: string
  level: TeacherObservationLevel
  comment: string
}

export interface TeacherObservationReceipt {
  contract: 'Be1ObservationV1'
  observation_id: string
  child_id: string
  kind: 'observation'
}

export const observationService = {
  submitObservation: (input: TeacherObservationInput) => be1Request<TeacherObservationReceipt>(
    `/organizations/${encodeURIComponent(input.organizationId)}/classes/${encodeURIComponent(input.classId)}/observations`,
    {
      method: 'POST',
      body: JSON.stringify({
        session_id: input.sessionId,
        child_id: input.childId,
        kind: 'observation',
        content: { rubric: input.level, comment: input.comment },
        source_refs: [],
      }),
    },
  ),
  formatError: (error: unknown) => {
    if (error instanceof Error && 'code' in error) {
      const apiError = error as Be1ApiError
      if (apiError.code === 'CONSENT_NOT_EFFECTIVE') {
        return 'BE1 chưa xác nhận consent cho mục đích này; nhận xét chưa được lưu.'
      }
      if (apiError.code === 'CLASS_SCOPE_MISMATCH' || apiError.code === 'PROFILE_NOT_FOUND') {
        return 'Hồ sơ không thuộc lớp hoặc phiên hiện tại; nhận xét chưa được lưu.'
      }
    }
    return error instanceof Error ? error.message : 'BE1 chưa lưu được nhận xét.'
  },
}
