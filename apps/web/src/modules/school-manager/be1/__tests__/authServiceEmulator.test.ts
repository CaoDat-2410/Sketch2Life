import { beforeEach, describe, expect, it, vi } from 'vitest'

const firebaseMocks = vi.hoisted(() => {
  const app = { name: '[DEFAULT]' }
  const auth = { currentUser: null, authStateReady: vi.fn() }
  return {
    app,
    auth,
    connectAuthEmulator: vi.fn(),
    getApp: vi.fn(() => app),
    getApps: vi.fn(() => [app]),
    getAuth: vi.fn(() => auth),
    initializeApp: vi.fn(() => app),
  }
})

vi.mock('firebase/app', () => ({
  getApp: firebaseMocks.getApp,
  getApps: firebaseMocks.getApps,
  initializeApp: firebaseMocks.initializeApp,
}))

vi.mock('firebase/auth', () => ({
  connectAuthEmulator: firebaseMocks.connectAuthEmulator,
  getAuth: firebaseMocks.getAuth,
  EmailAuthProvider: { credential: vi.fn() },
  onAuthStateChanged: vi.fn(() => vi.fn()),
  reauthenticateWithCredential: vi.fn(),
  signInWithEmailAndPassword: vi.fn(),
  signOut: vi.fn(),
  updatePassword: vi.fn(),
}))

const servicePath = '../services/authService'

async function loadAuthService() {
  return import(servicePath)
}

function setFirebaseConfig(apiKey = 'test-api-key') {
  vi.stubEnv('VITE_FIREBASE_API_KEY', apiKey)
  vi.stubEnv('VITE_FIREBASE_AUTH_DOMAIN', 'test.firebaseapp.com')
  vi.stubEnv('VITE_FIREBASE_PROJECT_ID', 'test-project')
  vi.stubEnv('VITE_FIREBASE_APP_ID', 'test-app')
}

describe('Firebase Auth Emulator configuration', () => {
  beforeEach(() => {
    vi.resetModules()
    vi.unstubAllEnvs()
    vi.clearAllMocks()
    firebaseMocks.getApps.mockReturnValue([firebaseMocks.app])
    vi.stubEnv('DEV', true)
    vi.stubEnv('VITE_FIREBASE_AUTH_EMULATOR_URL', '')
    setFirebaseConfig()
  })

  it('does not connect when the optional URL is unset', async () => {
    const { authService } = await loadAuthService()

    authService.getCurrentUser()

    expect(firebaseMocks.connectAuthEmulator).not.toHaveBeenCalled()
  })

  it('connects once in dev and reuses the same auth instance', async () => {
    vi.stubEnv('VITE_FIREBASE_AUTH_EMULATOR_URL', 'http://127.0.0.1:9099')
    const { authService } = await loadAuthService()

    authService.getCurrentUser()
    authService.getCurrentUser()

    expect(firebaseMocks.connectAuthEmulator).toHaveBeenCalledTimes(1)
    expect(firebaseMocks.connectAuthEmulator).toHaveBeenCalledWith(
      firebaseMocks.auth,
      'http://127.0.0.1:9099',
      { disableWarnings: true },
    )
  })

  it('does not connect in production even when the URL is set', async () => {
    vi.stubEnv('DEV', false)
    vi.stubEnv('VITE_FIREBASE_AUTH_EMULATOR_URL', 'http://localhost:9099')
    const { authService } = await loadAuthService()

    authService.getCurrentUser()

    expect(firebaseMocks.connectAuthEmulator).not.toHaveBeenCalled()
  })

  it.each([
    'https://localhost:9099',
    'http://example.test:9099',
    'junk',
  ])('rejects invalid emulator URL %s without logging its value', async (value) => {
    vi.stubEnv('VITE_FIREBASE_AUTH_EMULATOR_URL', value)
    const warning = vi.spyOn(console, 'warn').mockImplementation(() => undefined)
    const { authService } = await loadAuthService()

    authService.getCurrentUser()

    expect(firebaseMocks.connectAuthEmulator).not.toHaveBeenCalled()
    expect(warning).toHaveBeenCalledTimes(1)
    expect(warning.mock.calls[0]?.[0]).not.toContain(value)
    warning.mockRestore()
  })

  it('uses the fake API key only when the dev emulator is enabled and the key is empty', async () => {
    vi.stubEnv('VITE_FIREBASE_AUTH_EMULATOR_URL', 'http://localhost:9099')
    setFirebaseConfig('')
    firebaseMocks.getApps.mockReturnValue([])
    const { authService } = await loadAuthService()

    authService.getCurrentUser()

    expect(firebaseMocks.initializeApp).toHaveBeenCalledWith(expect.objectContaining({ apiKey: 'fake-api-key' }))
    expect(firebaseMocks.connectAuthEmulator).toHaveBeenCalledTimes(1)
  })

  it('does not use the fake API key when the emulator is disabled', async () => {
    setFirebaseConfig('')
    const { authService } = await loadAuthService()

    expect(authService.getCurrentUser()).toBeNull()

    expect(firebaseMocks.initializeApp).not.toHaveBeenCalled()
    expect(firebaseMocks.connectAuthEmulator).not.toHaveBeenCalled()
  })
})
