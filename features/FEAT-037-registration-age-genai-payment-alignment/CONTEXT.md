# FEAT-037 registration and SRS alignment

- Status: IN_PROGRESS; the registration-form v1.8 task is complete and documented for review.
- Owner: Project owner
- Goal: keep the FA26 registration form aligned with the owner-approved collaborative creative-learning scope in canonical Master SRS v3.1.
- Current scope: derived form v1.8 and its provenance, content, and visual-review records.
- Non-goals: SRS or runtime changes, payment or provider work, data collection, deployment, and changes to unrelated working-tree files.
- Dependencies: `feat-029-master-srs`, `feat-039-collaborative-learning-scope`, and `registration-phieu-fa26se225` in `docs/context/SOURCE_REGISTER.md`.
- Current product authority: Master SRS v3.1 and the 2026-10-10 owner answers recorded by FEAT-039. Earlier under-9 and capstone-payment assumptions remain historical and do not govern the current form.
- Current form: `artifacts/Phieu_FA26SE225_v1.8.docx`, based directly on the user-selected `artifacts/Phieu_FA26SE225_v1.2.docx`; v1.7 remains preserved as the prior derivative from v1.5.
- Artifact note: the 2026-10-06 v1.6 evidence note names an output file that is absent from the repository. The v1.7 derivation uses extant v1.5 and records that lineage explicitly.

## Current direction — 2026-10-12

The registration form now describes ages 36–155 completed months, the age bands 3–5, 6–8, and 9–12, managed child profiles with QR/session-code admission, class and group drawing, Teacher-reviewed AI suggestions, reviewed knowledge/video, off-screen activity, reflection, assessment, consent, retention, and recovery. The one-school pilot target is one class of up to 40 children. The school collects legal-representative consent; authorized Teachers or Super Admins record its evidence and permitted purposes. Session and artwork retention defaults to 90 days after session end; other data classes have separate policies.

The current form removes the superseded under-9 population, Parent portal, package/payment/credit assumptions, fixed screen-time limit, and old story/video duration and exact-script requirements. It preserves the supplied form's section order, three tables, class/duration fields, and signature blocks. The v1.8 DOCX is rendered through Microsoft Word because the packaged renderer cannot find LibreOffice; all eight pages were visually inspected. It preserves the original v1.2 structure: 159 paragraphs and table shapes 2×5, 5×6, and 1×2.

## Historical context snapshot — 2026-10-06, superseded for current product scope

On 2026-10-06 the owner directly changed the product age target to `<9` and asked that SRS, context, and GenAI materials be aligned. The approved interpretation is 0–107 completed months inclusive, using the existing in-scope bands 0–3, 3–6, and 6–9. Existing 9–12 catalog records remain preserved as source data and are outside the supported product target.

The owner approved trying this capstone-trial package model: Free 10 credits/month; Gia đình 99,000 VND/month with 30 pooled credits for up to 3 profiles; Lớp học 499,000 VND/class/month with 120 pooled credits for one Guide and up to 25 assigned profiles. One-time top-ups: 10/49,000 VND, 30/129,000 VND, 60/239,000 VND. One credit covers a complete adult-approved drawing/story experience through off-screen handoff; reserve at session start, debit on success, release on failure/cancellation, and make same-session retries idempotent. Paid monthly plans are manually renewed; backend payment verification precedes entitlement/credit grant. These are capstone-trial assumptions, not cost-validated commercial prices. No provider or live billing integration is selected.

Age-boundary implementation keeps existing versioned wire DTOs compatible with historical/catalog values. The current target is enforced in application services before age-specific selection, Gate B media resolution, renderer localization, and GenAI provider execution. The 9–12 catalog rows and historical manifests remain readable and unchanged.

The originally registered path `owner-local attachment Phieu_FA26SE225.docx` was absent during the first review. On 2026-10-06 the owner attached `owner-local attachment Phieu_FA26SE225_updated.docx`, version 1.1, SHA-256 `21739477916a1fc2e03cc0e22b6f8dd383a03f6831f2ea4eeb1593747cabb548`, and requested a fix. Derived versions 1.2, 1.3 and 1.4 are preserved. Version 1.5 was derived directly from v1.1 to retain the original layout and three-table/signature structure while carrying the then-approved trial assumptions in the existing Other Comments slot. Its recorded SHA-256 is `47F23FD4486A4605208BB44A7B3696081F973DF74D4F1B8D56F7D35C34DF6956`. The v1.6 evidence note says it was used as the v1.6 source; the v1.6 DOCX itself is absent from the repository.

## Historical source boundary — 2026-10-06

- `registration-phieu-fa26se225` is the registered source for the capstone form; its original remains unchanged.
- FEAT-029 Master SRS v2.0/B35 was the product-requirements baseline for the prior under-9 and trial package/credit assumptions.
- FEAT-020 records the earlier three-band workflow and age-sensitive GenAI boundary; these age decisions are superseded by the replacement scope in SRS v3.1.
- Current competitor prices are comparison inputs only; they do not establish Sketch2Life's cost, willingness to pay, or approved prices.


## Registration form review draft — 2026-10-06

The owner supplied version 1.1 and requested a fix. Version 1.2 is now prepared as a review-only copy at `artifacts/Phieu_FA26SE225_v1.2_review_draft.docx`. It aligns the form with the under-9 / 0–107 completed-month boundary and SRS B33 complete-set activity discovery, and includes the candidate packages/prices only as unapproved proposals. The supplied original is preserved. Render and page-by-page visual-review evidence is recorded in `evidence/notes/FORM_SOURCE_RECEIVED_20261006.md`.


## Owner-approved capstone-trial package revision — 2026-10-06

The owner approved the researched trial prices, monthly allowances and one-time top-up prices. The current v1.6 form and SRS v2.0/B35 record them. FEAT-020 treats all story, illustration, TTS and video model steps as one credit-bearing experience rather than separate charges. No payment provider or live billing integration is selected; provider-specific, refund/tax and unused-credit expiry/rollover details remain implementation decisions outside the form.

## Original-form presentation correction — 2026-10-06

After reviewing v1.4, the owner asked to keep the original form style and remove wording that reads as waiting for approval. Version 1.5 is therefore derived directly from source v1.1, not from v1.4. It adds no new section or package table, retains all three original tables and signature blocks, and places the approved trial terms in the existing Other Comments paragraph. V1.4 remains preserved as a superseded presentation iteration.

## SRS-based detail revision — 2026-10-06

The owner then requested a more detailed form based on the SRS. Version 1.6 derives from v1.5, expands the existing fields using Master SRS v2.0/B5, B10–B12, B21 and B30–B35, and preserves the original section order, three tables and signature blocks. Added detail covers adult supervision and consent, distinct Gate A/Gate B/exact-script approval, B33 topic-and-exact-age discovery, reviewed-source/claim citation, the age-aware story/TTS/video pipeline and recovery, child-data privacy/provenance, package/payment/credit behavior and research measures. It adds no new form section or package table and contains no internal review/waiting-for-approval status notes. The final 11-page Word render was visually reviewed page by page.
