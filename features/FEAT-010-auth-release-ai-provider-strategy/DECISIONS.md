# FEAT-010 decisions

- Use Firebase Authentication as the managed identity provider, behind provider-neutral mobile/backend ports.
- Do not use Firebase Storage, Firestore, Realtime Database, or Firebase-hosted product state.
- Store artifacts through the backend's S3-compatible object-storage port.
- Build debug/signed APKs for device/internal testing; publish a signed AAB to Google Play later.
- Lightning AI is fixture-only development infrastructure on the current personal account.
- Runpod Serverless queue endpoints are the production AI target; use endpoint-scoped restricted keys.
- AI provider and object-storage credentials exist only in backend/worker runtime secret stores.
- Cross-feature rationale is recorded in `docs/adr/ADR-0005-auth-release-and-ai-provider-strategy.md`.
