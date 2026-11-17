# T2C — scoped BE1 facts, authoritative canvas source, and digest pin (GA2)

- Status: **APPROVED for this synthetic-only GA2 task by the owner's direct launch message**, subject to the append-only approval entry pinning this file's SHA-256.
- Parent: GOAL A2 REV2; V4 §1 and §3 D4; existing T2C blocker disposition is historical and remains unchanged.
- Goal: provide the PostgreSQL-backed BE1 facts and T4/T5 source/admission adapters needed by the existing BE2 assistance/Vision contracts, and pin freshness to the complete `ResolvedFacts` digest.

## Decisions and boundaries

1. `BE1FactSource.current_facts()` reads the requested organization/class/session/child/purpose scope in one SQL statement. The query must return one unambiguous row; missing or duplicate profile/membership/proof/group facts fail closed. The request purpose must equal `be1_sessions.configuration["purpose_ref"]`, and the selected synthetic proof must match the session's server-owned `pilot_run_ref` and session scope.
2. `AssistanceOwnerPort.members(..., *, scope=None)` remains callable without `scope` for old consumers. The new pilot PostgreSQL adapter requires a matching `EligibilityScope`, one participant, and a matching purpose; missing/mismatched scope returns no member facts. Existing fakes retain their no-scope behavior.
3. `PILOT_SYNTHETIC_POLICY_V1` is an explicit, immutable **test/pilot-only** profile, not a production policy decision: policy id/version `PILOT_SYNTHETIC_POLICY_V1`/`1`; purpose `ai_drawing_assistance`; enabled; `level_fx_1` and `level_fx_2`; debounce 5 seconds; per-target 3; per-session 20; cache enabled; age ref `age-policy:36-155-months:proposed`; region revision 2; only `region_fx_open` (unrestricted). Values follow existing synthetic fixtures where they exist; this profile grants no legal consent and cannot be used outside the synthetic local/test gate. No production-region or policy semantics are inferred.
4. `AssistanceSourcePort` resolves only a current T4 `CanvasSourceExportV1` binding and its T5 persisted render/receipt artifacts. T4 is passed as an injected callable to avoid an infrastructure-to-HTTP import. A Teacher checkpoint payload is never read. The adapter verifies source/export revision and epoch, asset organization and lineage, stored bytes hashes, canonical `CanvasAdmissionReceiptV1`, admission policy, and render binding; ambiguity or any mismatch returns unavailable.
5. `AssistancePin.context_digest` is `"sha256:" + request.facts.digest()`. A pilot `AnalysisContextPort` adapter obtains current recomputed `ResolvedFacts` for that same assistance request and returns its `context_digest` and the `context_revision` carried by those facts. It must not copy `BE1FactReader`'s distinct digest. `VisionAnalysisService` uses the pin digest as the expected digest in both pre-provider and post-provider freshness checks. Existing pins with no digest preserve current compatibility behavior.
6. Synthetic contexts remain `consent_effective=False` and `purpose_granted=False`, with the versioned synthetic eligibility basis/evidence already required by the existing gate. No consent row, consent-effective value, migration, route, composition, or provider is added.

## Exact allowlist

Source:

- `backend/src/sketch2life/application/ports/assistance.py`
- `backend/src/sketch2life/application/services/assistance.py`
- `backend/src/sketch2life/application/services/vision_analysis.py`
- `backend/src/sketch2life/domain/vision_analysis.py`
- `backend/src/sketch2life/infrastructure/assistance/be1_fact_reader.py`
- `backend/src/sketch2life/infrastructure/assistance/harness.py` (only where needed to assemble the digest-aware context)
- New: `backend/src/sketch2life/infrastructure/assistance/pilot_policy.py`
- New: `backend/src/sketch2life/infrastructure/assistance/postgres_fact_source.py`
- New: `backend/src/sketch2life/infrastructure/assistance/be1_owner_adapter.py`
- New: `backend/src/sketch2life/infrastructure/assistance/be1_canvas_source_adapter.py`
- New: `backend/src/sketch2life/infrastructure/vision_analysis/resolved_facts_context.py`

Tests:

- New `backend/tests/unit/test_assistance_t2c_adapters.py`
- New `backend/tests/unit/test_t2c_digest_pin.py`
- `backend/tests/unit/test_assistance_service.py` only for scope/no-scope compatibility assertions if the new focused modules cannot cover the public call boundary.
- `backend/tests/integration/test_be1_synthetic_pilot_postgres.py` only for T2C source, T4/T5 adapter, and digest assertions using its existing disposable synthetic harness.
- `backend/tests/unit/test_sketch_generation_chain.py` and the existing assistance test modules are regression-only; do not edit them unless an independently demonstrated compatibility failure is inside the stated `members()` contract.

Task records: this plan, one new T2C report, append-only FEAT-064 approval/goal-ledger entries, and one GA2 snapshot. No other path is allowed.

## Implementation sequence and acceptance

| Layer | Work | Acceptance evidence |
|---|---|---|
| L1 contracts/domain | Add optional keyword-only `scope` to `members`; append validated optional `context_digest` to `AssistancePin`. | Old no-scope call works; malformed digest rejected; positional pin construction remains compatible. |
| L2 application | Reuse one `_current_resolved_facts()` path for current digest and context adapter; expose a read-only current-facts lookup by assistance id; pin request digest; pass scope to the scoped owner adapter; use pin digest in pre/post-provider freshness checks. | Valid synthetic request with matching recomputed facts is not `STALE_CONTEXT`; changed fact digest is; legal path and no-digest legacy pins retain existing outcomes. |
| L3 persistence | Implement one-statement PostgreSQL `BE1FactSource`; map current profile, session configuration/state, admitted membership/group, and exact current synthetic proof to `BE1FactSnapshot`. | SQL-count assertion is one statement; scope/purpose/run/proof mismatch, revoked/expired proof, non-synthetic origin, inactive session/profile, absent/duplicate rows all fail closed; consent refs stay null and effective/granted stay false. |
| L4 adapters | Add owner adapter, immutable synthetic policy, T4 callback-backed source resolver, and current-`ResolvedFacts` context adapter. | Missing scope or callback/artifact/receipt/lineage ambiguity fails closed; accepted operations are source; Teacher checkpoint bytes are never consumed. |
| L7 integration | Exercise end-to-end synthetic adapter path in the existing loopback PostgreSQL harness and retain prior assistance compatibility. | Valid synthetic request avoids `STALE_CONTEXT`; changing membership/proof/source produces stale/unavailable; existing named caller regressions remain green. |

Required test matrix: focused unit tests; all nine existing assistance/vision modules named in GOAL A2 REV2; `test_sketch_generation_chain.py`; PostgreSQL T2C integration tests under the corrected T12 procedure using synthetic IDs only. Test-first baseline counts are recorded after this plan and approval, before implementation. No test result is presumed.

Static checks after implementation: Ruff check/format with `backend/pyproject.toml`; focused strict mypy for changed modules; `validate_harness.py`, `validate_repository_security.py`, `validate_architecture.py`, `git diff --check`; UTF-8/LF/trailing-whitespace scan for new evidence. Record only actual results.

## Exclusions and stop conditions

- No migration/schema, endpoint/router/composition, legal-consent changes, policy mutation, `ai_jobs` service/port/contract/table, sketch-generation adapter, Modal/GPU/provider, external network, real-child data, or Git stage/commit/push.
- No import from `interfaces/**` in infrastructure. T4 remains an injected callable.
- If the T4/T5 contract cannot be verified from stored metadata and receipt bytes, leave that adapter fail-closed and mark only the affected acceptance NOT DONE; do not invent provenance.
- If one-statement scope, digest parity, or test isolation cannot be achieved within this allowlist, stop that subtask and record the exact blocker; do not broaden scope.
- `OwnerFenceV1` signatures remain unsigned; this implementation is synthetic pilot evidence only and ends `XONG-CHƯA REVIEW`.
