# FEAT-064 B1 — P2 independent-review fixes addendum

- Status: owner-authorized execution addendum; implementation must stop at `FIXED — XONG-CHƯA REVIEW` and wait for an independent re-review. This does not open B2.
- Date: 2026-11-04.

## 1. Pinned inputs and execution baseline

- B1 plan `CHAIN_B1_REV2_PLAN_20261103.md`: SHA-256 `BAA53AC8DB529107C3C9EB340FE2C900251535AB0D183209C157B6F4082A62B4`.
- B1 implementation report: SHA-256 `4BCBBDFE3AF11D751904FC13E836905665B5499ACBAD89787C579C9D9CFECDF1`.
- Baseline manifest `GB1_BASE_20261103T225233/manifest.json`: SHA-256 `C054C0CD6D5FC32727974DF19B3249A586451CFA1E975078DD9C61559A9ADED0`.
- Final B1 manifest `GB1_20261104T003700/manifest.json`: SHA-256 `47359E7E8331775CE58ED86608D945B4BD57FFAC95BDE4B142C0DDD542E1021C`.
- Execution checkout: branch `feature/feat063-be-foundation`, HEAD `b6dbfa68e66718f3f40902c093e9ebd634b1ebb9`, index empty. All other pre-existing working-tree paths are preserved.
- Current pre-edit hashes: `app.py` `5C735CFF2CA2B3E3665275C6C7A59B2A10B968896AC651B74D63FFBD16C041D9`; `be1_runtime.py` `A74B5885A2B7B5B430D4D76D61E437FBA6DD686F8B8AC388118BFF7DD86067AA`; `pilot_composition.py` `D6731A9221DA65712BC9CC7AE79A441E398D72A1813810010AC7FFA878886E09`; `test_app_composition.py` `7717BD672F98D413E5489855F58A13BF453BF6366905FA785BD116250A5A5207`; `test_pilot_queue_composition_b1.py` `5917CAAD6E318765CBA2026CA513D6FAED9C22BD0D739052F5D64E96EBC711F4`; `test_be1_synthetic_pilot_postgres.py` `D39A7F93717D281BDDB757DD490CE4E6778AA825E9B66FB1D3CFA5706FDD057D`.

## 2. Exact scope

This addendum covers only the two P2 findings supplied in the owner's 2026-11-04 launch message.

### P2-A — real app composition

- Minimal gated wiring in `backend/src/sketch2life/interfaces/http/app.py` to pass the already-approved pilot factory into `build_be1_runtime`.
- Use the existing `backend/src/sketch2life/infrastructure/vision_analysis/pilot_composition.py` and A2/BE1 adapters. Keep the existing local/test + explicit synthetic-pilot gate and default-off behavior. Missing or invalid required dependencies fail closed; production must never construct the pilot implicitly.
- Add tests only in `backend/tests/contract/test_app_composition.py` and `backend/tests/unit/test_pilot_queue_composition_b1.py` for gate-off, valid-gate composition, and invalid/missing dependency behavior through the real app composition path.
- No route, schema, migration, AI Jobs core, provider configuration, UI, or other source path is in scope.

### P2-B — durable guarded acceptance using task-owned PostgreSQL

- Add or extend acceptance tests only in `backend/tests/integration/test_be1_synthetic_pilot_postgres.py`. Use the real SQL job repository, invocation ledger, analysis repository, BE1 authorization/eligibility, owner fence and worker/composition. The model boundary is a deterministic in-process or loopback stub that records send count; it must not call a real provider.
- Prove: committed `SUCCEEDED` is visible from a new transaction before result acceptance; `UNKNOWN`/`HOLD` do not accept and do not resend; stale fence rejects; duplicate/concurrent dispatch and restart/replay after `SENT` never send twice or accept invalid results; at most one attempt; zero Sketch/cache/prohibited second-event effects.
- Use only a new random, task-owned database on local PostgreSQL 17 at `127.0.0.1:5433`, authenticated as `postgres`. Never target or mutate any existing application database, including `sketch2life` or `storyrun_lite_runtime`. Any application test connection must target the exact task database name recorded in the report. Migrations and minimal synthetic seed are allowed only on that newly created database. No historical-row cleanup.
- Database name format: `s2l_b1_review_<UTC timestamp>_<8 lowercase hex>`. Verify uniqueness by attempting database creation; on collision, generate a different suffix. Record the exact successful name in the report and snapshot metadata; do not record a credential or connection URL.
- The database can be dropped only if this run created it, the exact name/cluster target is reverified, all test connections are closed, and no uncertain state remains. Otherwise retain it and report why.
- The owner explicitly resolved the maintenance-connection ambiguity in this chat: one short administrative connection to the maintenance database is permitted solely to issue `CREATE DATABASE` for the random task-owned DB. Do not read or alter application data through that connection. No connection to any existing application DB is permitted.

## 3. Verification and evidence

- Run focused tests for both findings, then the pinned offline regression runner from the B1 harness. PostgreSQL acceptance runs only after the database gate in §2 is resolved.
- Run Ruff with `backend/pyproject.toml`, strict mypy over the changed Python files, all three repository validators, and `git diff --check`. Record exact commands, output summaries and exit codes; distinguish tests not run from passing results.
- Append a review-fix report, append-only status/ledger entries, and create a new ignored snapshot. Preserve the existing B1 report, prior plans/reviews/approvals, and all unrelated working-tree changes.
- No stage, commit, push, merge, reset, checkout, stash, cleanup, Modal, GPU, provider, or external network.
- Final state is `FIXED — XONG-CHƯA REVIEW` only if both findings have passing evidence. Otherwise record the actual blocker and stop without claiming the findings fixed.

## 4. Authority and approval boundary

- This addendum is pinned by the owner’s direct launch message in this chat. The corresponding approval entry must name this exact addendum hash before any PostgreSQL connection or database creation.
- The B1 report and independent review remain historical inputs; this addendum does not revise their conclusions or mark B1 accepted. Independent re-review is required after implementation.
