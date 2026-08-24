# Contracts and integration rules

## Single source of truth

Backend contracts are authoritative for session/job/artifact identity. Mobile types are generated or derived from versioned schemas; they are not independently redefined by screen code.

## Contract envelope

Every async command/result should carry, as applicable:

- `contract_name` and `contract_version`
- `session_id` and `expected_session_version`
- `artifact_id` and `artifact_version`
- `source_artifact_ids[]`
- `created_at`
- `provenance` (model/config/actor/reason where relevant)

## Integration checkpoints

1. Contract review before feature implementation.
2. Fixture round-trip between backend and mobile.
3. Stale-version and failure/fallback tests.
4. One vertical slice before parallel expansion.
5. E2E evidence attached to the feature that owns the behavior.

## MVP progress contract

- Mobile polls a versioned backend job resource, not a provider endpoint.
- Polling starts at roughly 2 seconds, backs off to at most 10 seconds, uses ETag/job version where available, and stops on terminal state.
- The client pauses or greatly reduces polling while backgrounded and handles retry-after/back-pressure responses.
- Switching to SSE or WebSocket requires measured latency/load need and an ADR update; contract semantics must remain transport-independent.

## Forbidden shortcuts

- Mobile code directly querying the database.
- Mobile code calling Lightning/Runpod/S3 or containing provider credentials/endpoints.
- Mobile or backend product code using Firebase Storage, Firestore, or Realtime Database.
- FastAPI routers directly calling model SDKs.
- Workers mutating session rows without an application completion command.
- Screen navigation treated as Gate A/B approval.
- Shared mutable files used as an implicit cross-feature data store.
