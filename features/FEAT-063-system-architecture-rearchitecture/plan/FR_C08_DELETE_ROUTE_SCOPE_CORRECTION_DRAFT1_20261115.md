# FR-C-08 DELETE route and contract-scope correction — Draft 1

**Status: DRAFT / BLOCKED FOR IMPLEMENTATION / NOT APPROVED / NOT LAUNCHED.**  
**Date:** 2026-11-15  
**Purpose:** Correct the route-scope omission found after the independent Draft 4 review. This document accompanies Lifecycle Contract Draft 2, Specification Draft 4, Lifecycle Plan Draft 4, and Allowlist Draft 4. It supersedes only their statements that exclude or fail to select the SRS-required explicit DELETE operation. No source, schema, approval, decision, or SRS file is changed.

## 1. Authority and scope

Use the unsigned canonical working Rev68 in the active `.worktrees/m2-s2` worktree under D-203/D-208. The owner-supplied Rev67 file remains historical provenance for D-203. The main/root checkout's authority pointer still says Rev60; this is a recorded lineage difference, not a reason to silently switch the active FEAT-063 worktree back to Rev60. This correction is scoped to the active BE worktree and preserves the root/worktree authority discrepancy for coordinator reconciliation.

Rev68 §21.2 specifies two different operations:

- `POST /v1/story-runs/{id}/cancel` for eligible unfinished runs.
- `DELETE /v1/story-runs/{id}` for an explicit user-requested deletion of COMPLETED, FAILED, or ABANDONED.

Therefore `DELETE /v1/story-runs/{id}` is **already a product-contract operation in Rev68**. It is missing from the inspected BE HTTP source. Planning it is implementation of an existing SRS requirement, not invention of another SRS route. The source gap must not be hidden by the phrase “no new route.”

## 2. Current source observation

At the pinned worktree observation:

- `parent_story_runs.py` is 14,626 bytes / `A2BA4553785BE7367A7F105708CE1A7F618DFE4A3538D85F00DDD9AE938467DD`. Its router prefix is `/v1/story-runs`; it declares GET detail and POST cancel, and contains no DELETE handler. The cancel handler calls the Parent-only `_require_parent`; this does not establish current-Teacher authorization.
- `parent_story_runs.py` GET detail returns the existing Parent response. Its current `run_state` schema does not enumerate the full Rev68 18-state inventory and omits `DELETED`; the source's current values include compatibility values outside the Rev68 inventory.
- The Parent router has prefix `/v1/story-runs` and is included directly by the existing composition when `include_parent_story_runs` is true; app construction supplies `not story_demo_enabled`. This makes the SRS path statically present in the non-demo source composition if a DELETE decorator is added. It is conditional source composition only; no runtime, deployed route, or generated OpenAPI output was inspected for this correction.
- This operation belongs in the existing Parent StoryRun router/composition and the existing schema/test paths already listed as E/N candidates in Allowlist Draft 4. The source router prefix matches the SRS path; no proxy rewrite is asserted.

The Dirty M2 source pins are observations, not clean-branch or runtime attestations. Any later difference is “changed since observation” and requires fresh review.

## 3. SRS-bounded contract for the operation

| Contract aspect | Settled by Rev68/D-208 | Still open; do not infer |
|---|---|---|
| Method and SRS path | `DELETE /v1/story-runs/{id}` (Rev68 §21.2); the router prefix is already `/v1/story-runs`. | Any extra route. Runtime/OpenAPI exposure remains unverified. |
| Eligibility | Explicit user request only for COMPLETED, FAILED, or ABANDONED; never automatic purge for FAILED/ABANDONED; DELETE_PENDING and DELETED accept no new user delete/cancel command. | Any additional eligible state or implicit deletion trigger. |
| Authorization | Current Parent owner or currently assigned Teacher, checked against current BE1 assignment/version (D-208 item 4). | Exact shared adapter/port and failure mapping; current source's Parent-only dependency does not satisfy Teacher support. |
| Acceptance | HTTP 202 lifecycle request; Story becomes/remains publicly DELETE_PENDING until required purge is verified, then DELETED; use owner-scoped GET as default read. | Exact response envelope/receipt fields, lifecycle-request identifier, and persistence owner/schema. |
| Idempotency | Required for state-changing commands by principal, operation, and target; same key/payload replays the original result; changed payload with reused key returns INVALID_IDEMPOTENCY_KEY (Rev68 §21.4). | Header parsing limits, canonical payload hash, receipt ownership/storage, and exact replay body/status where not already specified by an approved common contract. |
| Revision precondition | Rev68 §21.2 DELETE row does not state an `expected_revision` precondition. | Do not copy POST cancel's expected-revision requirement to DELETE without an approved contract decision. |
| Purge | Owner-module purge, immediate revocation, best-effort job/provider cancellation, late-result fencing, shared-reference verification, and preservation rules remain governed by Rev68/D-208. | Cross-module request/receipt schema, retry/reconciliation evidence, terminal proof, audit field/read permissions, physical Parent mapping, and retention mapping. |

The current GET is the default read. It must expose the SRS-defined state correctly and must only report DELETED after an owner-module proof of required purge. If that cannot be established through the existing GET, propose the smallest read-contract change for review; do not introduce a new read route, public state, progress percentage, or count by inference.

## 4. Exact planning corrections

Read this document together with the named Draft 4 inputs. It supersedes only the following route-scope statements:

1. **Lifecycle Contract Draft 2 §4.3:** replace “This draft adds no route” with: “The required `DELETE /v1/story-runs/{id}` operation is specified by Rev68 §21.2 and is absent from current HTTP source; the operation must be included in the versioned implementation contract. No other route is proposed.”
2. **Specification Draft 4 §4 and §5.2:** the 18-state matrix adds no state, but the implementation must add the already-SRS-defined DELETE operation. Replace “It is not a new route” with the source fact and scope: “This SRS-defined operation is absent from current source and must be implemented in the existing Parent StoryRun router after contract decisions; no route beyond Rev68 §21.2 is selected.”
3. **Allowlist Draft 4 §4.1 row for `parent_story_runs.py`:** include both existing `POST /{run_id}/cancel` and the required `DELETE /{run_id}` operation under the router prefix `/v1/story-runs`. It is not a selection of any route beyond Rev68 §21.2.
4. **Allowlist Draft 4 §4.2 opening:** replace the blanket “No new route ... is proposed” with: “The only route operation in this plan beyond the currently declared source is the already-SRS-defined `DELETE /v1/story-runs/{id}`; no additional path/method, schema field, migration, audit table, or provider adapter is selected.”
5. Preserve the existing E/N/H path classes and all other Draft 4 constraints. The route/schema/test files are dirty M2 candidates: no future edit may overwrite or discard their existing bytes. Re-hash and resolve each selected-path collision before launch. The N contract test can cover DELETE only after the wire contract has been independently reviewed.

## 5. Remaining blockers and next gates

The correction resolves a planning omission; it does not resolve these technical blockers:

1. Typed `PARENT_ACCOUNT` scope, cross-module versioned request, durable receipt owner and schema; never use a fabricated `organization_id`.
2. Complete 18-state mapping and current-source compatibility for `SCRIPT_GENERATION_UNKNOWN`; the present cancel allowlist is not the 13-state UC-11 set.
3. Current Parent/Teacher authorization, including current assignment/version checks, and immediate fencing for API, download, playback/token, stream/cache, upload/partial upload, and job dispatch.
4. Story event/lock/fence integration; best-effort AI Jobs cancellation; late/duplicate/unknown result fencing.
5. Core Asset reference enumeration/removal, object/metadata deletion, incomplete-upload cleanup, valid-independent-reference proof, retries, and evidence for terminal DELETED.
6. Audit field allowlist/readers, typed Parent physical storage mapping, and the mapping of record types to 180/365-day retention.
7. The dirty/partial M2 baseline is now captured in `evidence/FR_C08_M2_BASELINE_SNAPSHOT_20261115.md` (60 paths, 0 staged, 24 modified and 36 untracked at 2026-11-15 16:16:55 UTC). This pins the observed state; M2 remains PARTIAL / NOT COMPLETE. Rehash selected paths at any future launch and do not reuse M2 approvals or command ceilings.

The ordered next step is: independently review this correction with the Draft 2 contract and Draft 4 specification/allowlist; resolve the remaining versioned technical contracts and schema dependencies; then prepare an exact revised allowlist and obtain separate implementation approval. Named module owners are a before-launch gate, not a prerequisite to draft/review/Task Approval. Issue or activate the pinned launch instruction only after names are recorded. M3 implementation also remains gated on the separate M2 exit/S3 disposition.

## 6. Pins and evidence limits

- Worktree Rev68: 639,948 bytes / `69C83FE49CD4689D5D2540656D3319721838CF7343BAD00E24CDE558B8F5E944`.
- D-208 in DECISIONS.md: 216,212 bytes / `52F2E141244829281FF762BA100D1A991D5CADFF042A237C8C125F324300725F`.
- M2 baseline snapshot: 12,860 bytes / `4826D95ED4DD2C57D2091F89DB2ECCD97628E522630B67C35ABADF700F7D455B`.
- M2 S2 implementation report: 25,879 bytes / `F49D1FDB2B3C26387FFABC51C316F226C5D1FC5FC12B4856B0A6172A81941F55`.
- Lifecycle Contract Draft 2: 46,791 bytes / `567B28A6C85BD3BB8608C7B48D1F60CABC36B5AEA28E25D52784A11FB2BAC712`.
- Specification Draft 4: 20,897 bytes / `BC268E2354AED6FDC142CCD58BFDF89BACF6585F15B7ED75C8AE7C4C41ED9B70`.
- Allowlist Draft 4: 65,130 bytes / `F4C76422DDE39A2B34A5364BC6F7F77B3A960331F4DBA00939082FBE54E3512A`.
- Draft 4 independent review: 3,084 bytes / `9C6A39CD071DA247C3B7F484C7536ED84BDF33CEA2D3BAE3BDCFF0C56F23118F`.

This document is a correction proposal, **not** an implementation contract approval, allowlist approval, Task Approval, command authorization, DDL/migration approval, or launch. No source or test file was changed. No tests, validators, runtime/backend, database, migration, Docker, network, provider, or Modal command was run. `OWNER_MODAL_CALL_APPROVED=NO`.

