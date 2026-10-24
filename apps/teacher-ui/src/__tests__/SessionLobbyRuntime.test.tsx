import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { saveActiveSession } from '../services/activeSessionStore'
import { SessionLobbyRuntime } from '../pages/SessionLobbyRuntime'

const mock = vi.hoisted(() => ({
  listJoinRequests: vi.fn(),
  readSession: vi.fn(),
  readRoster: vi.fn(),
  listProfiles: vi.fn(),
  admitDevice: vi.fn(),
  revokeDevice: vi.fn(),
  createGroup: vi.fn(),
  assignMember: vi.fn(),
  startSession: vi.fn(),
  startChildTurn: vi.fn(),
}))

vi.mock('../services/sessionService', () => ({
  sessionService: {
    listJoinRequests: mock.listJoinRequests,
    readSession: mock.readSession,
    readRoster: mock.readRoster,
    listProfiles: mock.listProfiles,
    admitDevice: mock.admitDevice,
    revokeDevice: mock.revokeDevice,
    createGroup: mock.createGroup,
    assignMember: mock.assignMember,
    startSession: mock.startSession,
    startChildTurn: mock.startChildTurn,
  },
}))

afterEach(() => cleanup())

beforeEach(() => {
  vi.clearAllMocks()
  sessionStorage.clear()
  saveActiveSession({
    organizationId: 'org-1',
    sessionId: 'session-1',
    classId: 'class-1',
    revision: 3,
    state: 'lobby',
    drawMode: 'group',
    title: 'Khu vườn',
    joinCode: 'invite-code-123',
    admittedChildren: [],
    groups: [],
    turns: [],
  })
  mock.listJoinRequests.mockResolvedValue([{ grant_id: 'grant-1', requested_at: null }])
  mock.readSession.mockResolvedValue({
    contract: 'Be1SessionV1', session_id: 'session-1', organization_id: 'org-1',
    class_id: 'class-1', state: 'lobby', revision: 3, configuration: { title: 'Khu vườn' },
  })
  mock.readRoster.mockResolvedValue({
    contract: 'Be1SessionRosterV1', session_revision: 3, members: [], groups: [], turns: [],
  })
  mock.listProfiles.mockResolvedValue([{
    child_id: 'child-1', class_id: 'class-1', display_name: 'Hồ sơ A', age_months: 72,
  }])
  mock.admitDevice.mockResolvedValue({ membership_id: 'membership-1', state: 'admitted', session_revision: 4 })
  mock.createGroup.mockResolvedValue({ group_id: 'group-1', display_name: 'Nhóm cùng vẽ', state: 'active', session_revision: 5 })
  mock.assignMember.mockResolvedValue({ membership_id: 'membership-1', group_id: 'group-1', session_revision: 6 })
  mock.startSession.mockResolvedValue({
    contract: 'Be1SessionV1', session_id: 'session-1', organization_id: 'org-1',
    class_id: 'class-1', state: 'active', revision: 7, configuration: { title: 'Khu vườn' },
  })
  mock.startChildTurn.mockResolvedValue({ turn_id: 'turn-1', child_id: 'child-1', group_id: 'group-1', state: 'active' })
})

describe('SessionLobbyRuntime', () => {
  it('admits a selected managed profile and starts one persisted group turn', async () => {
    render(<MemoryRouter initialEntries={['/session/lobby']}><Routes>
      <Route path="/session/lobby" element={<SessionLobbyRuntime />} />
      <Route path="/session/orchestrate" element={<h1>Class started</h1>} />
    </Routes></MemoryRouter>)

    expect(await screen.findByText('Thiết bị chờ xác nhận')).toBeTruthy()
    fireEvent.change(await screen.findByRole('combobox', { name: 'Chọn hồ sơ cho grant-1' }), { target: { value: 'child-1' } })
    fireEvent.click(screen.getByRole('button', { name: 'Tiếp nhận' }))

    expect(await screen.findByText('Hồ sơ A')).toBeTruthy()
    expect(mock.admitDevice).toHaveBeenCalledWith('session-1', 'grant-1', 'child-1')
    fireEvent.click(screen.getByRole('button', { name: 'Bắt đầu lớp' }))

    expect(await screen.findByRole('heading', { name: 'Class started' })).toBeTruthy()
    expect(mock.createGroup).toHaveBeenCalledWith('session-1', 'Nhóm cùng vẽ')
    expect(mock.assignMember).toHaveBeenCalledWith('session-1', 'group-1', 'child-1', 5)
    expect(mock.startSession).toHaveBeenCalledWith('session-1', 6)
    expect(mock.startChildTurn).toHaveBeenCalledWith('session-1', 'group-1', 'child-1')
  })
})
