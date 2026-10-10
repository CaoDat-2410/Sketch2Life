# FEAT-037 registration, age and GenAI alignment

- Status: IN_PROGRESS
- Owner: Project owner
- Goal: align the registered product scope and age-sensitive GenAI target with children younger than nine, and record the owner-approved capstone-trial package/payment/credit assumptions.
- Scope: age-boundary requirements and enforcement; SRS/context/GenAI alignment; market comparison; a detailed derived registration form v1.6; trial package and credit documentation.
- Non-goals: live billing, payment provider selection, catalog deletion, deployment, and changes to unrelated working-tree files.
- Dependencies: `feat-029-master-srs`, `feat-020-backend-ai-workflow-demo`, `registration-phieu-fa26se225` in `docs/context/SOURCE_REGISTER.md`.
- Risks: GenAI usage cost and payment fees are not yet measured; no payment provider is selected for live integration.

## Context snapshot

On 2026-10-06 the owner directly changed the product age target to `<9` and asked that SRS, context, and GenAI materials be aligned. The approved interpretation is 0–107 completed months inclusive, using the existing in-scope bands 0–3, 3–6, and 6–9. Existing 9–12 catalog records remain preserved as source data and are outside the supported product target.

The owner approved trying this capstone-trial package model: Free 10 credits/month; Gia đình 99,000 VND/month with 30 pooled credits for up to 3 profiles; Lớp học 499,000 VND/class/month with 120 pooled credits for one Guide and up to 25 assigned profiles. One-time top-ups: 10/49,000 VND, 30/129,000 VND, 60/239,000 VND. One credit covers a complete adult-approved drawing/story experience through off-screen handoff; reserve at session start, debit on success, release on failure/cancellation, and make same-session retries idempotent. Paid monthly plans are manually renewed; backend payment verification precedes entitlement/credit grant. These are capstone-trial assumptions, not cost-validated commercial prices. No provider or live billing integration is selected.

Age-boundary implementation keeps existing versioned wire DTOs compatible with historical/catalog values. The current target is enforced in application services before age-specific selection, Gate B media resolution, renderer localization, and GenAI provider execution. The 9–12 catalog rows and historical manifests remain readable and unchanged.

The originally registered path `owner-local attachment Phieu_FA26SE225.docx` was absent during the first review. On 2026-10-06 the owner attached `owner-local attachment Phieu_FA26SE225_updated.docx`, version 1.1, SHA-256 `21739477916a1fc2e03cc0e22b6f8dd383a03f6831f2ea4eeb1593747cabb548`, and requested a fix. Derived versions 1.2, 1.3 and 1.4 are preserved. Version 1.5 was derived directly from v1.1 to retain the original layout and three-table/signature structure while carrying the approved trial assumptions in the existing Other Comments slot; it remains unchanged as the direct source for current v1.6.

## Source boundary

- `registration-phieu-fa26se225` is the registered source for the capstone form; its original remains unchanged.
- FEAT-029 Master SRS v2.0/B35 is the current product-requirements baseline for age and trial package/credit assumptions.
- FEAT-020 holds the current three-band workflow, story/video plans, and age-sensitive GenAI boundary aligned with the under-9 target; final verification is still pending.
- Current competitor prices are comparison inputs only; they do not establish Sketch2Life's cost, willingness to pay, or approved prices.


## Registration form review draft — 2026-10-06

The owner supplied version 1.1 and requested a fix. Version 1.2 is now prepared as a review-only copy at `artifacts/Phieu_FA26SE225_v1.2_review_draft.docx`. It aligns the form with the under-9 / 0–107 completed-month boundary and SRS B33 complete-set activity discovery, and includes the candidate packages/prices only as unapproved proposals. The supplied original is preserved. Render and page-by-page visual-review evidence is recorded in `evidence/notes/FORM_SOURCE_RECEIVED_20261006.md`.


## Owner-approved capstone-trial package revision — 2026-10-06

The owner approved the researched trial prices, monthly allowances and one-time top-up prices. The current v1.6 form and SRS v2.0/B35 record them. FEAT-020 treats all story, illustration, TTS and video model steps as one credit-bearing experience rather than separate charges. No payment provider or live billing integration is selected; provider-specific, refund/tax and unused-credit expiry/rollover details remain implementation decisions outside the form.

## Original-form presentation correction — 2026-10-06

After reviewing v1.4, the owner asked to keep the original form style and remove wording that reads as waiting for approval. Version 1.5 is therefore derived directly from source v1.1, not from v1.4. It adds no new section or package table, retains all three original tables and signature blocks, and places the approved trial terms in the existing Other Comments paragraph. V1.4 remains preserved as a superseded presentation iteration.

## SRS-based detail revision — 2026-10-06

The owner then requested a more detailed form based on the SRS. Version 1.6 derives from v1.5, expands the existing fields using Master SRS v2.0/B5, B10–B12, B21 and B30–B35, and preserves the original section order, three tables and signature blocks. Added detail covers adult supervision and consent, distinct Gate A/Gate B/exact-script approval, B33 topic-and-exact-age discovery, reviewed-source/claim citation, the age-aware story/TTS/video pipeline and recovery, child-data privacy/provenance, package/payment/credit behavior and research measures. It adds no new form section or package table and contains no internal review/waiting-for-approval status notes. The final 11-page Word render was visually reviewed page by page.
