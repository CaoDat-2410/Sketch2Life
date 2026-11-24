# Task approval

## Current canonical replacement — 2026-10-10

The owner explicitly authorized replacement with the new collaborative creative learning scope, confirmed Android and retained FastAPI/React Native, then requested a more detailed SRS foundation for the whole system. The canonical v3.1 update is governed by FEAT-039 plan revision 3 and its APPROVED TASK_APPROVAL.md, with school/profile/consent owner answers recorded there. Exact v2.0 and v3.0 were preserved. Prior approvals below remain history; they do not approve new runtime migration, adopted proposed contracts/full stack or override replacement scope proposals/TBD.

- Status: APPROVED
- Approver: Project owner; direct request and explicit scope answers in the current conversation
- Approved scope: create one Vietnamese master Markdown SRS based on the current Sketch2Life repository and the supplied workflow/product-flow references, including actor and scope model, business rules, entities/ERD, state machine, functional/non-functional requirements, detailed versioned contract inventory, traceability, and TBD decisions.
- User-confirmed target requirements: use the supplied product workflow; Parent and Guide are adult guardians participating with the child; include Admin; narration is editable and can be recorded again when unclear; digital flow target is about 10 minutes maximum excluding physical activity; parent/guardian selects 30/60/90-day retention.
- Contract treatment: include discovered contract families and preserve unresolved same-name shape conflicts as unadopted/open; do not migrate or adopt contracts.
- Plan revision: 1
- Approved at: 2026-09-18
- Notes: Documentation-only approval. Product/runtime changes, provider execution, contract migration, cloud changes, frontend asset generation/application, release, commit/push, and modification of pre-existing user changes are excluded.

## Addendum — expanded registration-aligned SRS scope

- Status: APPROVED for source review, requirements gap analysis, and preparation of owner clarification questions.
- Owner instruction (2026-09-18): expand the master SRS to match the full scope of Phieu_FA26SE225.docx, include authentication, ask across all requirement sections, check carefully, and do not invent missing decisions.
- Approved next scope after owner answers: revise the same master Markdown SRS, preserving source traceability and distinguishing confirmed requirements, accepted repository constraints, proposed scope, and OPEN_TBD decisions.
- Approval does not authorize application implementation, provider calls, real-child data collection, deployment, publication/release of a dataset, or changes to pre-existing user work.

## Addendum — owner clarification responses

- 2026-09-18: Owner selected the supplied workflow image and confirmed the experience includes a narrated story; set target age range to 0–12; confirmed the repository authentication approach; set Admin as the highest system role; and limited Parent/Guide access to their own children.
- 2026-09-18: Retention data scope and research protocol remain undecided. Expand the SRS using confirmed form facts and repository auth constraints, and label these unresolved details OPEN_TBD.
- Clarification still required: how Guide's own-child boundary interacts with the registration's Guide classroom functions; whether Admin may inspect child content; which listed features are MVP versus extended; detailed auth account lifecycle; and research/retention values.

## Addendum — complete SRS structure, relationships and logical schemas

- 2026-09-19: Owner requested one detailed Markdown system SRS with relationships, schemas and the sections normally expected in a complete SRS.
- Approved documentation scope: add introduction/overall-description sections, external interfaces, relationship/cardinality model, logical data dictionary, proposed request/response schemas, API/error/idempotency contract surface, use cases, verification/acceptance matrix, operational/security constraints, traceability and glossary.
- Schema/API additions are logical SRS proposals and must be labelled PROPOSED_UNADOPTED unless they already match an approved repository contract. No runtime contract migration or implementation is authorized.

## Addendum — owner-approved scope closure and observability

- 2026-09-19: Owner approved the proposed scope strategy: MVP includes animation, narrated story and micro-video; Parent Web is Phase 2 but must be described and share the same backend authorization model.
- 2026-09-19: Owner approved one Owner Caregiver per ChildProfile, many ChildProfiles per owner, many Guide assignments per ChildProfile, immediate assignment, 3/7/15/30-day share, immediate Parent revoke, one active session per Guide, and overlapping Guide assignments.
- 2026-09-19: Owner approved immediate revoke behavior during a running Guide session: stop the session, show an on-screen message, and emit notifications.
- 2026-09-19: Owner approved Parent live visibility of all necessary session information with data minimization; Parent Web is management/monitoring/information surface and is not implicitly a session runner.
- 2026-09-19: Owner approved combined notification channels, Grafana-based observability, durable business/audit logs, and separate audit retention.
- 2026-09-19: Owner approved full child/session data retention classes under the 30/60/90-day policy, archive-to-restricted-storage before purge, and Admin raw-content access only through break-glass.
- 2026-09-19: Documentation scope authorizes updating the master Markdown SRS and feature records. It does not authorize application implementation, provider calls, cloud provisioning, contract migration, or deployment.

## Addendum — owner requirements closure for v1.5

- 2026-09-23: Owner approved updating the SRS and feature records with the architecture and
  requirements answers recorded in `evidence/notes/OWNER_REQUIREMENTS_CLOSURE_20260923.md`.
- Approved target: FastAPI/Python modular monolith, PostgreSQL, Redis/RQ, MinIO local, Android
  React Native, desktop-first Guide Console, responsive Parent Web, REST/OpenAPI and bounded polling.
- Approved test authentication: real owner-controlled Firebase Authentication project with backend
  token verification. Secrets remain runtime-only and no Firebase data products may be introduced.
- Approved role model: mutually exclusive adult `PARENT`, `GUIDE`, `ADMIN`; no child role or child
  credential.
- Approved scope: Parent Web and Guide Console are required operational surfaces; Parent Web is not
  deferred to a Phase 2 scope. Vietnamese is the first UI language.
- Approved Parent projection: phase, status, progress and update time only, with minimum aliases;
  technical errors and internal processing metadata are excluded.
- Approved test requirements: rate limits, retry budgets, idempotency, concurrency guards and
  redacted backend operational monitoring. Lightning connectivity, AI stress testing, cloud
  provisioning and production release remain outside this documentation update.
- This addendum authorizes SRS/context/ADR/evidence/status updates only. It does not authorize
  runtime implementation or Firebase/provider calls in this turn.

## Addendum — implementation-grade SRS detail expansion v1.6

- 2026-09-23: The owner requested a more detailed SRS for the complete target and test operation.
- Approved documentation expansion: local test topology, bounded contexts, role/resource matrix,
  state transitions, API behavior, screen requirements, monitoring signals, rate-limit/idempotency
  behavior, synthetic personas/fixtures, verification layers and implementation sequencing.
- No new product decision is inferred by this expansion. Numeric production SLO/capacity, provider
  execution, cloud deployment, production release and unresolved B28 questions remain unchanged.
- This addendum authorizes documentation/evidence/status updates only; it does not authorize runtime
  code, Firebase calls, Lightning calls or deployment.

## Addendum — owner story/video scope amendment v1.7

- **Date:** 2026-09-28
- **Status:** `APPROVED_FOR_DOCUMENTATION_ONLY` by the owner's direct request to update the plans and master SRS.
- **Authorized:** revise the master Markdown SRS; create two detailed FEAT-020 planning documents; update feature context, decision, evidence, status and approval records.
- **Confirmed target:** 40–60 second illustrated story video; age/readiness-aware educational knowledge; adult editing through quick controls and free text; full script returned and approved before image generation; supported language/voice selection; independent TTS; retain Wan2.2 TI2V-5B baseline; redraw allowed only as derivative while original remains immutable.
- **Contract treatment:** proposed schemas, endpoint names, error codes and state mappings remain `PROPOSED_UNADOPTED` until registry reconciliation and approval.
- **Not authorized:** runtime/frontend code, provider/model calls, model downloads, contract migration, cloud changes, deployment, release, commit/push, real-child media collection, or modification of unrelated pre-existing changes. This documentation approval does not approve FEAT-020 implementation.

## Addendum — supported-age SRS amendment v1.9 (2026-10-06)

- Status: approved by the project owner's direct request to narrow the supported product target to `<9` and align SRS/context/GenAI scope.
- Authorized documentation: update the master SRS, project context, decisions, and status to record 0–107 completed months, preserve 9–12 catalog records as source data, and keep research cohort scope separate.
- Package/payment values remain proposed and outside the approved SRS baseline pending owner review.
- Runtime boundary implementation is separately governed by FEAT-037 approval; no V1 contract migration is part of this SRS amendment.

## Addendum — owner-approved capstone-trial package and credit amendment v2.0

- 2026-10-06: The owner approved trying the package/credit proposal in the capstone documents and authorized updating the master SRS, project context, feature records, GenAI/story/video planning, and the derived registration form.
- Approved trial values: Free 10 monthly credits; Gia đình 99,000 VND/month, 30 pooled credits, up to 3 child profiles; Lớp học 499,000 VND/class/month, 120 pooled credits, one Guide and up to 25 assigned profiles. One-time top-ups: 10 credits/49,000 VND, 30/129,000 VND, 60/239,000 VND.
- Approved trial credit lifecycle: one credit covers a complete adult-approved drawing/story experience and normal off-screen handoff; reserve at session start, debit at successful handoff, release on failure/cancellation, and do not double-charge same-session retries. Monthly paid plans are manually renewed; backend verification precedes entitlement/credit grant.
- Documentation scope only. No provider, instrument, live transaction, mobile payment credential storage, or commercial-launch claim is authorized. Provider-specific states, expiry/rollover, refunds/chargebacks and taxes remain implementation decisions.
- SRS baseline updated to v2.0/B35; age range remains `<9` / 0–107 completed months under the prior v1.9 amendment.

## Addendum — Teacher Web billing change request B29 (2026-10-25)

- Status: APPROVED FOR DOCUMENTATION BY DIRECT OWNER REQUEST.
- The owner requested adding MoMo, VNPay, VietQR, architecture/technology, FR/NFR, exception handling and package options to the documents and Master SRS, asked for reference pricing and stated prices need owner review before adoption.
- The owner confirmed the purchase surface is Teacher Web and selected Free Trial + Plus subscription + quota top-ups as the proposal structure.
- Authorized documentation: append a separate proposed B29 change request to the Master SRS, preserving the v3.3/B28 baseline and existing IDs; prepare source-dated price/quota recommendations, current legal/platform/business-rule review, and derived Draw.io billing diagrams; refresh the four local Review 2 DOCX/PDF dossier pairs.
- Owner-approved product positioning: “Sketch2Life is a collaborative creative learning platform for children aged 3–12, inspired by Montessori, Reggio Emilia, and social constructivist learning.” Use consistently in the Registration derivative, BM01/report summary and SRS overview. In the Registration v1.2 derivative, this supersedes only the opening sentence of existing section 3.2(a) Context; the selected source remains byte-identical and all other form text/table content remains unchanged.
- B29 is a proposal only. All pricing/quota values, exact plan entitlement and term, purchase/provider contracts, merchant fees, tax/refund/cancellation policy, legal interpretation, Google Play policy applicability, and rollout remain for owner/team/qualified review. No payment integration, merchant setup, real transaction, runtime claim, or compliance certification is authorized.
- Plan: `plan/PLAN_B29_TEACHER_WEB_BILLING_CHANGE_REQUEST_20261025.md`.
- No app code, application tests, provider call, migration, deployment, commit/push, tag, or publication is authorized by this addendum.

## Owner clarification — existing portals and school-level billing (2026-10-25)

- The owner clarified that no new role and no standalone billing UI are needed. Reuse Teacher Desktop and Super Admin Portal.
- Document the proposed `billing:manage` permission on existing Teacher accounts. Authorized Teachers manage their school's billing; other Teachers can view plan and usage read-only. Super Admin manages catalog, add-ons, school subscriptions and transactions through the existing portal.
- Attach subscriptions, payments, add-ons and shared quota/credit balances to `school_id`, never to an individual Teacher account. The 10-class / 500-credit example in the owner's note is illustrative and needs confirmation.
- Keep the existing v3.3/B28 baseline intact. B29 remains a proposed scope-change request. Prepare price options for owner approval before exporting final PDFs.
- Owner price selection — 2026-10-25: use Option B's school-level structure at 999,000 VND/month for the document proposal (up to 10 classes, 500 shared credits). The proposed one-trial-per-school terms and add-on rates (extra class, Teacher seat and AI credits) are still recommendations pending owner review; no billing terms are adopted into the baseline.
- Owner pricing-status clarification — 2026-10-25: include the complete package and add-on pricing/quota table in B29 and both synchronized SRS copies. Label every Sketch2Life amount and quota PROPOSED. The owner-selected 999,000 VND/month Plus amount is a candidate within the proposal, not adopted baseline pricing or an approval to sell. In the Registration form, mention only that billing/payment is proposed; omit all prices and quota amounts.

## Owner authorization — billing promoted into baseline (2026-10-25)

- Status: APPROVED FOR DOCUMENTATION BY DIRECT OWNER REQUEST.
- The owner directed that billing/payment be included in the product baseline, with complete FR, NFR, business rules and error/exception handling; the feature is planned for implementation but has not been implemented yet.
- The owner clarified that only the proposed price amounts retain the `PROPOSED` label. Package structure, entitlement quotas and payment capability are baseline target requirements.
- Authorized: publish SRS v3.4, synchronize the canonical Master SRS and FEAT-039 copy, preserve v3.3/B28 and registration v1.2, and update related baseline records and Review 2 documents/diagrams.
- No runtime code, migration, provider onboarding, live payment, release, commit or push is authorized by this amendment.
- Plan: `plan/PLAN_B29_BILLING_BASELINE_SRS_V3_4_20261025.md`.
- Owner scope amendment — 2026-10-26: the owner supplied the “School plans and billing” image and requested the pricing/package be updated accordingly. Plan `PLAN_B29_SCHOOL_PACKAGE_UPDATE_SRS_V3_5_20261026.md` (SHA-256 `BBF1CBAF2E1BAF21A260203A21908607EACAE7EEB746AD41C11116D166D95F38`) is approved by this direct request. It authorizes SRS v3.5 with 1-class/3-credit Free Trial, 5-class/10-seat/100-credit Plus and 15/45/80-credit one-time packs, synchronized in FEAT-029 and FEAT-039; all monetary amounts remain PROPOSED. Preserve v3.4, v3.3/B28, historical proposals and Registration v1.2. Billing remains NOT IMPLEMENTED. No runtime code, application tests, provider call, live transaction, commit, push, tag, deployment or publication is authorized.
