# FEAT-063 M3–M6 roadmap — PR #26 integration placement, Draft 3

**Status: OWNER-ACCEPTED FOR PLANNING ONLY / NOT APPROVED FOR IMPLEMENTATION / NOT LAUNCHED.**  
**Date:** 2026-11-16  
**Predecessor:** `M3_M6_SRS_ALIGNED_ROADMAP_ADDENDUM_DRAFT2_20261115.md`.  
**Scope:** Add a bounded disposition and integration point for PR #26. Preserve Draft 2's Rev68 requirements and critical-path order. This addendum does not approve, merge, or launch PR work.

## 1. Authority and decision boundary

For the active BE worktree, use the unsigned canonical working SRS Rev68 recorded in `.worktrees/m2-s2/docs/context/SRS_AUTHORITY.md` and governed by D-203/D-208. Rev68 is the latest working baseline for this lane, not a signed final SRS. The repository-root authority still points to Rev60; reconcile that pointer before publishing this lane's requirements or merge package into the root/default branch. Do not mix Rev60 and Rev68 requirements in one implementation contract.

Roadmap Draft 3 and Roadmap Addendum Draft 2 remain planning inputs. Addendum Draft 2's critical-path order is preserved: reconcile and accept M2 S2/S3; resolve and separately approve/implement FR-C-08; only then enter M3 Parent. This Draft 3 inserts the selected Parent-AI integration slice from PR #26 at the start of M3 and keeps Teacher Web candidates in M4. It does not authorize implementation, provider calls, or real-data use.

## 2. PR #26 snapshot and disposition

Read-only GitHub observation on 2026-11-16:

| Field | Observed value |
|---|---|
| PR | `CaoDat-2410/Sketch2Life#26`, `DRAFT: FEAT-063 Parent Docker/Modal seed and SVG guide integration` |
| State | Open, draft, not merged; GitHub reports `mergeable=false` |
| Base | `dev` at `c87d8008b70910eb0a4d3579b9490312e7e3143f` |
| Head | `codex/feat063-parent-docker-modal-seed-20261111` at `78f3b5eece7dc4010631889c3599cf4dbacd9550` |
| Comparison | Diverged; 6 commits ahead, 14 behind; merge base `1f5bb0b5b1ab501a7120598a7e6e0de75217ddb3` |
| Diff | 1,231 files; 73,643 additions; 964 deletions |
| Review | No submitted PR reviews or inline review threads were present at observation |

The changed paths span Parent mobile, Parent backend/API, Teacher Web/SVG, Docker/Compose, Firebase Auth emulator, MinIO, Modal workers/assets, migrations, and FEAT-063 plans/evidence/approval/context. Current local status has path overlap with 1 root path, 14 paths in `.worktrees/m2-s2`, and 9 paths in `.worktrees/mobile`. A path overlap is a collision requiring content reconciliation; it does not prove the branch contains the same change. This snapshot is not a test/CI result; no CI status was evaluated here.

The 2026-11-15 M2 baseline snapshot records 60 status entries. A read-only status check on 2026-11-16 reports 69 entries in `.worktrees/m2-s2`; the worktree is therefore **changed since that snapshot**, and that old manifest is not a current integration pin. Reconcile and pin the current M2 paths before using them as a merge baseline. No file-level conflict resolution was attempted for this roadmap.

**Disposition:** keep PR #26 itself open as a draft and do not merge it as one unit. Treat it as a candidate source for phase-scoped work only. Do not resolve its conflicts inside the active M2 or mobile worktrees, and do not cherry-pick its overlapping paths into them.

## 3. PR work mapped to the Rev68 sequence

| PR candidate | Roadmap placement | Conditions before use |
|---|---|---|
| Minimal local Compose/Auth-emulator/MinIO/synthetic-seed support | P0/M2 only if a named M2 or FR-C-08 owner test depends on it | Extract a minimal infrastructure-only change set. Review configuration and seed provenance, verify no real credentials or personal/child data, align with the pinned SRS/approval, and obtain a separate exact-path review/approval. Local infrastructure does not prove production readiness. |
| Parent APIs, activity suggestion/selection, Parent capture/context screens, Parent SVG/line-guide UI and required worker integration | **M3/P1 integration slice**, immediately before the synthetic Parent-AI acceptance run | First freeze the BE/FE API contracts against Rev68 and identify which PR operations are implemented, mounted, documented, and actually called by the UI. Include only exact reviewed paths needed by the M3 acceptance journey. Resolve the 14 BE and 9 mobile path collisions against the accepted M2/FE baselines. |
| Teacher Web SVG guide/editor, lesson visual and Teacher-facing service changes | **M4/P2 candidate**, after M3 acceptance | Review against Rev68 §5.2, the approved Teacher API contracts, current-assignment authorization, Teacher review/publication lifecycle, and separate M4 task approval. Do not bring these paths into the M3 Parent test slice. |
| Modal workers, model/runtime assets, generated evidence, migrations, FEAT-063 SRS/approval/status changes | No automatic phase assignment | Reconcile each item to an SRS requirement, approved feature plan, source/license/security evidence, and exact task allowlist. Evidence is not acceptance by file presence. Migration execution and provider calls need their own explicit authorization. |

The PR's embedded plans and historical evidence are not proof that a current contract or test passed. In particular, recheck all source and pins against Rev68; do not treat Rev67-era plan language, route declarations, screenshots, or test files as current approval or runtime evidence.

## 4. Revised single critical path

| Order | Gate / outcome | PR #26 action | Exit condition |
|---:|---|---|---|
| 0 | Align the active SRS authority and pin the exact working baselines | Keep PR unchanged. Record Rev68 as the FEAT-063 lane baseline and reconcile the root Rev60 pointer before cross-worktree publication. | One pinned authority per task; current M2 and mobile collision paths are inventoried without overwriting active changes. |
| 1 | Complete M2 S2 evidence and the separately authorized S3 remainder | Do not import PR's overlapping M2 files. | S2 evidence is reconciled without representing failed/unavailable checks as passes; S3 route/schema inventory, AT ledger, limitations, independent review and owner closure are accepted. M2 is not called complete until its actual closure rules pass. |
| 2 | Resolve and complete FR-C-08 under its own reviewed contract, exact allowlist, Task Approval and launch instruction | Do not use PR #26 as FR-C-08 implementation evidence. | Rev68/D-208 lifecycle contract, authorization, revocation, purge/reference proof, audit/retention decisions, and owner-run test evidence meet their approved gates. `OWNER_MODAL_CALL_APPROVED=NO` remains in force unless separately changed by the owner. |
| 3 | **After FR-C-08, reconcile FE/BE Parent API contracts** | Keep PR #26 unchanged; do not implement APIs during this audit. | Re-read current Rev68, BE routes/schemas/composition/OpenAPI, and FE clients/controllers/UI. Produce one row per required Parent API with method/path, request/response, errors/status, required headers, auth, revision/idempotency, declared/mounted/OpenAPI/runtime evidence, FE method, and actual UI caller. Classify gaps as BE missing, FE unconnected/blocked, contract mismatch, proposal/conditional mount, outside SRS, or unverified. Include consent policy, profile CRUD, image upload, context/subject confirmation, persisted activity selection/replacement, StoryRun create/read, story/script confirmation, jobs, and lifecycle operations. Treat cancel/delete/read after FR-C-08 as one final lifecycle contract, not a duplicate design. Deliver a separate BE/FE work split and owner questions; no code or runtime checks. |
| 4 | Prepare a narrow Parent-AI integration PR at M3/P1 entry | From a clean isolated branch based on current `dev`, select only approved Parent paths from PR #26; reconcile conflicts file by file; exclude Teacher Web and unrelated evidence. Keep the original PR #26 draft unchanged. | The API matrix and contract decisions from Order 3 are reviewed; exact path list and hashes are pinned; all conflict resolutions are reviewed; seed/secret/license/security checks and required approved automated gates pass; the integration PR is independently reviewed and owner-approved. |
| 5 | Merge the narrow Parent slice, then owner tests the synthetic Parent-AI journey | This is the planned **merge point** for the Parent-AI subset of PR #26. | Merge occurs immediately before M3 Parent integration acceptance, not during M2 or FR-C-08. Owner runs the exact approved UI/API test sequence with synthetic data. Any Modal/provider inference requires separate explicit authorization; merge alone grants none. |
| 6 | Complete M3/P1 Parent | Use only accepted contract-backed BE and mobile paths; do not add PR paths merely because they are available. | Rev68 §5.1 and applicable FR-P/FR-AI/NFR acceptance evidence passes, with open limitations explicit. |
| 7 | Complete M4/P2 Teacher Web | Review and merge a separate Teacher-only slice from PR #26 if it passes M4 gates. | Rev68 §5.2 and Teacher presentation, assignment, review, quota and lifecycle evidence pass under separate approval. |
| 8 | Complete M5/P3 Billing/Notifications, then M6/P4 Production Readiness | Reuse only individually reviewed/approved infrastructure or provider work. | Separate sandbox and readiness approvals/evidence pass; no real-data or production enablement is inferred. |

## 5. Parent-AI merge gate in operational terms

The full FE/BE Parent API reconciliation is a distinct gate **after FR-C-08 and before Parent-AI PR preparation**. It must use current source and Rev68, identify the actual FE UI caller, and distinguish source declaration, composition/mount, OpenAPI presence, test-run evidence, and runtime verification. FR-C-08 owns the final cancel/delete/lifecycle contract; the API matrix must consume that contract rather than restate it independently.

The Parent-AI portion should be merged **at the beginning of M3/P1**, after M2 S2/S3 closure, FR-C-08/P0 acceptance, and the reviewed Parent API matrix, and immediately before the owner's synthetic Parent-AI integration test. The table must cover method/path, request/response, headers/idempotency, authorization, composition/mount status, OpenAPI status, FE caller, and evidence level.

The PR #26 branch must not be merged wholesale to achieve that test. If the minimal Parent slice cannot be cleanly separated or its conflict resolutions cannot be reviewed against the pinned M2/mobile baselines, stop and keep the test blocked rather than importing Teacher M4 or unrelated changes early. No real child data is allowed. The standing `OWNER_MODAL_CALL_APPROVED=NO` prohibits Modal/provider calls until the owner explicitly authorizes a specific run.

## 6. Owners, dependencies, and open decisions

- **Owner:** accept Rev68 as the active FEAT-063 working baseline and synchronize the root authority pointer; accept the revised M2 → FR-C-08 → M3 ordering; approve exact implementation/merge/test gates; run the designated synthetic Parent-AI check; separately authorize any Modal/provider call.
- **BE lane:** reconcile S2/S3 and FR-C-08 gates; after FR-C-08, participate in the full Parent API contract matrix; provide source/mount/OpenAPI/runtime evidence distinctions and prepare the isolated Parent integration slice.
- **FE lane:** after FR-C-08, audit current mobile API methods and actual UI callers against the same matrix; disposition the 9 overlapping paths and provide mobile acceptance evidence under its own approval.
- **Web/Teacher lane:** review the Teacher-only PR subset against Rev68 P2 after M3; no Teacher work is pulled into the Parent-AI merge.
- **Open:** exact PR #26 files needed for the minimal Parent-AI slice; whether any local Compose/Auth/MinIO subset is necessary; the separate provider/Modal authorization and exact test command; and final named task owners/command ceilings. No source-level allowlist is inferred from this roadmap.

## 7. Approval boundary and review status

The owner accepted this integrated roadmap sequence in the current conversation on 2026-11-16 and clarified that full FE/BE Parent API contract reconciliation occurs after FR-C-08 and before the Parent-AI PR slice. This acceptance covers planning order and PR #26 placement only. It does not revise existing S2/S3 or FR-C-08 approvals; approve PR #26; authorize file reconciliation, conflict resolution, merge, tests, implementation, provider calls, or M3/M4 launch. The prior independent reviews apply only to their pinned Draft 2/Draft 3 inputs and do not review this updated roadmap text. Any implementation or merge package still requires its own exact scope, review, Task Approval, and launch authorization.

This planning acceptance is recorded in this roadmap only; no implementation approval was appended to `approvals/TASK_APPROVAL.md`. No test, build, validator, backend/runtime, database/migration, Docker, network, provider, Modal, stage, commit, or push action is authorized by it.

## 8. Source pins at planning observation

| Input | Observed value |
|---|---|
| Worktree canonical SRS Rev68 | 639,948 bytes; SHA-256 `69C83FE49CD4689D5D2540656D3319721838CF7343BAD00E24CDE558B8F5E944` |
| Worktree SRS authority | 4,313 bytes; SHA-256 `D6153D38000C95E43A4091C5DF2E856FAD872A33177E3A8542E30EF2BEDCAB60` |
| D-208 DECISIONS.md snapshot | 216,212 bytes; SHA-256 `52F2E141244829281FF762BA100D1A991D5CADFF042A237C8C125F324300725F` |
| M2 S2 implementation report | 25,879 bytes; SHA-256 `F49D1FDB2B3C26387FFABC51C316F226C5D1FC5FC12B4856B0A6172A81941F55` |
| M2 baseline snapshot | 12,860 bytes; SHA-256 `4826D95ED4DD2C57D2091F89DB2ECCD97628E522630B67C35ABADF700F7D455B` |
| M3–M6 Roadmap Draft 3 | 22,691 bytes; SHA-256 `DC6AFE31344437E97D800450AEAD0BEE56EAF05B8FB1AA20E701126C71C47D88` |
| Roadmap Addendum Draft 2 | 8,024 bytes; SHA-256 `8CE372A6F35F01C16EF67376636D3E0BA6A75E1F7D9F0CCCF6549E9B4B11D2C8` |
| Current PR #26 base/head | Base `c87d8008b70910eb0a4d3579b9490312e7e3143f`; head `78f3b5eece7dc4010631889c3599cf4dbacd9550` |

These are last-observed planning pins, not merge-time pins. Rehash and recheck all selected files and GitHub refs immediately before any future approval or integration task.
