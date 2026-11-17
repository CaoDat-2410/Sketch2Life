# FEAT-060 Plan revision 4 — implement approved classroom contracts

- **Status:** APPROVED by the project owner's direct instruction “implement” on 2026-10-24, recorded in `approvals/TASK_APPROVAL.md`.
- **Baseline:** existing dirty `dev` tree documented in `evidence/notes/IMPLEMENTATION_BASELINE_20261024.md`; preserve unrelated work.
- **Supersedes:** Plan Rev3 only for implementation gating of the already proposed room-code and shared-stage/completion contracts. FEAT-057, Modal deployment and production data gates remain.
- **Intent:** implement the owner-confirmed classroom behavior from SRS v3.3 B28 through versioned BE1 APIs and connect the corresponding UI without claiming unsupported stages are complete.

## Approved implementation scope

1. **Start boundary:** serialize session Start with admission; commit session activation and revocation of every still-pending device grant in one transaction; retain admitted grants. Refresh on a revoked request returns `revoked`.
2. **Shared room code:** add Teacher display/rotation and Child join APIs for the six-digit shared lobby code; cryptographic generation; HMAC digest only at rest; closed after Start; generic invalid/closed result; durable 10-invalid-attempt/source-IP/15-minute throttle. Do not trust forwarded-IP headers. Fail closed if the room-code HMAC key is not configured.
3. **Durable Teacher reload:** add authorized roster/group/turn reads using existing records, so browser storage is only a navigation hint and not the authority.
4. **Shared SRS stage:** add persisted ordered stage state, next-stage-only command with expected stage revision and idempotency receipt, Assistance disposition, and server rejection of rewind/skip. Persist a group draft before advance when unfinished work is declared. Preserve lifecycle as a separate state.
5. **Terminal outcome:** persist `completed` or `ended_early` separately from lifecycle `finished`; early stop requires one of `time|safety|technical|other`, note optional. Use durable idempotent command receipts.
6. **Clients:** connect the six-digit Child join and Teacher room-code/roster/stage/outcome controls to these contracts; keep AI, video, off-screen execution and any unsupported child-reflection/assessment workflow visibly blocked until its owning contract/card is implemented.
7. **Persistence:** add one additive BE1 migration on the documented `be1_core` lineage. Do not merge or edit the other Alembic module lineages.

## Acceptance criteria

- Successful Start atomically sets lifecycle active and revokes all pending grants; an unsuccessful/stale Start changes neither. Admitted grants survive.
- QR and numeric join reject new requests after Start. Multiple Child devices may use one active room code. Rotation invalidates the previous code. Raw code is returned only to an authorized Teacher operation and is absent from persisted state, audit, event, and error payloads.
- Persistent throttle enforces no more than 10 invalid attempts per trusted direct source IP in a rolling 15-minute window across processes; valid requests do not consume invalid-attempt quota. Invalid/closed/unknown code errors do not reveal which condition occurred.
- Teacher can reload current admitted roster, group assignments and turns from BE1 after client refresh.
- Stage starts at the first ordered stage, advances exactly one step per accepted command, cannot rewind or skip, rejects stale revisions, and repeated idempotency key/body returns its stored receipt. Key reuse with a different body conflicts.
- Any declared unfinished group included in advance has a durable `save_draft` record before the stage changes; no draft is marked complete.
- `completed` is accepted only at the final stage; `ended_early` records a required category and optional bounded note; both outcome writes are idempotent and separate from `finished` lifecycle.
- Additive migration upgrades/downgrades only BE1-owned additions on `be1_core`; automated backend, client, type/build/lint and focused synthetic-flow checks pass. Database-backed tests run where an isolated PostgreSQL test profile is available; otherwise the limitation is explicit.
- FEAT-057-dependent stages and Modal stay blocked without their owning approvals/configuration; no claim of full nine-stage production readiness or 40-child capacity is made.

## Execution order

1. Record this implementation addendum and hash; inspect the current model/migration lineage and only edit scoped BE1/FE files.
2. Add additive models/migration/schemas for room-code throttling, stage history/receipts, group draft disposition and terminal outcomes.
3. Implement and test transaction/authorization/idempotency behavior in BE1; add room-code and durable reload endpoints.
4. Wire Child and Teacher service/UI to those endpoints and remove unsupported local-success assumptions from these paths.
5. Run focused tests, UI build/typecheck/lint, backend checks, security validator, update traceability/status/evidence manifest.

## Risks and retained gates

- The direct source IP is `request.client.host`; deployment proxy topology must preserve the original trusted transport address. Forwarded headers are intentionally ignored. Deployment behind a proxy that masks clients requires reviewed proxy middleware/configuration before enabling the numeric route.
- HMAC key provisioning and rotation are runtime operations; no secret is stored in the repo. Numeric room-code endpoints fail closed if the key is missing.
- Existing database may not yet be upgraded to this migration. The application must report persistence unavailable until the BE1 migration is applied; no live DB migration is authorized here.
- PostgreSQL-specific atomic rate limiting and row locks need isolated PostgreSQL verification; SQLite/unit checks are not a substitute.
- FEAT-057 cross-lane adoption, Modal deployment/profile/spend cap, artifact-storage/retention approvals, OD07 rewind policy, school metadata, deployment, commit and push remain outside this addendum.
