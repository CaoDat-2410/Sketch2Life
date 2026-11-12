import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { MemoryRouter } from 'react-router-dom'
import { saveActiveSession } from '../services/activeSessionStore'
import { ObservationFeedbackPage } from '../pages/ObservationFeedbackPage'

const mock = vi.hoisted(() => ({ submitObservation: vi.fn(), formatError: vi.fn((error: unknown) => error instanceof Error ? error.message : 'failed') }))

vi.mock('../services/observationService', () => ({
  observationService: {
    submitObservation: mock.submitObservation,
    formatError: mock.formatError,
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
    revision: 7,
    state: 'active',
    drawMode: 'group',
    title: 'Khu vườn',
    admittedChildren: [{ childId: 'child-1', displayName: 'Hồ sơ A', membershipId: 'member-1', grantId: 'grant-1' }],
    groups: [],
    turns: [],
  })
  mock.submitObservation.mockResolvedValue({
    contract: 'Be1ObservationV1', observation_id: 'observation-1', child_id: 'child-1', kind: 'observation',
  })
})

describe('ObservationFeedbackPage', () => {
  it('saves a teacher-authored observation and reports the BE1 receipt', async () => {
    render(<MemoryRouter><ObservationFeedbackPage /></MemoryRouter>)

    fireEvent.click(screen.getByLabelText('Thể hiện với hỗ trợ'))
    fireEvent.change(screen.getByLabelText('Ghi chú dựa trên điều giáo viên trực tiếp quan sát'), {
      target: { value: 'Trẻ mô tả gân lá khi cùng vẽ.' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Lưu observation qua BE1' }))

    expect(await screen.findByText(/BE1 đã xác nhận lưu observation/)).toBeTruthy()
    expect(mock.submitObservation).toHaveBeenCalledWith({
      organizationId: 'org-1',
      classId: 'class-1',
      sessionId: 'session-1',
      childId: 'child-1',
      level: 'with_support',
      comment: 'Trẻ mô tả gân lá khi cùng vẽ.',
    })
  })

  it('does not show sample students or allow a write without an active session roster', () => {
    sessionStorage.clear()
    render(<MemoryRouter><ObservationFeedbackPage /></MemoryRouter>)

    expect(screen.getByText(/Chưa có phiên và danh sách trẻ/)).toBeTruthy()
    expect(screen.queryByText('Mây')).toBeNull()
    expect(mock.submitObservation).not.toHaveBeenCalled()
  })
})
