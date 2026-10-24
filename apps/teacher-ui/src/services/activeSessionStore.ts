export interface ActiveSessionChild {
  childId: string
  displayName: string
  membershipId: string
  grantId: string
}

export interface ActiveSessionGroup {
  groupId: string
  displayName: string
  childIds: string[]
}

export interface ActiveSessionTurn {
  childId: string
  groupId: string
  turnId: string
}

export interface ActiveSessionRecord {
  organizationId: string
  sessionId: string
  classId: string
  revision: number
  state: string
  drawMode: 'individual' | 'group'
  title: string
  joinCode?: string
  roomCode?: string
  roomCodeError?: string
  admittedChildren: ActiveSessionChild[]
  groups: ActiveSessionGroup[]
  turns: ActiveSessionTurn[]
}

const ACTIVE_SESSION_KEY = 'be1.activeSession'

export function loadActiveSession(): ActiveSessionRecord | null {
  try {
    const raw = sessionStorage.getItem(ACTIVE_SESSION_KEY)
    if (!raw) return null
    const value: unknown = JSON.parse(raw)
    if (!value || typeof value !== 'object') return null
    const row = value as Record<string, unknown>
    if (
      typeof row.organizationId !== 'string' ||
      typeof row.sessionId !== 'string' ||
      typeof row.classId !== 'string' ||
      typeof row.revision !== 'number' ||
      typeof row.state !== 'string' ||
      typeof row.title !== 'string' ||
      (row.drawMode !== 'individual' && row.drawMode !== 'group')
    ) return null
    return {
      organizationId: row.organizationId,
      sessionId: row.sessionId,
      classId: row.classId,
      revision: row.revision,
      state: row.state,
      title: row.title,
      drawMode: row.drawMode,
      joinCode: typeof row.joinCode === 'string' ? row.joinCode : undefined,
      roomCode: typeof row.roomCode === 'string' ? row.roomCode : undefined,
      roomCodeError: typeof row.roomCodeError === 'string' ? row.roomCodeError : undefined,
      admittedChildren: Array.isArray(row.admittedChildren) ? row.admittedChildren as ActiveSessionChild[] : [],
      groups: Array.isArray(row.groups) ? row.groups as ActiveSessionGroup[] : [],
      turns: Array.isArray(row.turns) ? row.turns as ActiveSessionTurn[] : [],
    }
  } catch {
    return null
  }
}

export function saveActiveSession(session: ActiveSessionRecord) {
  sessionStorage.setItem(ACTIVE_SESSION_KEY, JSON.stringify(session))
}
