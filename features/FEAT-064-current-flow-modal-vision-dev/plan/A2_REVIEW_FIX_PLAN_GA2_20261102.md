# GOAL A2 review-fix plan — GA2

Status: **approved for the exact review-fix scope by the owner launch message in this conversation; implementation must stop at `XONG-CHƯA REVIEW`**.

## Authority and baseline

- V4 SHA-256: `E11FFBCE0F655C010E679773D231D3E36930A0B960E705450499E2A2A69191F6`.
- GOAL A2 REV2 SHA-256: `47CEA408AA9A4984C2EFD9E71A2EF0CDB2DF02C46E56FD7281086EBAE574AE10`.
- T2C plan GA2 SHA-256: `1B1EB635FEA67D6EFCD19B3506F83538454D5A75012742F54B2CA0EA15086774`.
- T7b plan GA2 SHA-256: `FDA943CE81C207F51616032A05AC1FB976934178A019BDCEF95DA73478A40C46`.
- Fake-owner scope addendum SHA-256: `E04F41D3F765C24DDB1E59A36ED2E24A0287A40AD8CC5FF1215B054287E15857`; existing reviewed `fakes.py` SHA-256 begins `E97A40AB5EEC4937BF1F9336162D731E4185F3A7B583DC16FAB11AAC636B71D5`.
- Baseline HEAD: `a88de875ff92e9b4d4fa5cc2f5f8d5fc1f626f58`; branch `feature/feat063-be-foundation`; starting index must be empty. Compare every A2 path to snapshot `GA2_20261102T111006`; retain all other working-tree bytes.
- The independent review findings were pasted into the owner launch conversation. The exact launch is the user message beginning `TIẾP TỤC REVIEW-FIX GOAL A2 — KHÔNG COMMIT`; do not substitute a saved draft as its source.

## Findings and acceptance

### P1 — same-connection facts through real SQL acceptance

1. `AssistanceService.current_resolved_facts()` accepts an optional already-loaded `AssistanceRequest`. If supplied, its id must match and no AssistanceRepository transaction may be opened; the default path remains backward compatible.
2. Extend the synthetic PostgreSQL integration test to persist the assistance request with the real `SqlAssistanceRepository`, read owner/source facts with the real `PostgresAssistanceOwnerAdapter` and `PostgresCanvasSourceAdapter`, and invoke the real `AiJobService.create_job` through the real `SqlAiJobRepository` acceptance transaction.
3. Test-local PostgreSQL ports may provide the pilot AuthorizationPort and EligibilityPort only when they derive their decisions from the real synthetic BE1 rows and current `ResolvedFacts`. The acceptance UoW must hold both decisions' fences; its owner resolver must receive and use the exact SQLAlchemy connection supplied by `SqlAiJobRepository`. No fake/mock AssistanceOwner or AssistanceRepository is allowed in this regression.
4. Verify successful acceptance, stale facts, owner-fence lock timeout, and an injected failure before commit. Stale/timeout/failure must fail closed and leave no accepted job, command receipt, semantic index, or outbox row. Use synchronization and connection identity assertions, not sleep alone. Do not claim `FOR SHARE` blocks new membership INSERTs or hold a transaction over any provider.
5. Hard stop before implementation if this exact acceptance path cannot be exercised with the approved source/test paths, or if it requires changing AI Jobs source/port/repository/schema/migration, routes, or composition. Report the specific extra scope instead.

### P2 — one full-facts binding for revision, digest and owner fence

- Derive the typed-facts compatibility `context_revision` from the canonical, complete `ResolvedFacts` payload with its self-referential revision field set to zero, using the existing domain-separated SHA-256 / positive signed-31-bit formula. Keep the integer contract. The final `ResolvedFacts.digest()` includes the derived revision; the owner-fence epoch continues to derive from that final full digest using the existing `context_revision.py` helper. Metadata-free legacy requests retain their existing revision and digest behavior.
- Keep pin and current context derived from the same recomputed facts. Add a test that changes a member age/proof fact while canvas revision is unchanged and proves both revision and full digest change according to the pinned formula; retain stale and legacy compatibility tests.

### P2 — fail-closed canvas source callbacks

- Exporter/artifact loader exceptions and malformed callback objects/field access become unavailable (`None`). Catch `Exception` only; never catch `BaseException`. Preserve every existing scope, lineage, hash, receipt and source validation.
- Add tests for exporter `RuntimeError`, artifact loader `RuntimeError`, and a malformed object whose field access raises.

### P2 — scoped fake owner regression

- Add direct tests for `FakeAssistanceOwner.members`: valid scope returns the expected member; organization, participant, and purpose mismatches each return `()`; omitted scope keeps the existing behavior.
- Owner's later direct authorization supplements the approved A2 scope only for `backend/src/sketch2life/infrastructure/assistance/fakes.py`: the existing keyword-only `scope: EligibilityScope | None = None` and organization/participant-membership/purpose checks. Do not make any other source change there. The already approved addendum and supplementary approval remain authoritative; this plan pins them for the review-fix record.

## Exact allowlist

### Product source

- `backend/src/sketch2life/application/services/assistance.py`
- `backend/src/sketch2life/infrastructure/assistance/be1_owner_adapter.py`
- `backend/src/sketch2life/infrastructure/assistance/be1_canvas_source_adapter.py`
- `backend/src/sketch2life/infrastructure/assistance/fakes.py` — only the narrow owner-approved scope above; if already correct, do not change it.
- `backend/src/sketch2life/infrastructure/vision_analysis/resolved_facts_context.py`

### Tests

- `backend/tests/integration/test_be1_synthetic_pilot_postgres.py`
- `backend/tests/unit/test_assistance_t2c_adapters.py`
- `backend/tests/unit/test_t2c_digest_pin.py`

### Task records

- This new plan; append-only `features/FEAT-064-current-flow-modal-vision-dev/approvals/TASK_APPROVAL.md`; one new report `evidence/A2_REVIEW_FIX_REPORT_GA2_20261102.md`; append-only `status/PILOT_GOAL_LEDGER_20261101.md`; and one new ignored `.claude/handoff/snapshots/GA2_REVIEWFIX_<timestamp>/` snapshot.

Everything else is excluded. In particular: `infrastructure/assistance/owner_fence.py`, any `ai_jobs` source/port/repository/schema, migrations, routes, app/router composition, provider/Modal/GPU/network, real-child data, stage/commit/push, A1/M1/T7a/T6, B1/B2, T8/T9/T13.

## Verification

1. Focused tests for all four findings, followed by the pinned offline GA2 runner. The runner must receive all intended test paths explicitly; record exact arguments/output/exit code.
2. PostgreSQL T2C/T7b regression only if the already-approved T12 local-loopback safety gates pass: authorized ignored connection file is readable; database name contains `be1_acceptance`; effective host/query are loopback-only; connection succeeds; schema contains only repository-owned tables. No Alembic, database creation, `DROP`, `TRUNCATE`, external network, or deletion of data not created by the test. If a gate fails, mark the PG run `NOT RUN` and continue non-DB checks.
3. Ruff and mypy on the scoped files; three repository validators; `git diff --check`; UTF-8/LF/no-BOM/whitespace checks for new evidence. Report actual counts and baseline-only issues.
4. Recheck the seven protected file hashes and the starting A2 snapshot. Create a final GA2 review-fix snapshot with source/test hashes and command outputs.

No source change is authorized until this plan has been SHA-256 pinned by a new append-only approval entry. No independent acceptance or goal completion may be claimed.
