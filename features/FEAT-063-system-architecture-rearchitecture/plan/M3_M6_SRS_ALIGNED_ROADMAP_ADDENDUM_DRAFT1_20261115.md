# FEAT-063 M3–M6 roadmap — FR-C-08 gate addendum Draft 1

Status: DRAFT / PROPOSED FOR OWNER REVIEW / NOT APPROVED / NOT LAUNCHED  
Date: 2026-11-15

## 1. Purpose and authority

This addendum updates the dependency and readiness interpretation in `M3_M6_SRS_ALIGNED_ROADMAP_DRAFT3_20261115.md` after a live FR-C-08 source audit. It does not replace Draft 3, the previously accepted historical roadmap, the SRS, D-208, or any Task Approval. The owner-supplied Rev67 file is verified as the exact D-203 source, but the m2-s2 worktree authority is now unsigned Rev68 under D-208. Roadmap Draft 3 already uses Rev68 and its independent cold review was CLEAN (0 findings; 13/13 recorded input pins matched). No M3, M4, M5, or M6 product requirement is removed or downgraded here.

## 2. What changed in the dependency view

The FR-C-08 review package is clean as a planning-document review, but the live source audit shows the existing M2 cancel route is only a bounded state/lock/receipt operation. It does not satisfy the full Rev68 lifecycle. Rev68 §21.2 already specifies `DELETE /v1/story-runs/{id}`, but no such route is present in the current backend HTTP source; Spec Draft 4 §5.2 and Allowlist Draft 4 §4.2 need a correction so the approved implementation scope includes that SRS-defined operation. The response type lacks `DELETED` and other Rev68 states; the cancel repository accepts seven current code values, including out-of-inventory `SCRIPT_GENERATING` and `SCRIPT_GENERATION_UNKNOWN`, rather than the 13 UC-11 states; the route is Parent-only; the existing request/notice persistence requires `organization_id`; and no completed cross-module purge/revocation proof is recorded. The exact detail and pins are in `FR_C08_IMPLEMENTATION_READINESS_ADDENDUM_DRAFT1_20261115.md`.

This changes the **readiness status and gate sequence**, not the SRS-to-milestone mapping:

| Milestone | Current planning disposition after the FR-C-08 audit |
|---|---|
| M2 / S2 and S3 | M2 S2 remains PARTIAL / NOT COMPLETE. Reconcile and pin the dirty baseline and disposition failed/unavailable evidence before any FR-C-08 code. Separately complete/accept M2 and any authorized S3 remainder before treating M2 as the completed foundation for M3. These are related but distinct gates. |
| M3 / P1 Parent | Keep the full Rev68 Parent acceptance scope. Preserve Draft 3's critical path: reconcile M2, resolve FR-C-08/P0 contracts and API dependencies, then start the separately approved M3 implementation. Do not claim M3 complete or FR-C-08 acceptance while the lifecycle contract, SRS-defined DELETE operation, verified purge and separate approval remain open. Use synthetic data. |
| M4 / P2 Teacher | Keep the full Rev68 Teacher occurrence, authorization, presentation and media scope. Current Teacher assignment/version and reassignment revocation remain required. Do not claim lifecycle-complete acceptance until FR-C-08 is implemented and verified. |
| M5 / P3 Billing and Notifications | Keep P0 quota and hard-cost admission as dependencies of accepted video paths; do not defer admission to M5. Planning may proceed, but implementation still needs separate task authorization and owner-approved integration allocation. |
| M6 / P4 Production readiness | Keep retention, backup/purge proof, privacy/legal, threat model, operational ownership and all Rev68 §29.2 gates. Named accountable people are required before launch. Real-data/provider use remains gated; completing a synthetic milestone does not enable it. |

## 3. Ordered critical path

1. Reconcile and pin the partial/dirty M2 baseline, recording which failed or incomplete evidence may be relied on. Do not report S2 as complete from a frozen baseline.
2. Resolve the FR-C-08 versioned contracts and technical blockers in the readiness addendum: add the Rev68 §21.2 DELETE operation to the reviewed contract/scope; define typed Parent scope and receipt ownership; reconcile existing GET/state mapping; specify current Parent/Teacher authorization; immediate revocation; job cancellation and late-result fencing; Core Asset/reference closure and retry evidence; audit fields/readers/physical mapping/retention.
3. Update and independently review the corresponding Rev68-aligned implementation contract. Prepare a fresh exact-path allowlist, account for all current dirty-path collisions, obtain an independent allowlist review, separate owner Task Approval and a pinned launch instruction. No current M2 approval or command ceiling transfers.
4. After the M2 foundation is accepted and the relevant implementation task is separately approved, deliver M3 Parent and then M4 Teacher vertical slices in SRS order. Keep FR-C-08 as a cross-cutting P0 gate and report partial acceptance honestly until lifecycle evidence passes.
5. Deliver M5 sandbox billing/notification evidence without live merchant or production provider use. Deliver M6 only after the applicable legal, privacy, security, retention, backup/restore and operational gates have named owners and evidence.

## 4. Clarifications and open boundaries

- The FR-C-08 M2-baseline freeze is a prerequisite before FR-C-08 code; it is not by itself proof M2 is complete. M3’s foundation dependency additionally requires the separately defined M2 exit/S3 disposition.
- Named human accountability is a before-launch gate under D-208. It must not be misclassified as a prerequisite to drafting/reviewing technical contracts. Module responsibility and interface gaps remain technical blockers regardless of when names are assigned.
- The current owner-scoped GET remains the default lifecycle read. Its source response’s missing `DELETED` value is an identified contract gap. The separate `DELETE /v1/story-runs/{id}` command path is already specified by Rev68 §21.2 but is absent from current source; this addendum does not add any route beyond that SRS-defined operation.
- Keep all M3–M6 work synthetic until the Rev68 §29.2 real-data gates and separate owner authorization are satisfied. `OWNER_MODAL_CALL_APPROVED=NO` remains in force.
- The root checkout still points to Rev60 while `.worktrees/m2-s2` points to Rev68. This addendum is scoped to the m2-s2 worktree and must not be copied to root without authority reconciliation.

## 5. Review and approval status

Roadmap Draft 3 remains the reviewed predecessor. This addendum is not independently reviewed or owner-accepted. It is a planning clarification only: no code, test, validator, database, migration, runtime, network, provider, Modal, approval, launch, staging, commit, or push is authorized. No milestone is declared complete by this addendum.

## 6. Input pins

| Input | Bytes | SHA-256 |
|---|---:|---|
| Worktree SRS authority | 4313 | D6153D38000C95E43A4091C5DF2E856FAD872A33177E3A8542E30EF2BEDCAB60 |
| Worktree canonical SRS Rev68 | 639948 | 69C83FE49CD4689D5D2540656D3319721838CF7343BAD00E24CDE558B8F5E944 |
| Owner-supplied SRS Rev67 / D-203 source | 634291 | B704163C9AAF7BB198D8578699F75DB8766C2226A52CD48B0ED1314AF5E21996 |
| DECISIONS.md through D-208 | 216212 | 52F2E141244829281FF762BA100D1A991D5CADFF042A237C8C125F324300725F |
| Roadmap Draft 3 | 22691 | DC6AFE31344437E97D800450AEAD0BEE56EAF05B8FB1AA20E701126C71C47D88 |
| Roadmap Draft 3 independent review capture | 1600 | 59714ECA1C056FB10E76D6C3168B97FC7B4E21DE671EEBF8FBC52291E0A8AC4A |
