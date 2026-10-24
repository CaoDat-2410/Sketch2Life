# Feature context

## Current authorization and status (2026-10-24)

The project owner directly approved local implementation of FEAT-060 Plan Rev4, SHA-256 `61ECCDA79033BA5EBDE15FBA22B553B9D92C6947D2B224D5BA0EC686E984C11D`. Rev4 adds the owner-confirmed BE1 classroom contracts, additive BE1 migration, and Child/Teacher connections. The preserved baseline is `dev@0a7ce768c153f2104cff930569c3eda6e484532c` with the dirty tree recorded in `evidence/notes/IMPLEMENTATION_BASELINE_20261024.md` and `evidence/raw/implementation-baseline-20261024/`.

### Rev4 implementation boundary

- Implemented locally: shared six-digit Lobby code (only HMAC stored), persistent invalid-attempt throttle, QR/code closure and pending-grant revocation at Start, device join-status endpoint, Teacher roster/stage/outcome reads, ordered stage transitions with idempotency receipts, `save_draft`, SRS guards, and `completed`/`ended_early` outcome write. Child/Teacher runtime screens call these BE1 routes.
- Added Alembic revision `20261024_0005` on the BE1 `be1_core` chain. It does not consolidate the eight other existing Alembic heads.
- Not verified against PostgreSQL: the test suite requires `BE1_TEST_DATABASE_URL`, which is not configured in this workspace. UIs use mocked transport in tests. No live migration, Firebase login, physical-device join, proxy deployment, or Modal request was performed.
- Remaining product contracts: BE2 assistance, knowledge media, off-screen activity and child reflection are blocked; later-stage advance guards fail closed until those contracts are adopted. Completion outcome is separate from lifecycle `finished`, but an approved product-wide completion snapshot is not yet implemented.

Rev4 checks: Child `npm run check` passed (typecheck/build/lint and 18 suites/26 tests); Teacher `npm run check` passed (build/lint and 3 suites/6 tests); focused backend passed 22 tests and skipped four PostgreSQL cases because `BE1_TEST_DATABASE_URL` is unset; changed backend files pass Ruff and Alembic offline SQL generation passed. Detailed logs are indexed in `evidence/README.md`.

### Historical Rev3 scope and verification snapshot (superseded above)

- Scope delivered in this pass: Child QR/deep-link request, device-grant refresh, canvas reconnect and acknowledged stroke append; Teacher assigned-class setup, lobby, pending request review, profile mapping/admit/revoke, group/member/turn setup, start, pause/resume, and Teacher-authored observation; Admin Firebase/BE1 role gate and class list/create; classroom-only and demo-only backend composition while preserving the compatibility app.
- Verification: combined Child, Teacher and Admin build/lint/test checks passed; BE1 composition/session contract tests passed 10/10. Exact logs and limitations are indexed in `evidence/README.md` and `evidence/notes/API_INTEGRATION_CATALOGUE_20261024.md`.
- Evidence boundary: UI tests use mocked/deterministic HTTP responses, and backend contract tests ran separately. No configured disposable PostgreSQL profile was available, so the FE-to-DB classroom flow has not been run as a true end-to-end test. No live Firebase account, physical-device deep-link test, or Modal request was used.
- Still gated for implementation: six-digit shared room-code route and persistent anti-guess controls; durable roster/group/turn reads; authoritative shared nine-stage API; completion snapshot and terminal outcome contract; BE1 security/transaction and migration root/order review; FEAT-057 BE2 adoption; Modal deployment profile and spend cap. Product policies for code controls and pending-at-start disposition are now owner-confirmed in SRS v3.3 B28.
- Non-goals remain: no commit/push/tag/merge, production deploy, paid GPU provisioning, real child data, source secrets, or unreviewed DB schema/migration changes.

## Product and repository context

The product has three primary clients: `apps/child-ui` (Expo/RN), `apps/teacher-ui` (React/Vite), and `apps/admin-ui` (React/Vite). The current runtime routes now use Firebase authentication for adults and BE1 device grants for Child. Only the connected screens listed above claim live-contract wiring; other prototype routes/services are not evidence of backend functionality. Teacher and Admin unsupported routes report that they are not connected, and Teacher fixtures require explicit `?demo=1`.

The backend exposes versioned BE1 endpoints for identities/assignments, classes/profiles/consent, sessions/admission/groups/turns, canvas operations, artifacts/gallery, observations, and data requests. Adult calls require a Firebase-verified bearer token and role/class assignment. Child calls require an admitted device grant and active membership. Durable backend routes fail closed when persistence is not configured.

Backend entrypoints now separate `classroom_main.py` (health + BE1 classroom composition) and `demo_main.py` (local/in-memory routers); `create_app()` preserves the compatibility composition. Composition contract tests pass. The actual deployment command/process and live database were not exercised, so runtime deployment separation is not yet verified.

Modal remains selected for future bounded AI inference behind the backend provider adapter. There is no configured Modal product endpoint/profile, model, GPU, region, scaling, timeout, secret policy, or spending cap in the local evidence. FEAT-057 BE2 cross-lane approvals remain incomplete. Do not claim an AI product flow from offline BE2 tests or this classroom integration.

## SRS authority and confirmed product behavior

The canonical sequence is the nine stages in FEAT-029 Master SRS §B5, with detailed semantics in §B19.4–B19.5. Current SRS v3.3 (B28) is synchronized to the FEAT-039 feature copy; exact v3.2 is preserved there. The owner-confirmed classroom policies are:

- The six-digit value is a shared room code for the class, not an OTP or per-child identity. Multiple children use the same code.
- Once Teacher successfully starts the session, neither QR/deep link nor six-digit code accepts new join requests. Previously admitted devices keep their grants.
- Join requests still pending at the successful Start boundary are atomically revoked; the Child sees `revoked` on refresh.
- Six-digit room code lives for the Lobby, Teacher may rotate it before Start, the backend uses collision-safe cryptographic generation/keyed-hash storage/generic error, and persistent throttling is 10 invalid attempts per source IP per 15 minutes. BE1 still reviews trusted-proxy attribution and cross-replica durability.
- The saved product outcome distinguishes fully completed work (`completed`) from Teacher stopping early (`ended_early`). Existing lifecycle `finished` does not prove either result.
- Teacher advances only to the next stage after a backend guard and durable receipt; Assistance may interleave or be recorded `not_needed`; arbitrary skips are forbidden.
- Rewind remains disabled until OD07 is resolved; OD07's final pedagogical policy is still open.
- Before advancing past unfinished group work, Teacher must persist `save_draft` for the group; early stop requires category `time`, `safety`, `technical`, or `other`, with an optional short Teacher note.
- The nine-stage learning position is separate from session lifecycle and member/group progress.

These product semantics do not approve API fields, concurrency guards, trusted-proxy/source-IP handling, keyed-hash lifecycle, durable draft receipts, completion snapshot schema, or Alembic order. Those remain BE1-owner and migration review gates. No unsupported client success is shown while the authoritative contracts are absent.

## Findings to close

- **SR-01:** Child QR join and stroke persistence are wired; six-digit join, durable snapshot hydration and database-backed reconnect still need implementation/evidence.
- **SR-02:** classroom/demo composition is separated in code and contract-tested; deployed process separation is not yet verified.
- **SR-03:** nine Alembic heads remain; mapping, clean-install, upgrade and rollback require BE1 migration ownership/review.
- **SR-04:** SRS product semantics are recorded, but backend currently persists lifecycle `configured/lobby/active/paused/finished`; no shared stage or distinct terminal result API exists.
- **SR-05:** consent checks exist in BE1, but end-to-end purpose/retention/export/delete/archive/purge receipts are missing.
- **SR-06:** deterministic UI and backend tests pass, but there are no single-run DB-backed WF-01/WF-02 receipts, WF-03/WF-04 product workflows, or capacity measurements for 40 children.
- **SR-07:** no configured Modal product profile or live request.
- **SR-08:** NFR thresholds and measured RPO/RTO, AI latency, safety-review, and non-session retention profiles remain unapproved/unmeasured.
- **SR-09:** official class/project metadata remains TBD; do not infer it from the form filename.
- **SR-10:** authentication and connected screens use real Firebase/BE1 adapters; several other prototype capabilities remain intentionally unavailable and must not present fixture success as saved data.

## Evidence and ownership

See `evidence/notes/SRS_STAGE_API_TRACEABILITY_20261023.md` for the current nine-stage map and `evidence/notes/API_INTEGRATION_CATALOGUE_20261024.md` for detailed endpoint-to-screen mapping. D01–D20 record the FE/BE decisions; D12 is the exact Plan Rev3 approval and D15–D20 record the six owner answers. No external message to Khoa/BE1 owner was sent. Technical review items remain listed in `evidence/notes/OWNER_DECISIONS_REQUIRED_20261024.md`; Modal remains selected with deployment values TBD.
