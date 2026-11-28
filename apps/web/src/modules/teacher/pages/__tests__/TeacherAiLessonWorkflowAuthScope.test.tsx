import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { act, cleanup, fireEvent, render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { TeacherAiLessonWorkflowPage } from '../TeacherAiLessonWorkflowPage'
import { clearAiWorkflowSession } from '../../services/aiWorkflowSession'
import { authService } from '../../../school-manager/be1/services/authService'

const workflowStorageKey = 'sketch2life:teacher-ai-workflow:v1:teacher-1:org-1'
let resolveObservedUser: ((user: { uid: string } | null) => void) | undefined

beforeEach(() => {
  sessionStorage.clear()
  window.sketch2lifeConfig = { organizationId: 'org-1' }
  resolveObservedUser = undefined
  vi.spyOn(authService, 'getCurrentUser').mockReturnValue(null)
  vi.spyOn(authService, 'observe').mockImplementation((callback) => {
    resolveObservedUser = callback as (user: { uid: string } | null) => void
    return () => undefined
  })
})

afterEach(() => {
  cleanup()
  clearAiWorkflowSession()
  sessionStorage.clear()
  vi.restoreAllMocks()
  window.sketch2lifeConfig = undefined
})

describe('Teacher AI workflow scope subscription', () => {
  it('changes to the resolved account scope without exposing the anonymous edit', async () => {
    sessionStorage.setItem(workflowStorageKey, JSON.stringify({
      topic: 'Saved account draft',
      busy: 'suggestion',
    }))

    const getCurrentUser = vi.mocked(authService.getCurrentUser)
    render(<MemoryRouter><TeacherAiLessonWorkflowPage /></MemoryRouter>)
    fireEvent.change(screen.getByLabelText(/Chủ đề/), { target: { value: 'Typed before account was known' } })

    await act(async () => {
      await Promise.resolve()
      getCurrentUser.mockReturnValue({ uid: 'teacher-1' } as never)
      resolveObservedUser?.({ uid: 'teacher-1' })
    })

    expect((screen.getByLabelText(/Chủ đề/) as HTMLInputElement).value).toBe('Saved account draft')
    let stored = JSON.parse(sessionStorage.getItem(workflowStorageKey) ?? '{}') as Record<string, unknown>
    expect(stored.topic).toBe('Saved account draft')
    expect(stored.topic).not.toBe('Typed before account was known')
    expect(stored.busy).toBe('interrupted')

    fireEvent.change(screen.getByLabelText(/Chủ đề/), { target: { value: 'Typed after account was known' } })
    stored = JSON.parse(sessionStorage.getItem(workflowStorageKey) ?? '{}') as Record<string, unknown>
    expect(stored.topic).toBe('Typed after account was known')
  })
})
