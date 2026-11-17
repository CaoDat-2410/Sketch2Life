# T2B rework to the owner decision record

- Status: **APPROVED for the bounded implementation recorded in the appended T2B rework approval**.
- Feature: FEAT-064, synthetic-only current-flow pilot.
- Baseline HEAD: `20e87e17931ec18f4e99ddbe52ea7118b94159dc`, direct child of `9f337affdc142978f6ba5de0124bae2574528f62`.
- Canonical decision inputs (read-only):
  - `evidence/OWNER_DECISIONS_T2B_T3_20261101.md`, SHA-256 `53F588785258FDBC43ED53FE9A45A72D58209916F7E63647CBFE1C7E2136AB64`.
  - `plan/T2B_BE1_TO_BE2_FACT_ADAPTER_PLAN_20261101.md`, SHA-256 `781A561AEC08BF0990AA18CBDBD27DB7CEB84CB23EA3CDD5ABB483A6A10D83C7`.
  - `plan/T3_STROKE_PROFILE_AND_UI_BLOCKERS_PLAN_DRAFT1_20261101.md`, SHA-256 `8BD963281672AB97599E2B26CBA500AB629C5F3BAF076ED48B1735E1FEFA1F70`.

## 1. Goal and changed design

Replace the earlier T2B implementation's constant age revision / child-ID provenance and integer-only freshness with the owner's selected persisted age provenance plus a separate, versioned SHA-256 context digest. Preserve `context_revision` as a compatibility integer. Keep A2 and A4–A6 as recorded: consent fields are nullable only for synthetic facts, synthetic consent remains ineffective, and this task supplies only `MemberFact` plus `ContextDecision` for one audience member in `IMAGE_ONLY` mode. No legal path is opened by this work.

## 2. R1 source inventory

The inventory was reopened at baseline HEAD above. Line references below refer to that source revision.

| Concern | Current evidence | Consequence for this task |
|---|---|---|
| Age writes | `backend/src/sketch2life/interfaces/http/routers/be1_registry.py:349-361` creates the adult-declared profile and writes `age_months` at 358. `backend/src/sketch2life/infrastructure/persistence/core_store.py:486-516` creates the synthetic profile and writes it at 508. No managed-profile age update route or `age_months` ORM/Core update was found in `backend/src/sketch2life`. | Add explicit provenance to these two creation paths. Keep the static detector's creation allowlist; no age-edit route is added. Any future age mutation must update `age_months` and increment `age_revision` atomically in the same statement. |
| Profile schema | `backend/src/sketch2life/infrastructure/persistence/be1_models.py:98-140` has `age_months` but no persisted age source or revision. | Add the two owner-pinned columns and closed checks. |
| Existing legal profile-create gate | `backend/src/sketch2life/interfaces/http/routers/be1_registry.py:328-342` only creates a profile when the consent lookup finds `state == "effective"`; `ConsentRecordModel` at `backend/src/sketch2life/infrastructure/persistence/be1_models.py:212-216` has a CHECK limited to `pending` or `revoked`, and the existing `backend/tests/integration/test_be1_postgres_api.py:660-698` confirms pending consent is refused. | Do not alter legal-consent/schema behavior in T2B. Verify registry writer assignment with an offline unit seam; the PostgreSQL route-create subcase cannot be performed without an out-of-scope consent-state change and will be reported NOT DONE. |
| Existing age detector | `backend/tests/unit/test_profile_age_invariant.py:108-208,231-290` detects constructor, assignment, SQLAlchemy update, bulk and raw-SQL shapes (fixtures a–g). | Retain all existing detector cases; add paired-age/revision update assertions without authorizing an update path. |
| Reader snapshot | `backend/src/sketch2life/infrastructure/assistance/be1_fact_reader.py:49-73` carries age but no persisted age source/revision. `_context_payload` at 157-184 hardcodes revision 1; `MemberFact` at 323-327 uses `be1-profile-age-v1:{child_id}`; `ContextDecision` is built at 342-357. No PostgreSQL-backed `BE1FactSource.current_facts()` implementation is present in `backend/src/sketch2life`. | Extend the snapshot and reader contract. Report the missing production source/runtime wiring as NOT DONE; do not create it here. |
| Current integer freshness | `backend/src/sketch2life/infrastructure/assistance/context_revision.py:10-41` canonicalizes sorted scalar JSON with the v1 domain separator and returns the first signed 31-bit SHA-256 value. `be1_fact_reader.py:322` computes it from `_context_payload`. | Keep the domain separator and 31-bit extraction; compute the full prefixed digest from the same bytes. Set payload schema to `be1-fact-context-v2` and add stored `age_revision` and `age_source`; do not include read time. |
| Vision equality sites | `backend/src/sketch2life/application/services/vision_analysis.py:392,461,556,618` compares integer revisions; `:761-769` delegates applicability. `backend/src/sketch2life/domain/vision_analysis.py:868-940,988-996` stores an internal `AnalysisHead` with integer revision and checks equality in `is_applicable`. | Compare the versioned digest alongside the integer at these service/head boundaries. Missing digest on either side when the other is present is stale/fail-closed. Keep legal callers with no digest unchanged. |
| Vision claim boundary | `backend/src/sketch2life/domain/vision_analysis.py:331-422` pins request/observation lineage with `context_revision` only. BE2 `ObservationClaim` has no whole-context digest. | Do not extend this claim or its external gateway contract in this task. A `ContextDecision` with a digest cannot match an integer-only synthetic claim and must be refused before provider invocation. Synthetic end-to-end inference therefore remains NOT DONE pending a separately approved gateway/claim change. |
| AI Jobs boundary | `backend/src/sketch2life/application/ports/ai_jobs.py:93-147`, `backend/src/sketch2life/contracts/schemas/ai_jobs.py:44-46,219-222`, `backend/src/sketch2life/infrastructure/ai_jobs/sql/tables.py:193`, and `backend/src/sketch2life/application/services/ai_jobs.py:1116-1118` store/send/compare only integer `context_revision`. | This is an AI Jobs claim/persistence contract, not `ContextDecision`. Adding its digest needs ports, public schemas, queue/repository and SQL changes outside this allowlist. Keep current behavior and record digest propagation there as NOT DONE. |
| Assistance and typed-context digests | `backend/src/sketch2life/application/services/assistance.py:926,1112,1169-1171` uses `assistance_context_digest` for its own request facts. `domain/vision_analysis.py:650-681`, `infrastructure/vision_analysis/context_adapter.py:133-158,273-277`, and `contracts/schemas/analysis_context_results.py:52-63,108-132` use the distinct typed-context binding digest. | Do not conflate either digest with the new BE1 whole-fact digest or change their contracts. |
| Migration graph | Static Alembic `ScriptDirectory` inventory at baseline: 23 revisions and 10 terminal heads. `backend/tests/integration/ai_jobs/test_migrations.py:41-48` explicitly models the six-revision `BE1_CHAIN`, currently headed by `20261031_be1_se_0001`. | Add revision `20261101_be1_age_0001` with sole parent `20261031_be1_se_0001`; update that explicit chain to seven entries. The graph should then have 24 revisions and still 10 terminal heads. |

## 3. Pinned data and digest contract

### Age provenance

- `ManagedProfileModel.age_revision`: integer, non-null, default and server default 1, CHECK `age_revision >= 1`.
- `ManagedProfileModel.age_source`: non-null string with CHECK membership in exactly `LEGACY_UNKNOWN`, `SYNTHETIC_FIXTURE`, `ADULT_DECLARED`.
- New migration: `backend/alembic/versions/20261101_be1_age_provenance.py`; revision `20261101_be1_age_0001`; sole `down_revision = "20261031_be1_se_0001"` on the existing `be1_core` chain. Existing profiles are backfilled to revision 1 / `LEGACY_UNKNOWN`; do not infer source from ID, timestamps, session revision or other fields. Downgrade removes only the two columns and their checks.
- Registry profile creation writes `ADULT_DECLARED`, revision 1. The operator synthetic profile creation writes `SYNTHETIC_FIXTURE`, revision 1. No age-update route is introduced. A future actual age change must update the value and increment revision atomically; a source-only correction does not increment age revision.
- Reader provenance reference: `be1-profile-age-v2:{age_source}:{age_revision}`; it contains no child ID.

### Whole-context digest

- `ContextDecision.context_digest` is optional for backwards compatibility and uses `sha256:<64 lowercase hex>`.
- The digest input is the existing strict canonical scalar JSON payload plus stored `age_revision` and `age_source`. The schema value in the payload is `be1-fact-context-v2`. Retain the current `sketch2life/context-revision/v1\n` domain separator, sorted compact UTF-8 JSON and positive signed-31-bit extraction; derive the integer from the first 31 bits of the same full SHA-256 digest. Preserve the integer field and do not order revisions.
- Exclude `evaluated_at` and any read timestamp. Proof, consent, profile, membership, session, purpose and pilot inputs already in the payload remain represented. Each relevant input change must change digest or produce an eligibility denial.
- When comparing two context pins, integer revisions must match and, if either side has a digest, both must carry the identical digest. A digest-bearing context compared with an integer-only Vision claim or correction request is stale/refused. Synthetic fact contexts missing a digest are invalid. Legal legacy contexts with no digest keep prior behavior.
- No AI Jobs SQL/queue/API digest field is authorized here. The known integer-only gateway boundary is fail-closed; this task does not claim a live synthetic request can traverse it.

## 4. Files authorized

### Implementation and tests

Only these exact paths may change:

- `backend/src/sketch2life/infrastructure/persistence/be1_models.py`
- `backend/src/sketch2life/infrastructure/persistence/core_store.py`
- `backend/src/sketch2life/interfaces/http/routers/be1_registry.py` (profile creation only)
- `backend/src/sketch2life/infrastructure/assistance/be1_fact_reader.py`
- `backend/src/sketch2life/infrastructure/assistance/context_revision.py`
- `backend/src/sketch2life/application/ports/vision_analysis.py`
- `backend/src/sketch2life/application/services/vision_analysis.py`
- `backend/src/sketch2life/domain/vision_analysis.py` (needed to retain/compare the digest on internal AnalysisHead replay)
- New `backend/alembic/versions/20261101_be1_age_provenance.py`
- `backend/tests/unit/test_profile_age_invariant.py`
- `backend/tests/unit/test_be1_fact_reader.py`
- `backend/tests/unit/test_context_revision.py`
- `backend/tests/unit/test_synthetic_audience_limit.py` only if the new snapshot fields require fixture changes
- `backend/tests/contract/test_be1_fact_reader_contract.py`
- `backend/tests/integration/ai_jobs/test_migrations.py`
- `backend/tests/integration/test_be1_synthetic_pilot_postgres.py`
- New `backend/tests/unit/test_age_provenance_columns.py`
- New `backend/tests/unit/test_context_digest_equality.py`
- New `backend/tests/integration/test_be1_age_provenance_postgres.py`

The digest changes in `domain/vision_analysis.py` and `application/services/vision_analysis.py` are required for the integer-only claim to fail closed when the current context has a digest, and for internal replay to compare digest equality. No digest claim field is added to AI Jobs or public request schemas.

### Documentation and approvals

- New `plan/T2B_REWORK_TO_OWNER_RECORD_PLAN_20261101.md` (this file).
- New `evidence/notes/T2B_REWORK_REPORT_20261101.md`.
- Update `evidence/notes/T2B_DECISION_DIVERGENCE_20261101.md` to `RESOLVED` after implementation, describing the exact reconciliation.
- Append only to FEAT-064 and FEAT-063 `approvals/TASK_APPROVAL.md` as listed below. Preserve all existing entries byte-for-byte.

## 5. Exclusions and known limitations

- No edits to the owner decision record, canonical T2B plan, T3 plans, Rev2 plan or their approval entries.
- No router/runtime/composition wiring beyond the profile-creation call; no new age-update endpoint; no `BE1FactSource` PostgreSQL implementation; no public Vision contract or AI Jobs SQL/queue/schema changes; no T2C, B4b, T3 code, B5/B6 code, Child/Teacher UI, Modal/GPU or external provider request.
- A digest-bearing synthetic fact cannot pass the current integer-only `ObservationClaim` or correction-input boundary. It is rejected before provider execution until a separately approved cross-process contract change carries the digest. This is an intentional safety boundary, not a successful end-to-end pilot result.
- Legacy profile rows receive explicitly unknown provenance; downgrade necessarily discards the added age provenance columns. No real-child data is used.

## 6. Test and validation matrix

| Area | Required evidence |
|---|---|
| Age columns and migration | Offline upgrade/downgrade SQL, exact revision and parent, columns/non-null/defaults/CHECKs, legacy backfill to `1`/`LEGACY_UNKNOWN`, no unrelated schema mutation. |
| Writers and invariant | Registry creation = `ADULT_DECLARED`/1; operator creation = `SYNTHETIC_FIXTURE`/1; detector cases a–g remain caught; no age mutation path is added; a paired age-change/update assertion requires `age_revision + 1` in the same update. |
| Reader | Reject absent/invalid age source or revision; provenance reference uses only source/revision; consent references remain `None` for synthetic and `consent_effective=false`; existing one-member IMAGE_ONLY rules stay in force. |
| Digest | Stable across mapping insertion order; correct `sha256:` format; excludes read time; each frozen input affects digest; integer revision is derived from the same digest using the existing positive 31-bit algorithm; v1 legal contexts without digest remain valid. |
| Vision freshness | Equal integer + equal digest proceeds at the internal matching helper/head; mismatch, missing peer digest, synthetic missing digest are stale/fail-closed; the integer-only claim path refuses a digest-bearing context before provider invocation; typed-context digest remains independent. |
| PostgreSQL | New migration test for old-row backfill and checks; the T1 synthetic pilot test still passes; new real-PG test covers both creation sources and cleans only rows it created. R5 is conditional on all five database safety checks. |
| Regression | R0 offline tests and known baseline failures are rerun at R6. Ruff, mypy (zero new errors), validators, byte/whitespace checks and repository security are recorded with real outputs. |

## 7. Approval scope

This task approval is limited to the exact paths in §4, the behavior in §3 and the tests in §6. It pins the age-source enum above and the new migration id/parent. PostgreSQL authorization is limited to one disposable database whose name contains `be1_acceptance`, connected through loopback, after the safety checks in `CODEX_PROMPT_T12_POSTGRES_RUN_20261101.md` pass. Writes are only repository Alembic migrations and test-owned synthetic rows using `synthetic-` identifiers; no `DROP`/`TRUNCATE`, no deletion of non-test rows, no other database, no Modal/GPU, no external provider, and no real-child data.

The same owner instruction separately confirms the exact proposed T3 allowlist in §1 of DRAFT1 for documentation only. It adds no paths and does not approve T3 code.

## 8. Acceptance and completion boundary

- Persisted age provenance follows §3, with historical source explicitly unknown and no inferred facts.
- Whole-context digest is a distinct versioned field; the legacy integer is preserved and derived from the same canonical digest. Every in-scope equality boundary compares both or fails closed when one peer lacks the digest.
- A2 synthetic consent invariants and A4–A6 boundaries remain unchanged.
- No unapproved path changes. The AI Jobs cross-process propagation gap and absence of a PostgreSQL-backed `BE1FactSource` are reported as NOT DONE.
- R5 database results are reported only if every safety gate passes; otherwise R5 is NOT RUN and offline phases still complete.
- No Modal or full end-to-end AI result is claimed. No push is allowed.
