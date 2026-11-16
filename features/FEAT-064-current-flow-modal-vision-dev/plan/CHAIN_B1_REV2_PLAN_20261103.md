# FEAT-064 chain — GOAL B1 revision 2 plan

- Status: **DRAFT / AWAITING OWNER REVIEW**. Not an implementation approval or launch prompt.
- Chain position: second only after A2 is independently reviewed **ACCEPTED** and the owner sends a separate B1 launch prompt. B1 then ends `B1 XONG-CHƯA REVIEW`; wait for independent **ACCEPTED** and another owner launch before B2.
- Goal: implement only the analysis-only/zero-Sketch path and T8 in-process worker/composition pilot under V4 §3 D6 (with the already approved D3 retry policy). No T9, T13, or T12 work.

## 1. Planning base and start gate

This plan was drafted against branch `feature/feat063-be-foundation`, HEAD `b6dbfa68e66718f3f40902c093e9ebd634b1ebb9`, and read-only snapshot `.claude/handoff/snapshots/FEAT064_CHAIN_BASE_20261103T165013/manifest.json` (SHA-256 `249C34A8E3FA6B1C98076AEC629E02F4158A5F19905378EBEBF6B81F4AEB4D7C`). That is a planning reference only. A B1 implementation launch must capture a new byte-copy/hash baseline after A2 review acceptance, then pin the actual post-A2 branch, HEAD, and dirty paths. Do not use the A2-era hashes for B1 and do not assume the worktree is clean.

Start only when all are true:

1. The independent A2 review records **ACCEPTED**, and the owner has appended the final A2 disposition so the latest ledger status is **COMPLETE**. The earlier `XONG-CHƯA REVIEW` implementation checkpoint remains historical evidence; it is not the required post-review status.
2. Owner's B1 launch cites V4 `E11FFBCE0F655C010E679773D231D3E36930A0B960E705450499E2A2A69191F6`, this plan's exact SHA-256, current branch/HEAD, current snapshot, allowlist, and says B1 is the active goal.
3. A1/A2 prerequisites in V4 and the current ledger are not BLOCKED. If not, stop; no provisional implementation.

## 2. Frozen scope: analysis-only + T8

### Analysis-only / zero-Sketch

- Add an explicit `analysis_only` path that gates `put_cache`, `add_sketch_intent`, the second event, and `request_sketch`, while preserving the existing `hand_off` behavior.
- Adapt the A2 T4 export + T5 receipt into the complete `CheckpointBinding` (five required fields) and `RenderBinding`. Use `source_ref` as checkpoint identity, the export canvas/epoch/revision/checksum for source fields, and admission policy/renderer/media type from the verified receipt artifact. Never trust a Teacher-sent checkpoint as source.
- Acceptance: the pilot path creates no Sketch intent/request, cache write, or prohibited second event; the legacy sketch path remains fail-closed; a missing/mismatched export or receipt is unavailable/fail-closed.

### T8 / worker and composition pilot

- Add `InProcessDispatchQueue` implementing `DispatchQueuePort` and a separate `pilot_composition` that constructs its own `AiJobService`, the already approved single-attempt `PILOT_VISION_RETRY_POLICY`, repository, guard, and worker.
- Attach it only through `Be1Runtime.pilot_vision`, defaulting to `None`; do not enable it by default.
- Build authorization/eligibility adapters from current BE1 facts; these must be real pilot adapters, not fakes. Use only explicitly labelled `PILOT_FAKE_*` in-memory implementations for audit/artifact/capability/IDs, and document residual risk. “Atomic acceptance” is the analysis repository transaction, not a cross-database transaction with the assistance repository.
- Prove the guarded observe → durable acceptance → analysis-only reconciliation sequence. `UNKNOWN`/`HOLD` must not dispatch another attempt. The child/teacher projection uses the permitted `NOT_SENT_*` meanings; no retry control is added. A stale fence cannot accept results.
- Transport-count acceptance with a stub loopback: exactly one call for accepted work, zero for rejected work, at most one under duplicate/concurrent dispatch; crash/restart after SENT produces no additional call. Zero Sketch remains invariant.

## 3. Exact proposed allowlist

Source:

- `backend/src/sketch2life/application/services/assistance.py`
- `backend/src/sketch2life/domain/assistance.py`
- `backend/src/sketch2life/application/ports/assistance.py` — only if needed for the analysis-only seam.
- New `backend/src/sketch2life/infrastructure/vision_analysis/analysis_only.py` — map the verified A2 source/receipt to analysis bindings and gate zero-Sketch effects.
- New `backend/src/sketch2life/infrastructure/vision_analysis/pilot_queue.py`.
- New `backend/src/sketch2life/infrastructure/vision_analysis/pilot_composition.py`.
- `backend/src/sketch2life/interfaces/http/be1_runtime.py` — only add the default-`None` pilot field and its explicitly gated construction/wiring.
- Read-only reuse of A2's `backend/src/sketch2life/infrastructure/assistance/be1_canvas_source_adapter.py`; do not modify it under B1 unless the B1 launch explicitly lists an exact additional change.

Tests:

- New `backend/tests/unit/test_assistance_analysis_only_b1.py`.
- New `backend/tests/unit/test_pilot_queue_composition_b1.py`.
- `backend/tests/contract/test_app_composition.py` only for the `pilot_vision` default-off/wiring contract.
- Other A2/AI Jobs tests may be run as read-only regressions when in the approved offline suite; they are not editable under this plan.

Task records after separate launch approval: this plan, one B1 report, append-only FEAT-064 approval and ledger entries, and one ignored `GB1_*` snapshot.

Explicit exclusions: all route files, `router_composition.py`, `openapi_contract.py`, T9 routes/profile lookup, T13 script, T12 PostgreSQL acceptance, migrations/schema, `services/ai_jobs.py` and AI Jobs ports/contracts/tables/repository, Modal/GPU/provider/live calls, UI, and any path not listed above. Keep all unrelated current working-tree changes byte-identical to the B1 launch snapshot.

## 4. Verification and gates

- Run focused analysis-only and queue/composition tests, then the pinned offline regression suite with recorded command/output/exit status. Use only synthetic fixtures and stub loopback; no PostgreSQL is required by this goal. If a selected test requires a database, do not run it; report it as blocked or move it to B2 only through a later owner-approved plan.
- Run Ruff using `backend/pyproject.toml`, focused strict mypy, the three repository validators, and `git diff --check`; inspect the final exact-path diff and snapshot it.
- Acceptance is not “tests passed” alone: prove no Sketch/cache/event side effects for analysis-only; the pilot is default-off; the queue cannot create retries after UNKNOWN/HOLD; one attempt maximum; BE1-based authorization/eligibility; fake-port names/risk; and the stale-fence behavior.
- Any need to alter AI Jobs implementation, persistence schema, routes, composition outside the single runtime seam, provider configuration, or to weaken a test is a hard stop requiring a new plan and owner approval.

## 5. Approval and stop point

Before implementation, the owner must review this plan and append a separate approval pinning its full SHA-256, the fresh post-A2 launch snapshot and exact allowlist. This document's current baseline does not authorize code. B1 ends `XONG-CHƯA REVIEW` or `BLOCKED`; it never self-accepts. Wait for independent **ACCEPTED** and a separate B2 launch. Do not start B2 automatically.

## 6. Authority checked

- V4 `OWNER_DECISIONS_G3G4_V4_20261101.md`: SHA-256 `E11FFBCE0F655C010E679773D231D3E36930A0B960E705450499E2A2A69191F6`.
- Old B1 goal `CODEX_GOAL_G3G4_B1_20261101.md`: SHA-256 `6B16C5D9ED64F3A0CC687F8E9258E37B4B499C6B0756BE4D7EC7AB10152EE692`.
- Old A2 and B1 HEAD pins are historical. B1 launch must use the fresh post-A2 baseline, not `1e93bc3f…` or `a88de875…`.
