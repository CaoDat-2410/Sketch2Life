# FEAT-057 G0 contract direction review — 2026-10-21

## Verdict and scope

**PASS — G0 direction finalized at FEAT-057 scope, with card-owner adoption blockers.**

The X01/X05/X09-08 and POLICY-08 directions are consistent with the candidate
interfaces when stated as requirements for later owner adoption. This review
does not treat candidate interfaces or fixture behavior as a durable,
cross-card contract. It is not card-owner adoption, implementation approval,
acceptance, or runtime authorization.

## Reviewed snapshot and preserved baseline

- Worktree: `.worktrees/be2-01-14-integration-linked`
- Branch / HEAD: `feature/be2-backend-ai-integration` /
  `1649b72978877d82b4d7662040ff3555dee0a3a7`
- Plan revision: 3
- Plan SHA256 before this review update:
  `32D772C0592F65F9BC038DDC902868178627E5F771E03AB20499B91DF81B8A5D`
- Plan SHA256 after this review update:
  `5500B0CA5ED839C4FF5150D66FC19F2751F6C1F93261DE37BB1629747FF41C04`
- Initial index: empty. The pre-existing dirty source, test, approval, context,
  status, plan and evidence paths were inventoried before review and preserved.
  No stage, reset, cleanup, source/test edit, approval edit, branch/worktree
  change, commit, push or merge was made.

## Contract findings

| Direction | Finding |
|---|---|
| X01 source fence | BE2-07 `resolve_exact` and the FEAT-057 adapter validate the pinned bundle identity, source references/hashes, organization/session, and editorial/context/audience revisions. The exact read is point-in-time; the repository transaction ends before BE2-08 finalization. BE2-07 acceptance leaves actual BE2-08 lease/fence adoption open. Require the exact identity and an adopted fence held or atomically checked through finalization. Keep X01 `PARTIAL`. |
| X05a boundaries | Candidate `AtomicVideoSubmission` and `AtomicVideoFinalizer` protocols support two distinct UoWs and do not span provider work. They specify candidate transaction contents, CAS and recovery expectations, but BE2-08 status says the actual durable CR08-01 bridge and adapters are open. Require separate card-owner adoption for submission and finalization. |
| Replay/race/late result | Candidate source documents body-bound submission replay, authorization before semantic dedup, authoritative finalizer lookup (`None` means known absent), and pending recovery after ambiguous finish. They do not prove a durable cross-card winner protocol. BE2-01/08 must confirm receipt identity/scope, replay authorization, duplicate winner, current-attempt CAS and late-result behavior under held source/policy fences. Treat same-result/no-duplicate behavior as a required adopted contract, not demonstrated integration. |
| X09-08 | The foundation worker calls its provider directly; no typed route to BE2-08 `VideoWorker` exists. `VideoWorker` rejects a job type it does not recognize. The current envelope carries message/job/attempt/type/request reference and capability, but not an explicit source pin or idempotency key. BE2-01/08 must adopt a fail-closed route and map subject/session/source pin/idempotency from the immutable job/run or a versioned envelope contract. No BE2-13 route. |
| X05b / CR09-01 | BE2-09 has candidate guarded review-write/head storage, but its dependency register leaves canonical-head and combined DATA-27 projection adoption open. Direction requires the canonical review projection to bind the exact BE2-08 artifact hash/version. Do not edit BE2-08 rows or migrations. |
| X05d | Exact source resolution exists, but no owner-adopted current-source resolver/fence through use/finalization was established. Use only one already adopted by its owner; otherwise X05 remains incomplete. Keep X02 and any new receiver/event outside this slice. |
| POLICY-08 | BE2-08 candidate `RenderAuthority` checks cover preparation, source, generation, validation, staging and finalization phases. BE2-14 current-use eligibility does not provide worker/provider execution authorization or budget/concurrency reservation/accounting. Require those separately, phase by phase, fail-closed through finalization. |
| X05c / CR09-02 | BE2-09 records playback intent/receipt as historical and leaves actual BE1 session/access receipt plus the each-use gateway open. Keep this open; intent is not actual session start or playable access. |
| OD-ENV | Keep Modal deferred until a separate explicit resume instruction. |

The direction is reviewable and final at FEAT-057 scope. The adoption items
above block implementation and cross-card claims until recorded by the owning
cards. X01 remains `PARTIAL`; X02–X09 remain `NOT_IMPLEMENTED`; all card status
and acceptance records remain unchanged.

## Current owner-record review

- BE2-01 / FEAT-044: Phase B B1–B6 approval exists; BE2-01 remains
  `IN_PROGRESS`, and the foundation approval does not adopt BE2-08 routing,
  BE2-07 source fencing or BE2-09 review/session access.
- BE2-07 / FEAT-056: offline component acceptance exists; card remains
  `IN_PROGRESS / NOT_DONE`; actual BE2-08 adoption/lease/fence is expressly open.
- BE2-08 / FEAT-050: card-local approval exists; card remains `IN_PROGRESS`;
  actual atomic start/completion bridge and durable adapters remain open.
- BE2-09 / FEAT-051: card-local approval and own SQL evidence exist; card
  remains `IN_PROGRESS`; CR09-01/02 adoption and actual gateway/session access
  remain open.
- BE2-14 / FEAT-049: card-local component and SQL approval/evidence exist;
  card remains `IN_PROGRESS`; owner/provider bindings, worker authorization and
  atomic budget/concurrency adoption remain open.

Frozen plan headers were not used to override the current approval/status
records. No owner approval file was changed.

## Source hashes reviewed

| Current source file | SHA256 |
|---|---|
| `backend/src/sketch2life/application/services/knowledge_bundle.py` | `AF6C3C55E3CF0FEDF155B8C0EBBF720EF7E6AEC121B5B1871F94191A1E2F6C9F` |
| `backend/src/sketch2life/infrastructure/cross_lane/knowledge_script_video.py` | `0A22E50557B3AC57B9913B80B273D0A672423946277AF3E7CFA9A0829E7F6F42` |
| `backend/src/sketch2life/application/ports/knowledge_video.py` | `966FE8BF2237C956298164F28EB461527B7E2A0BBA1EBFF0084E91D834113340` |
| `backend/src/sketch2life/application/ports/knowledge_video_worker.py` | `8B5A3175717DB3411C4A6B80B8FBEF2E5865DC3530598A2F35919D6954CC1D36` |
| `backend/src/sketch2life/application/knowledge_video_media.py` | `A5B569BFC0C83079A066719324A446AC0566A9A171B2192AAD7C795064C6BAFB` |
| `backend/src/sketch2life/application/knowledge_video_worker.py` | `02BE5A965EABEAE4792AD0915CB2B5EBBE48D452FA37595AA32C52EAEC373C90` |
| `backend/src/sketch2life/infrastructure/ai_jobs/worker.py` | `241B4AE77164FDC3FCF01952473D726F74FCF381B683E6583F307448046A1B40` |
| `backend/src/sketch2life/application/ports/ai_jobs.py` | `6C6967070D5042B5A6DB33E7D28D856E03FE1BD6DC1302E55D73EACC047B33DF` |
| `backend/src/sketch2life/application/ports/video_review_write.py` | `C6D627598E42651E499A104AA71D5EE529349AA166BC602A2B8D467E575D864F` |
| `backend/src/sketch2life/application/ports/ai_policy_use.py` | `5EF8B7370DC4E644EAE5AE885A38DC1C928596EE5096C790D9721ABE92C00155` |

## Checks

- `python tools/validate_harness.py`: **PASS** (exit 0).
- `python tools/validate_repository_security.py`: **PASS** (exit 0; 4,547
  publishable files scanned).
- `python tools/validate_architecture.py`: **PASS** (exit 0).
- `python tools/validate_skeleton.py`: **PASS** (exit 0).
- `git diff --check`: **PASS** (exit 0).
- Plan and review receipt: LF endings, final LF, no trailing whitespace.
- Tests, Modal, Lightning, provider, service, database and runtime: **NOT RUN**
  by instruction. These documentation checks do not authorize implementation
  or alter card status.
