# Plan B29 — School-level billing change request in existing portals

Date: 2026-10-25 (Asia/Saigon)
Status: APPROVED BY DIRECT OWNER REQUEST
Scope owner: Project owner

## Objective

Add a segregated owner-review proposal to the Master SRS for Free Trial, Plus subscription, and quota top-ups managed through the existing Teacher Desktop and Super Admin Portal. Do not add a role or standalone UI. Propose a `billing:manage` permission for authorized Teachers; attach school subscriptions and shared quota balances to `school_id`. Evaluate MoMo, VNPay, and VietQR as candidate payment routes; propose architecture, technology fit, functional/non-functional requirements, business rules, exceptions, child-safety controls, and a source-dated price/quota recommendation. Preserve the approved product baseline and make clear that no billing implementation exists.

## Scope

1. Preserve the current SRS v3.3/B28 baseline byte-for-byte as a local snapshot before editing; append a separately labeled `B29 — PROPOSED CHANGE REQUEST` to the editable master copies, retaining the baseline version and existing requirement IDs.
2. Use the owner-approved English product positioning consistently: “Sketch2Life is a collaborative creative learning platform for children aged 3–12, inspired by Montessori, Reggio Emilia, and social constructivist learning.” Do not imply that the current supported runtime age range is 3–12; the authoritative supported target remains under 9 where the current-system comparison applies.
3. Add a Subscription & Billing section to the existing Teacher Desktop for current plan, upgrade/renewal, add-ons, payment and transaction history. Keep existing roles. Teachers with proposed `billing:manage` may purchase/manage billing for their school; other Teachers may view plan and usage read-only. Add Billing Management to the existing Super Admin Portal. Do not create a separate portal or UI application. The child-facing Android application has no purchase button, payment link, or alternate checkout route.
4. Define Free Trial, Plus subscription, and add-ons (classes, Teacher seats, shared AI credits) as proposed school-level plan concepts. Every subscription, payment, add-on and shared entitlement/credit balance is keyed to `school_id`, not to an individual Teacher. The owner selected 999,000 VND/month for the document proposal at up to 10 classes / 500 shared credits. Proposed 99,000 VND/month per added class, 49,000 VND/month per added Teacher seat, AI credit top-up rates, trial duration, expiry/rollover, renewal, usage definition, school/class mapping, and billing permission assignment remain owner-review items.
5. Compare public education/creative-AI pricing benchmarks and propose ranges or a worked candidate price/quota table. Explicitly state that cost-to-serve, provider fees, taxes, refunds, merchant pricing and demand have not been validated; all values require owner approval before adoption.
6. Align proposed components with repository architecture and ADRs: Teacher Web, existing FastAPI application, application-owned payment gateway port, provider adapters, relational payment/entitlement/credit ledger, idempotent callback processing, reconciliation and backend-only secrets. Do not introduce a new framework or claim these components exist.
7. Add proposed FR/NFR identifiers scoped to B29, business rules, state lifecycle, interface/data proposals and exception handling. Keep all new requirements `PROPOSED`, all unresolved decisions `OPEN_TBD`, and implementation status `NOT IMPLEMENTED / NOT VERIFIED`.
8. Record Vietnam privacy, AI, e-commerce and consumer-protection review items; UNICEF child-centred AI guidance; provider integration requirements; and Google Play billing-policy applicability as risk/review gates with authoritative citations. Do not claim legal compliance or replace qualified review.
9. Create a concise owner decision list for commercial terms, classroom entitlement, platform policy, provider/merchant choice, privacy impact, reconciliations and implementation sequencing.

## Acceptance criteria

- AC1: The existing v3.3/B28 bytes are retained in a clearly named preserved artifact; the additive B29 section is visibly separate and does not alter B28 meaning or reuse/renumber existing FR/NFR IDs.
- AC2: Billing is added to existing Teacher Desktop and Super Admin Portal surfaces without adding a role or standalone UI. A proposed `billing:manage` permission gates Teacher purchase/manage actions; other Teachers are read-only. Child Android displays no purchase affordance or direct payment navigation.
- AC3: Free Trial, Plus and quota top-ups are present as proposed school-level plan types; subscription, add-on and shared quota ownership use `school_id`. All unapproved terms, including the example 10 classes/500 credits, are labeled as illustrative and assigned to the owner decision list.
- AC4: MoMo and VNPay signature/callback verification, order/amount matching, idempotency, pending status, reconciliation and failure paths are described. VietQR is modeled through a participating bank/acquirer/gateway with verified transaction status, not as a standalone static-QR guarantee.
- AC5: Proposed technical design matches existing repository technologies and dependency direction. It explicitly identifies which pieces are existing capability vs proposal and does not claim implementation.
- AC6: B29 provides individually traceable proposed FRs, NFRs, business rules and exception/recovery cases covering adult purchaser authorization, child-data minimization, teacher review/safety invariants, duplicate/late/mismatched callbacks, provider outages and refunds/reversals TBD.
- AC7: Source-dated price/quota analysis provides public comparisons and distinguishes them from Sketch2Life unit economics. The owner-selected 999,000 VND/month Plus proposal is recorded at up to 10 classes/500 shared credits; add-on prices, trial quota/term and operational credit rules remain pending owner review and are not adopted baseline values.
- AC8: Legal/privacy/platform sources distinguish binding rules, policy requirements and non-binding guidance; applicability and release gates remain explicit and no compliance certification is claimed.
- AC9: The English project-positioning statement appears in the Registration derivative and relevant report/SRS summaries without changing the age scope or implementation evidence.

## Boundaries

- Documentation and editable diagrams only. No payment code, database migration, merchant enrollment, secret/configuration, provider API call, real transaction, child-facing upsell, app test, deployment, tag, commit or push.
- B29 does not adopt prices, commercial terms, final payment provider, payment implementation contracts, or scope into the approved product baseline. Owner review and subsequent ADR/feature approval are required before adoption or implementation.
- Preserve the existing SRS and supplied Draw.io sources; create derived editable diagrams with provenance and no embedded source-credit text.
- Store plans, SRS snapshots, comparisons, decisions and validation/render evidence under their owning feature folders.
