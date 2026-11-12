import { be1Request, classroomPurposeRef, organizationId } from './be1Client'
import { profileService, type ManagedProfile } from './profileService'

export interface Be1Class {
  class_id: string
  display_name: string
  state: 'active' | 'inactive'
}

export interface Be1Session {
  session_id: string
  organization_id: string
  class_id: string
  state: string
  revision: number
  configuration: Record<string, unknown>
  join_code?: string
}

export interface PendingJoinRequest {
  grant_id: string
  requested_at: string | null
}

export interface Be1Group {
  group_id: string
  display_name: string
  state: 'active' | 'locked' | 'archived'
  session_revision: number
}

export interface Be1Admission {
  membership_id: string
  state: 'admitted'
  session_revision: number
}

export interface Be1Turn {
  turn_id: string
  child_id: string
  group_id: string
  state: 'active'
}

export type Be1LearningStage =
  | 'preparation' | 'join' | 'explore_draw' | 'assistance' | 'sharing'
  | 'knowledge' | 'off_screen' | 'reflection' | 'completion'

export interface Be1Roster {
  session_revision: number
  members: Array<{
    membership_id: string
    child_id: string
    display_name: string
    group_id: string | null
    progress: 'not_started' | 'in_progress' | 'ready' | 'completed'
    device_grant_id: string | null
  }>
  groups: Array<{ group_id: string; display_name: string; state: 'active' | 'locked' | 'archived' }>
  turns: Array<{
    turn_id: string
    child_id: string
    group_id: string
    state: 'active' | 'closed' | 'revoked'
    canvas_id: string
  }>
}

export interface Be1StageState {
  stage: Be1LearningStage
  stage_revision: number
  lifecycle_state: string
}

export const sessionService = {
  listClasses: async () => {
    const organization = organizationId()
    const result = await be1Request<{ items: Be1Class[] }>(`/organizations/${encodeURIComponent(organization)}/classes`)
    return result.items
  },

  listProfiles: (classId: string): Promise<ManagedProfile[]> => profileService.listForClass(classId),

  readSession: async (sessionId: string) => {
    const organization = organizationId()
    return be1Request<Be1Session>(
      `/organizations/${encodeURIComponent(organization)}/sessions/${encodeURIComponent(sessionId)}`,
    )
  },

  createSession: async (input: { classId: string; title: string; drawMode: 'individual' | 'group' }) => {
    const organization = organizationId()
    const purposeRef = classroomPurposeRef()
    return be1Request<Be1Session>(`/organizations/${encodeURIComponent(organization)}/sessions`, {
      method: 'POST',
      body: JSON.stringify({
        class_id: input.classId,
        purpose_ref: purposeRef,
        configuration: { title: input.title, draw_mode: input.drawMode },
      }),
    })
  },

  openLobby: async (sessionId: string, expectedRevision: number) => {
    const organization = organizationId()
    return be1Request<Be1Session>(
      `/organizations/${encodeURIComponent(organization)}/sessions/${encodeURIComponent(sessionId)}/lobby`,
      { method: 'POST', body: JSON.stringify({ expected_revision: expectedRevision }) },
    )
  },

  rotateRoomCode: async (sessionId: string) => {
    const organization = organizationId()
    return be1Request<{ contract: 'Be1SharedRoomCodeV1'; room_code: string; state: 'lobby' }>(
      `/organizations/${encodeURIComponent(organization)}/sessions/${encodeURIComponent(sessionId)}/room-code/rotate`,
      { method: 'POST' },
    )
  },

  readRoster: async (sessionId: string) => {
    const organization = organizationId()
    return be1Request<Be1Roster>(
      `/organizations/${encodeURIComponent(organization)}/sessions/${encodeURIComponent(sessionId)}/roster`,
    )
  },

  readLearningStage: async (sessionId: string) => {
    const organization = organizationId()
    return be1Request<Be1StageState>(
      `/organizations/${encodeURIComponent(organization)}/sessions/${encodeURIComponent(sessionId)}/learning-stage`,
    )
  },

  readOutcome: async (sessionId: string) => {
    const organization = organizationId()
    return be1Request<{
      contract: 'Be1SessionOutcomeReadV1'
      outcome: null | {
        value: 'completed' | 'ended_early'
        reason_category: string | null
        teacher_note: string | null
        outcome_refs: string[]
        stage_revision: number
        created_at: string
      }
    }>(`/organizations/${encodeURIComponent(organization)}/sessions/${encodeURIComponent(sessionId)}/outcome`)
  },

  advanceLearningStage: async (
    sessionId: string,
    input: {
      expected_stage_revision: number
      target_stage: Be1LearningStage
      assistance_disposition?: 'not_needed'
      unfinished_group_ids: string[]
      unfinished_group_disposition?: 'save_draft'
    },
  ) => {
    const organization = organizationId()
    return be1Request<{
      contract: 'Be1SharedLearningStageReceiptV1'
      stage: Be1LearningStage
      stage_revision: number
      session_revision: number
      command_id: string
      saved_drafts: string[]
    }>(
      `/organizations/${encodeURIComponent(organization)}/sessions/${encodeURIComponent(sessionId)}/learning-stage/advance`,
      {
        method: 'POST',
        headers: { 'Idempotency-Key': crypto.randomUUID() },
        body: JSON.stringify(input),
      },
    )
  },

  completeSession: async (
    sessionId: string,
    input: {
      expected_stage_revision: number
      outcome: 'completed' | 'ended_early'
      reason_category?: 'time' | 'safety' | 'technical' | 'other'
      teacher_note?: string
      outcome_refs?: string[]
    },
  ) => {
    const organization = organizationId()
    return be1Request<{
      contract: 'Be1SessionOutcomeReceiptV1'
      outcome: 'completed' | 'ended_early'
      reason_category: string | null
      session_revision: number
      lifecycle_state: string
    }>(
      `/organizations/${encodeURIComponent(organization)}/sessions/${encodeURIComponent(sessionId)}/completion`,
      {
        method: 'POST',
        headers: { 'Idempotency-Key': crypto.randomUUID() },
        body: JSON.stringify(input),
      },
    )
  },

  listJoinRequests: async (sessionId: string) => {
    const organization = organizationId()
    const result = await be1Request<{ items: PendingJoinRequest[] }>(
      `/organizations/${encodeURIComponent(organization)}/sessions/${encodeURIComponent(sessionId)}/join-requests`,
    )
    return result.items
  },

  admitDevice: async (sessionId: string, grantId: string, childId: string) => {
    const organization = organizationId()
    return be1Request<{ membership_id: string; state: 'admitted'; session_revision: number }>(
      `/organizations/${encodeURIComponent(organization)}/sessions/${encodeURIComponent(sessionId)}/join-requests/${encodeURIComponent(grantId)}/admit`,
      { method: 'POST', body: JSON.stringify({ child_id: childId }) },
    )
  },

  revokeDevice: async (sessionId: string, grantId: string) => {
    const organization = organizationId()
    return be1Request<{ contract: 'Be1DeviceGrantV1'; grant_id: string; state: 'revoked' }>(
      `/organizations/${encodeURIComponent(organization)}/sessions/${encodeURIComponent(sessionId)}/join-requests/${encodeURIComponent(grantId)}/revoke`,
      { method: 'POST' },
    )
  },

  createGroup: async (sessionId: string, displayName: string) => {
    const organization = organizationId()
    return be1Request<Be1Group>(
      `/organizations/${encodeURIComponent(organization)}/sessions/${encodeURIComponent(sessionId)}/groups`,
      { method: 'POST', body: JSON.stringify({ display_name: displayName }) },
    )
  },

  assignMember: async (sessionId: string, groupId: string, childId: string, expectedRevision: number) => {
    const organization = organizationId()
    return be1Request<{ contract: 'Be1GroupAssignmentV1'; membership_id: string; group_id: string; session_revision: number }>(
      `/organizations/${encodeURIComponent(organization)}/sessions/${encodeURIComponent(sessionId)}/groups/${encodeURIComponent(groupId)}/members/${encodeURIComponent(childId)}`,
      { method: 'PUT', body: JSON.stringify({ child_id: childId, expected_revision: expectedRevision }) },
    )
  },

  startChildTurn: async (sessionId: string, groupId: string, childId: string) => {
    const organization = organizationId()
    return be1Request<Be1Turn>(
      `/organizations/${encodeURIComponent(organization)}/sessions/${encodeURIComponent(sessionId)}/groups/${encodeURIComponent(groupId)}/turns/${encodeURIComponent(childId)}`,
      { method: 'POST' },
    )
  },

  pauseSession: async (sessionId: string, expectedRevision: number) => {
    const organization = organizationId()
    return be1Request<Be1Session>(
      `/organizations/${encodeURIComponent(organization)}/sessions/${encodeURIComponent(sessionId)}/pause`,
      { method: 'POST', body: JSON.stringify({ expected_revision: expectedRevision }) },
    )
  },

  resumeSession: async (sessionId: string, expectedRevision: number) => {
    const organization = organizationId()
    return be1Request<Be1Session>(
      `/organizations/${encodeURIComponent(organization)}/sessions/${encodeURIComponent(sessionId)}/resume`,
      { method: 'POST', body: JSON.stringify({ expected_revision: expectedRevision }) },
    )
  },

  startSession: async (sessionId: string, expectedRevision: number) => {
    const organization = organizationId()
    return be1Request<Be1Session>(
      `/organizations/${encodeURIComponent(organization)}/sessions/${encodeURIComponent(sessionId)}/start`,
      { method: 'POST', body: JSON.stringify({ expected_revision: expectedRevision }) },
    )
  },
}
