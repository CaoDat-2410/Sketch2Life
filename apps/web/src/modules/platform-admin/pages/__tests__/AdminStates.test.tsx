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
    expect(screen.queryByRole('button', { name: 'Trước' })).toBeNull()
    expect(screen.queryByRole('button', { name: 'Tiếp' })).toBeNull()
    if (panel === 'queues') {
      expect(screen.getByText('Chưa có bản ghi công việc AI')).toBeTruthy()
      expect(screen.queryByText('Chưa có bản ghi công việc ai')).toBeNull()
    } else {
      expect(container.querySelector('.s2l-empty-state')).toBeTruthy()
    }
  })
  it.each(panels)('%s keeps an API failure distinct from an empty dataset and offers retry', async panel => {
    vi.stubGlobal('fetch', vi.fn(async () => response({ code: 'PROVIDER_UNAVAILABLE' }, 503)))
    const { container } = mount(panel)
    expect((await screen.findAllByRole('alert')).length).toBeGreaterThan(0)
    expect(screen.getAllByText('Không tải được dữ liệu').length).toBeGreaterThan(0)
    expect(screen.getAllByRole('button', { name: 'Tải lại' }).length).toBeGreaterThan(0)
    expect(screen.queryByText('Chưa có dữ liệu')).toBeNull()
    const errorStates = container.querySelectorAll('.s2l-admin-load-error')
    expect(errorStates.length).toBeGreaterThan(0)
    errorStates.forEach(state => {
      expect(state.querySelector('h2')?.textContent).toBe('Không tải được dữ liệu')
      expect(state.querySelector('[role="alert"]')?.textContent).toBeTruthy()
      expect(state.querySelector('button')).toBeTruthy()
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
    expect(await screen.findByText('Tài nguyên khác')).toBeTruthy()
    expect(screen.queryByText('private_resource')).toBeNull()
    expect(screen.queryByRole('alert')).toBeNull()
  })

  it('uses Vietnamese labels for audit history and retention guidance', async () => {
    vi.stubGlobal('fetch', vi.fn(async (input: RequestInfo | URL) => {
      const url = typeof input === 'string' ? input : input instanceof URL ? input.href : input.url;
      if (url.endsWith('/audit/retention/preview')) return response({ retention_days: 365, policy_revision: 2, cutoff: '2025-11-20T07:00:00Z', candidate_count: 0, batch_count: 0, batch_limit: 100, oldest_candidate_at: null });
      if (url.endsWith('/audit/retention')) return response({ retention_days: 365, revision: 2, total_entries: 12, eligible_count: 0, oldest_entry_at: null, newest_entry_at: null, last_purged_at: null, last_purged_count: 0 });
      if (url.endsWith('/audit')) return response({ items: [], total: 0, next_cursor: null });
      return response(emptyResponse(url));
    }));
    const view = mount('audit');

    fireEvent.click(await screen.findByText(/Chính sách lưu nhật ký/, { selector: 'summary' }));
    expect(await screen.findByText('Tổng nhật ký')).toBeTruthy();
    fireEvent.click(await screen.findByRole('button', { name: 'Xem trước bản ghi đến hạn' }));
    expect(await screen.findByText('Chưa có nhật ký đến hạn')).toBeTruthy();
    expect(view.container.textContent).not.toMatch(/\baudit\b/i);
  })

  it('labels known class audit actions and uses a generic label for unknown actions', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => response({ total: 3, items: [
      { audit_id: 'archive-1', action: 'class.archive', resource_type: 'class', organization_id: 'org-1', created_at: '2026-11-20T07:00:00Z' },
      { audit_id: 'suspend-1', action: 'class.suspend', resource_type: 'class', organization_id: 'org-1', created_at: '2026-11-20T07:01:00Z' },
      { audit_id: 'unknown-1', action: 'UNRECOGNIZED_PRIVATE_CODE', resource_type: 'class', organization_id: 'org-1', created_at: '2026-11-20T07:02:00Z' },
    ] })))
    mount('audit')
    expect(await screen.findByText('Lưu trữ lớp')).toBeTruthy()
    expect(screen.getByText('Tạm ngưng lớp')).toBeTruthy()
    expect(screen.getByText('Hoạt động quản trị')).toBeTruthy()
    expect(screen.queryByText('UNRECOGNIZED_PRIVATE_CODE')).toBeNull()
  })

  it('labels backend lesson, data request and class actions and resources in Vietnamese', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => response({ total: 5, items: [
      { audit_id: 'lesson-1', action: 'lesson.create', resource_type: 'lesson', organization_id: 'org-1', created_at: '2026-11-20T07:00:00Z' },
      { audit_id: 'grant-1', action: 'lesson.access_grant.create', resource_type: 'lesson_access_grant', organization_id: 'org-1', created_at: '2026-11-20T07:01:00Z' },
      { audit_id: 'request-1', action: 'data_request.export', resource_type: 'data_request', organization_id: 'org-1', created_at: '2026-11-20T07:02:00Z' },
      { audit_id: 'class-1', action: 'class.create', resource_type: 'class', organization_id: 'org-1', created_at: '2026-11-20T07:03:00Z' },
      { audit_id: 'class-2', action: 'class.archive', resource_type: 'class', organization_id: 'org-1', created_at: '2026-11-20T07:04:00Z' },
    ] })))
    mount('audit')

    expect(await screen.findByText('Tạo bài học')).toBeTruthy()
    expect(screen.getByText('Cấp quyền truy cập bài học')).toBeTruthy()
    expect(screen.getByText('Yêu cầu xuất dữ liệu')).toBeTruthy()
    expect(screen.getByText('Tạo lớp học')).toBeTruthy()
    expect(screen.getByText('Lưu trữ lớp')).toBeTruthy()
    expect(screen.getByText('Bài học')).toBeTruthy()
    expect(screen.getByText('Quyền truy cập bài học')).toBeTruthy()
    expect(screen.getByText('Yêu cầu dữ liệu')).toBeTruthy()
    expect(screen.getAllByText('Lớp học')).toHaveLength(2)

    expect(screen.queryByRole('option', { name: 'Tạo bài học' })).toBeNull()
    expect(screen.queryByRole('option', { name: 'Yêu cầu xuất dữ liệu' })).toBeNull()
  })

  it('labels every data request type in the lifecycle table in Vietnamese', async () => {
    vi.stubGlobal('fetch', vi.fn(async (input: RequestInfo | URL) => {
      const url = typeof input === 'string' ? input : input instanceof URL ? input.href : input.url
      if (url.includes('/lifecycle')) return response({ total: 2, next_cursor: null, items: [
        { request_id: 'request-export', request_type: 'export', organization_id: 'org-1', state: 'requested', unresolved_items: 0, created_at: '2026-11-25T00:00:00Z', completed_at: null },
        { request_id: 'request-delete', request_type: 'delete', organization_id: 'org-1', state: 'requested', unresolved_items: 0, created_at: '2026-11-25T00:00:00Z', completed_at: null },
      ] })
      return response(emptyResponse(url))
    }))
    mount('lifecycle')

    expect(await screen.findByText('Xuất dữ liệu')).toBeTruthy()
    expect(screen.getByText('Xóa dữ liệu')).toBeTruthy()
    expect(screen.queryByText('export')).toBeNull()
    expect(screen.queryByText('delete')).toBeNull()
  })

  it('keeps the selected audit action value unchanged in the server filter', async () => {
    const requestedUrls: string[] = []
    vi.stubGlobal('fetch', vi.fn(async (input: RequestInfo | URL) => {
      const url = typeof input === 'string' ? input : input instanceof URL ? input.href : input.url
      requestedUrls.push(url)
      return response({ items: [], total: 0, next_cursor: null })
    }))
    mount('audit')
    fireEvent.click(screen.getByRole('combobox', { name: 'Lọc theo thao tác' }))
    fireEvent.click(await screen.findByRole('option', { name: 'Thêm trường học' }))

    await waitFor(() => expect(requestedUrls.some((url) => new URL(url, 'http://localhost').searchParams.get('action') === 'ORGANIZATION_CREATED')).toBe(true))
  })
})
