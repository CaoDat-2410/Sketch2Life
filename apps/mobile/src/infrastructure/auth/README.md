# Managed authentication boundary

The current adapter uses Firebase Authentication REST endpoints only. Screens and feature view-models depend on `AuthSessionPort`; they do not import Firebase directly.

Public client settings come from the repository-root `.env` using `VITE_FIREBASE_API_KEY`, `VITE_FIREBASE_AUTH_DOMAIN`, `VITE_FIREBASE_PROJECT_ID`, and `VITE_FIREBASE_APP_ID`. `apps/mobile/babel.config.js` reads that one file and inlines only those four allow-listed client values. Restart Metro after changing the root `.env`.

The ID and refresh tokens remain in memory for the current app process. They are not written to AsyncStorage or logs; after the process is cleared, the adult signs in again. Sign-up creates the Firebase Authentication identity through the backend registration API, which assigns the Parent role server-side. Parent and child profile creation remain separate capabilities.

Explicitly forbidden in the mobile app:

- Firebase Storage, Firestore, and Realtime Database;
- direct S3 access or embedded bucket credentials;
- persisting ID tokens in plain AsyncStorage or logs;
- using client role state as backend authorization.

The client sends a fresh Firebase ID token to the Sketch2Life backend over HTTPS. The backend verifies the token and applies its own authorization policy. Product media and artifacts are uploaded through backend-issued workflows and stored by the backend's S3-compatible adapter.
