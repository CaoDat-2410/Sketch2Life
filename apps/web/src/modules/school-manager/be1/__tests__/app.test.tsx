import { cleanup, render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { PortalSessionProvider } from '../../../../shared/auth/PortalSessionContext'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import type { User } from 'firebase/auth'
import App from '../App'
import { authService } from '../services/authService'
import { classService } from '../services/classService'
import { SCHOOL_MANAGER_NAVIGATION } from '../../../../shared/navigation/WebAppShell'

vi.mock('../pages/SchoolOverviewPage', () => ({ SchoolOverviewPage: () => <h1>Tổng quan</h1> }))

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

  it.each(['inbox', 'capacity', 'quota', 'billing'])('keeps %s unavailable', async (route) => {
    signedIn = true
    render(<PortalSessionProvider><MemoryRouter initialEntries={[`/school/${route}`]}><App /></MemoryRouter></PortalSessionProvider>)
    expect((await screen.findAllByText('Chưa khả dụng')).length).toBeGreaterThan(0)
  })

  it('redirects the removed teacher groups route and updates the navigation', async () => {
    signedIn = true
    render(<PortalSessionProvider><MemoryRouter initialEntries={['/school/teacher-groups']}><App /></MemoryRouter></PortalSessionProvider>)
    await screen.findByRole('heading', { name: /tổng quan/i })
    const links = SCHOOL_MANAGER_NAVIGATION.flatMap((group) => group.items)
    expect(links.some((item) => item.href === '/school/teacher-groups')).toBe(false)
    expect(links.find((item) => item.href === '/school/feedback')?.state).toBe('available')
    expect(links.find((item) => item.href === '/school/teacher-assignments')?.state).toBe('available')
  })
})
