# B1 P2 Independent Review — 2026-11-04

**Review disposition:** F1 **ACCEPTED**; F2 **NOT_DETERMINED**; overall B1 P2 **NOT ACCEPTED**. Keep the handoff at **XONG-CHƯA REVIEW** until the owner decisions and the unverified PostgreSQL acceptance are resolved.

**Scope:** Cold review of the B1 P2 Addendum 4 artifact-fence change and its evidence. The review followed the FEAT-064 context, source register, status, approval record, and the ordered B1 implementation / P2 plan / blocked review / Addenda 2–4 dossier. It made no source, test, status, approval, plan, or snapshot changes. It added this report and kept run logs in a task-local directory under TEMP.

## R1 — Baseline, scope, and implementation comparison

Baseline before review:

- Branch: feature/feat063-be-foundation
- HEAD: b6dbfa68e66718f3f40902c093e9ebd634b1ebb9
- Index: empty
- Existing dirty status entries: 107
- Review report target did not exist at baseline.

The four requested final-file SHA-256 values matched the Addendum 4 manifest:

| File | SHA-256 |
|---|---|
| backend/src/sketch2life/infrastructure/vision_analysis/pilot_composition.py | D79726EAEB949DA5EDBC7C95F5AF5C101A3BFC29A9114A165B35F7EB71C6AE9F |
| backend/tests/integration/test_be1_synthetic_pilot_postgres.py | 25278C81DC842265B2CC73F7E62C8D9CBA4275B87983A3E8AF61DC9918244C7C |
| backend/tests/unit/test_be1_pilot_artifact_fence.py | 364C430A317F569082F2578CA1EB190DB871F9E39D0ACEF6FE5459A309763756 |
| backend/tests/unit/test_pilot_queue_composition_b1.py | 5917CAAD6E318765CBA2026CA513D6FAED9C22BD0D739052F5D64E96EBC711F4 |

Snapshot baseline/final comparison, after normalizing line endings:

- The queue-composition unit test is identical between baseline and final.
- The final hold-before-send test now expects no worker dispatch and no provider call after eligibility is revoked. This matches the intended pre-send gate; the earlier helper incorrectly required one captured worker message.
- The final stale-facts test injects the owner-fact revision change after a successful provider call and before completion is decided. That places the race at the intended boundary. Earlier attempts failed for fixture/test-rewrite reasons recorded in the snapshot logs; the final three saved runs passed. These earlier attempts do not establish flakiness in the final test.
- The test now asserts WorkerOutcome status rejected and persisted result disposition is not accepted. Because the latter permits NULL, it does not establish a durable rejected disposition or receipt; see FND-05.
- Addendum 4 adds the canonical artifact-fence scope, store epoch/quarantine checks, and tests. Existing auth and BE1-facts paths still route to their prior checks; duplicate and unknown scopes fail closed. No AI Jobs service/repository, schema, migration, or route file changed during P2. app.py and be1_runtime.py match the earlier P2 blocked snapshot; their initial local composition wiring was part of the P2 scope.

## R2 — Findings

| ID | Severity | Finding and evidence | Minimal follow-up |
|---|---|---|---|
| FND-01 | P2 | The artifact check is a point-in-time check, not a lock held through SQL commit. PilotFakeArtifacts.hold_fences releases its process lock before returning (pilot_composition.py:428–447); AiJobService then performs CAS, receipt, and outbox writes before transaction commit (ai_jobs.py:871–884; SQL transaction:repository.py:986–1003). A concurrent quarantine after the check and before commit can make the artifact stale while the job still commits acceptance from the earlier check. The generic port says owner fences are held until commit (application/ports/ai_jobs.py:366–368). This race is not covered by the test that quarantines before the completion fence. | Owner decision (c): decide whether point-in-time process-local checking is sufficient for this local synthetic pilot, or whether quarantine must be excluded/rechecked through commit. Do not treat this review as making that product/architecture decision. |
| FND-02 | P2 | Stale-facts completion can exhaust the bounded STALE_CONTEXT decision rounds without settling the job. The Addendum 3 diagnostic recorded job_state running, result_disposition null, no completion receipt, and no attempt outcome after two failed holds; the current stale-owner test only checks that the job is not succeeded and that result disposition is not accepted (test_be1_synthetic_pilot_postgres.py:3447–3497). The current final PostgreSQL case was skipped in this review, so this state was not remeasured after Addendum 4. | Owner decision (d): decide whether stale completion should persist a terminal rejection/receipt or remain running for an explicit recovery path. The current evidence does not settle the intended lifecycle. |
| FND-03 | P2 evidence gap | The required crash/restart-after-durable-SENT guarantee is not demonstrated against the PostgreSQL ledger. The BE1 UNKNOWN test reuses the same composition and envelope and observes UNKNOWN (test_be1_synthetic_pilot_postgres.py:3378–3399). The separate restart test uses MemoryInvocationLedger, not a newly constructed PostgreSQL-backed ledger (test_invocation_guard_transport_ga1.py:545–558). The six focused PostgreSQL nodes were skipped in this review. | Add a focused PostgreSQL restart test that reconstructs the guard/worker around the existing durable SENT row and proves no second provider request. |
| FND-04 | P3 evidence gap | The successful PostgreSQL helper reads persisted completion_receipts (test_be1_synthetic_pilot_postgres.py:3188–3199, 3232–3239), but the success test does not assert that tuple (3303–3370). The service source writes the receipt in the same transaction as the job CAS (ai_jobs.py:880–884; repository.py:540–554), but the current test does not directly verify the durable row. | Assert exactly one persisted authoritative completion receipt with the expected disposition and revision in the success case. |
| FND-05 | P3 evidence gap | The stale-owner test permits result_disposition to be NULL because it asserts only not accepted (test_be1_synthetic_pilot_postgres.py:3488–3496); WorkerOutcome rejected is not a durable receipt. It therefore can pass without proving the intended durable negative decision. This overlaps the lifecycle question in FND-02 but is a separate assertion gap. | Once owner decision (d) is recorded, make the test assert the selected durable state and receipt semantics. |
| FND-06 | P3 coverage gap | Artifact digest equality is implemented, but the unit case labelled sha256 substitutes the malformed string forged (test_be1_pilot_artifact_fence.py:151–190). It exercises parser rejection, not a syntactically valid 64-character digest that differs from the stored digest. | Add a valid-format mismatching digest case to prove metadata binding independently of format validation. |
| FND-07 | P3 maintainability | Strict mypy reports nine errors in the changed pilot_composition.py: one attr-defined and eight no-untyped-def. The new focused unit files have no remaining errors. | Owner decision (e): decide whether this pre-existing/newly visible strict-typing debt is accepted for this pilot handoff or needs a narrow typing addendum. Avoid broad unrelated annotation changes. |

The implementation visibly fails closed for malformed/noncanonical scopes, duplicate scopes, unknown scopes, missing artifacts, quarantined artifacts, organization/digest mismatch, invalid epoch type, stale epoch, and caught owner-fence exceptions. The unit tests cover these categories, though the valid-format digest mismatch remains untested. The store is explicitly process-local and non-durable; that known limitation does not remove the in-process hold-to-commit race in FND-01.

## R3 — Test evidence and NOT RUN items

### Independently run in this review

| Command / scope | Result |
|---|---|
| From backend: .\.venv\Scripts\python.exe -m pytest -o addopts= -q --tb=short tests/unit/test_be1_pilot_artifact_fence.py tests/unit/test_pilot_queue_composition_b1.py | 27 passed, exit 0 |
| From backend, one invocation per node: .\.venv\Scripts\python.exe -m pytest -o addopts= -q --tb=short tests/integration/test_be1_synthetic_pilot_postgres.py::<node> | Each of six nodes skipped, exit 0; 0 passed. Nodes: test_b1_succeeded_is_durable_before_real_app_result_acceptance; test_b1_unknown_after_sent_is_not_accepted_or_replayed; test_b1_hold_before_send_creates_no_result_or_invocation; test_b1_stale_owner_fence_rejects_result_after_provider_success; test_b1_stale_artifact_fence_rejects_result_after_provider_success; test_b1_concurrent_duplicate_delivery_uses_one_attempt_and_one_send. |
| Offline regression runner | **NOT RUN** because the Addendum 4 gate requires every focused PostgreSQL case to pass first, and this review observed skips rather than passes. The implementer-reported command was backend/.venv/Scripts/python.exe .claude/handoff/snapshots/GB1_P2_A4_20261104T142953/run_offline_with_b1_addons.py .claude/handoff/snapshots/GB1_P2_A4_20261104T142953/offline_check.py. |

The PostgreSQL fixture skips before creating a connection when BE1_TEST_DATABASE_URL is absent (test_be1_synthetic_pilot_postgres.py:371–384). No alternate environment flag or database URL was supplied, and no database connection was made. The skipped nodes were: success-before-acceptance, UNKNOWN, hold-before-send, stale owner facts, stale artifact, and concurrent duplicate delivery. This is an environment-gated result, not a pass.

### Implementer-reported snapshot evidence, not independently verified here

- Three final focused PostgreSQL repetitions are recorded in the Addendum 4 snapshot, each with six named nodes passing: 18 passing node logs total.
- The saved offline regression log reports 460 passed.
- The final Addendum 4 report records the exact snapshot and per-run logs. Those results are attributed to the implementer; this review did not reproduce them.
- The snapshot also contains earlier failed attempts before the final test rewrites. The final saved repetitions passed, so the earlier failures are not evidence of final-code flakiness.

The offline GA1 test does show a restarted guard refusing a repeat call when its ledger reports SENT, but its ledger is in memory. It does not fill the PostgreSQL restart evidence gap in FND-03.

## R4 — F1: application composition gate

**F1 verdict: ACCEPTED.**

The real-app composition contract passed independently: .\.venv\Scripts\python.exe -m pytest -o addopts= -q --tb=short tests/contract/test_app_composition.py::test_real_app_composes_pilot_only_for_valid_local_synthetic_gate reported one passed. The test checks enabled local/test synthetic PostgreSQL composition and disabled/invalid gates. Source wiring is present in app.py:731–733 and runtime gating is in be1_runtime.py:94–125; the pilot factory also enforces local/test, enabled flag, and PostgreSQL at pilot_composition.py:921–932.

A separate route-surface comparison produced three failures on both the current checkout and a detached clean-HEAD worktree: compatibility route set, classroom /health, and demo /v1/sessions expectations. These are baseline failures on HEAD, not regressions introduced by B1 P2. The temporary detached worktree was removed after comparison.

## R5 — Static checks and repository validators

| Check | Independently observed result |
|---|---|
| Ruff: ruff check --no-cache --config backend/pyproject.toml on the four scoped source/test files | Pass: All checks passed, exit 0 |
| Ruff: ruff format --check --no-cache --config backend/pyproject.toml on those files | Exit 1: two files would be reformatted (pilot_composition.py and the pre-existing dirty PostgreSQL integration test); two already formatted. No formatting changes were made. |
| Strict mypy: --strict --no-incremental --cache-dir under TEMP --config-file backend/pyproject.toml on the four scoped files | Exit 1: 69 errors in 2 files; four files checked. |
| python tools/validate_harness.py | HARNESS_VALID, exit 0 |
| python tools/validate_repository_security.py after report creation | REPOSITORY_SECURITY_VALID; 6,412 files scanned; absolute machine paths absent; exit 0 |
| python tools/validate_architecture.py | ARCHITECTURE_VALID, exit 0 |
| git diff --check | Exit 0; only existing CRLF/LF notices |

Mypy breakdown: pilot_composition.py has 9 errors (8 no-untyped-def, 1 attr-defined). The existing dirty PostgreSQL integration test has 60 (44 no-untyped-def, 1 no-any-return, 2 union-attr, 9 arg-type, 2 no-untyped-call, 1 attr-defined, 1 var-annotated). The two new unit tests have no errors. The earlier snapshot final2 mypy log reports 76 errors; comparing diagnostics shows seven extra errors in that earlier test version (three no-untyped-def and four arg-type), with no diagnostics present only in the current run. The 69-error result is for the current final bytes and the same four logical files.

## R6 — Scope, security, and workspace boundary

- Current pre-report status matched the recorded baseline count of 107 dirty entries; index remained empty. After adding this report, the status count is 108, consisting of the same 107 entries plus this one new untracked report; the index remains empty.
- The AI Jobs service, SQL repository, AI Jobs ports, vision-analysis ports, and worker were baseline-clean for P2. owner_fence.py and be1_registry.py match their earlier P2 snapshot hashes. app.py and be1_runtime.py match the P2 blocked snapshot captured before Addendum 4.
- No tracked schema or migration path appears in the P2 diff. No route change was made for P2.
- Repository security validation passed. Review logs are local under TEMP at sketch2life-feat064-b1p2-independent-review-20261104; no connection URL, credential, token, absolute local path, or child data is included in this report.
- The only repository artifact created by this review is this report; local logs are under TEMP. Existing unrelated worktrees were left untouched; the temporary detached comparison worktree was removed. No commit or stage occurred.

## R7 — Current flow, invariants, and remaining decisions

1. The local/test pilot is constructed only when the feature flag is true and the app has PostgreSQL. The source artifact store supplies local input bytes; PilotFakeArtifacts stores synthetic output descriptors in process memory.
2. On successful provider completion, GuardedVisionJobProvider requires a succeeded invocation guard and authoritative analysis result before writing a synthetic output descriptor (pilot_composition.py:533–595). The descriptor carries a canonical artifact scope bound to artifact reference, organization, SHA-256, and epoch.
3. AiJobService re-reads job and completion state, decides the result, and includes the eligibility and artifact fences. Under its SQL unit-of-work transaction it checks the fences before mutating the job, inserts the completion receipt, and records outbox effects; the transaction commits before best-effort side-effect delivery (ai_jobs.py:821–903, 1068–1124, 1216–1222, 1370–1384; SQL repository.py:540–561, 986–1003).
4. The artifact fence check verifies exact integer epoch, canonical scope, current artifact existence, not quarantined, organization/digest match, and current epoch while holding the fake store lock (pilot_composition.py:428–447). First quarantine increments the epoch (449–454). The lock ends before SQL commit, creating FND-01.
5. The invocation ledger persists CLAIMED then SENT before the provider call, and allows terminal SUCCEEDED/FAILED/UNKNOWN only from SENT (vision_analysis/ledger.py:64–139). A new guard treats prior SENT or UNKNOWN as an unknown prior outcome and refuses to send again (invocation_guard.py:55–103). The state machine is plausible from source, but real PostgreSQL process-restart evidence is missing here.
6. The success integration test verifies persisted invocation SUCCEEDED before result acceptance, ordered head → observation → provider_result insertion, accepted job state, a result reference, one analysis, one attempt, and one provider call (test_be1_synthetic_pilot_postgres.py:3303–3370). It does not assert the persisted receipt row, as recorded in FND-04.
7. The stale-facts diagnostic has previously observed an unsettled RUNNING job after owner-fence rejection. The current test does not pin a terminal or recoverable state. Owner decision (d) remains open. Owner decision (c) is also open for the artifact-check lifetime. Owner decision (e) concerns the typing debt identified in R5.

## Verdict and report hash

F1 is **ACCEPTED**. F2 is **NOT_DETERMINED** because all six independent PostgreSQL node runs skipped at the environment gate and the offline runner was therefore **NOT RUN**. Overall B1 P2 is **NOT ACCEPTED** by this independent review; the owner decisions and evidence gaps above remain.

The final SHA-256 of this report is supplied in the handoff message after the file is frozen.

