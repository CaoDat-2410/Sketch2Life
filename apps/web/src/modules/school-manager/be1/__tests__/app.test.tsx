import { cleanup, render, screen, within } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { PortalSessionProvider } from '../../../../shared/auth/PortalSessionContext'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import type { User } from 'firebase/auth'
import App from '../App'
import { authService } from '../services/authService'
import { classService } from '../services/classService'
import { managerBusinessService } from '../services/managerBusinessService'
import { capacityService } from '../services/capacityService'
import { SCHOOL_MANAGER_NAVIGATION } from '../../../../shared/navigation/WebAppShell'

vi.mock('../pages/SchoolOverviewPage', () => ({ SchoolOverviewPage: () => <h1>Tổng quan</h1> }))

afterEach(() => {
  cleanup()
  vi.restoreAllMocks()
})

describe('School Manager BE1 organization gate', () => {
  let signedIn = false
  let user = { uid: 'manager-test', displayName: 'Nguyễn An', email: 'manager@example.com' } as User

  beforeEach(() => {
    signedIn = false
    user = { uid: 'manager-test', displayName: 'Nguyễn An', email: 'manager@example.com' } as User
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

  it('replaces the legacy settings route with read-only account details', async () => {
    signedIn = true
    render(<PortalSessionProvider><MemoryRouter initialEntries={['/school/settings']}><App /></MemoryRouter></PortalSessionProvider>)

    expect(await screen.findByRole('heading', { name: 'Thông tin tài khoản' })).toBeTruthy()
    const accountLink = screen.getByRole('link', { name: 'Thông tin tài khoản' })
    expect(accountLink.getAttribute('href')).toBe('/school/account')
    expect(accountLink.getAttribute('aria-current')).toBe('page')
    expect(screen.queryByRole('link', { name: 'Cài đặt' })).toBeNull()
    const accountInfo = screen.getByRole('region', { name: 'Thông tin tài khoản' })
    expect(within(accountInfo).getByText('Tên hiển thị')).toBeTruthy()
    expect(within(accountInfo).getByText('Nguyễn An')).toBeTruthy()
    expect(within(accountInfo).getByText('Thư điện tử')).toBeTruthy()
    expect(within(accountInfo).getByText('manager@example.com')).toBeTruthy()
    expect(within(accountInfo).getByText('Vai trò')).toBeTruthy()
    expect(within(accountInfo).getByText('Quản lý trường')).toBeTruthy()
    expect(screen.queryByRole('textbox')).toBeNull()
    expect(screen.queryByRole('button', { name: /Lưu/ })).toBeNull()
    expect(SCHOOL_MANAGER_NAVIGATION.flatMap((group) => group.items).find((item) => item.href === '/school/account')).toMatchObject({ label: 'Thông tin tài khoản', state: 'available' })
    expect(classService.currentAssignments).toHaveBeenCalledOnce()
  })

  it('uses the required account fallbacks when identity fields are empty', async () => {
    signedIn = true
    user = { uid: 'manager-test' } as User
    render(<PortalSessionProvider><MemoryRouter initialEntries={['/school/account']}><App /></MemoryRouter></PortalSessionProvider>)

    expect(await screen.findByRole('heading', { name: 'Thông tin tài khoản' })).toBeTruthy()
    const accountInfo = screen.getByRole('region', { name: 'Thông tin tài khoản' })
    expect(within(accountInfo).getByText('Chưa có tên hiển thị')).toBeTruthy()
    expect(within(accountInfo).getByText('Chưa có thông tin')).toBeTruthy()
    expect(within(accountInfo).getByText('Quản lý trường')).toBeTruthy()
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

  it('routes capacity to the live page and marks its navigation item available', async () => {
    signedIn = true
    vi.spyOn(managerBusinessService, 'organization').mockResolvedValue({
      contract: 'Be1OrganizationV1',
      organization_id: 'org-test',
      display_name: 'Trường kiểm thử',
    })
    vi.spyOn(capacityService, 'getCapacity').mockResolvedValue({
      data: {
        contract: 'Be1OrganizationCapacityV1',
        organization_id: 'org-test',
        subscription_id: null,
        capacity: 10,
        active_class_count: 1,
        available_slots: 9,
        subscription_state: 'NONE',
        revision: 0,
        period_start: null,
        period_end: null,
        scheduled_change: null,
      },
      etag: '"0"',
      revision: 0,
    })
    render(<PortalSessionProvider><MemoryRouter initialEntries={['/school/capacity']}><App /></MemoryRouter></PortalSessionProvider>)

    expect(await screen.findByRole('heading', { name: 'Sức chứa lớp' })).toBeTruthy()
    expect(await screen.findByText('Trường chưa có gói sức chứa. Sức chứa mặc định gồm 10 lớp.')).toBeTruthy()
    const capacityLink = screen.getByRole('link', { name: /^Sức chứa$/ })
    expect(capacityLink.getAttribute('href')).toBe('/school/capacity')
    expect(capacityLink.getAttribute('aria-current')).toBe('page')
    expect(capacityLink.textContent).not.toContain('Chờ dịch vụ')
    expect(SCHOOL_MANAGER_NAVIGATION.flatMap((group) => group.items).find((item) => item.href === '/school/capacity')?.state).toBe('available')
  })

  it('routes organization data requests to the new page', async () => {
    signedIn = true
    render(<PortalSessionProvider><MemoryRouter initialEntries={['/school/data-requests']}><App /></MemoryRouter></PortalSessionProvider>)

    expect(await screen.findByRole('heading', { name: 'Yêu cầu dữ liệu' })).toBeTruthy()
    expect(screen.getByRole('link', { name: 'Yêu cầu dữ liệu' }).getAttribute('href')).toBe('/school/data-requests')
    expect(classService.currentAssignments).toHaveBeenCalledOnce()
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
