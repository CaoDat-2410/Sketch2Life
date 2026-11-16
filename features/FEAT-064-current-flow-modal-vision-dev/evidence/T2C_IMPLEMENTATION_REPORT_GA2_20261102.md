# T2C scoped owner facts, T4/T5 source, and digest pin — GA2

Status: **Code verified; TẠM DỪNG at final scope gate**. The missing exact-path approval described below prevents GOAL A2 closeout. This report is not an independent review, owner signature, production approval, or evidence of model quality.

## Authority and baseline

- Branch: `feature/feat063-be-foundation`; HEAD: `a88de875ff92e9b4d4fa5cc2f5f8d5fc1f626f58`; index empty.
- Owner launched GOAL A2 REV2 after independent A1 review and A1 COMPLETE. V4 SHA-256: `E11FFBCE0F655C010E679773D231D3E36930A0B960E705450499E2A2A69191F6`; goal SHA-256: `47CEA408AA9A4984C2EFD9E71A2EF0CDB2DF02C46E56FD7281086EBAE574AE10`.
- Approved plan: `plan/T2C_BE1_CANVAS_OWNER_FACT_ADAPTER_PLAN_GA2_20261102.md`, SHA-256 `1B1EB635FEA67D6EFCD19B3506F83538454D5A75012742F54B2CA0EA15086774`. Its approval entry predates implementation; plan and old approval entries are unchanged.
- Baseline snapshot: `.claude/handoff/snapshots/GA2_BASE_LAUNCH_20261102T010622/`, 35 rows. Changes outside this task remain byte-identical to that snapshot. Earlier draft/blocker records remain historical.

## Implemented behavior and layer evidence

| Layer | Implementation | Evidence |
| --- | --- | --- |
| L1 contract | `members(..., *, scope=None)` and optional validated `AssistancePin.context_digest`. | Legacy no-scope members and no-digest pins retain their behavior; malformed digest rejected. |
| L2 application | Current `ResolvedFacts` recomputation is shared by freshness and the request-bound context adapter. Synthetic pin is exactly `sha256:` plus stored assistance digest; expected digest is checked before and after the fake observation. | Valid synthetic reaches analysis-ready; changed age facts refuse before observation, or store stale when facts change during observation. |
| L3 facts | `PostgresBE1FactSource` reads current profile/session/membership/group/proof with one SQL statement on the injected connection. Proof join is restricted to the exact session/run/purpose; duplicate matching rows fail closed. | Real PG valid/read-count and historical-proof case; purpose/run, expiry, revocation, inactive profile/group, non-admitted membership and non-synthetic origin cases. |
| L4 owner | `PostgresAssistanceOwnerAdapter` supplies scoped canvas, full roster revision, current turn and members. It checks authoritative export against current aggregate revision; each projection is one statement. | PG request submission uses these owner methods, real T4 export and persisted T5 artifacts. |
| L4 source | `PostgresCanvasSourceAdapter` binds the injected T4 export to one persisted PNG and admission receipt. It verifies scope, source hash/epoch/revision, exact lineage, canonical receipt, byte hashes and render/source binding. | 23 unit tests plus PG service submission. No Teacher checkpoint payload is consumed. |
| L4 context | `ResolvedFactsAnalysisContext` computes the digest from current full `ResolvedFacts`, never copies the BE1 reader digest. Cross-scope/missing facts deny; synthetic keeps consent-effective and purpose-granted false. | PG compares the two distinct digest domains; unit scope and digest cases. |
| L6 UI | DEFERRED-BY-OWNER. | No UI work. |
| L7 compatibility | Existing assistance, Vision, synthetic basis and Sketch-chain callers. | Offline suite described below. |

The fixed `PILOT_SYNTHETIC_POLICY_V1` includes immutable age policy, region policy revision/regions, allowed levels, debounce, limits, caching and purpose. Its provider is enabled only in explicit local/test pilot mode. The owner projection requires the session purpose to equal this profile. No legal consent row or grant of legal consent is introduced.

Legacy compatibility is explicit: requests whose members all lack eligibility-basis metadata keep their historical no-digest fixture pin/context. Every context with eligibility-basis metadata, including all PG synthetic pilot requests, pins the full digest. This preserves the mandated old callers; it is not a production legal-consent adapter. Scope is checked before the legacy fallback is selected.

## Actual verification and corrections

- Final offline runner: **396 passed, 0 failed, 0 skipped**, exit 0. It runs the existing assistance unit/contract modules, Sketch chain, Vision unit modules, BE1 fact-reader and synthetic-basis contracts, plus the three new A2 modules. Full arguments/output are in the new GA2 snapshot. New A2 unit modules contain 23 source tests, 6 digest/profile tests, and 21 fence tests.
- PG focused after the proof-scope/context corrections: **11 passed, 56 deselected**, exit 0. Full PG module at the preceding checkpoint: **67 passed**, exit 0. The final PG run, including the additional real lock-timeout case, is recorded in the T7b report.
- Initial resumed regression was red: 34 failures across the assistance/Sketch-chain suite. The newly installed context adapter had replaced the fixture's separate context revision, and legacy fixture pins no longer matched the plain legacy context. Preserving the legacy metadata-free pin and its original context fixed the regression without changing Sketch source or old test assertions.
- Source adapter test-first checkpoint: 20 failures due to missing adapter module; subsequent source matrix: 23 passed. For implementation that was already in progress before this continuation, an original red count is unavailable; it is not invented.
- A newly added post-observation assertion initially expected uppercase `CONTEXT_CHANGED`; the contract uses `InvalidationReason.CONTEXT_CHANGED` with lowercase wire value. The test now compares the actual enum, with the stale requirement unchanged.
- First offline runner blocked all sockets and broke Windows asyncio's loopback socketpair (11 failures). The corrected runner permits loopback plumbing and blocks external sockets. A subsequent run caught boto3's EC2 credential-metadata lookup in an unchanged route-surface test; metadata lookup and credential/config files are disabled in the runner. The final run passes without allowing external network access. Both failed outputs are preserved locally.
- Ruff check is run on all 16 touched source/test paths; format check covers all 9 new Python files. Strict mypy on 11 affected source files: **Success: no issues found**. Adding the existing assistance harness reports one pre-existing `CoordinatedAiJobRepository(InMemoryAiJobStore)` protocol error; the byte-for-byte HEAD harness also reproduces it. There are **0 new mypy errors**. The default mypy cache encountered a local SQLite-cache error; a separate temporary cache yielded the stated verdicts.
- Three repository validators and `git diff --check` are recorded with actual outputs in the final snapshot. New evidence is checked separately for UTF-8, LF, BOM and whitespace because untracked files are not scanned by `git diff --check`.

## Limits and preserved state

No migration/schema, route/composition, `ai_jobs` source, Sketch adapter, provider configuration or production legal-consent flow was changed. No Modal/GPU/provider/external call, real-child data, stage, commit or push occurred. The provider used by observation tests is the offline fake. PostgreSQL is only the owner-approved disposable loopback acceptance database; only test-owned synthetic rows are written/cleaned, with no Alembic/DROP/TRUNCATE operation.

The source-adapter callback is trusted infrastructure wiring and must execute the authoritative T4 exporter on the caller's connection. The pilot composition/worker that wires this for live use belongs to a later goal. T2C provides the adapter and same-connection resolver pieces; it does not declare the later live chain ready.

Seven protected file prefixes remain: SOURCE_REGISTER `0B43E4BA`; FEAT-063 CONTEXT `E7C8143A`; STATUS `F1ADB793`; REMAINING_AI `8BBFD0ED`; REV36_DELTA `B61B0607`; VIDEO_FLOW `93374E96`; S1_DECISION_CARD `4D95D303`.

Await an independent review of GA2; do not start the next goal from this report.

## Final scope-gate finding — not yet closed

The continuation began with existing A2 WIP changes in `backend/src/sketch2life/infrastructure/assistance/fakes.py`: an `EligibilityScope` import, optional keyword `scope` in `FakeAssistanceOwner.members`, and rejection of a supplied mismatching scope. V4/Goal authorize the assistance area and the optional-scope contract, but the frozen T2C plan's exact source list omitted this file. It is not in the 35-row launch baseline. Therefore the byte audit cannot classify it as an approved exact-path task change or unchanged launch-baseline file. This continuation did not further edit it. The previous statements about preserved outside-scope hashes refer to existing baseline rows; they do not resolve this newly detected path omission.

Owner has been asked to approve a narrow supplementary scope record. No old plan/approval was edited and no retrospective approval is claimed. All code/tests and seven protected files are retained. Until that decision and its record exist, **GOAL A2 remains active/TẠM DỪNG, not complete and not yet released for independent-review closeout**. The final snapshot includes the visible WIP file with this exception explicitly marked.

The concrete proposed record is now `plan/T2C_FAKE_OWNER_SCOPE_ADDENDUM_GA2_20261102.md`, DRAFT/AWAITING_OWNER_APPROVAL, SHA-256 `E04F41D3F765C24DDB1E59A36ED2E24A0287A40AD8CC5FF1215B054287E15857`. It accepts no scope by itself. No source/test/approval was changed while preparing it.

## Owner scope decision — scope hold resolved

The owner subsequently approved precisely the `fakes.py` optional keyword and organization/participant/purpose checks, retaining its no-scope behavior. The new append-only `T2C fake-owner keyword compatibility — GA2 supplementary scope` entry pins addendum SHA-256 `E04F41D3F765C24DDB1E59A36ED2E24A0287A40AD8CC5FF1215B054287E15857` and reviewed source SHA-256 `E97A40AB5EEC4937BF1F9336162D731E4185F3A7B583DC16FAB11AAC636B71D5`. The historical plan and earlier approval entries remain unchanged; the supplementary entry does not backdate approval.

Rechecked all 16 source/test files against snapshot `GA2_20261102T111006`: **0 mismatches**. The previous 396 offline / 68 PostgreSQL results therefore apply to the same source/test bytes; no runtime tests were rerun for this documentation-only decision. Ruff on the fake file, three repository validators and `git diff --check` passed. Focused strict mypy reported only the same pre-existing `CoordinatedAiJobRepository` harness error already reproduced from HEAD; no new error. Seven protected file hashes were rechecked and remain unchanged.

This owner approval resolves the scope gate and does not replace independent review. **GOAL A2 XONG-CHƯA REVIEW**; no Modal/provider call or stage/commit/push.
