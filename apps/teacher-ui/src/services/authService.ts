import { getApp, getApps, initializeApp } from 'firebase/app'
import {
  getAuth,
  EmailAuthProvider,
  connectAuthEmulator,
  onAuthStateChanged,
  reauthenticateWithCredential,
  sendPasswordResetEmail,
  signInWithEmailAndPassword,
  signOut,
  updatePassword,
  type User,
} from 'firebase/auth'

const emulatorConnectedAuth = new WeakSet<ReturnType<typeof getAuth>>()

function configuredAuth() {
  const config = {
    apiKey: import.meta.env.VITE_FIREBASE_API_KEY,
    authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN,
    projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID,
    appId: import.meta.env.VITE_FIREBASE_APP_ID,
  }
  if (Object.values(config).some((value) => typeof value !== 'string' || !value.trim())) {
    throw new Error('Firebase Authentication is not configured for this app.')
  }
  const app = getApps().length ? getApp() : initializeApp(config)
  const auth = getAuth(app)
  const emulatorUrl = import.meta.env.VITE_FIREBASE_AUTH_EMULATOR_URL?.trim()
  if (emulatorUrl && !emulatorConnectedAuth.has(auth)) {
    connectAuthEmulator(auth, emulatorUrl, { disableWarnings: true })
    emulatorConnectedAuth.add(auth)
  }
  return auth
}

export const authService = {
  login: async (credentials: { email: string; pass: string }) => {
    const result = await signInWithEmailAndPassword(
      configuredAuth(),
      credentials.email.trim(),
      credentials.pass,
    )
    return result.user
  },
  logout: async () => {
    const auth = configuredAuth()
    if (auth.currentUser) await signOut(auth)
  },
  getAccountRole: async (): Promise<string> => {
    const auth = configuredAuth()
    const user = auth.currentUser
    const baseUrl = import.meta.env.VITE_BE1_BASE_URL?.trim()
    if (!user) throw new Error('Sign in to continue.')
    if (!baseUrl) throw new Error('Set VITE_BE1_BASE_URL before connecting the account service.')
    const response = await fetch(`${baseUrl.replace(/\/+$/, '')}/api/auth/v1/me`, {
      headers: { Authorization: `Bearer ${await user.getIdToken()}`, Accept: 'application/json' },
      signal: AbortSignal.timeout(15_000),
    })
    const body = await response.json().catch(() => null) as { role?: unknown; message?: unknown } | null
    if (!response.ok || typeof body?.role !== 'string') {
      throw new Error(typeof body?.message === 'string' ? body.message : 'Không xác minh được vai trò tài khoản.')
    }
    return body.role
  },
  resetPassword: async (email: string) => {
    await sendPasswordResetEmail(configuredAuth(), email.trim())
  },
  changePassword: async (currentPassword: string, newPassword: string) => {
    const user = configuredAuth().currentUser
    if (!user?.email) throw new Error('Đăng nhập lại để đổi mật khẩu.')
    const credential = EmailAuthProvider.credential(user.email, currentPassword)
    await reauthenticateWithCredential(user, credential)
    await updatePassword(user, newPassword)
  },
  getIdToken: async (): Promise<string> => {
    const user = configuredAuth().currentUser
    if (!user) throw new Error('Sign in with a school account before using BE1.')
    return user.getIdToken()
  },
  getCurrentUser: (): User | null => {
    try {
      return configuredAuth().currentUser
    } catch {
      return null
    }
  },
  observe: (callback: (user: User | null) => void) => {
    try {
      return onAuthStateChanged(configuredAuth(), callback)
    } catch {
      callback(null)
      return () => undefined
    }
  },
}
