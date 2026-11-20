import { afterEach, beforeEach, expect, it, vi } from 'vitest'
import { cleanup, render, screen, waitFor } from '@testing-library/react'
import { backendApi, BackendApiError } from '../api/backendApi'
import { PortalSessionProvider, usePortalSession } from './PortalSessionContext'

function SessionProbe() {
  const { isAuthenticated } = usePortalSession()
  return <span>{isAuthenticated ? 'signed-in' : 'signed-out'}</span>
}

beforeEach(() => {
  sessionStorage.setItem('s2l-web-role', 'ADMIN')
  sessionStorage.setItem('s2l-web-authenticated', 'true')
  sessionStorage.setItem('s2l-web-session-source', 'firebase-role-verified-v1')
  window.sketch2lifeAuth = {
    signIn: vi.fn(async () => undefined),
    signOut: vi.fn(async () => undefined),
    getIdToken: vi.fn(async () => 'test-token'),
  }
})

afterEach(() => {
  cleanup()
  sessionStorage.clear()
  delete window.sketch2lifeAuth
  vi.restoreAllMocks()
})

it('clears the local session when the server revokes its role', async () => {
  vi.spyOn(backendApi, 'accountRole').mockResolvedValue({ role: 'teacher' })
  render(<PortalSessionProvider><SessionProbe /></PortalSessionProvider>)
  await screen.findByText('signed-out')
  expect(sessionStorage.getItem('s2l-web-authenticated')).toBeNull()
  expect(window.sketch2lifeAuth?.signOut).toHaveBeenCalledOnce()
})

it('clears a session rejected by the server', async () => {
  vi.spyOn(backendApi, 'accountRole').mockRejectedValue(new BackendApiError('Expired', 'UNAUTHORIZED', 401))
  render(<PortalSessionProvider><SessionProbe /></PortalSessionProvider>)
  await screen.findByText('signed-out')
})

it('keeps the session during a network outage', async () => {
  const check = vi.spyOn(backendApi, 'accountRole').mockRejectedValue(new BackendApiError('Offline', 'NETWORK_ERROR', 0))
  render(<PortalSessionProvider><SessionProbe /></PortalSessionProvider>)
  await waitFor(() => expect(check).toHaveBeenCalledOnce())
  expect(screen.getByText('signed-in')).toBeTruthy()
  expect(window.sketch2lifeAuth?.signOut).not.toHaveBeenCalled()
})
