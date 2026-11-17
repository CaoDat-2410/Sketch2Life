# FEAT-063 FR-C-08 Parent/Teacher StoryRun Cancellation and Purge Lifecycle — Draft 1

- **Status:** DRAFT / NOT APPROVED / NOT LAUNCHED.
- **Task type:** Planning proposal for a separate BE lifecycle task aligned to canonical FEAT-063 SRS Rev67.
- **Date:** 2026-11-15.
- **Scope owner:** Not assigned. Story, BE1 lifecycle, AI Jobs, Core Asset, Billing, and Lesson owners require confirmation.
- **Approval boundary:** This document is not a Task Approval, implementation allowlist, launch prompt, command ceiling, database/migration approval, or amendment to D-199 through D-207. It authorizes no implementation or checks.
- **OWNER_MODAL_CALL_APPROVED:** NO.

## 1. Goal and definition of done

Plan the remaining work needed for the integrated StoryRun lifecycle to satisfy FR-C-08 for Parent and Teacher actors: cancel an unfinished run or delete a completed run, revoke access immediately, cancel work best-effort, prevent late output from becoming usable, purge linked private content, report lifecycle progress, and retain the required quota, sample-claim, and minimal audit records.

The task is done only when the SRS requirements have an owner-approved contract and implementation scope, each cross-module responsibility has an identified owner, the acceptance evidence is complete, and an independent review finds no unresolved requirement gap. This plan does not claim implementation or runtime readiness.

## 2. Authority and requirement trace

Use only the canonical working SRS routed by `docs/context/SRS_AUTHORITY.md`: FEAT-063 v2.7-draft Rev67. It remains unsigned. The plan uses these requirements as its baseline:

| SRS source | Required outcome for the future task |
|---|---|
| FR-C-08; BR-26 and BR-40 | Support cancel of unfinished runs and deletion of completed runs through lifecycle. Release the active lock immediately on cancel; remove linked content; retain minimal audit metadata, consumed quota, and a successful Teacher sample claim. |
| §6.1.1 StoryRun lifecycle | `DELETE_PENDING` begins purge; it is not a completed deletion state. `DELETED` is reached only after lifecycle work completes. |
| UC-07 | Authorize the Parent owner or currently assigned Teacher to delete a completed run; create a lifecycle request, block new playback tokens, remove linked private content, retry object-delete failures idempotently, and finish with metadata-only audit. Preserve shared assets with other valid references. |
| UC-11 | Authorize the Parent owner or currently assigned Teacher to cancel an unfinished run. Atomically record `DELETE_PENDING` and release the active lock, then revoke playback/upload, record the cancellation notice and lifecycle request, request best-effort job/provider cancellation, purge linked content, and finish at `DELETED`. Late provider output must remain stale and unplayable and be purged. |
| §21.2 API rows | Reconcile the existing `POST /v1/story-runs/{id}/cancel`, the `DELETE /v1/story-runs/{id}` completed-run operation, and lifecycle-status reads against the route table. Do not add a route or response field without a documented contract and separate approval. |
| §21.6 lifecycle status behavior | While `DELETE_PENDING`, show that deletion is underway, block playback and new runs on the deleted profile, let the client poll lifecycle status, and retry object deletion on the server. |
| §9.8 and §21.4 | Keep public errors safe and version/idempotency behavior explicit. Existing owner decisions for the M2 cancel response remain in force unless a separately recorded decision changes them. |
| `StoryRunCancellationRequestedV1` and `StoryRunDeletedV1` event rows | Use versioned, metadata-only cross-module contracts. Cancellation request data includes run, actor, expected revision, lifecycle-request reference, and safe reason code; it must not include media/content. |
| NFR-34 and Core Asset requirements | Apply revocation consistently to APIs, downloads, tokens, caches, and job dispatch; Core Asset remains the source of asset metadata and lineage. |

Relevant canonical SRS locations include §6.1.1, FR-C-08, UC-07, UC-11, §§9.8, 21.2, 21.4 and 21.6, and the event catalog. The SRS/Data Table Register and physical schema must be reconciled before any implementation or migration proposal is approved.

## 3. Current baseline and boundary

- SRS authority and Rev67 are pinned below. Rev67 is the product baseline, not a formal owner sign-off.
- D-199 through D-207 and Draft 18 define a bounded M2 S2 slice. D-199 adds the Parent cancel route with a `CANCEL_RUN` receipt, a transactional `DELETE_PENDING` transition, active-lock release, and `purge_state=PENDING`; it explicitly excludes a purge worker and provider/AI-job cancellation. D-207 approves only the pinned M2 implementation allowlist and command ceilings.
- The M2 implementation report remains **PARTIAL / NOT COMPLETE**. It records selected late-result guards for current Parent artwork/story writers, but no cancellation worker, provider/job cancellation, or purge worker. Its recorded pytest run failed the OpenAPI tag assertion and errored during `tmp_path` setup; mypy and Ruff also failed. Those M2 run ceilings are consumed and do not transfer to this separate task.
- Current `cancel_run` stores/replays a `CANCEL_RUN` receipt and allows a fixed set of seven existing run states. The future task must reconcile that current-state list against the Rev67 lifecycle states and D-199's unfinished-run rule. It must not silently claim full-state coverage.
- Current M2 evidence establishes the Parent cancel route and some state-based write guards. It does not establish revocation of existing playback/download tokens, Teacher authorization, completed-run deletion, a durable lifecycle request, job cancellation, purge progress, or a completed purge.
- The OpenAPI mapper correction plan is a separate plan-only item. It changes no cancellation behavior and must not be combined with this lifecycle scope.
- The current worktree contains unrelated existing changes. Any future task must preserve them, recheck exact inputs, and use a fresh implementation allowlist. No existing M2 approval or run ceiling authorizes this task.

## 4. Proposed scope

### Included

1. Produce an owner-reviewed StoryRun cancellation/deletion state-transition and authorization matrix for both Parent and Teacher-current-assignment actors, covering every Rev67 run state and the completed-run deletion path.
2. Reconcile API contracts and versioned events for accepted cancel, completed-run delete, lifecycle request, cancellation notice, lifecycle-status polling, and successful deletion. Preserve the existing D-204 HTTP 202 body and D-206 cancel stale-revision field unless a separate owner decision approves a contract change.
3. Define an immediate access fence for new and existing upload/playback/download access, including current assignment checks, upload-session revocation, playback-token/cache behavior, and stale work after reassignment.
4. Define best-effort cancellation requests for queued/running jobs and provider work, with worker checks before costly stages and before accepting results. A provider that cannot be interrupted must not publish or expose a late result; the late result must enter the purge lifecycle.
5. Define an idempotent lifecycle worker for all linked private content and object references, including safe handling of partial failures, shared assets, retry/reconciliation, progress reporting, and the final `DELETED` state.
6. Preserve accepted Billing usage and Teacher sample claims; retain only the permitted audit metadata and avoid child content in events, logs, and audit records.
7. Prepare synthetic-only contract, unit, and isolated integration evidence and a separate implementation allowlist/command ceiling for owner approval.

### Excluded unless separately approved

- Expanding or rewriting M2 S2, changing D-199 through D-207, or reusing D-207's allowlist or command ceilings.
- Any route, response, state, event, table, migration, or error contract not traced to Rev67 or a separately recorded owner decision.
- Real child data, production data, provider/Modal calls, deployment, external storage mutation, database mutation, or production backup deletion.
- Changing quota/refund policy, reopening a consumed Teacher sample claim, deleting invoice/usage history, or broad account/profile deletion.
- The OpenAPI mapper correction, FE/mobile changes, and unrelated S2 verification failures.

## 5. Work breakdown

| ID | Task | Depends on | Parallel with | Acceptance check | Effort | Risk |
|---|---|---|---|---|---|---|
| C0 | Reconcile the live M2 baseline and build a FR-C-08 trace matrix. Inventory current run states, route composition, authorization, receipts, asset/upload/playback paths, jobs, lifecycle storage, and current tests. Separate observed facts from runtime-unverified claims. | Owner opens this separate planning task; fresh read-only pins | None; this is the common baseline | Every FR-C-08/UC-07/UC-11/§21 requirement maps to current evidence, a planned change, or an explicit open item. Resolve the seven-state cancel guard against the complete Rev67 state list. | Small | Medium: active uncommitted work can change source pins. |
| C1 | Agree the cross-domain contract and ownership. Define request/notice/event references, idempotency and revision semantics, lifecycle status/progress contract, and the existing-route versus new-route mapping. Identify the Story, BE1 lifecycle, AI Jobs, Core Asset, Billing, and Lesson owners. | C0 | Asset/job ownership inventory can be researched in parallel; contract decisions cannot be implemented in parallel | Independent review confirms every event/API field is SRS-backed or marked OPEN; no content is placed in lifecycle events; no owner or dependency is invented. | Medium | High: SRS names cross-domain records but leaves physical mapping/status details open. |
| C2 | Implement access fencing and authorization for cancel/delete. Enforce current Parent ownership or current Teacher assignment; revoke upload and playback/download access promptly, including existing tokens/sessions and cache paths. | C1 and owner assignment for BE1/Core/Story boundaries | C3 may be designed in parallel; source changes touching shared contracts must serialize | Synthetic contract tests show authorized current owners succeed, non-owners/old Teachers fail closed, new upload/playback is denied after acceptance, and no existing token path bypasses revocation. | Large | High: existing token/cache lifetimes and module ownership are not yet verified. |
| C3 | Implement best-effort job/provider cancellation and complete late-result fencing. The cancellation transaction emits durable work; job workers check cancellation before dispatch/stage and before result acceptance. Late output remains non-playable and is routed to purge. | C1; coordinate with AI Jobs/provider adapter owners | C2 design only; shared contract/code edits must serialize | Synthetic queued, running, duplicate-callback, unknown-outcome, and cancellation-race tests show no post-cancel output becomes current/playable; provider interruption failure does not delay lock release. | Large | High: asynchronous races and provider interruption are technical uncertainties. |
| C4 | Implement lifecycle request processing, purge and status progression. Delete only run-owned eligible content, preserve still-referenced shared assets, retry object deletion idempotently, expose/poll lifecycle status, and reach `DELETED` only after required work completes. | C1, C2, C3; Core Asset and BE1 lifecycle ownership | C5 invariant tests can be designed in parallel | Synthetic tests cover complete purge, partial object failure/retry, duplicate work, process restart/reconciliation, shared asset references, observable pending/progress, and terminal deletion. No content is marked deleted before its deletion criteria pass. | Large | High: DTR/physical mapping and progress semantics are not yet settled. |
| C5 | Verify retained accounting and audit invariants. Keep accepted quota usage and Teacher sample claims/tombstones; retain permitted audit metadata only; exclude child content from event/log/audit payloads. | C1; detailed purge behavior from C4 | Contract review for C2/C3 | Tests/assertions prove no quota refund or sample-slot reopening, invoices/usage remain intact, and audit/event payloads contain no media or child narrative. | Medium | Medium: physical owner boundaries for quota, lesson claims and audit need confirmation. |
| C6 | Run the separately approved verification gates and obtain a fresh independent review. Record actual test, typecheck, lint, validator, and isolated integration results; resolve findings in scope. | C2–C5 implementation complete; owner-issued pins, allowlist and run ceilings | None during final review | All plan acceptance criteria pass; reviewers verify exact pins and route/status evidence; no runtime claim exceeds captured output. | Large | High: M2 has unresolved failures and its exhausted ceilings cannot be reused. |

### Milestone mapping and critical path

- **M5 planning/implementation focus:** worker cancellation, current-assignment fencing, and late-result rejection for video work. Existing M2 guards may be reused only after source review; they do not prove video-worker coverage.
- **M6 planning/implementation focus:** actual purge, retention interaction, lifecycle progress/retries, cross-domain asset/history cleanup, and minimal audit retention.
- **Critical path:** C0 → C1 → C2/C3 → C4/C5 → C6. The M5 cancellation and stale-result boundary must be designed before M6 purge completion; M6 must not treat `DELETE_PENDING` or released lock as deletion completion.
- **Ownership:** The roadmap assigns lifecycle milestones but names no accountable person for this task. Named module owners and task-level dependencies are **UNVERIFIED** and must be assigned before approval.

## 6. Acceptance criteria for the future implementation task

- **FR08-01 — Actor and operation coverage:** Parent owner and currently assigned Teacher can cancel an unfinished run; creator-only access after reassignment is rejected. Authorized Parent/Teacher can delete only a completed run. Terminal and invalid transitions return safe, contract-defined errors.
- **FR08-02 — State coverage:** Every SRS StoryRun state is accounted for. Cancel eligibility, terminal rejection, and any phase-specific limitation are explicit and independently reviewed; no unlisted state is silently rejected as if the SRS allowed it.
- **FR08-03 — Atomic cancel acceptance:** State transition, revision precondition, active-lock release, durable command receipt, cancellation notice and lifecycle request are consistent under concurrency, retry, and process restart. Existing D-204/D-206 response behavior remains unchanged absent a new owner decision.
- **FR08-04 — Immediate revocation:** After command acceptance, APIs refuse new access and previously issued upload/playback/download credentials or cache paths cannot continue serving run content. Upload-session partial bytes cannot later be attached to another run.
- **FR08-05 — Job fencing:** Cancellation is requested best-effort for queued/running work. Workers check the cancellation fence before expensive stages and before committing results. Duplicate, late, or unknown provider outcomes cannot replace current content or become playable.
- **FR08-06 — Idempotent purge:** Lifecycle work deletes all eligible run-owned input, transcript, context, story, scene/video, and derived private content; preserves shared assets with valid references; retries partial failures safely; survives duplicate delivery and restart; and reaches `DELETED` only when the required deletion work is complete.
- **FR08-07 — Progress and client behavior:** The owner-approved read contract communicates pending/in-progress/completed or other approved states. Clients can poll without generating another command. No status names or percentage semantics are invented before contract review.
- **FR08-08 — Accounting and audit:** Accepted quota usage is not refunded; successful Teacher sample claims are not reopened; invoice/usage records remain; only the approved minimal audit metadata remains; no child content enters events, logs, or audit payloads.
- **FR08-09 — Security and architecture:** Cross-module communication uses versioned contracts/ports or the approved outbox pattern; no direct cross-module SQL or transaction is introduced. Current assignment and profile scope are rechecked at every protected read/token/job boundary.
- **FR08-10 — Evidence:** Isolated synthetic tests cover each criterion and failure/race path. Integration tests use a task-owned isolated environment. No real child data or provider/Modal call is required for the contract gates. Test/runtime evidence is reported separately and accurately.

## 7. Open decisions and stop conditions

Resolve before the implementation allowlist is approved:

1. **Progress contract:** Does the existing owner-scoped `GET /v1/story-runs/{id}` adequately expose purge progress, or is a separate lifecycle-status route required? Rev67 requires polling status but does not make this plan invent a new route or response shape.
2. **Lifecycle status model:** Which existing or separately approved values represent queued, running, retryable failure, and terminal deletion? Do not add states or percentage semantics without an owner decision and SRS/DTR trace.
3. **Lifecycle request owner:** BE1 is named for `be1.data_lifecycle_requests`; confirm who owns creation, status updates, retries, and cross-module contracts. The current physical schema and task database have not been verified here.
4. **Teacher authorization:** Confirm the current assignment source and the route/application owner for Teacher cancellation and completed-run deletion. Do not use creator provenance as current authorization.
5. **Upload/playback revocation:** Inventory short-lived token, cache, download, upload-session, and partial-upload behavior. If immediate revocation cannot be enforced through existing contracts, stop for an owner-reviewed design.
6. **M2 state compatibility:** Reconcile the current seven-state cancel guard and existing M2 state vocabulary with Rev67's full state inventory. If supporting additional states needs new storage or state transitions, stop for a separate owner decision.
7. **Storage and retention:** Identify private versus shared asset references and the supported object-delete retry contract. Backup expiry/provider-copy deletion and real-data retention remain separate real-data gates under the SRS; do not claim those are solved by this task.
8. **S2 disposition:** M2 remains incomplete with failed/incomplete checks and exhausted run ceilings. The owner must decide how to close or accept that baseline before this work relies on M2 evidence.

Stop and report if the SRS/authority pins change, a required route/event/state is not specified, owners cannot be assigned, existing contracts cannot enforce revocation, migration/physical database work is needed but not approved, or acceptance requires real data/provider/Modal/network access.

## 8. Approval and execution gates

1. Independent cold review of this plan against Rev67, DTR, D-199–D-207, the M2 report, and the M5/M6 roadmap.
2. Owner resolves the open decisions and explicitly approves a separate task specification. This plan does not amend the M2 approval ledger.
3. Prepare a fresh exact-path implementation allowlist with source pins, module owners, route/event contracts, migration disposition, and per-command ceilings. Obtain a separate independent review and owner approval.
4. Only after the owner supplies a pinned launch prompt may implementation begin. Define isolated synthetic test environments and actual command ceilings in that approval. Do not inherit M2 ceilings or run authorization.
5. Before any future commit/push, follow repository-required validators and security checks; this plan authorizes no commit or push.

## 9. Planning input pins observed 2026-11-15

These are planning snapshots, not permission to edit. Re-hash every input at the next review/implementation preflight and stop on any hard-pin mismatch. Dirty worktree source pins are informational until the owner freezes a task baseline.

| Input | Bytes | SHA-256 |
|---|---:|---|
| `docs/context/SRS_AUTHORITY.md` | 4,054 | `E3783924BCDF0327CCCDA8806773FB4407ED311C7074289D74AB9B9124EAF662` |
| Canonical Rev67 SRS | 634,291 | `B704163C9AAF7BB198D8578699F75DB8766C2226A52CD48B0ED1314AF5E21996` |
| `artifacts/DATA_TABLE_REGISTER.md` | 171,609 | `7CDFDBECDC24E28BB08E62C98A33B338165350204447EBC59B86F5BE69899BC2` |
| `DECISIONS.md` through D-207 | 212,068 | `191D68D7344FE2146E75F339185065234D092887C341AB487FB2DBEA8511C2BF` |
| `approvals/TASK_APPROVAL.md` including D-207/overlay | 410,676 | `C6A506404AF68A6180E150B83DE120113CE5EA54FCD7DEDFF9EAB01E4D375088` |
| Draft 18 specification | 101,153 | `5CA09CC6F9D936C1BA74772251F4D3A9C0480F3E6F82818FE11114205FD3E331` |
| Draft 18 cold review | 5,169 | `4CE583BA092D140C62E7F1600E4B58778569885D7F7E3B62FB812839DD09835B` |
| M2 implementation allowlist | 14,768 | `7DCEEB785C2121D250B7C016EDC2030E2CD7912F87BE537F07CC8B359A2A0CE8` |
| M2 allowlist cold review R2 | 2,715 | `6872DA02B2CD88644AED71BA039D9ABBD38F243639DD44EDCCBAF2000C57645D` |
| M2 implementation report | 25,879 | `F49D1FDB2B3C26387FFABC51C316F226C5D1FC5FC12B4856B0A6172A81941F55` |
| M5/M6 BE roadmap | 20,115 | `A0A485EE421FBB1DA9DEC99DD8EC08279D14EAF27EC548AD6A0A4CE8F234F8FA` |
| Current `parent_story_repository.py` (dirty worktree snapshot) | 69,489 | `237398C01E11BECFD89CE095C217035680D01E2EFFCF95CDD61C7438DEC5DA8C` |
| Current `parent_story_runs.py` (dirty worktree snapshot) | 14,626 | `A2BA4553785BE7367A7F105708CE1A7F618DFE4A3538D85F00DDD9AE938467DD` |
| Separate OpenAPI mapper correction plan | 20,784 | `48B7A95133BDEAB9D14EE947BAF44D5B475ED60B99D118EAC24B51C9E0561BD6` |

## 10. Work performed for this draft

Created this planning document only. No source, test, SRS, decision, approval, prior plan, or evidence file was changed. No test, typecheck, validator, linter, backend, database, migration, Docker, network, provider, Modal, stage, commit, or push command was run. Existing worktree changes were preserved.

This plan remains **DRAFT / NOT APPROVED / NOT LAUNCHED**. `OWNER_MODAL_CALL_APPROVED=NO`.
