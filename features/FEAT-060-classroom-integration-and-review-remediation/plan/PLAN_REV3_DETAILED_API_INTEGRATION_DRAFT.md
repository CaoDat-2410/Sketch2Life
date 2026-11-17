# FEAT-060 Plan revision 3 — detailed SRS API integration

- **Status:** APPROVED — project owner approval recorded 2026-10-24 in `approvals/TASK_APPROVAL.md` against the SHA-256 of this plan revision.
- **Baseline:** local `dev@0a7ce768c153f2104cff930569c3eda6e484532c` plus pre-existing dirty FEAT-059/FEAT-060 worktree.
- **Supersedes:** none until approved. Plan revision 2 and its approval remain a historical authority record; revision 3 is a proposed expansion, especially for shared learning-stage and six-digit join contracts.
- **Owner:** Project owner (Đạt, fullstack).
- **Contributors by lane:** Bảo (Child UI), Hiếu (BE2), Khoa (BE1), Đạt (integration/fullstack), subject to actual team agreement.
- **Purpose:** finish the actual classroom loop according to the nine-stage Master SRS; record exactly what each API does, which screen/service calls it, what persistent effect it has, and how failure is shown.

## Plan at a glance

The class needs one real saved flow from Teacher setup through Child join, drawing, learning activities, reflection and class completion. Several current screens still use sample names, local data, or buttons without a backend call. This plan connects each screen to an exact API or marks it unavailable until that API exists.

1. **Teacher prepares the class:** load assigned classes → save a session → open the lobby → display a QR and a shared six-digit room code.
2. **Children enter the room:** scan the QR or type the same room code, like Quizizz/Kahoot → backend creates a waiting request → Teacher selects the child's profile and admits the device after the consent check.
3. **Teacher starts the class:** create real groups → assign admitted children → start the session and a child's drawing turn.
4. **Children draw:** load the server-saved drawing, send each stroke, and show “saved” only after the backend accepts it. Reconnect reloads the checkpoint and accepted strokes.
5. **Follow all nine SRS stages:** drawing, help, sharing, knowledge, off-screen activity, reflection, completion. Each stage needs a saved result or a visible reason it is blocked; clicking a screen alone does not advance the class.
6. **AI runs behind the backend:** clients never call Modal directly. Modal is an AI worker only after BE2 approval and deployment setup. The whole classroom API container does not need to move to Modal.
7. **Test and report:** run build/typecheck/lint and synthetic main flows, save API IDs/revisions and failure receipts, then report which SRS stages passed and which remain blocked.

**Current main gaps:** BE1 does not store which of the nine learning stages the class is on; the shared room-code API is missing; Teacher cannot reload admitted roster/groups from current read APIs; AI/video/activity routes are not mounted in the classroom runtime; `/finish` does not distinguish normal completion from ending early. These are explicit contract tasks in this plan.

## 1. Goal and definition of “done”

Deliver a source-backed API catalogue, a reviewed gap/contract plan, then wire only approved routes across Child, Teacher, Admin, and BE1. The project must not present a local screen change as an accepted class transition. Each stage must have (a) a canonical source requirement, (b) a specific command/query and responsible service, (c) an authorization/consent guard, (d) a durable receipt or explicit blocked state, and (e) a reproducible test/evidence receipt.

“Full classroom loop” means Preparation → Join → Explore & Draw → Adaptive Assistance → Artwork Sharing → Knowledge Discovery → Off-screen Exploration → Reflection & Assessment → Completion, including early end, pause/resume, stale state, failures, and recovery. Assistance may occur between other stages as SRS permits. Group progress is separate from class stage. It is not enough for the Teacher to click through nine pages.

## 2. What this plan records from current source

- API-to-screen mapping and exact current gaps are recorded in `evidence/notes/SRS_STAGE_API_TRACEABILITY_20261023.md`.
- Shared learning stage and completion outcome proposal is in `artifacts/BE1_SHARED_STAGE_CONTRACT_PROPOSAL.md`.
- Shared room-code proposal (Quizizz/Kahoot style, not OTP) is in `artifacts/BE1_NUMERIC_JOIN_CONTRACT_PROPOSAL.md`.
- Modal/container placement review is in `artifacts/MODAL_HOSTING_BOUNDARY_REVIEW_20261023.md`.
- Current frontend changes are incomplete and were not tested as a full flow in this plan phase. The dirty working tree predates this addendum; preserve all unrelated files and do not merge/reset/stash.

## 3. Target connection map

```mermaid
sequenceDiagram
  participant T as Teacher UI
  participant F as Firebase Auth
  participant B as BE1 Classroom API
  participant DB as PostgreSQL / approved artifact store
  participant C as Child UI
  participant M as Modal AI Function (future, approved contract only)

  T->>F: sign in and obtain ID token
  T->>B: classes/profiles/consents (Bearer ID token)
  T->>B: create session → open lobby (revision guarded)
  T-->>C: display QR high-entropy invite / approved six-digit code
  C->>B: join request (device key; no child identity)
  B->>DB: persist pending device grant
  T->>B: select managed profile and admit (purpose consent check)
  C->>B: poll grant refresh; receive rotated secure key after admission
  T->>B: create group → assign member → start class → start child turn
  C->>B: reconnect snapshot/operations; append canvas operation + idempotency key
  B->>DB: durable operation receipt / revision
  T->>B: artifact, gallery, observation and completion commands (when contract is ready)
  B->>M: bounded AI job request (future, BE2 and Modal gates)
  M-->>B: typed job/result reference; never direct to child without review
```

Modal is not in the current WF-01/WF-02 path. Do not move the BE1 system of record to Modal merely to call an AI model there.

## 4. Detailed work packages and sequence

### WP0 — Freeze source and scope

1. Record current `git status`, `HEAD`, hashes of touched FE/BE files, BE1 route/schema snapshots, Alembic heads, FEAT-057 gate IDs, and FEAT-059 manifest comparison.
2. Classify all existing dirty paths as prior cleanup, prior integration, or unrelated; never reset or overwrite an unclassified path.
3. Update feature status/evidence after each review. Keep external form/handbook originals untouched.

**Exit:** a reproducible source manifest and preservation boundary.

### WP1 — Review the API contracts before coding new server behavior

1. Review every endpoint in `SRS_STAGE_API_TRACEABILITY_20261023.md` against `be1_registry.py`, `be1_sessions.py`, `be1_canvas.py`, `be1_artifacts.py`, `be1_records.py`, the schema models and the current frontend service call sites.
2. Ask Khoa/BE1 owner to review the shared stage proposal, room-code proposal, session group/membership list gap, max-40 enforcement, migration root/order, and normal-completion vs early-end representation.
3. Record decisions in feature `DECISIONS.md` and, for cross-feature architecture, an ADR. Do not silently change ADR-0019.
4. Treat the six-digit room code as a shared room key, not an OTP. **Owner-confirmed:** QR/deep-link and the shared code both reject new joins as soon as Teacher start succeeds; already admitted child grants remain. Confirm pending-request disposition, persistent guessing/spam protection, collision behavior, generic errors, and Teacher rotation.
5. Confirm whether SRS “40 children” is a hard admission limit or an operational target. If hard, the backend must enforce it atomically; frontend-only counting does not count.

**Exit:** approved exact API/data contract and accepted migration path for any schema work. If the contract is rejected, revise only the draft and ask again; no production route/migration is written.

### WP2 — Complete versioned BE1 read/write surface required by the classroom UI

Implement only after WP1 approval:

- Shared stage query/advance + completion outcome commands from the approved contract, with separate stage revision, idempotency key, append-only history, stale-version conflict, stage guard failures, and atomic commit.
- Shared room-code create/rotate/join behavior from approved proposal; code stored as keyed hash, collision checked in persistent store, persistent rate limiting, generic failure response, and same Teacher admission path as QR. Enforce the owner-confirmed close-on-start behavior for both QR/deep-link and numeric-code requests; preserve already admitted grants. Resolve pending requests at the start boundary with BE1 owner review.
- Add authorized session roster/group read endpoint(s) so Teacher can reconstruct admitted profiles, group membership and turn state after browser refresh; existing `GET join-requests` returns pending requests only and is not a roster endpoint.
- Add server-side max-roster check only if SRS owner confirms 40 is a hard requirement; make capacity test exercise concurrent admissions.
- Add only the missing transition/report endpoints needed for completion and early end; retain existing lifecycle compatibility and document exact mapping. Product outcome must distinguish fully completed (`completed`) from Teacher stopping early (`ended_early`), as the owner confirmed; exact fields/guards/reason requirements remain for BE1 review. Do not mutate `finished` semantics by inference.
- Preserve domain/application/infrastructure dependency direction; route layer adapts versioned DTOs to application ports; do not put stage rules in React or FastAPI router functions.

**Exit:** contract tests cover payload validation, permission, consent, state/revision/idempotency, enumeration/rate limits and DB persistence on isolated PostgreSQL; migration bootstrap/upgrade/rollback is approved and reproducible.

### WP3 — Teacher UI: create → lobby → admit → group → start → turn

1. Login uses Firebase Auth ID token; BE1 verifies organization and class assignment. Missing Firebase/base URL/purpose config remains a visible setup error.
2. `SessionSetupPage` maps the actual form values to session config: authorized class, topic, age constraints, tools, preset/version, individual/group mode and grouping. Remove fixture labels or mark unconnected fields. Do not send a pretend config for fields BE1 has not approved.
3. Create session and open lobby with expected revision. Show returned session ID/state and one-time high-entropy QR invite; no raw invite in general logs or client error telemetry.
4. Lobby polls pending joins and loads managed profiles. For each anonymous pending grant, Teacher deliberately chooses a child profile; the backend validates consent and produces a membership receipt.
5. Create actual BE1 group(s), assign admitted membership using the latest session revision, refresh state after conflict, and persist enough server state to survive browser reload.
6. Explicitly start the session only when the roster and SRS preconditions are satisfied. Start the active child turn via the turn endpoint; never navigate to an active-looking fixture page before BE1 confirms.
7. Add pause/resume and separate normal completion/early-end actions only after their semantics/contract are approved.

**Exit:** component/service tests use typed responses/errors; UI test proves each button calls the exact method, refreshes on stale revision, and never displays a false success.

### WP4 — Child UI: QR/six-digit join → waiting → admitted → turn → durable draw/recovery

1. QR deep link carries only organization/session/high-entropy join material required by the existing BE1 route; it creates a pending grant, not a profile identity or session read capability.
2. Six-digit submit remains disabled/explicitly unavailable until WP1/WP2 numeric contract and anti-enumeration controls pass. After approval, the numeric request returns the same pending grant shape and converges to existing teacher admission.
3. Keep device key in Expo SecureStore; on admission persist the rotated key before subsequent canvas calls.
4. Keep child screen in waiting state until `refresh` reports admitted and reconnect returns a valid active turn. Do not let “ready” local state bypass server lifecycle/turn.
5. Rehydrate canvas from checkpoint plus ordered accepted operations. Add operation to local pending state; display “saved” only after `Be1CanvasOperationReceiptV1`. Handle stale revision, revoked grant, lost network, failed operation and retry idempotently. Do not claim offline-durable writes unless an approved local outbox/replay contract exists.
6. Remove fake names, “saved” labels, local join success, and live-stage controls from connected runtime screens; keep prototype content behind explicit demo/test mode.

**Exit:** client tests cover QR request, six-digit only when enabled, pending/admitted/revoked, SecureStore rotation, canvas acceptance/rejection, and checkpoint+operation recovery; deterministic synthetic BE1 workflow verifies durable operation receipts.

### WP5 — Explore & Draw slice plus supported gallery/observation endpoints

- Connect group/member/turn/canvas operations first. Verify individual and group modes do not silently mix or lose attribution; verify turn switching closes prior write scope.
- Connect artifact upload/download with explicit contributors and purpose checks only after durable artifact storage is selected. Gallery uses returned artifact refs; do not use bundled images as uploaded user artwork.
- Connect Teacher-authored observation/reflection/assessment POST calls with explicit record kind/source refs. Keep child-authored reflection unavailable until a child-auth contract exists. Portfolio route stays visibly unavailable while server returns consent-purpose failure.

**Exit:** artifact hash/integrity, contributor consent, gallery draft→publish, annotations, and observation receipts verified with synthetic data; production storage/portfolio purpose remain gated if unconfigured.

### WP6 — BE2/Modal stages (assistance, knowledge, activity)

1. Read FEAT-057 current card gates immediately before implementation; route is ineligible until exact owning cards and cross-lane gate approve it.
2. Connect Child request → backend-owned BE2 assistance job → safety/policy check → Teacher review of exact version → Child availability, with stale/blocked/failed/rejected cases. Modal adapter is server-side only and injected behind approved port.
3. Connect Knowledge video draft/source/license generation, exact-version Teacher review, playback/skip receipt, and failure handling. Unapproved media never autoplays.
4. Connect real-world activity assignment/preparation/material/safety checks, child/class outcome, and explicit performed/skipped/failure state before reflection.
5. Compare backend entrypoint: classroom factory mounts health + BE1 only; do not assume candidate BE2 routers are mounted because their fixture app tests pass.

**Exit:** FEAT-057 gate records, endpoint composition/route tests, provider-free deterministic integration and exact version lineage pass. Live Modal call requires a deployed endpoint/profile, approved spend cap, synthetic payload, and provider config; no deployment or GPU provisioning under current scope.

### WP7 — Reflection, completion, lifecycle, and migration evidence

- Save child reflection (when contract exists), Teacher observation, and Teacher-confirmed assessment as separate versioned records; AI assessment stays advisory until Teacher confirms.
- Implement SRS `completion` only via approved completion command that stores outcome refs and unfinished-group disposition. `ended_early` requires an explicit reason and must not discard artifacts.
- Trace retention, export/delete, archive/purge, backups, audit events, and unresolved data copies. A `requested` data request is not completed deletion.
- Inventory all migration roots/heads and logical-to-physical mapping. Do not add Alembic merge revisions or alter schema before Khoa approves the install/upgrade/rollback sequence.

**Exit:** transition matrix proves valid/invalid commands, concurrency/stale events, retry/idempotency, pause/resume and explicit completed/early-end outcomes; synthetic privacy/delete evidence matches the approved policy.

### WP8 — Admin integration and unsupported functionality

- Replace mock Admin auth with Firebase Auth + BE1 verified role when a matching Admin route exists.
- Connect only supported registry, class/profile/consent, data-request, gallery/observation endpoints where current role checks allow the Admin action.
- Remove fake successful writes for dashboard metrics, generic user CRUD, AI policy/settings, audit export, content authoring/template automation, and other endpoints without a BE contract. Mark unavailable/prototype-only in connected mode.
- Verify Admin cannot cross organization/class authorization boundaries.

**Exit:** admin build/test proves no mock token or false mutation success in runtime mode; each feature maps to an exact route or visible gap.

### WP9 — Verification, evidence and closeout

1. Before changes: baseline hashes, branch status, route/schema/source-register snapshot, migration heads, env presence check without reading secret values.
2. Per application: build, typecheck, lint and focused unit/client/UI tests. User previously selected these and main-flow checks as the minimum.
3. Backend: focused router/service contract tests, route composition snapshots, permission/consent/revision/idempotency tests, and isolated synthetic PostgreSQL run for any persistent contract change.
4. Workflow tests: WF-01 preparation/join, WF-02 draw/turn/reconnect, WF-03 exact AI review, WF-04 knowledge/activity/reflection/completion. WF-03/04 stay GATED if FEAT-057 or provider/runtime evidence is missing.
5. Modal: preflight first; make one bounded synthetic request only through an already configured endpoint/profile. Otherwise record `NOT_TESTED_CONFIGURATION_UNAVAILABLE`.
6. Keep target thresholds separate from approved thresholds and measured results. One class / 40 children is not a measured capacity claim without a bounded load profile.
7. Store commands, outputs, timestamps, commit/source hashes, API request IDs, synthetic fixture IDs and interpretation under feature-local `evidence/`; run `python tools/validate_repository_security.py` before any commit/push. No commit/push/deploy/GPU provision is in scope.

**Exit:** 9-stage API matrix updated to exact implemented routes; each accepted workflow has a reproducible receipt or a precise gated reason; source register/context/decisions/status match evidence.

## 5. Stage-by-stage planned API connections

| SRS stage | UI query/command | Backend path / current status | Needed after review | Owner lane |
|---|---|---|---|---|
| Preparation | Teacher loads authorized classes; creates configured session; opens lobby | `GET /organizations/{org}/classes`, `POST /organizations/{org}/sessions`, `POST .../sessions/{id}/lobby` — exists; current UI config partial | Validated SRS config DTO, `GET current stage`/current session read; configuration approval | Bảo + Đạt; Khoa contract |
| Join | Child scans QR or enters the same shared six-digit room code like Quizizz/Kahoot; Teacher sees pending request, chooses profile, admits, then starts | `POST .../sessions/{id}/join`, `GET .../join-requests`, `GET .../profiles`, `POST .../admit`, `POST .../start`, Child `POST .../device-grants/{id}/refresh` — QR exists, room-code route absent | Room-code join-window/rotation and persistent anti-guess/spam controls; roster read/40 cap decision; shared-stage guard | Bảo + Đạt; Khoa |
| Explore & Draw | Teacher creates group, assigns profile, starts child turn; Child reconnects/appends/syncs | Group create/assign/turn + canvas operations/reconnect — backend exists; Teacher methods/UI incomplete, Child partial | Authorized group/membership/current turn reads; synthetic durable canvas proof | Bảo + Đạt; Khoa |
| Adaptive Assistance | Child asks; backend job; Teacher exact-version review; Child receives only approved result | Membership help flag exists but is not AI; BE2 candidate routers not classroom mounted | FEAT-057 owner/card gates; BE2 versioned route adoption; server-side Modal adapter | Hiếu + Khoa; Bảo/Đạt |
| Artwork Sharing | Upload artifact; Teacher drafts/publishes scoped gallery item; Child presents exact ref | Artifact/gallery routes exist; production storage unselected; UI disconnected | Durable storage provider; canvas export contract; UI services; consent/audience checks | Bảo + Đạt; Khoa |
| Knowledge Discovery | Teacher selects/generates/reviews exact media; explicit playback/skip | Candidate routes not classroom mounted | FEAT-057 adoption and exact-version review/playback contract | Hiếu + Bảo; Khoa/Đạt |
| Off-screen Exploration | Teacher assigns/edits activity; records preparation and result | No BE1 activity route; candidate activity router is not mounted | Adopted ActivityExecution contract, safety/material fields, durable outcome | Hiếu + Teacher UI |
| Reflection & Assessment | Child reflects; Teacher observes and confirms assessment | Adult observation POST exists; portfolio GET fails closed; no Child reflection API | Child-authored reflection contract, portfolio-purpose decision, review/consent gates | Bảo + Khoa + Đạt |
| Completion | Teacher complete or ends early with reason; outcomes/artifacts and unfinished group work preserved | `/finish` writes only `finished`; per-member progress only | Stage/completion proposal, approved persistence/migration, outcome refs/disposition | Đạt + Khoa; owner |

## 6. API-specific test contract

Every endpoint adopted by a screen must have a test table with exact request and expected durable response. Minimum cases:

| API family | Positive receipt | Must remain visible as blocked/failure |
|---|---|---|
| Identity / class / profiles / consent | Firebase token + assigned role returns only assigned resources | Missing/expired token, wrong organization/class, pending/revoked consent |
| Session configuration/transitions | Create → lobby → start increments/returns persisted revision | stale revision, invalid lifecycle, no admitted member, consent pending |
| QR and room-code join | Pending grant, Teacher profile choice/admit, device key rotation | invalid/closed/rotated room code, rate limit, profile mismatch, consent blocked |
| Groups and turn | Group creation, assignment, one active admitted child turn | no membership, wrong group, paused/finished session, group locked, stale revision |
| Canvas operation/sync/reconnect | Append receipt increments durable revision; replay reconstructs same state | duplicate key with different payload, stale revision, wrong turn/epoch, lost consent, offline network |
| Artifact/gallery | hash-verified artifact; draft then published with audience/contributors | missing production storage, changed consent, invalid image, wrong session artifact |
| Assistance/knowledge/activity | exact job/media/activity/outcome version persists after owning gate | unsafe/stale/rejected/failed/unreviewed outputs do not reach Child |
| Reflection/completion/delete | durable separate records, explicit terminal outcome and request status | child reflection unsupported, no portfolio authorization, requested delete not mislabeled complete |

## 7. Acceptance criteria for this expanded plan

- **AC-API:** all endpoints have method/path, caller/auth, body/query, result, purpose, side effect, failure codes, consuming UI/service, source owner, and proof status documented.
- **AC-SRS:** exactly the nine SRS stages are represented; assistance interleaving and group-progress independence are preserved; no UI-only transition claims.
- **AC-JOIN:** QR and six-digit paths converge on the same pending-grant → Teacher profile/consent admission path; six-digit is disabled until persistent anti-enumeration contract passes. Once start succeeds, reject new joins through both entry methods while preserving admitted grants; resolve requests already pending at start according to the reviewed BE1 contract.
- **AC-DRAW:** Child sees pending/durable-accepted/error states; local state is not called saved; reconnect hydrates snapshot+operations; Teacher controls actual group/turn APIs.
- **AC-STATE:** lifecycle, shared stage, individual progress and terminal outcome are distinct contracts; the saved product outcome distinguishes full completion from early Teacher stop, and `finished` is not relabeled without a durable outcome receipt.
- **AC-BE2/MODAL:** no BE2 UI claims success before FEAT-057 gates; Modal call only through backend adapter and configured approved endpoint.
- **AC-PRIVACY:** Firebase is authentication only; purpose and consent are checked server-side; no tokens, device keys, raw join codes or real child data in evidence/source.
- **AC-REPRO:** every claimed check has a local receipt tied to exact source hashes and synthetic fixtures; gated checks identify the owner/decision that remains.
- **AC-SOURCE:** all unrelated dirty/untracked content is preserved; no reset/stash/merge/commit/push/tag/deploy/GPU provision.

## 8. Risks, owners and explicit open decisions

| Open decision | Why needed | Proposed owner |
|---|---|---|
| Approve shared stage API, guard matrix, revision and idempotency | A frontend-only stage indicator cannot implement SRS transition semantics | Project owner + Khoa |
| Terminal outcome contract: fields, mandatory early-stop reason, saved-state refs and guard conditions | Outcome semantics are confirmed; `/finish` currently only persists `finished` | Project owner + Khoa |
| Pending requests at the exact start boundary | Both QR and numeric entry close to new requests after start; disposition of already pending items is not yet specified | Project owner + Khoa |
| Persistent rate-limit thresholds/source IP trust | Six digits can be guessed or used to flood pending requests without backend protection | Project owner + Khoa |
| Hard cap 40 vs target load | Need atomic count check or load-only measurement | Project owner/SRS authority + Khoa |
| Stage group-disposition/OD07 return behavior | Avoid losing unfinished art or accidental rewind | Project owner/SRS authority |
| Migration root/head and rollback order | Multiple existing roots/heads; shared DB risk | Khoa/BE1 owner |
| Durable artifact storage and retention | Current production route is explicitly unconfigured | Project owner + infrastructure owner |
| BE2 per-card and cross-lane runtime adoption | Candidate routers are not classroom-mounted | Hiếu + FEAT-057 owners |
| Modal endpoint/model/GPU/region/scale/spend/retention | No deployed product profile exists | Project owner + Hiếu |
| Official school class/project metadata | Cannot infer from filenames | Project owner / official source |

## 9. Approval boundary

The project owner approved this exact revision on 2026-10-24; its SHA-256 is recorded in `approvals/TASK_APPROVAL.md`. Implementation may proceed within this plan, preserving every explicit owner/card/security/provider/migration gate. Approval does not authorize production deployment, paid GPU provisioning, real child data, unresolved BE1 semantics, Git merge/commit/push/tag, or work outside the listed scope. Revision 2 remains a historical approval record and is not used to define this expanded scope.
