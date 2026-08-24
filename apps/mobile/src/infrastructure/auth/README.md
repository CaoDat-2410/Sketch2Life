# Managed authentication boundary

The initial adapter will use Firebase Authentication only. Screens and feature view-models depend on `AuthSessionPort`; they do not import Firebase directly.

Explicitly forbidden in the mobile app:

- Firebase Storage, Firestore, and Realtime Database;
- direct S3 access or embedded bucket credentials;
- persisting ID tokens in plain AsyncStorage or logs;
- using client role state as backend authorization.

The client sends a fresh Firebase ID token to the Sketch2Life backend over HTTPS. The backend verifies the token and applies its own authorization policy. Product media and artifacts are uploaded through backend-issued workflows and stored by the backend's S3-compatible adapter.
