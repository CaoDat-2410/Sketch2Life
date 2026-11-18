# FR-C-08 implementation readiness and gate sequence — Draft 2

**Status: DRAFT / BLOCKED FOR IMPLEMENTATION / NOT APPROVED / NOT LAUNCHED.**  
**Date:** 2026-11-15  
**Predecessor:** `FR_C08_IMPLEMENTATION_READINESS_ADDENDUM_DRAFT1_20261115.md`. This revision preserves its source findings and addresses its independent review findings.  
**Purpose:** state the exact current implementation blockers and ordered gates after the M2 baseline snapshot and the SRS-defined DELETE route audit.

## 1. Authority and scope

For this active BE worktree, use its `docs/context/SRS_AUTHORITY.md` and unsigned Rev68 SRS under D-203/D-208. Rev67 is preserved as the prior D-203 source. The main/root checkout still points to Rev60; that authority discrepancy is visible and must not be silently reconciled. This Draft 2 governs only planning for the current `.worktrees/m2-s2` snapshot; it does not alter either authority record.

Rev68 §21.2 already specifies both `POST /v1/story-runs/{id}/cancel` and `DELETE /v1/story-runs/{id}`. Current BE source declares the Parent detail GET and cancel POST but no DELETE handler. The DELETE path is therefore a missing implementation of an existing SRS operation, not an invented route. The detailed correction is [FR_C08_DELETE_ROUTE_SCOPE_CORRECTION_DRAFT1_20261115.md](FR_C08_DELETE_ROUTE_SCOPE_CORRECTION_DRAFT1_20261115.md).

## 2. Current source and M2 status

The BE worktree is `feature/feat063-m2-s2` at `5de30674bc826591ad4b3cc00fca53c7597ead51`. It remains dirty and the M2 report is **PARTIAL / NOT COMPLETE**.

The exact 60-path dirty snapshot is recorded at [FR_C08_M2_BASELINE_SNAPSHOT_20261115.md](../evidence/FR_C08_M2_BASELINE_SNAPSHOT_20261115.md): 24 modified, 36 untracked, 0 staged at 2026-11-15 16:16:55 UTC. The record classifies the M2 test/typecheck/lint results as historical non-passing or unavailable evidence; it does not mark M2 complete or approve any evidence for reuse. Recheck selected paths at a future launch; an approval must name which exact source/evidence snapshot it relies on. No M2 approval or command ceiling transfers.

The live source audit found:

- Existing `GET /v1/story-runs/{id}` is the default lifecycle read under D-208, but the current response schema omits `DELETED` and is not the Rev68 18-state inventory.
- Existing cancel is Parent-only in source and its repository accepts seven current values, including `SCRIPT_GENERATING` and `SCRIPT_GENERATION_UNKNOWN`, rather than the 13 UC-11 eligible states.
- The required explicit DELETE operation is absent from the Parent router. Adding only this SRS-defined method/path to the existing router/composition is required; no other route is selected.
- Current BE1 lifecycle request/cancellation records require `organization_id`; the source does not establish typed Parent request/receipt persistence or current Teacher assignment/version authorization.
- Core source exposes metadata/object primitives, but the inspected contract does not provide complete run-reference closure, safe shared-asset deletion proof, and terminal purge evidence.
- Runtime, database state, API mounting in a running environment, revocation behavior, worker/provider cancellation, and purge completion remain **NOT VERIFIED**.

## 3. Ordered gates

| Order | Gate | Status | What closes it |
|---:|---|---|---|
| 0 | Reconcile/pin M2 baseline | **Snapshot recorded; M2 remains partial.** | Snapshot and failed/unavailable evidence disposition are pinned. Any future implementation approval must select exact reusable evidence and paths; fresh rehashes are required at launch. This is not M2 completion. |
| 1 | Versioned lifecycle contract and typed Parent request/receipt | **BLOCKED.** | Review the route correction and specify BE1 coordination, Story transition/event/lock, Core Asset ownership, AI Jobs best-effort cancellation, typed `PARENT_ACCOUNT`, durable receipt owner/replay boundary, and DTR/schema consequence. Never fabricate `organization_id`. |
| 2 | SRS operations, read and state mapping | **BLOCKED.** | Include `DELETE /v1/story-runs/{id}` and its Rev68 §21.2 behavior in the contract and existing router/schema scope. Reconcile the owner-scoped GET with all 18 SRS states and verified `DELETE_PENDING`/`DELETED`; reconcile source compatibility to exactly the 13 cancel states without adding a state. |
| 3 | Current authorization and immediate revocation | **BLOCKED.** | Specify current Parent ownership and current Teacher assignment/version checks; fail-closed fences for API, download, playback token, stream/cache, upload/partial upload, and job dispatch, including already-issued access and reassignment. |
| 4 | Owner-module cancellation, purge and reconciliation | **BLOCKED.** | Specify Story event/late-result fence, AI Jobs best-effort cancellation, Core Asset reference enumeration/removal, incomplete-upload cleanup, shared-reference proof, idempotent retries/restart reconciliation, and evidence before `DELETED`. No cross-module SQL assumption. |
| 5 | Audit fields and retention | **BLOCKED for dependent audit behavior and full acceptance.** | Obtain approved field allowlist, reader permission, Parent physical mapping and record-type mapping to 180/365 days. Do not implement dependent audit reads/writes before that contract exists. |
| 6 | Contract/allowlist review and separate Task Approval | **NOT READY.** | Independently review the corrected versioned contract and exact-path allowlist; obtain a distinct FR-C-08 Task Approval with selected paths and fresh command ceilings. No launch instruction is included in this gate. |
| 7 | Named accountable people | **OPEN — before-launch gate.** | Record named accountable module owners under D-208. Names are not required to draft/review a contract or to issue a bounded pre-launch Task Approval; technical ownership/interface blockers remain separate. |
| 8 | Pinned launch instruction | **NOT READY; comes after Gate 7.** | Issue or activate the pinned launch instruction only after named accountable owners are recorded and all implementation blockers/approval gates are closed. An earlier instruction must be explicitly conditional and non-executable. |
| 9 | Real-data / production use | **GATED.** | Synthetic-only evidence until Rev68 §29.2 and D-208 requirements are separately met and the owner grants the required authorization. `OWNER_MODAL_CALL_APPROVED=NO`. |

## 4. Remaining technical blockers

The next work is not a code implementation prompt. The versioned contract must settle the operation details left open by Rev68: exact request/body (Rev68 does not specify an `expected_revision` for DELETE), shared idempotency-key parsing/replay representation, receipt/request ownership, current Teacher authorization adapter, proof and failure semantics for existing GET, Story event/outbox boundary, every revocation fence, Core Asset reference-closure API, purge retry/reconciliation, and audit mapping. The route method/path/status/eligible states are already fixed by Rev68 and must not be treated as open.

The current source’s parent-only auth, seven-value cancel set, response-state mismatch, lack of DELETE handler, org-only lifecycle persistence and incomplete Core delete/reference contracts are source facts at the pinned observation; none proves runtime behavior.

## 5. Independent review disposition

The independent review of Addendum Draft 1 returned **CHANGES REQUIRED — 0 P1, 1 P2, 1 P3**. Its capture is [FR_C08_READINESS_ADDENDUM_DRAFT1_COLD_REVIEW_CAPTURE_20261115.md](../evidence/FR_C08_READINESS_ADDENDUM_DRAFT1_COLD_REVIEW_CAPTURE_20261115.md). Draft 2 corrects both findings: Task Approval precedes named-owner assignment, while the launch instruction follows it; the Draft 4 CLEAN verdict is described only as the result of that historical review snapshot.

The route-scope correction and this successor addendum still require independent review. A prior CLEAN review of Draft 4 does not review these changes.

## 6. Pins

| Input | Bytes | SHA-256 |
|---|---:|---|
| Worktree SRS authority | 4,313 | `D6153D38000C95E43A4091C5DF2E856FAD872A33177E3A8542E30EF2BEDCAB60` |
| Worktree canonical Rev68 SRS | 639,948 | `69C83FE49CD4689D5D2540656D3319721838CF7343BAD00E24CDE558B8F5E944` |
| Owner-supplied Rev67 / D-203 provenance | 634,291 | `B704163C9AAF7BB198D8578699F75DB8766C2226A52CD48B0ED1314AF5E21996` |
| D-208 decision register | 216,212 | `52F2E141244829281FF762BA100D1A991D5CADFF042A237C8C125F324300725F` |
| M2 S2 implementation report | 25,879 | `F49D1FDB2B3C26387FFABC51C316F226C5D1FC5FC12B4856B0A6172A81941F55` |
| M2 dirty baseline snapshot | 12,860 | `4826D95ED4DD2C57D2091F89DB2ECCD97628E522630B67C35ABADF700F7D455B` |
| Route-scope correction Draft 1 | 10,582 | `E19028505E3945F3F290525332F33BD8292EB5EC29CEBAD2F978EDB407E698CD` |
| Readiness Addendum Draft 1 review capture | 2,446 | `677A1D91FE84338035B5024AFEE6041985A79EFF9F475781640CF1F7BF07177F` |
| Spec Draft 4 | 20,897 | `BC268E2354AED6FDC142CCD58BFDF89BACF6585F15B7ED75C8AE7C4C41ED9B70` |
| Allowlist Draft 4 | 65,130 | `F4C76422DDE39A2B34A5364BC6F7F77B3A960331F4DBA00939082FBE54E3512A` |
| Roadmap Draft 3 independent review | 1,600 | `59714ECA1C056FB10E76D6C3168B97FC7B4E21DE671EEBF8FBC52291E0A8AC4A` |

This is a planning addendum only. It does not change code, tests, SRS, DTR, decisions, approval records, status records, or prior reviewed files. No tests, typecheck, Ruff, validators, runtime/backend, database, migrations, Docker, network, provider, Modal, staging, commit, or push ran for this update.

