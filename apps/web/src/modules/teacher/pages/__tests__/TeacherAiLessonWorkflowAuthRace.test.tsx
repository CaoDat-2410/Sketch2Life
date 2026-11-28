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
  vi.spyOn(authService, 'getCurrentUser').mockReturnValue({ uid: 'teacher-1' } as never)
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

describe('Teacher AI workflow auth initialization', () => {
  it('keeps the first field edit when auth resolves after render and restores the account draft', async () => {
    sessionStorage.setItem(workflowStorageKey, JSON.stringify({
      topic: 'Saved account draft',
      busy: 'suggestion',
    }))

    const view = render(<MemoryRouter><TeacherAiLessonWorkflowPage /></MemoryRouter>)
    const topic = screen.getByLabelText(/Chủ đề/) as HTMLInputElement
    fireEvent.change(topic, { target: { value: 'Typed before auth resolves' } })

    await act(async () => {
      await Promise.resolve()
      resolveObservedUser?.({ uid: 'teacher-1' })
    })
    view.rerender(<MemoryRouter><TeacherAiLessonWorkflowPage /></MemoryRouter>)

    expect((screen.getByLabelText(/Chủ đề/) as HTMLInputElement).value).toBe('Typed before auth resolves')
    let stored = JSON.parse(sessionStorage.getItem(workflowStorageKey) ?? '{}') as Record<string, unknown>
    expect(stored.topic).toBe('Typed before auth resolves')
    expect(stored.busy).toBe('interrupted')

    fireEvent.change(screen.getByLabelText(/Chủ đề/), { target: { value: 'Typed after auth resolves' } })
    stored = JSON.parse(sessionStorage.getItem(workflowStorageKey) ?? '{}') as Record<string, unknown>
    expect(stored.topic).toBe('Typed after auth resolves')
  })
})
