# Feature plan

- Status: APPROVED
- Plan revision: 7
- Implementation status: IN_PROGRESS
- Date: 2026-10-06

## Goal

Align Sketch2Life's registered product target, SRS, project context, and age-sensitive GenAI paths with the owner's target population of children younger than nine years. Record the owner-approved package, payment-flow, and credit assumptions for the capstone trial in the master SRS and project contexts, and maintain a detailed registration form derived from the supplied version 1.1 source.

## Scope

### Approved age and GenAI update

- Define the supported product population as age `< 9` years, represented by 0–107 completed months inclusive.
- Keep the three in-scope age bands `0–3`, `3–6`, and `6–9` with existing inclusive completed-month semantics. A child turns out of scope at 108 completed months.
- Preserve existing `9–12` catalog records and historical evidence as source data. They are not eligible for supported product profiles or GenAI generation after this change.
- Apply the supported-age boundary before age-specific activity selection and before any age-sensitive GenAI provider call. Do not infer age from a drawing, narration, or model output.
- Keep existing versioned wire DTOs able to read their historical/catalog values; enforce the current product boundary in the application service before selection/provider execution. Any new wire-level age error/status contract needs its own versioned change.
- Update the master SRS, global project context, FEAT-018 supervised-flow/mobile age boundary, FEAT-029 context/decision/status records, and FEAT-020 age, story, video, context, and GenAI workflow records so the target is consistent and traceable.
- Keep prior owner decisions and evidence immutable as history; add a dated owner amendment that explicitly supersedes only their age-range statements.

### Capstone-trial packages, payment, and credits

- Use the owner-approved capstone-trial package assumptions: Free includes 10 credits/month; Gia đình costs 99,000 VND/month and includes 30 pooled credits/month for up to 3 child profiles; Lớp học costs 499,000 VND/class/month and includes 120 pooled credits/month for one Guide and up to 25 assigned child profiles.
- Use the owner-approved one-time top-up assumptions: 10 credits for 49,000 VND; 30 for 129,000 VND; 60 for 239,000 VND.
- One credit covers one complete adult-approved drawing/story experience, including standard AI outputs and the normal off-screen activity handoff. Reserve at session start; commit only after successful handoff; release for failure or cancellation; same-session retries remain idempotent and do not consume another credit.
- Describe monthly paid plans as manually renewed. Verify payment on the backend before granting the time-bounded package entitlement or purchased credits. Do not select a payment processor or claim that live billing exists.
- Treat the listed prices and limits as the approved capstone-trial assumption, not a commercial launch commitment. Cost/unit economics, provider integration, expiry/rollover, refunds, tax and cancellation details remain implementation decisions outside the registration form.
- Keep public education-app prices as comparison evidence only; they do not establish Sketch2Life cost or willingness to pay.

### Registration source

- Update a clean derived v1.4 registration form from the existing derived v1.3 and the user-attached `Phieu_FA26SE225_updated.docx` (version 1.1), preserving the source and earlier derivatives and recording source provenance.
- Align the draft's age range and recommendation description with the current SRS, including the exact-age/topic discovery rules.
- Include the approved trial package prices, monthly allowances, top-up prices and credit lifecycle. Remove internal review/draft labels and unresolved implementation notes from the user-facing form while retaining relevant adult content-review requirements.
- Render and inspect every page of the revised DOCX before delivery; if the canonical renderer is unavailable on Windows, record that diagnostic and use Word's PDF export for page-image review.

## Non-goals

- Deleting, rewriting, or republishing the existing 9–12 activity/catalog records.
- Selecting a payment service provider or enabling live transactions.
- Collecting real child data, making model/provider calls, changing cloud resources, or deploying/releasing.
- Updating unrelated pre-existing working-tree files or visual assets.

## Steps

1. Record the owner change and this approved plan before product implementation.
2. Review supported-age validators, age-matrix entry points, and age-sensitive GenAI request/prompt paths.
3. Update FEAT-018 age validation and request construction so supported sessions cannot request 108–155 months and age-specific generation receives an adult/profile-sourced in-range band.
4. Align the master SRS, global context, FEAT-018/029/020 records; preserve the 9–12 catalog data and prior evidence as historical/reference data.
5. Record the owner's accepted capstone-trial package prices and credit behavior in the SRS and aligned contexts; keep live payment integration outside scope.
6. Preserve v1.2 and v1.3. Create a clean version 1.4 registration form with approved trial pricing and credit behavior; record provenance, render it, and inspect all pages.
7. Record evidence, status, the approved trial assumption, and remaining implementation verification limitations in this feature.

## Acceptance criteria

- [x] Product age target is consistently stated as `< 9` years / 0–107 completed months in authoritative SRS and context records.
- [x] Manual source review confirms FEAT-018 user/profile/API and FEAT-020 GenAI boundaries reject ages of 108 months or more before age-specific activity selection or provider execution; automated tests remain unrun.
- [x] GenAI story/video requirements use only the in-scope age bands; age is profile/adult sourced and never inferred from media.
- [x] Historical catalog entries for `9–12` remain unchanged and are explicitly marked outside the supported product target.
- [x] The owner-approved capstone-trial package prices, 10 / 30 / 120 monthly credits, top-up prices, payment confirmation, and one-credit lifecycle are recorded consistently in SRS and contexts.
- [x] The attached version 1.1 source and prior derived v1.2/v1.3 documents remain unchanged. Version 1.4 derives from v1.3 and records provenance; every page is visually reviewed.
- [x] The final registration form presents the approved trial packages, monthly credits, top-ups and payment/credit behavior without internal review/draft/TBD notes; it preserves the original supervisor, student, and signature sections.
- [x] Payment-provider selection and live billing implementation are not claimed; remaining implementation decisions stay in internal records, not in the registration form.
- [x] Feature-local evidence and status record the changes, verification performed, and any pending owner decisions.
- [x] The corrected user-facing form keeps the supplied v1.1 structure and formatting, retains its three original tables and signature blocks, and adds no standalone package table or new form section.
- [x] The corrected form states the under-9 age scope and approved capstone-trial packages/credit/payment terms in existing content slots, with internal draft/review/waiting-for-owner-approval notes removed.
- [x] Revision 7: expand existing form fields from Master SRS v2.0 for the supervised workflow, adult gates, activity discovery, story/video GenAI, privacy/recovery, package/payment/credits and research measures while preserving the v1.1 layout and excluding internal approval-status commentary.
- [x] Version 1.6 derives from preserved v1.5; it retains 159 paragraphs, three original tables, section order and signature blocks, with only `word/document.xml` changed in the DOCX package.
- [x] All 11 rendered v1.6 pages were inspected; the original form presentation remains intact, with the added detail flowing across pages without clipped text or orphaned section headings.

## Risks and mitigations

| Risk | Mitigation |
|---|---|
| Existing catalog fixtures contain 9–12 records | Preserve them unchanged; enforce the product boundary at profile/session entry and expose no 9–12 GenAI request path. |
| Age-specific scripts could use a mismatched age band | Bind the adult/profile-sourced month value and canonical band to each generation request and reject inconsistent pairs before provider execution. |
| AI inference and transaction costs exceed the capstone-trial assumptions | Measure cost per completed experience and payment fees before considering a commercial launch. |
| Trial package terms could be mistaken for commercial launch terms | State their capstone-trial scope in project records; the registration form describes them as the capstone-trial model. |
| Provider-specific payment behavior is not selected | Keep provider integration, refunds/taxes, and unused-credit expiry/rollover in internal implementation planning until separately approved. |

## Verification plan

- Review all changed age comparisons, request construction, and prompt assembly for inclusive 0–107-month behavior and fail-closed handling at 108 months.
- Review SRS/context/GenAI wording against this plan and the owner change record.
- Do not claim automated verification unless the relevant checks are explicitly run and recorded.
- For the registration DOCX, run the canonical renderer first. If the Windows runtime has no packaged LibreOffice, record that failure, export a PDF through Microsoft Word, rasterize it with the bundled Python PDF library, and inspect every page image.

## Revision 2 clarification

Keep existing versioned wire DTOs compatible with their historical/catalog values. Enforce the supported-age boundary in application services before product selection or provider execution. A new wire-level age status requires its own versioned contract change. This clarifies implementation under the repository's architecture rules and does not expand the approved scope or acceptance criteria.

## Revision 3 clarification

The owner attached `owner-local attachment Phieu_FA26SE225_updated.docx` (source version 1.1, SHA-256 `21739477916a1fc2e03cc0e22b6f8dd383a03f6831f2ea4eeb1593747cabb548`) and directly requested that it be fixed. This authorizes one derived version 1.2 review draft containing the proposed package/payment values with visible provisional status. It does not approve those values for final adoption.

## Evidence plan

Store the owner amendment, source availability, package research/proposal, code/document review, and any later validation under this feature's `evidence/` directory. Do not store child media, credentials, or external handbook/workbook originals.


## Revision 7 clarification — SRS-based detail (2026-10-06)

The owner asked: “chi tiết hơn, dựa trên srs”. This authorizes a more detailed derived form v1.6 from v1.5. Use Master SRS v2.0 as the content baseline, especially B5, B10–B12, B21, and B30–B35. Expand the existing Context, Proposed Solutions, Functional/Non-Functional Requirements, Theory & Practical, Products, Proposed Tasks, Research Information, and Other Comments fields with accurate product behavior: adult-supervised capture and consent; separate Gate A, Gate B, and exact-script approval; complete topic/exact-age activity discovery with only catalog/topic/age/safety/supervision exclusions and interest-based ordering; cited age-aware story content; revision, TTS, illustration/video, READY, fallback and recovery flow; privacy/provenance; adult package purchase and backend-verified credit lifecycle; and research measures without invented samples or results.

Preserve the user-supplied v1.1 visual system, section order, three original tables, signature blocks, and existing field structure. Content may flow naturally across pages; do not add a new section or package table. Keep readiness and prerequisite sequence as context for adult guidance/story and activity execution, not discovery filters where B33 says otherwise. Retain real adult supervision, consent, safety and human review requirements. Do not put implementation statuses, requests for approval, unresolved provider decisions, or other internal notes in the registration form. Preserve v1.1 and v1.5 unchanged.


## Revision 4 clarification — monthly credit proposal (2026-10-06)

The owner requested a credit mechanism and higher monthly limits: about 10 for Free, 30 for Family, and about 120 for Classroom. Record these as 10 / 30 / 120 provisional monthly credits in an updated v1.3 review draft and the package proposal. For a coherent review proposal, define one credit as one completed adult-approved drawing/story experience; reserve it during the attempt, debit it only at successful completion/handoff, and release it on failure/cancellation. A retry within the same attempt does not consume another credit. Monthly reset/rollover, optional top-up pack size/price, payment-provider choice, refunds and taxes remain undecided. This request authorizes updating review artifacts only; it does not approve prices, entitlements, top-up sales, payment implementation or adoption into the authoritative SRS. Preserve v1.1 source and prior v1.2 review draft.

## Revision 5 clarification — approved capstone-trial price assumptions (2026-10-06)

The owner approved trying the package/credit price proposal in the capstone documents. Use Free = 10 monthly credits; Gia đình = 99,000 VND/month with 30 pooled credits and up to 3 child profiles; Lớp học = 499,000 VND/class/month with 120 pooled credits, one Guide and up to 25 assigned profiles. One-time top-ups are 10 credits/49,000 VND, 30/129,000 VND, and 60/239,000 VND. Adopt these as capstone-trial assumptions in a clean v1.4 form, SRS v2.0, and aligned contexts/GenAI planning. Monthly paid plans are manually renewed; payment is verified server-side before entitlement/credit grant; no provider or live payment integration is selected. Do not put internal review/TBD labels in the form. Preserve the v1.1 source and v1.2/v1.3 derivatives. This approval covers documentation and the trial pricing assumption only, not production billing implementation or commercial rollout.

## Revision 6 clarification — preserve the original registration form (2026-10-06)

After reviewing v1.4, the owner directed: keep the original form as it was, and remove wording that reads like it is waiting for approval. Create a new v1.5 directly from the preserved supplied v1.1 source, retaining the source layout, its three existing tables, and its signature blocks. Do not carry forward v1.4's standalone package table or added subsection. Make only the content corrections needed to align the existing form fields with the under-9 target, B33 activity-discovery requirements, and approved capstone-trial package/credit/payment terms. Put the package details in the form's existing Other Comments text slot. Remove internal review/draft/provisional/waiting-for-owner-approval notes and irrelevant implementation-state commentary; keep real adult Gate A/Gate B and child-research consent safeguards. Preserve v1.1 and v1.4 unchanged. This direct user instruction authorizes the clean v1.5 derivation.
