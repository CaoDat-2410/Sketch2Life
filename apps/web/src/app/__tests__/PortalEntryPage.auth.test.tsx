import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { PortalEntryPage } from '../PortalEntryPage'
import { PortalSessionProvider } from '../../shared/auth/PortalSessionContext'
import { apiBaseUrl, configuredOrganizationId, type FirebaseAuthBridge } from '../../shared/api/backendApi'
import { resolveBackendRuntimeConfig } from '../../shared/api/backendRuntimeConfig'

function jsonResponse(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

function renderLogin(state?: unknown) {
  return render(
    <PortalSessionProvider>
      <MemoryRouter initialEntries={[{ pathname: '/login', search: '?role=manager', state }]}>
        <Routes>
          <Route path="/login" element={<PortalEntryPage />} />
          <Route path="/school" element={<main>Manager portal</main>} />
          <Route path="/school/classes" element={<main>Manager classes</main>} />
        </Routes>
      </MemoryRouter>
    </PortalSessionProvider>,
  )
}

describe('School Manager login auth API flow', () => {
  let accountRole: string
  let accountStatus: number
  let assignments: Array<{ role: string; class_id: string | null }>
  let authBridge: FirebaseAuthBridge
  let fetchMock: ReturnType<typeof vi.fn>

  beforeEach(() => {
    accountRole = 'school_manager'
    accountStatus = 200
    assignments = [{ role: 'school_admin', class_id: null }]
    window.sessionStorage.clear()
    window.sketch2lifeConfig = {
      apiBaseUrl: 'https://api.example.test',
      organizationId: 'org-manager-test',
    }
    authBridge = {
      signIn: vi.fn(async () => undefined),
      getIdToken: vi.fn(async () => 'unit-test-id-token'),
      signOut: vi.fn(async () => undefined),
    }
    window.sketch2lifeAuth = authBridge

    fetchMock = vi.fn(async (input: RequestInfo | URL, _init?: RequestInit) => {
      const path = new URL(String(input)).pathname
      if (path === '/api/auth/v1/me') {
        return jsonResponse({ role: accountRole, state: 'active', role_revision: 1 }, accountStatus)
      }
      if (path === '/api/be1/v1/organizations/org-manager-test/me') {
        return jsonResponse({
          contract: 'Be1AdultAssignmentsV1',
          subject: 'manager-test-subject',
          organization_id: 'org-manager-test',
          assignments,
        })
      }
      return jsonResponse({ detail: { code: 'NOT_FOUND', message: 'Not found' } }, 404)
    })
    vi.stubGlobal('fetch', fetchMock)
  })

  afterEach(() => {
    cleanup()
    vi.unstubAllGlobals()
    vi.restoreAllMocks()
    window.sessionStorage.clear()
    delete window.sketch2lifeConfig
    delete window.sketch2lifeAuth
  })

  it('uses the documented BE1 environment variables as runtime fallbacks', () => {
    expect(resolveBackendRuntimeConfig({
      VITE_BE1_BASE_URL: 'https://api.example.test',
      VITE_BE1_ORGANIZATION_ID: 'org-manager-test',
    }, {})).toEqual({
      apiBaseUrl: 'https://api.example.test',
      organizationId: 'org-manager-test',
    })
  })

  function submitManagerCredentials() {
    fireEvent.change(screen.getByLabelText('Email tài khoản'), {
      target: { value: 'manager@example.test' },
    })
    fireEvent.change(screen.getByLabelText('Mật khẩu'), {
      target: { value: 'unit-test-only-password' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Đăng nhập' }))
  }

  it('signs in, resolves backend role and organization assignment, then opens Manager', async () => {
    expect(apiBaseUrl()).toBe('https://api.example.test')
    expect(configuredOrganizationId()).toBe('org-manager-test')
    renderLogin()
    submitManagerCredentials()

    expect(await screen.findByText('Manager portal')).toBeTruthy()
    expect(authBridge.signIn).toHaveBeenCalledWith('manager@example.test', 'unit-test-only-password')
    expect(window.sessionStorage.getItem('s2l-web-role')).toBe('MANAGER')

    const requests = fetchMock.mock.calls.map(([input, init]) => ({
      path: new URL(String(input)).pathname,
      authorization: new Headers(init?.headers).get('Authorization'),
    }))
    expect(requests.map((request) => request.path)).toEqual([
      '/api/auth/v1/me',
      '/api/be1/v1/organizations/org-manager-test/me',
      '/api/auth/v1/me',
    ])
    expect(fetchMock.mock.calls.map(([input]) => new URL(String(input)).origin)).toEqual([
      'https://api.example.test',
      'https://api.example.test',
      'https://api.example.test',
    ])
    expect(requests.every((request) => request.authorization === 'Bearer unit-test-id-token')).toBe(true)
  })

  it('returns to the requested Manager page after login', async () => {
    renderLogin({ from: { pathname: '/school/classes', search: '?view=active' } })
    submitManagerCredentials()

    expect(await screen.findByText('Manager classes')).toBeTruthy()
  })

  it('rejects a non-Manager backend role and signs Firebase back out', async () => {
    accountRole = 'teacher'
    renderLogin()
    submitManagerCredentials()

    expect((await screen.findByRole('alert')).textContent).toContain('Tài khoản này không có quyền xem hoặc sửa dữ liệu.')
    expect(authBridge.signOut).toHaveBeenCalledOnce()
    expect(fetchMock).toHaveBeenCalledOnce()
    expect(window.sessionStorage.getItem('s2l-web-role')).toBeNull()
    expect(screen.queryByText('Manager portal')).toBeNull()
  })

  it('rejects a Manager without the required organization assignment', async () => {
    assignments = [{ role: 'teacher', class_id: null }]
    renderLogin()
    submitManagerCredentials()

    expect((await screen.findByRole('alert')).textContent).toContain('Tài khoản này không có quyền xem hoặc sửa dữ liệu.')
    expect(authBridge.signOut).toHaveBeenCalledOnce()
    expect(fetchMock).toHaveBeenCalledTimes(2)
    expect(window.sessionStorage.getItem('s2l-web-role')).toBeNull()
    expect(screen.queryByText('Manager portal')).toBeNull()
  })

  it('rejects an auth API failure and does not request organization assignments', async () => {
    accountStatus = 401
    renderLogin()
    submitManagerCredentials()

    expect((await screen.findByRole('alert')).textContent).toContain('Phiên đăng nhập không hợp lệ hoặc đã hết hạn. Đăng nhập lại.')
    expect(authBridge.signOut).toHaveBeenCalledOnce()
    expect(fetchMock).toHaveBeenCalledOnce()
    expect(window.sessionStorage.getItem('s2l-web-role')).toBeNull()
    expect(screen.queryByText('Manager portal')).toBeNull()
  })
})
