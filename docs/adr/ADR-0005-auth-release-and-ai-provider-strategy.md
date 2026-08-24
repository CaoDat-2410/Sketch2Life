# ADR-0005: Authentication, Android release, and AI provider strategy

- Status: ACCEPTED
- Date: 2026-08-24
- Owner: Sketch2Life project owner
- Refines: ADR-0003 and ADR-0004

## Context

The owner wants installable APKs before public Google Play release, managed authentication without Firebase-hosted storage, S3 artifact storage, Lightning AI development on a normal low-credit account, and Runpod production inference.

## Decision

### Android distribution

- Use debug APKs only for developer/device smoke tests.
- Before distributing a non-debug APK, create and safely back up a production upload/signing key; never reuse the template debug key.
- Keep `com.sketch2life.mobile` unchanged.
- Produce a release AAB for Google Play. Progress through Play internal/closed testing before public production.
- Preserve key ownership evidence because off-Play installation before Play registration can require package/key ownership proof.
- The project owner is the accountable Firebase/Google Play and release/upload-key custodian.

### Managed authentication

- Select Firebase Authentication as the initial identity provider.
- Authenticate parent/guide users with Google Sign-In and email/password. Child mode has no independent child account.
- Mobile obtains a Firebase ID token and sends it to the Sketch2Life backend over HTTPS.
- Backend verifies token signature, issuer, audience, expiry, and revocation through an infrastructure adapter, then maps accepted claims to a provider-neutral `VerifiedPrincipal`.
- Backend authorization remains authoritative. Child/parent/guide role mode in the client is not an authorization decision.
- Firebase Storage, Firestore, and Realtime Database are forbidden. Product media, derivatives, provenance, and session state remain in backend-owned PostgreSQL/S3-compatible systems.

### AI providers

- Lightning AI is a fixture-only development provider while the project uses a normal account/credit balance. It is not treated as private networking.
- Production AI uses a Runpod Serverless queue endpoint behind the existing `AiGateway` port.
- Use a restricted Runpod API key scoped to the selected endpoint and stored only in the backend/worker runtime secret manager.
- Mobile never receives provider URLs/keys and never calls Lightning or Runpod directly.
- S3 artifacts are exchanged by short-lived references or backend-controlled transfer; permanent S3 credentials are never sent in a job payload.

## Consequences

- Firebase and AI provider SDKs remain infrastructure adapters and can be replaced without changing domain/application rules.
- A Firebase project and Android configuration file are still required before auth integration; they are not generated in this setup feature.
- Lightning testing must remain fixture-only because the current account cannot guarantee the earlier private-network goal.
- Runpod's queue/status semantics align with bounded backend polling, but its provider job ID is mapped to an internal job ID.

## Evidence

- [Android App Bundles](https://developer.android.com/guide/app-bundle)
- [Firebase ID-token verification](https://firebase.google.com/docs/auth/admin/verify-id-tokens)
- [Runpod Serverless endpoints](https://docs.runpod.io/serverless/endpoints/overview)
- [Runpod restricted API keys](https://docs.runpod.io/get-started/api-keys)
- Feature record: `features/FEAT-010-auth-release-ai-provider-strategy/`
