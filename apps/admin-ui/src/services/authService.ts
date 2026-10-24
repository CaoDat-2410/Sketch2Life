import { getApp, getApps, initializeApp } from 'firebase/app'
import {
  getAuth,
  onAuthStateChanged,
  signInWithEmailAndPassword,
  signOut,
  type User,
} from 'firebase/auth'

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
  return getAuth(app)
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
  getIdToken: async (): Promise<string> => {
    const user = configuredAuth().currentUser
    if (!user) throw new Error('Sign in with a school administrator account before using BE1.')
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
