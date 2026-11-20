import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { act, cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { A01ContentModerationPage, A02PlatformOperationsPage } from '../AdminScreens'

const panels = ['overview', 'orgs', 'queues', 'lifecycle', 'audit', 'permissions', 'inbox', 'settings', 'feedback', 'catalog', 'billing', 'quota', 'capacity', 'lessons']
const response = (body: unknown, status = 200) => new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } })
function emptyResponse(url: string) {
  if (url.includes('/organizations/summary')) return { total: 0, active: 0, paused: 0, disabled: 0, other: 0 }
  if (url.includes('/settings')) return { environment: 'local', real_payments_enabled: false, billing_sandbox_enabled: true, smtp_configured: true, preferences: { locale: 'vi-VN', email_notifications: true, revision: 1 } }
  if (url.includes('/operations')) return { jobs: [], core_outbox: [], email: [], lifecycle: [] }
  if (url.includes('/session')) return { account_id: 'admin', items: [] }
  return { items: [], total: 0, unread_count: 0, next_cursor: null }
}
function mount(panel: string) {
  return render(<MemoryRouter initialEntries={['/?panel=' + panel]}>{panel === 'lessons' ? <A01ContentModerationPage /> : <A02PlatformOperationsPage />}</MemoryRouter>)
}
beforeEach(() => { window.sketch2lifeAuth = { getIdToken: async () => 'synthetic-token' } })
afterEach(() => { cleanup(); vi.unstubAllGlobals(); delete window.sketch2lifeAuth })

describe('Every admin screen handles absent data and unavailable APIs', () => {
  it.each(panels)('%s keeps loading visible until the request resolves', async panel => {
    let waiting = true
    const pending: (() => void)[] = []
    vi.stubGlobal('fetch', vi.fn((url: string) => waiting
      ? new Promise<Response>(resolve => pending.push(() => resolve(response(emptyResponse(url)))))
      : Promise.resolve(response(emptyResponse(url)))))
    mount(panel)
    expect(screen.getAllByRole('status', { name: 'Đang tải dữ liệu' }).length).toBeGreaterThan(0)
    expect(screen.queryByRole('alert')).toBeNull()
    await act(async () => { waiting = false; pending.forEach(resolve => resolve()) })
    await waitFor(() => expect(screen.queryByRole('status', { name: 'Đang tải dữ liệu' })).toBeNull())
  })
  it.each(panels)('%s shows a successful empty result without an error or useless pager', async panel => {
    vi.stubGlobal('fetch', vi.fn(async (url: string) => response(emptyResponse(url))))
    const { container } = mount(panel)
    await screen.findAllByText(/Chưa có|Chưa chọn|Không tìm thấy quản trị viên/)
    expect(screen.queryByRole('alert')).toBeNull()
    expect(container.querySelector('.pa-pager')).toBeNull()
    expect(container.querySelector('.pa-data-state')).toBeTruthy()
  })
  it.each(panels)('%s keeps an API failure distinct from an empty dataset and offers retry', async panel => {
    vi.stubGlobal('fetch', vi.fn(async () => response({ code: 'PROVIDER_UNAVAILABLE' }, 503)))
    const { container } = mount(panel)
    expect((await screen.findAllByRole('alert')).length).toBeGreaterThan(0)
    expect(screen.getAllByText('Không tải được dữ liệu').length).toBeGreaterThan(0)
    expect(screen.getAllByRole('button', { name: 'Tải lại' }).length).toBeGreaterThan(0)
    expect(screen.queryByText('Chưa có dữ liệu')).toBeNull()
    const errorStates = container.querySelectorAll('.pa-data-state.is-error')
    expect(errorStates.length).toBeGreaterThan(0)
    errorStates.forEach(state => {
      expect(state.querySelector('.pa-data-state-copy h2')?.textContent).toBe('Không tải được dữ liệu')
      expect(state.querySelector('.pa-data-state-copy [role="alert"]')?.textContent).toBeTruthy()
      expect(state.querySelector('.pa-data-state-actions button')).toBeTruthy()
    })
  })
  it('recovers from a temporary error to a genuine empty school directory', async () => {
    let unavailable = true
    vi.stubGlobal('fetch', vi.fn(async (url: string) => unavailable ? response({}, 503) : response(emptyResponse(url))))
    mount('orgs')
    await screen.findByRole('alert')
    unavailable = false
    const buttons = screen.getAllByRole('button', { name: 'Tải lại' })
    fireEvent.click(buttons[buttons.length - 1])
    expect(await screen.findByText('Chưa có trường học')).toBeTruthy()
    expect(screen.queryByRole('alert')).toBeNull()
  })
  it('shows school statistics from the dedicated complete summary API', async () => {
    vi.stubGlobal('fetch', vi.fn(async (url: string) => response(url.includes('/organizations/summary')
      ? { total: 101, active: 100, paused: 1, disabled: 0, other: 0 }
      : { items: [], total: 101 })))
    mount('orgs')
    const statistics = await screen.findByRole('region', { name: 'Thống kê trường học' })
    await waitFor(() => expect(statistics.textContent).toContain('101'))
    expect(statistics.textContent).toContain('100')
    expect(statistics.textContent).toContain('1')
    expect(statistics.textContent).not.toContain('Chưa tải được thống kê')
  })
  it('renders a redacted audit entry without assuming actor or resource identifiers exist', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => response({ total: 1, items: [{ audit_id: 'audit-1', action: 'REVIEW', resource_type: 'private_resource', organization_id: 'platform', created_at: '2026-11-20T07:00:00Z', decision: 'allow' }] })))
    mount('audit')
    expect(await screen.findByText('private resource')).toBeTruthy()
    expect(screen.queryByRole('alert')).toBeNull()
  })
})
