# BE2-07 → BE2-01 → BE2-08 persisted-flow status handoff — Rev5 draft

Date: 2026-10-22 (Asia/Saigon)
Disposition: **DRAFT / NOT_SENT / NOT_READY_FOR_BE1_INTEGRATION**
Review status: **NOT_INDEPENDENTLY_COLD_REVIEWED**. The separate Rev5 plan review covered the plan, not this handoff or its companion `BE2_DURABLE_SOURCE_FENCE_ROUTE_INVENTORY_20261022.md` (SHA256 `6A0F3AFE49ABF300E97244B9AEB63F1A2092BFCFCE4C50605B6F4267D8E7F4C8`).

This documentation-only successor preserves Rev2, Rev3 and Rev4 as local-only files; they are untracked and excluded from the proposed three-file publication set. The earlier `BE2_07_01_08_PERSISTED_FLOW_HANDOFF_DRAFT_20261022.md` is already tracked at the candidate HEAD and remains unchanged; it is historical and is not one of the three changed files proposed for publication. This Rev5 handoff is prepared for publication on `feature/be2-backend-ai-integration` as a reference; publication alone is not delivery to the BE1 owner/AI, and the handoff has not been delivered. It adds a read-only Route B investigation request for the receiving BE1 AI if the owner later sends it. It does not select a route, grant implementation approval, or make BE1 integration ready.

## Candidate and bounded approved scope

- Worktree name: `be2-01-14-integration-linked` (local checkout identifier; no machine-specific path is included).
- Branch: `feature/be2-backend-ai-integration`
- HEAD when this note was prepared: `af3e28fc402f69e5a10ba55a54631c5d1f995a50`
- FEAT-057 scope path recorded by the test receipt: `BE2_01_07_08_PERSISTED_VIDEO_SEAM_SCOPE_REV2_DRAFT_20261022.md`; receipt scope SHA256 `1C199CF6CD1E7C2F2D5981D253256278079D840197CB1B05D304E2620FD2E90D`.
- Current bytes at that same scope path hash to SHA256 `F170809FCBB71D1B588960466350D6086568EFB6384232AB0F178DF7D350C052`.
- The FEAT-044/050 approval records state that the owner authorized removal of a machine-specific Worktree locator and that contract terms, §2 boundaries, §3 environment limits and §4 manifests are unchanged. The earlier `1C199CF6…` bytes are not recoverable from this checkout, so this note does not claim independent byte-for-byte verification of that metadata-only equivalence or that the 9/9 receipt used the current file bytes.
- Contract: `BE2-VIDEO-LIFECYCLE/1`, A (submit), S (start), B (accepted finalization) and identity-failure behavior only.
- Approval manifests recorded for that implementation: FEAT-044 7/7, FEAT-050 14/14, FEAT-057 1/1.

The PostgreSQL receipt is pinned to its recorded scope/test/log/JUnit hashes. It does **not** pin the production `sketch2life.*` module closure or prove those production bytes equal this HEAD. The HEAD above identifies the candidate snapshot at note preparation, not a claim that every production source byte at HEAD was the byte set imported by pytest.

## Reader map and referenced terms

All paths below are repository-relative. “Tracked at candidate HEAD” means the recipient can inspect the path after checking out that branch. “Local-only” means it is not part of the proposed three-file publication package. These anchors locate the current meanings; they do not enlarge any approval.

| Term | Meaning and current state | Anchor |
|---|---|---|
| **A / S / B / F** | A = submit; S = admitted start; B = accepted finalization; F = failure, cancel, timeout, retry, dispatch loss or reject. Current `BE2-VIDEO-LIFECYCLE/1` covers A/S/B and identity-failure behavior only; F needs separate review and supplemental approval. | Tracked scope `features/FEAT-057-be2-01-14-offline-integration/plan/BE2_01_07_08_PERSISTED_VIDEO_SEAM_SCOPE_REV2_DRAFT_20261022.md` (SHA256 `F170809FCBB71D1B588960466350D6086568EFB6384232AB0F178DF7D350C052`); approval anchors below. |
| **X01** | BE2-07 exact source export to BE2-08 media preparation. It remains `PARTIAL`; the current test edge registry is an evidence index, not a durable source fence. | Tracked `backend/tests/integration/be2_cross_lane/edge_registry.py` and `features/FEAT-057-be2-01-14-offline-integration/evidence/metrics/CROSS_LANE_X01_20261020.json`. |
| **X05c / CR09-02** | Playback session/access gateway. Status remains `OPEN`; a read of artifact metadata or a playback intent does not establish a session or access authorization. | Tracked draft `features/FEAT-050-be2-knowledge-video/plan/CROSS_LANE_BE2_08_ARTIFACT_READ_MODEL_SCOPE_DRAFT_20261021.md` (SHA256 `F24823A192A90F11649871348AC0C539C3E63501AAA3A75C21DBC36EB7F15FA1`). |
| **X05d** | Current-source resolver/fence for BE2-09 review/current-use and playback intent. Status remains `BLOCKED`; no already-adopted resolver/fence was identified. | Same tracked FEAT-050 artifact-read scope above; see its “Proposed boundary” and “Access, freshness, and visibility questions” headings, especially lines 44–70. |
| **X09 / X09-08** | X09 is the single aggregate job-type-routing registry row and remains `NOT_IMPLEMENTED`. “X09-08” is shorthand for the BE2-08 branch in feature material, not a separate registry row. | Tracked `backend/tests/integration/be2_cross_lane/edge_registry.py`. |
| **CR08-01 / `BE2-VIDEO-LIFECYCLE/1`** | Paired persisted video lifecycle contract, adopted for A/S/B and identity-failure only. The BE2-01 transaction owns begin/commit/rollback; BE2-08 participates only on its own video rows. | Tracked approvals: `features/FEAT-044-be2-ai-job-foundation/approvals/PHASE_B_TASK_APPROVAL.md` (SHA256 `885D51F7C80A9EB86A60E3F0FCC415DEF4B72E4FBD49E9C467CFB7F06C42FE44`), `features/FEAT-050-be2-knowledge-video/approvals/TASK_APPROVAL.md` (SHA256 `DB7FEC36F5E3EAB9E7CCBA6E2718890A491D9978CA304EF49D988C78E0A476A1`), and `features/FEAT-057-be2-01-14-offline-integration/approvals/TASK_APPROVAL.md` (SHA256 `10CC6F9F752E80927F98C6418E79201D9B22E740F26BA9BCE5C9FEC699800ABB`). |
| **D1** | Owner design direction for paired job/run lifecycle UoWs and job → run → canonically sorted source-fence lock order; it is not implementation approval. | Tracked `features/FEAT-057-be2-01-14-offline-integration/evidence/notes/CROSS_LANE_UOW_OWNER_DECISION_D1_20261021.md` (SHA256 `3EECF89A488F7B2539AF41BE5CEF830D4C2509D6E93D478F624DF46B4F32A16D`). |
| **D4** | Completion-time budget disposition remains pending; no unit, limit or numeric value is assumed. | The detailed ballot `features/FEAT-057-be2-01-14-offline-integration/evidence/notes/CROSS_LANE_UOW_OWNER_D4_COMPLETION_BUDGET_BALLOT_DRAFT_20261021.md` is local-only and is not required to understand this handoff. |
| **Creation lease** | A separate BE2-08 logical guard around submission, outside A's foundation job/run UoW; no atomicity with that UoW is claimed. | Tracked `features/FEAT-050-be2-knowledge-video/plan/CROSS_LANE_BE2_08_SCOPE_REV3_DRAFT_20261021.md` §3 (SHA256 `66C614FF268E418F27FA4923FB7272A845F7BC7DA8BB225B8CD10032D364F801`). |
| **`OwnerFenceV1/0.1-candidate`** | Synthetic fixture label `ASSUMED_CONTRACT`, not an adopted producer contract or production fence. | Tracked `backend/src/sketch2life/infrastructure/ai_jobs/sql/owner_fence_fixture.py`; additional limits are recorded in the companion inventory. |

The source of the current canonical product requirements is tracked at `features/FEAT-029-master-srs/artifacts/Sketch2Life_Master_SRS.md` (SRS v3.1; SHA256 `A95C89589843E3555E967C5E486F3BCAF4BBDF9446CB3BC9C49ED16F672964D9`). The FEAT-050 scope and three lifecycle approval paths above are named explicitly so a reviewer need not infer their locations from feature IDs.

Route labels in the read-only request below mean: **A** = create a new BE2-07-owned SQL source store; **B** = use an existing BE1-owned authoritative store through its producer-published same-connection contract; **C** = stop durable source-fence work at the existing bounded A/S/B evidence and keep X01 `PARTIAL`. These are choices for the project owner, not recommendations or decisions made by this handoff.

## What the recorded 9/9 result supports

The receipt reports 9 passed, 0 failed, 0 errors and 0 skipped on loopback PostgreSQL 17.11 using synthetic records, a fresh random database per test and only the two already-approved migrations; cleanup left no test database. It exercises persisted A/S/B job/run composition and the real `VideoWorker` with the unchanged dispatch envelope. The test source hash is `C18D6FD373F83C617B0FF470DC523C99E3A5EDB5B0D2DF1A040ECC0E6F7E67ED`; log and JUnit hashes are recorded in the receipt and metrics.

The test also uses an in-memory knowledge harness, fake owner fences/authorization/eligibility/artifacts/queue, no-op lease-current and offline-authority checks, and a test-local source resolver. Its fence factory ignores the supplied SQL connection. It therefore does not prove a durable source fence held through finalization. The receipt's `production_source_changed: false` means production source was not edited during that test run; it is not a pre-edit baseline or source-hash attestation.

## Remaining boundary and readiness

- X01 remains `PARTIAL` until the authoritative source owner/store and versioned fence contract are adopted, an exact connection/UoW held-fence implementation is approved, and two-connection invalidation/finalization race tests pass.
- The current source's start path locks the job, holds an eligibility fence, then touches the run; accepted finalization locks the job, holds eligibility plus artifact fences, then touches the run. These are not BE2-07 source fences, and no BE2-07 source row is held by either path today. D1 records the owner-directed order job → run → source-fence rows. The adopted serialization mechanism and race proof are still missing. Neither the receipt nor this note claims D1 is implemented across all lifecycle paths.
- CR08-01 is adopted narrowly as `BE2-VIDEO-LIFECYCLE/1` for A/S/B and identity-failure behavior. The adopted persisted-seam scope is silent about creation lease; FEAT-050 scope Rev3 describes it as a separate logical guard outside A, matching the current service flow. Do not claim it is atomic with the BE2-01 job/run UoW. Any future change to enlist it requires exact revised scope and approval.
- Current `BE2-VIDEO-LIFECYCLE/1` does not cover F (fail, cancel, timeout, retry, reject); F remains a separate review/supplemental-approval gate.
- The edge registry has one aggregate X09 row, currently `NOT_IMPLEMENTED`; there is no separate X09-08 row. The “BE2-08 branch of aggregate X09” is often called X09-08 in source/feature material. The 9/9 result is evidence for that bounded branch only and does not change the aggregate row.
- X05d remains `BLOCKED`; X05c/CR09-02 remains `OPEN`. BE2-09/14, D4, budget work and BE1-owned implementation/adoption are outside this scope.
- BE1 status remains **NOT_SENT / NOT_READY_FOR_BE1_INTEGRATION**. This note is for internal review only.

## Read-only Route B investigation for the receiving BE1 AI

This check is intentionally assigned to the AI that receives this handoff on the BE1 side. Codex has not pre-queried BE1, and this handoff does not choose a route. The request is to gather evidence about B; the receiving AI must not select A or C. If the owner sends this note, inspect the BE1 repository/worktree, producer contracts, approvals, and current-state records actually available to you. Keep the investigation read-only and report the exact repository, branch, HEAD, and files inspected.

Determine whether an existing BE1-owned authoritative store and producer-published, versioned contract can fence the BE2-07 source identity within the exact connection and transaction/UoW used by BE2-01 finalization. Report evidence for each item below, using file paths, line references, and SHA-256 hashes wherever the inspected material permits:

1. Store identity, accountable owner, and the authoritative source identity/version fields.
2. Every relevant writer/invalidation path and whether its source-version change commits through the same authoritative record.
3. The published contract/function/port that lets the finalizer check and hold that record on its own transaction connection; state whether this is supported by current code or only proposed.
4. Serialization and stale-result behavior when finalization races with source mutation, including how lock timeout/deadlock errors are distinguished from a stale source result.
5. The proposed adapter owner, architecture boundary, and exact PostgreSQL 17 least-privilege grants required by the chosen mechanism. Do not infer grants from a different statement; cite the relevant contract or database documentation.
6. The owning approval/contract records and hashes that authorize the mechanism, if any.

Conclude whether the inspected evidence demonstrates Route B, fails to support Route B, or leaves it indeterminate. If evidence is absent from your inspected checkout, say “not found in the inspected checkout”; do not claim the mechanism does not exist elsewhere. State what evidence or owner decisions remain for the project owner to make the route decision; do not recommend or select Route A, B or C. Do not approve a migration or implementation, modify files, run tests/databases/services/providers, or contact other people. Return the findings to the project owner.

This request does not authorize BE1 integration work. Until a route and exact scopes are separately adopted and approved, preserve X01 as `PARTIAL`, X05d as `BLOCKED`, X05c/CR09-02 as `OPEN`, and aggregate X09 as `NOT_IMPLEMENTED`. BE1 remains `NOT_SENT / NOT_READY_FOR_BE1_INTEGRATION` until the owner separately decides to send the handoff and readiness is established.

Rev2, Rev3 and Rev4 are local-only/untracked and remain outside the proposed three-file publication set. The earlier `BE2_07_01_08_PERSISTED_FLOW_HANDOFF_DRAFT_20261022.md` is tracked at the candidate HEAD and unchanged; it is preserved as historical context, not as one of the three changed files proposed for publication. This note itself does not contact BE1 or authorize source/test/schema/migration changes, a database run, Git publication, card acceptance, or runtime work.
