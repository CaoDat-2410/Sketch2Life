# Managed authentication security guide

## Boundary

```text
Android Firebase Auth adapter
  | ID token over HTTPS
  v
FastAPI authentication dependency
  | IdentityTokenVerifier port
  v
Firebase verification adapter
  | VerifiedPrincipal
  v
Application authorization policy
```

Firebase proves identity; Sketch2Life decides authorization. The backend must never accept a client-supplied role, `uid`, child/guardian relationship, or navigation mode without verified server-side policy.

Only parent/guide users authenticate. Child mode runs inside an authorized supervised session and never creates or stores a separate child login credential. Initial sign-in methods are Google Sign-In and email/password.

## Firebase scope

Allowed:

- Firebase Authentication client SDK;
- Firebase Admin token verification in backend infrastructure;
- Firebase Authentication Emulator for local fixture tests;
- minimal custom claims only when a separately approved role model requires them.

Forbidden:

- Firebase Storage;
- Firestore or Realtime Database;
- Firebase-hosted session/product state;
- service-account JSON in source control/mobile bundles;
- plain-text ID/refresh tokens in logs or AsyncStorage.

All media and artifact persistence goes through the backend's S3-compatible object-storage port. Authentication configuration must not include a Firebase storage bucket.

## Verification requirements

- Verify signature, `kid`, issuer, audience/project ID, expiry, issued-at, subject, and auth time.
- Check revocation for sensitive operations and after account/role changes.
- Cache public verification keys according to their cache headers; do not cache accepted user tokens indefinitely.
- Map provider exceptions to generic `401`/`403` responses without leaking token contents.
- Keep authorization policy in application/domain services, not FastAPI route conditionals or mobile screens.
- Audit privileged changes using stable internal principal IDs; redact email, token, and child data.

## Environment rules

- Local/test may use development identities or Firebase Auth Emulator fixtures.
- Staging/production require Firebase Authentication and an explicit project ID.
- Service credentials are runtime secret references; use workload identity where hosting supports it.
- Production must enable appropriate provider protections, quota alerts, account recovery, and least-privilege administrator access.
