# BE2-01 Phase A — candidate specification (fixture scope)

- Status: LOCAL_PROPOSAL (fixture scope only; not adopted stack/schema/policy)
- Date: 2026-10-14, Asia/Saigon (Q00 amendment same day: review findings R01–R11)
- Author: Claude (executor) under `approvals/TASK_APPROVAL.md` Phase A revision 1
- Sources: SRS v3.1 DATA-25 (l.1660), CMD-44 (l.1788), B19.10 (l.948), B19.11 (l.976), B22.1 (l.1706), B22.3 (l.1833), numeric table (l.770–790); FEAT-040 `BE_AI_TASKS.md` BE2-01/BE2-05/BE2-14; ADR-0015.

Every choice below is a Phase A implementation proposal. Names, numbers and namespace stay
`PROPOSED`/candidate until a cross-review/ADR adopts them. Phase B (durable storage, outbox,
real CAS, broker) is out of scope.

**Q00 amendment (2026-10-14).** Sections 1, 3, 4, 5, 6 and 9 were corrected after the
independent review (`evidence/notes/PHASE_A_CODEX_INDEPENDENT_REVIEW_20261014.md`, R01–R11).
Changes are marked “(Q00 Rxx)”. Status stays LOCAL_PROPOSAL; nothing is adopted by the fix.

## 1. Fingerprints and receipt identity

| Concept | Identity | Fingerprint / content |
|---|---|---|
| Command receipt (B22.1) | `(organization_id, principal_id, contract_name, target_id, idempotency_key)` | sha256 of canonical JSON (sorted keys, `,`/`:` separators, UTF-8, strings NFC-normalised) over the normalised command payload. Excluded: idempotency key, correlation id, client timestamps, transport headers. |
| CreateJob payload fields | — | `contract_name`, `job_type`, `target_id`, `purpose_code`, `scope.session_id`, sorted `scope.subject_refs`, `request_ref.{request_id, request_revision, input_hash, context_revision}` |
| CancelJob payload fields | — | `contract_name`, `job_id`, `expected_job_revision`, `reason_code` |
| Semantic request dedup (Q00 R02) | `(organization_id, job_type, request_id, request_revision, input_hash, context_revision, target_id, purpose_code, session_id, sorted subject_refs)` | Separate index, bound to the immutable authorized scope: the same request under a different target/session/audience/purpose is a different job, never a silent merge. A semantic hit returns the existing job under the caller's **own** new command receipt; it never returns another principal's receipt, and job reads still recheck authority. |
| Completion receipt (B22.3) | `(job_id, attempt_id)` | sha256 over normalised outcome: `kind`, sorted `result_refs`, `output_hash`, `moderation`, `failure_code`, `retryable`. Same identity + same fingerprint → prior receipt; same identity + different fingerprint → `COMPLETION_CONFLICT` incident, job unchanged. |
| Cancellation notice | `notice_id` | Replay of the same notice is a no-op. |

Replay order follows B19.11: parse → principal + disclosure authority → receipt lookup → (new only)
eligibility → semantic dedup → atomic commit.

## 2. `job_revision` and `attempt_number`

`job_revision` starts at 1 on create and increments on every change to the public view: start,
progress change, failure, requeue (retry), cancel, completion outcome, unsafe block, timeout.
It does **not** change on duplicate receipts, stale/rejected completions that leave the job
unchanged, queue redelivery or reads. ETag uses it.

`attempt_number` starts at 1 and increments only when the named retry policy requeues a
`failed_retryable` job. Queue redelivery and duplicate completion never create an attempt.

## 3. Completion disposition matrix

Checked in order after worker capability (internal only) and completion-receipt lookup.

**Authoritative vs non-authoritative (Q00 R03).** Only an outcome that changes the job (settles
the attempt) is stored in the immutable `(job_id, attempt_id)` slot; a later different claim for
that slot is `COMPLETION_CONFLICT`. Guard rejections that leave the job unchanged
(`JOB_CANCELLED`, `JOB_TERMINAL`, `ATTEMPT_SUPERSEDED`, `INVALID_STATE`, `INPUT_MISMATCH`,
`MALFORMED_CLAIM`) return a receipt with `authoritative=false`, are audited, and are not stored,
so a later valid claim of an unchanged active attempt can still complete it.

**Worker outcome boundary (Q00 R04).** Before any guard, the claim is normalised: unknown
`kind`/`moderation`, non-boolean `retryable`, a success carrying `failure_code` or a failure
carrying outputs → non-authoritative `rejected` / `MALFORMED_CLAIM`. Failure codes outside
`{PROVIDER_TIMEOUT, PROVIDER_UNAVAILABLE, PROVIDER_ERROR, OUTPUT_MALFORMED}` (including
malformed/sensitive strings) map to `PROVIDER_ERROR`; only a sha256 of the original reaches audit.
The domain also rejects failure/cancel codes not matching `^[A-Z][A-Z0-9_]{1,79}$`.
(Q00 R04a) A non-string, non-null `failure_code` (list, object, number, bool, bytes, set) is
type-checked before the allowlist lookup and returns non-authoritative `MALFORMED_CLAIM` (only a
sha256 of its repr is audited); a later valid claim of the attempt still lands. A non-string
`job_id`/`attempt_id` is a typed `400 MALFORMED_REQUEST` on the internal port. Fingerprints of
non-JSON values are computed from a typed repr instead of raising.

**Artifact scope (Q00 R01).** An output ref is valid, and may be quarantined, only when the
artifact port's descriptor has the job's organization **and** producer lineage equal to the
claim's `job_id`/`attempt_id`. Unknown, foreign-organization or other-job/attempt refs are never
mutated on any path; a success with such refs is `OUTPUT_MALFORMED`.

**Temporary vs final rejection of outputs (Q00 R03a).** `INVALID_STATE` and `INPUT_MISMATCH`
leave the attempt completable, so they change no artifact state (incident audited for
mismatch). Only final outcomes quarantine the attempt's own outputs: `JOB_CANCELLED`,
`JOB_TERMINAL`, `ATTEMPT_SUPERSEDED`, eligibility revocation, `UNSAFE_CONTENT`,
`OUTPUT_MALFORMED`. Admission additionally rejects any ref whose descriptor reports a
`quarantine_reason` (→ `OUTPUT_MALFORMED`), so an accepted, projected ref is never quarantined
and quarantined bytes are never released by a later claim.

| Condition | Receipt disposition | Job effect |
|---|---|---|
| Job terminal `cancelled` (incl. revocation) | `rejected` / `JOB_CANCELLED` (non-authoritative) | unchanged; owned output refs quarantined |
| Other terminal state, new identity | `stale` / `JOB_TERMINAL` (non-authoritative) | unchanged; owned refs quarantined |
| `attempt_id` not the active attempt (superseded/timed out/unknown) | `stale` / `ATTEMPT_SUPERSEDED` (non-authoritative) | unchanged; owned refs quarantined |
| Active attempt but job not `running` | `rejected` / `INVALID_STATE` (non-authoritative) | unchanged; no artifact change (Q00 R03a) |
| `request_revision`, `input_hash` or `context_revision` differs from the attempt's pinned request | `rejected` / `INPUT_MISMATCH` (non-authoritative) + audit incident | unchanged; no artifact change (Q00 R03a) |
| Current eligibility denied (consent revoked, session ended, recall, source expired, kill switch) | `rejected` / reason | `cancelled` with that reason; quarantined |
| Failure outcome, retryable, attempts remain | `accepted` | `failed_retryable`, `retry_not_before` set |
| Failure outcome, retryable, attempts exhausted / non-retryable | `accepted` | `failed_exhausted` |
| Success outcome flagged unsafe by moderation | `rejected` / `UNSAFE_CONTENT` | `blocked_unsafe`; quarantined |
| Success outcome malformed (no refs, unknown/foreign/other-lineage ref, hash mismatch) | `rejected` / `OUTPUT_MALFORMED` | `failed_exhausted` (non-retryable, per VIDEO_RETRY_BUDGET "schema errors not auto-retried") |
| Success but current `context_revision` ≠ pinned | `stale` / `STALE_CONTEXT` | `succeeded`, `result_disposition=stale`; refs kept for lineage, never projected |
| Success, all checks pass | `accepted` | `succeeded`, `result_disposition=accepted` |

`succeeded` never means Teacher-approved, played or session complete. Child projections never
carry result refs (exposure belongs to BE1 CMD-59/60 after BE2-05 exact review).

## 4. Atomic fake mutation boundary

`InMemoryAiJobStore.transaction()` holds one re-entrant lock for the whole unit of work and
stages writes (jobs, command receipts, semantic index, completion receipts, outbox, notices);
it commits only on clean exit and discards on exception. Job writes are compare-and-swap on
`job_revision`. This simulates one authoritative transaction; it proves fake semantics only,
not database isolation, durability or restart recovery (Phase B).

Dispatch: create/requeue writes an outbox entry in the same transaction; `dispatch_outbox()`
moves entries to the fake queue and drops entries for jobs that are no longer `queued`.
(Q00 R09) Before enqueue it rechecks current eligibility; a denied job is `cancelled` with the
owner reason, its entry dropped, no attempt created and nothing sent. Queue outage still leaves
the entry pending and the job recoverably `queued`.

ProviderCopyLifecycle purge (Q00 R05/R06): the registry's `scope_lock(organization, scope)` is
the fake atomic boundary around receipt lookup → single adapter dispatch → stored receipt →
copy save; the first stored receipt is returned to every caller. Replaying an older key returns
that request's own immutable result (computed from its stored receipt) and never mutates or
re-dispatches a copy a newer request already advanced; current state comes from `discover`.
(Q00 A18a) `cancel_scope` and `register_copy` read, dispatch and save under the same
`scope_lock`, so a cancellation in flight cannot overwrite a purge result/receipt (purge waits),
and a cancel after deletion leaves the deleted copy untouched.

## 5. DATA-25 candidate details

- Contract `AsyncJobView`, version `0.1-candidate`; unknown fields rejected (`extra=forbid`), no
  silent coercion (strict validation).
- Required non-null: `job_id`, `organization_id`, `job_type`, `job_revision>=1`, `request_ref`,
  `attempt_id`, `attempt_number>=1`, `state`, `created_at`, `updated_at`, `correlation_id`.
- Nullable: `result_disposition`, `started_at`, `completed_at`, `failure`, `poll_after_ms`.
  `progress` is always present; `result_refs` is a list (empty when none).
- Progress: `unknown` → `value=null`, `stage_label=null`; `stages` → `stage_label` non-null,
  `value` null or [0,100]; `percentage` → `value` number in [0,100].
- Timestamps must be timezone-aware; serialised in UTC (`Z`). Naive input is rejected.
- Consistency: terminal states require `completed_at`; `queued` requires `started_at=null`;
  `succeeded` requires `result_disposition` in {accepted, stale}; (Q00 R08) non-terminal states
  carry `result_disposition=null`; `result_refs` non-empty only when `state=succeeded` **and**
  `result_disposition=accepted`; `failure` required for failed/blocked states.
- (Q00 R11) State rules shared by the full and Child views: failed/blocked → `failure`
  required; `succeeded` → `failure` null; terminal → `poll_after_ms` null.

## 6. Role projections (CMD-44)

| Field | Teacher (`T`) | Admin ops (`A`) | Device/Child (`D`) |
|---|---|---|---|
| ids, job_type, job_revision, state, progress, timestamps, poll_after_ms, correlation_id | yes | yes | job_id, job_type, job_revision, state, progress, poll_after_ms only |
| request_ref, attempt_id/number | yes | yes | no |
| result_disposition | yes | yes | no |
| result_refs | only if `succeeded`+`accepted` **and** current eligibility allows | never | never |
| failure | full | full | `code`, `retryable`, `public_message` |

Teacher/Admin use `AsyncJobView` (DATA-25 full shape, result refs possibly empty);
Device uses `AsyncJobChildView` (minimal candidate). All reads go through authorization
(grant/scope) first; unauthorized and missing jobs both return `404 RESOURCE_NOT_FOUND`.

ETag: `"job:{job_id}:{job_revision}:{variant}"` where `variant` is a short hash of role,
exposure decision and (Q00 R10) the computed `poll_after_ms`, so revocation that hides refs or a
changed backoff hint changes the tag and is never hidden behind `304`. The retry-wait component
of the hint is rounded up to whole seconds so the tag changes stepwise. Authorization and
eligibility run before any `If-None-Match` comparison.

## 7. Named fixture policies (PROPOSED)

| Name | Values | Source |
|---|---|---|
| `fixture.job_retry.v0` | max_attempts 3; backoff 1000 ms ×2 capped 8000 ms; attempt timeout 30000 ms | SRS VIDEO_RETRY_BUDGET "2 auto retries" PROPOSED; timeout fixture-only (VIDEO_JOB_DEADLINE TBD) |
| `fixture.job_poll.v0` | min 2000 ms (`JOB_POLL_MIN_INTERVAL`), max 10000 ms, doubling every 10 s without update | SRS JOB_POLL_MIN_INTERVAL PROPOSED |

No legacy hard-coded value is adopted; production values need a versioned policy decision.

## 9. Candidate shape validator (Q00 R07)

`check_shape` treats an enum field as valid only when the value is a string in the allowed set;
lists, objects, null and numbers return deterministic validation errors and never raise.

## 8. Namespace

HTTP route `GET {prefix}/jobs/{job_id}` with candidate prefix `/api/collaboration/v1`
(B22.1 proposal), mounted only in `interfaces/http/ai_jobs_fixture_app.py`. The live
`create_app()` composition is not modified. No worker completion route exists.
