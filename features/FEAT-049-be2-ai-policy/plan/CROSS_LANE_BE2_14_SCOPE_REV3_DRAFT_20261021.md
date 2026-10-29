# BE2-14 cross-lane deny/defer scope — revision 3 draft

- Status: DRAFT / OWNER_D3_RECORDED / AWAITING_INDEPENDENT_REVIEW.
- Owner: BE2-14 / FEAT-049; consumer/lifecycle owner: BE2-01 / FEAT-044; BE2-08 is the video participant.
- Review successor only to CROSS_LANE_BE2_14_SCOPE_DRAFT_20261021.md. The original approved exact-hash addendum/approval is preserved and does not expand to this revision.
- Owner D3: FEAT-057 evidence/notes/CROSS_LANE_UOW_OWNER_DECISION_D3_20261021.md, SHA256 C1799417AFD2DDB989D6C888A8B3F9702D4A6B4DC2A8B90637DBD6E11C3AE54C.
- Source manifest: FEAT-057 evidence/metrics/CROSS_LANE_UOW_SOURCE_HASHES_REV4_20261021.json, SHA256 2EAA11FCA7B510CA738D34ECED9EFD164C7734FCA8E6AD4792257F03AA68591F.
- Related joint CR: FEAT-044 plan/CROSS_LANE_BUDGET_DEFERRAL_CR_DRAFT_20261021.md; foundation schema CR is separate.

## 1. Owner direction and scope

BE2-14 supplies the versioned deny/defer contract needed by BE2-01. It does not assign an amount, invent budget availability, issue a provider-execution grant, or authorize execution merely because no denial was returned. Eligibility, execution authorization, and resource reservation remain separate authorities.

BE2-01 owns changes to _dispatch_one, start_attempt, retry_job, durable deferral, outbox/ack, retry/watchdog and cancellation behavior. BUDGET_EXCEEDED means durable resource deferral; consent/kill-switch denial retains paired cancellation. BE2-14 does not mutate foundation job/run rows.

D3 requires job and run to be QUEUED while budget-deferred, with no budget-specific JobState or video state. Video terminal STALE belongs to D2/C2, not to the resource contract. Unit, limit and maximum defer duration are unprovided; no values or TTLs are assumed.

## 2. Versioned contract requirements

The adopted contract must bind exact organization/job/actual attempt, phase, request/context/policy/resource-definition identity, typed reason, decision identity/revision, and evidence authority. The exact field names/version are draft CR work, not existing adopted schemas.

| Decision class | Meaning for this slice | BE2-01 responsibility |
|---|---|---|
| Consent/session/source/kill current-use denial | Existing eligibility cancellation remains authoritative when genuinely applicable | Pair cancellation and close any deferral under the foundation UoW. |
| Resource BUDGET_EXCEEDED / resource defer | No provider start; does not mean revoke/cancel | Persist/validate QUEUED hold and recovery generation through the joint CR. |
| Unknown/unavailable/missing definition or proof | Fail closed; cannot be converted to a grant or to a fabricated budget amount | Retain pending recovery and do not start S/provider. |
| Separately verified execution/reservation proof | Outside the deny/defer result itself | Recheck exact CURRENT proof for the actual attempt before ending hold/S. No inference from eligibility alone. |

A result for one phase is not evidence for another phase. Current accounting schema accepts create/dispatch/retry, not a new start phase. Admission S must use an explicitly adopted existing-phase mapping or a separately versioned phase CR. This scope does not silently add a phase.

## 3. Transaction and attempt boundaries

Accounting owns its separate transaction. No reserve/settle call occurs while foundation job/run/fence locks are held. Cross-store proof transfer, replay, and unknown commit recovery must be explicitly adopted.

For a retry, a proof naming the failed old attempt cannot authorize the new attempt. Under D3's QUEUED requirement, BE2-01 requeues a due/otherwise authorized retry exactly once, atomically with the hold, and only later verifies/reserves for that persisted new attempt before S. Repeated denial does not create another attempt or burn dispatch-loss recovery allowance. BE2-14 neither allocates the attempt nor changes its lifecycle.

Expiry/renewal, actual reservation grants, limits/units, settlement/refund and concurrency policy remain their separately versioned/adopted gates. Existing Reservation has no assumed expiry. No release/refund is inferred from timeout or unknown execution.

## 4. End of deferral

The shared contract defines an authorized resume with fresh eligibility plus actual-attempt reservation/execution verification; foundation atomically resolves the hold and activates a new recovery generation while the pair stays QUEUED until S. Genuine owner/eligibility cancellation closes the hold and cancels the pair. Other terminal transitions close and fence off the hold through the foundation protocol.

The owner's maximum defer duration is PENDING. The deadline action is also an explicit owner/contract gate; this revision chooses no automatic cancel/fail/refund action and no numeric bound. No budget-dependent runtime is declared ready before the missing terms are adopted.

## 5. Candidate allowed paths

Only a minimal reviewed subset may later be approved:

- backend/src/sketch2life/contracts/schemas/ai_policy_use.py;
- backend/src/sketch2life/application/ports/ai_policy_use.py;
- backend/src/sketch2life/application/ai_policy_use.py;
- accounting contract/port paths only if the adopted typed deny/defer/phase CR requires them:
  backend/src/sketch2life/contracts/schemas/ai_policy_accounting.py,
  backend/src/sketch2life/application/ports/ai_policy_accounting.py.
- Existing owned use/accounting contract and service tests for exact denial/phase/identity and non-grant semantics.
- Any new contract module/test path must be explicitly included before approval.

Actual resource-grant/accounting SQL, reservation expiry/renewal, foundation schema/queries, BE2-08 lifecycle, and FEAT-057 composition are outside this owning-card manifest. If policy persistence is required, prepare a separate owned schema/migration revision; do not edit published migrations.

## 6. Proposed acceptance evidence

| ID | Required behavior |
|---|---|
| PD01 | Exact authoritative identity/phase is checked; mismatches fail closed. |
| PD02 | Resource defer cannot be mistaken for consent/kill revocation or an execution/reservation grant. |
| PD03 | BE2-14 writes no foundation/video row and cannot open their UoW. |
| PD04 | Foundation integration classifies all three denial branches; resource hold keeps job/run QUEUED and prevents provider work. |
| PD05 | A failed-attempt proof cannot authorize a new retry attempt. |
| PD06 | No accounting call is nested under lifecycle locks; proof replay/unknown result remains explicit. |
| PD07 | No invented unit/limit/max-duration/expiry/renewal or provider authority. |
| PD08 | Existing component acceptance/status and X01/X05d/X05c/X09-08 gates remain unchanged. |

No test ran for this draft. Future tests require exact scoped implementation approval; SQL/database/provider/Modal/Lightning/runtime are separate gates.

## 7. Approval state

D3 authorizes recording design and preparing scope/CRs. This revision has no implementation approval. The joint BE2-01/14 CR, any schema/phase CR, BE2-08 participant agreement, exact file manifests, and independent review must precede supplemental S/F source approval. X01 PARTIAL; X05d BLOCKED; X05c/CR09-02 OPEN; X09-08 NOT_IMPLEMENTED.

### Rereview 4: completion-time resource result is a separate owner gate

D3 selected defer in the dispatch, start and retry branches. It did not decide the result when provider work has already completed and completion-time policy returns only BUDGET_EXCEEDED. The generic current source branch treats any ineligible result as cancel plus quarantine; that behavior is not adopted by D3 for resource-only completion denial.

Until the owner/card contract decides this case, do not classify completion-time BUDGET_EXCEEDED as consent/kill revocation, F-reject or the pre-execution C1 hold. Its paired state, receipt, durable recovery, output visibility and settlement remain PENDING under the D4 ballot. No implementation may infer cancellation/quarantine, acceptance/settlement, refund, retry or provider rerun from that resource result. Recommended option A is to keep output private and completion pending; this recommendation is not owner-approved behavior.

### Rereview 4: aligned deny/defer candidate paths

This section replaces the earlier candidate-path list in Section 5. Primary BE2-14 contract candidates are the existing ai_policy_use schema, port and application service. The ai_policy_accounting schema/port are conditional review inputs only for a separately adopted reservation/phase contract; they are not part of the deny/defer subset by default. This matches FEAT-044 budget CR Rev2. Exact files still require review and a supplemental manifest.
