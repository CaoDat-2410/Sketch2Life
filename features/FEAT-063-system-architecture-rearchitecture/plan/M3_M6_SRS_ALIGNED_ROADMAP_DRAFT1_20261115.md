# FEAT-063 BE Roadmap M3–M6 — SRS-Aligned Draft 1

Status: DRAFT / PROPOSED FOR OWNER REVIEW / NOT APPROVED / NOT LAUNCHED  
Date: 2026-11-15  
Purpose: condense the prior six-milestone M3–M6 outline into four outcomes aligned to the current SRS phases P1–P4. This is a planning proposal only. It drops no SRS requirement, authorizes no implementation, and does not replace the previously owner-accepted planning baseline unless the owner accepts it.

## 1. Authority and planning interpretation

The canonical working product requirements are the unsigned Rev68 SRS identified by docs/context/SRS_AUTHORITY.md. Rev68 is a draft, not final owner sign-off. The DATA_TABLE_REGISTER is companion data-model context, not an alternate SRS authority. D-208 provides FR-C-08 planning directions and does not authorize implementation or real-data use.

The prior BE_PARENT_TEACHER_VISION_DEMO_ROADMAP_20261102.md was accepted as a planning baseline against SRS v2.3-draft. It is retained unchanged as historical planning evidence. This Draft 1 proposes a shorter M3–M6 structure against Rev68; owner acceptance is required before it supersedes the old planning baseline. Historical B0–B13 labels are traceability context only and are not current requirements authority.

This mapping is deliberate: M2 remains the platform/foundation milestone corresponding broadly to SRS P0; M3 maps to P1 Parent; M4 to P2 Teacher; M5 to P3 Billing and Notifications; M6 to P4 Production Readiness. M2 subphases S1/S2/S3 are not the same thing as SRS phases P1/P2/P3. The SRS phase table is a proposed dependency order, not release approval or a team allocation.

## 2. Condensed milestone plan

| Milestone | SRS phase | Outcome and bounded planning scope | Exit evidence required before calling the phase complete |
|---|---|---|---|
| M3 — Parent vertical slice | P1 — Parent vertical slice | One synthetic Parent journey from consented/owned profile and image-first input through VLM/subject and context review, required main-activity selection, story review, video generation, private playback, and user-requested deletion. Include resumable media upload and the Billing-owned quota-admission plus AI compute-reservation gates required before an accepted video request. Catalog suggestions come before drafts; the parent explicitly confirms subject/context and chooses one main activity before story generation. Replacement suggestions exclude choices already shown or rejected. Optional lesson pinning follows the SRS; the optional line guide may be scheduled only after its model, license, cost, safety, retention, and capacity gates and must never block image capture or the main Parent flow. | A separately approved, synthetic end-to-end acceptance proves ownership and consent boundaries, image-first ordering, adult confirmation, activity-selection/recovery rules, immutable input/revision and idempotency behavior, quota/cost admission before dispatch, script approval before video, safe/private playback, and the Rev68 cancel/delete lifecycle including verified purge. No real child data. FR-C-08 must have its own resolved contract, reviewed allowlist, approval and launch evidence before M3 can claim the full playback/delete outcome. |
| M4 — Teacher vertical slice | P2 — Teacher vertical slice | One synthetic organization/class/roster path through current Teacher assignment, Teacher profile, lesson import and review, a pinned lesson/occurrence, one child sample, explicit Teacher confirmation, script confirmation, video/playback, reassignment and lifecycle handling. Preserve the SRS one-child/one-activity/one-run boundary; no classroom collaboration or batch generation. | A separately approved synthetic walkthrough proves current-assignment authorization on reads, writes, media and dispatch; lesson/version immutability; exactly one responsible Teacher; a single sample cannot be reused for another child or occurrence; Teacher confirmation occurs before run/job/quota/sample claim; script approval gates video; reassignment revokes the former Teacher; and FR-C-08 deletion/purge invariants hold. No real child data. |
| M5 — Billing and Notifications | P3 — Billing and notification | Add MoMo/VNPAY sandbox payment flows, class capacity, subscription/recurring state, quota top-up, inbox/email/Web Push, and an Android push-provider delivery proof of concept. Product quota remains owned by Billing; AI compute reservation remains owned by AI Policy. M5 may complete commercial/notification breadth but must not introduce quota admission for the first time: M3/M4 accepted-video paths already depend on the P0 admission and hard-cost reservation contract. | A separately approved sandbox/fixture evidence set proves payment signature/freshness and callback idempotency/reconciliation, capacity and subscription invariants, quota grants and append-only usage, no accepted/dispatch on failed admission, compute-reservation lifecycle, and notification delivery/failure/retry behavior. Android push remains a POC until delivery is demonstrated. No live merchant account, production payment, or real-data enablement. |
| M6 — Production readiness | P4 — Production readiness | Close hosting/region, SLO/RPO/RTO, privacy/legal and DSR/DPIA, retention and backup/purge policy, billing/tax, threat-model evidence, operational runbooks, restore/recovery, and live database schema/row inventory plus staged migration rehearsal. Assign named accountable owners and integration allocation. | A separate readiness review verifies each applicable Rev68 §29.2 gate with owner and evidence, approved production architecture/region, legal and store review, incident/DSR runbooks, retention and deletion proof, billing/legal readiness, security/threat model, backup/restore and migration/rollback rehearsal, capacity/cost guardrails, and operating ownership. Completion of M6 is not automatic production or real-data authorization; those require the explicit SRS gates and a separate owner decision. |

## 3. Cross-milestone gates

1. **M2 exit and baseline:** The latest pinned M2 S2 implementation report says PARTIAL / NOT COMPLETE, with required test, typecheck and lint evidence unavailable. Reconcile and pin S2, disposition failed/unavailable evidence, determine the remaining M2/S3 scope and obtain its separate approval if work is required, then obtain owner acceptance of the resulting M2 boundary before treating M2 as a complete foundation. No M2 approval, allowlist, command ceiling, or test run transfers to a later task.
2. **FR-C-08 lifecycle:** Treat cancellation, explicit deletion and verified purge as a separate cross-cutting P0 gate, not as duplicated M3/M4 work. Rev68/D-208 require the allowed cancel/delete state boundaries, current authorization, immediate access fencing, best-effort job/provider cancellation, late-result fencing, owning-module purge, shared-reference verification, preserved quota/sample claims, and DELETE_PENDING until purge is verified. The current FR-C-08 documents remain planning artifacts; the independent Draft 4 review explicitly says the implementation contract, technical blockers, M2 baseline, separate allowlist/approval and launch authorization remain open. M3/M4 cannot claim lifecycle-complete acceptance until these separate gates are met.
3. **Versioned contracts before integration:** Reconcile current BE and FE source for each API before implementation; define ownership, revision, idempotency, error and recovery behavior in versioned contracts. Do not treat an old API reconciliation list or source declaration as a current runtime guarantee.
4. **Privacy, safety and AI readiness:** Use synthetic data for these milestones. Before any model/provider path is accepted, name model/version, verify license and data-flow, safety, latency/cost, capacity and retention, and define fallback/retry behavior. Human review and the required image/subject/activity/script gates remain in their SRS order.
5. **Quota and compute admission:** Billing owns product quota and usage; AI Policy owns compute reservation. For every accepted video request, both admission and the hard-cost reservation must precede acceptance/dispatch. Do not defer this control to M5 merely because M5 expands billing features.
6. **Governance:** Create a scoped feature plan, dependencies, acceptance criteria, owner/rollback, exact allowlist and evidence location for each implementation task. Obtain separate owner Task Approval and a pinned launch instruction before changing product code or data. Planning approval does not equal implementation approval.

## 4. Critical path and sequencing

1. Complete and reconcile M2 S2 plus its separately authorized S3 remainder; pin the exact source and captured verification evidence.
2. Resolve the FR-C-08 implementation-contract and technical blockers; obtain its independent contract review, exact-path allowlist review, task approval and launch authorization. Do not infer these from the clean Draft 4 planning review.
3. Refresh the BE/FE API reconciliation from current source and obtain versioned contract decisions for Parent profile/consent, subject/context confirmation, activity selection, story revision and upload. Reuse no stale pin without checking it.
4. Finish P0 contracts, upload, quota admission, hard-cost reservation, authorization and synthetic fixtures needed by both vertical slices.
5. Deliver M3 Parent P1 before claiming the full Parent slice; then deliver M4 Teacher P2. Prepare M5 sandbox planning in parallel only if the owner separately approves team allocation and integration boundaries; the SRS dependency roadmap does not itself authorize parallel implementation.
6. Deliver M5 sandbox/notification evidence, then M6 readiness evidence. At each gate, report unmet acceptance as open; do not relabel it complete to preserve schedule.

Calendar durations are not estimated in this draft. M2 is not complete, the FR-C-08 implementation contract and blockers remain open, and current API contracts and named owners need reconciliation; a schedule now would be false precision. Once these inputs are settled, estimate each milestone from the reviewed allowlist, owner allocation, and acceptance evidence.

## 5. Explicit exclusions and stop conditions

- No product implementation, database migration, provider integration, production deployment, or real-data use is approved by this roadmap.
- No SRS requirement is removed or silently reclassified as optional. The optional Parent line guide is not a gate for image capture; other open SRS technical gates remain open until separately resolved.
- No migration from or deletion of the prior accepted roadmap is implied. Owner acceptance is required to adopt this Rev68-aligned planning proposal.
- Stop and return to the owner if a plan requires changing SRS authority, public state inventory, owner scope, quota ownership, data-use gates, schema, or a previously settled decision.

## 6. Traceability and pinned inputs

| Input | Observed bytes | SHA-256 |
|---|---:|---|
| docs/context/SRS_AUTHORITY.md | 4,313 | D6153D38000C95E43A4091C5DF2E856FAD872A33177E3A8542E30EF2BEDCAB60 |
| Rev68 canonical working SRS, unsigned | 639,948 | 69C83FE49CD4689D5D2540656D3319721838CF7343BAD00E24CDE558B8F5E944 |
| FEAT-063 DECISIONS.md through D-208 | 216,212 | 52F2E141244829281FF762BA100D1A991D5CADFF042A237C8C125F324300725F |
| DATA_TABLE_REGISTER.md companion source | 171,609 | 7CDFDBECDC24E28BB08E62C98A33B338165350204447EBC59B86F5BE69899BC2 |
| Prior six-milestone roadmap, historical baseline | 20,115 | A0A485EE421FBB1DA9DEC99DD8EC08279D14EAF27EC548AD6A0A4CE8F234F8FA |
| Current M2 S2 implementation report | 25,879 | F49D1FDB2B3C26387FFABC51C316F226C5D1FC5FC12B4856B0A6172A81941F55 |
| FR-C-08 Draft 4 independent review | 3,084 | 9C6A39CD071DA247C3B7F484C7536ED84BDF33CEA2D3BAE3BDCFF0C56F23118F |
| FR-C-08 Lifecycle Contract Draft 1 | 45,462 | 500E622667F32D80C4361E91EC216578ED716F1AC9DE1FF6F154F213E47DAF9A |

SRS mapping: §§5.1–5.2 (Parent/Teacher journeys), §6.1.1 (state and invariants), §8.1 (P0–P4 ordering), §9.10 (per-task contracts and approvals), §23.5 (quota and compute-reservation ownership), §29.2 (real-data/production gates), and §§31.9, 31.10, 31.17 (acceptance criteria and open technical gates). Rev68 states that the phase table does not remove requirements or approve a release. D-208 makes real-data use remain gated and requires a separately reconciled/pinned M2 baseline before FR-C-08 implementation.

## 7. Status and review boundary

This roadmap is DRAFT / PROPOSED FOR OWNER REVIEW / NOT APPROVED / NOT LAUNCHED. It condenses the planning structure; it does not shrink the product scope. No implementation, test, validator, backend, database, migration, Docker, network, provider, Modal, install, stage, commit, or push operation was performed.