# FEAT-063 M3–M6 roadmap — FR-C-08 gate addendum Draft 2

**Status: DRAFT / PROPOSED FOR OWNER REVIEW / NOT APPROVED / NOT LAUNCHED.**  
**Date:** 2026-11-15  
**Predecessor:** `M3_M6_SRS_ALIGNED_ROADMAP_ADDENDUM_DRAFT1_20261115.md`. This revision corrects the independent-review findings and records the pinned M2 snapshot and SRS-defined DELETE scope.

## 1. Authority and purpose

The active `.worktrees/m2-s2` authority points to unsigned canonical working SRS Rev68 under D-203/D-208. Rev67 remains the historical D-203 source. The root checkout authority still points to unsigned Rev60; this worktree-scoped addendum records that discrepancy rather than silently switching sources. Roadmap Draft 3 remains the complete Rev68-to-M3/M4/M5/M6 mapping and received a CLEAN independent review at its pinned snapshot. This addendum changes readiness/dependencies only; it removes no SRS acceptance requirement and grants no approval.

The independent review of Roadmap Addendum Draft 1 returned **CHANGES REQUIRED — 0 P1, 1 P2, 1 P3**. The review capture is recorded in `FR_C08_READINESS_ADDENDUM_DRAFT1_COLD_REVIEW_CAPTURE_20261115.md`. Draft 2 orders the launch instruction after named-owner assignment and describes the Draft 4 CLEAN verdict as historical. Draft 4's recorded CLEAN verdict remains true for its reviewed bytes; the subsequent source audit found that its route-scope text did not select Rev68's DELETE operation.

## 2. Current readiness and SRS comparison

The current BE worktree is `feature/feat063-m2-s2` at `5de30674bc826591ad4b3cc00fca53c7597ead51`. The dirty baseline was pinned at 2026-11-15 16:16:55 UTC in `FR_C08_M2_BASELINE_SNAPSHOT_20261115.md` (60 paths; 24 modified, 36 untracked; 0 staged). M2 remains **PARTIAL / NOT COMPLETE**. The snapshot does not make M2 complete or transfer its approval/command ceilings.

Rev68 §21.2 already requires `DELETE /v1/story-runs/{id}` for explicit deletion of COMPLETED, FAILED and ABANDONED. It is absent from the inspected Parent HTTP router. Planning this operation implements an SRS-defined requirement; it is not a new product endpoint. The corrective scope is pinned in `FR_C08_DELETE_ROUTE_SCOPE_CORRECTION_DRAFT1_20261115.md`. The current GET response/state mapping, current-Teacher authorization, immediate revocation, cross-module typed Parent request/receipt, purge/retry proof and audit mapping remain incomplete or unverified.

| Milestone | SRS-aligned disposition |
|---|---|
| M2 / S2 and S3 | S2 remains partial. The dirty snapshot and non-passing/unavailable evidence are documented. Separately reconcile the M2 exit and any approved S3 remainder before treating M2 as the completed foundation for M3. M2's frozen state is not M2 completion. |
| M3 / P1 Parent | Retain full Roadmap Draft 3 / Rev68 §5.1 acceptance: image-first flow, adult-confirmed context and activity selection, Parent quota/compute admission, video, history/reminder/closeout, optional guide safeguards. Start implementation only after the accepted M2 foundation, resolved FR-C-08/P0 contracts and API dependencies, and separate Task Approval. Do not claim full M3 or lifecycle acceptance while any required P0/FR-C-08 acceptance evidence remains open. |
| M4 / P2 Teacher | Retain full Rev68 §5.2 flow and editable presentation, current class assignment authorization, equal-probability one-child sample selection, Teacher quota scope and occurrence/sample invariants. Do not claim lifecycle-complete acceptance before FR-C-08 evidence. |
| M5 / P3 Billing and Notifications | Preserve the quota/compute-admission dependency before accepted video work; M5 adds sandbox billing/notification evidence. No live merchant or production provider use follows from this plan. |
| M6 / P4 Production readiness | Preserve the Rev68 §29.2 readiness gates for legal/privacy/security, retention, backup/purge, operations and data migrations. Named owners precede launch; synthetic milestone completion does not enable real-data use. |

No schedule estimate is supplied: M2/S3, lifecycle contracts and API dependencies remain unresolved, so calendar estimates would be false precision.

## 3. Ordered critical path

1. Preserve the recorded M2 snapshot, rehash selected inputs when a task is authorized, and separately complete/accept the M2 exit and any approved S3 remainder before M3.
2. Resolve the technical FR-C-08 contracts; explicitly include the already-SRS-defined DELETE method/path in the versioned contract and existing router/schema scope; independently review the corrected contract and exact allowlist. The route-scope correction and readiness package are not yet independently reviewed.
3. Reconcile current FE/BE APIs and complete the P0 contracts needed for both vertical slices, including Parent scope/receipt, current assignment authorization, quota admission, hard-cost reservation, upload, consent/context/activity and recovery behavior. Do not treat source declarations as runtime proof.
4. Obtain separate FR-C-08 Task Approval after its exact allowlist and gates are reviewed. Record named accountable module owners under D-208 before launch. Issue/activate a pinned launch instruction only after names are recorded and all implementation blockers are closed.
5. After M2 foundation acceptance, resolved FR-C-08/P0 contracts and API dependencies, and the applicable task approvals, deliver M3 Parent then M4 Teacher in SRS order. Keep FR-C-08 as a cross-cutting P0; do not label full M3 or lifecycle acceptance complete before the purge predicate is evidenced.
6. Deliver M5 sandbox billing/notification evidence and then M6 readiness evidence under separate approvals and owner allocation.

## 4. Gates, open questions and boundaries

- This roadmap does not approve FR-C-08 implementation or resolve its Parent-scope/receipt schema, Core Asset reference-closure, state compatibility, current Teacher adapter, revocation, audit mapping, or retention questions.
- FR-C-08 baseline pinning is complete only for the recorded dirty snapshot; M2 itself remains partial. At launch, selected-path changes or new worktree files require fresh reconciliation.
- Rev68 §21.2's DELETE path/status/eligibility are settled. Its request-body/receipt representation and exact revision precondition are not fully specified; do not copy the cancel request's `expected_revision` onto DELETE by inference.
- The route-scope correction says the current operation is absent in source; composition is conditional and runtime mounting has not been exercised.
- Keep work synthetic under Rev68 §29.2 and D-208. `OWNER_MODAL_CALL_APPROVED=NO`.

## 5. Pins and review boundary

| Input | Bytes | SHA-256 |
|---|---:|---|
| Worktree SRS authority | 4,313 | `D6153D38000C95E43A4091C5DF2E856FAD872A33177E3A8542E30EF2BEDCAB60` |
| Worktree Rev68 SRS | 639,948 | `69C83FE49CD4689D5D2540656D3319721838CF7343BAD00E24CDE558B8F5E944` |
| Rev67 source selected by D-203 | 634,291 | `B704163C9AAF7BB198D8578699F75DB8766C2226A52CD48B0ED1314AF5E21996` |
| D-208 DECISIONS.md | 216,212 | `52F2E141244829281FF762BA100D1A991D5CADFF042A237C8C125F324300725F` |
| M2 implementation report | 25,879 | `F49D1FDB2B3C26387FFABC51C316F226C5D1FC5FC12B4856B0A6172A81941F55` |
| M2 baseline snapshot | 12,860 | `4826D95ED4DD2C57D2091F89DB2ECCD97628E522630B67C35ABADF700F7D455B` |
| Route-scope correction Draft 1 | 10,582 | `E19028505E3945F3F290525332F33BD8292EB5EC29CEBAD2F978EDB407E698CD` |
| Roadmap Draft 3 | 22,691 | `DC6AFE31344437E97D800450AEAD0BEE56EAF05B8FB1AA20E701126C71C47D88` |
| Roadmap Draft 3 independent review capture | 1,600 | `59714ECA1C056FB10E76D6C3168B97FC7B4E21DE671EEBF8FBC52291E0A8AC4A` |
| Readiness Addendum Draft 1 review capture | 2,446 | `677A1D91FE84338035B5024AFEE6041985A79EFF9F475781640CF1F7BF07177F` |

This addendum is a planning update only. It changes no SRS, DTR, code, test, approval, decision, or status file. It authorizes no implementation, test, validator, backend, database, migration, Docker, network, provider, Modal, staging, commit, or push.

