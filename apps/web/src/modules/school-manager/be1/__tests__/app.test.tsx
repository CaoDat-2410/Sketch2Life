import { cleanup, render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { PortalSessionProvider } from '../../../../shared/auth/PortalSessionContext'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import type { User } from 'firebase/auth'
import App from '../App'
import { authService } from '../services/authService'
import { classService } from '../services/classService'

afterEach(() => {
  cleanup()
  vi.restoreAllMocks()
})

describe('School Manager BE1 organization gate', () => {
  let signedIn = false
  const user = { uid: 'manager-test' } as User

  beforeEach(() => {
    signedIn = false
    vi.spyOn(authService, 'observe').mockImplementation((callback) => {
      callback(signedIn ? user : null)
      return () => undefined
    })
    vi.spyOn(classService, 'currentAssignments').mockResolvedValue({
      contract: 'Be1AdultAssignmentsV1',
      assignments: [{ role: 'school_admin', class_id: null }],
    })
    vi.spyOn(classService, 'listClasses').mockResolvedValue([])
  })

  it('checks an organization-wide school_admin assignment before listing classes', async () => {
    signedIn = true
    render(<PortalSessionProvider><MemoryRouter initialEntries={['/school/classes']}><App /></MemoryRouter></PortalSessionProvider>)

    expect(await screen.findByRole('heading', { name: 'Lớp học' })).toBeTruthy()
    expect(classService.currentAssignments).toHaveBeenCalledOnce()
    expect(classService.listClasses).toHaveBeenCalledOnce()
  })

  it('denies a class-scoped assignment from the school-wide Manager portal', async () => {
    signedIn = true
    vi.mocked(classService.currentAssignments).mockResolvedValueOnce({
      contract: 'Be1AdultAssignmentsV1',
      assignments: [{ role: 'school_admin', class_id: 'class-1' }],
    })
    render(<PortalSessionProvider><MemoryRouter initialEntries={['/school/classes']}><App /></MemoryRouter></PortalSessionProvider>)

    expect(await screen.findByRole('heading', { name: 'Không thể mở cổng quản trị' })).toBeTruthy()
    expect(classService.listClasses).not.toHaveBeenCalled()
  })

  it('keeps unsupported administration screens explicitly unavailable', async () => {
    signedIn = true
    render(<PortalSessionProvider><MemoryRouter initialEntries={['/school/users']}><App /></MemoryRouter></PortalSessionProvider>)

    expect(await screen.findByRole('heading', { name: 'Chức năng trường học' })).toBeTruthy()
    expect(screen.queryByRole('heading', { name: 'Người dùng & vai trò' })).toBeNull()
  })
})
