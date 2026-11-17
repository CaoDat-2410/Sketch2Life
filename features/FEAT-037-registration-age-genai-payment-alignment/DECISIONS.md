# FEAT-037 decisions

- 2026-10-06: The supported product age range is `<9` years, inclusive of ages 0–107 completed months. The in-scope bands remain `0–3`, `3–6`, and `6–9`; 108 months is out of scope.
- 2026-10-06: Preserve `9–12` catalog rows and historical records; exclude them from the supported profile and GenAI request paths rather than deleting source data.
- 2026-10-06: Age-sensitive GenAI uses only adult/profile-sourced age context. Media-based age inference is prohibited.
- 2026-10-06: Initially, package/credit terms were proposal-only; the owner's later approval records the selected capstone-trial assumptions below. No provider or live billing is selected.
- 2026-10-06: The registration form must be updated as a derived copy after the original is attached; preserve provenance and visually inspect the rendered pages.
- 2026-10-06: Preserve existing versioned DTO compatibility for historical/catalog age values. Enforce the current `<9` product boundary in the application layer before selection or provider-dependent steps; any new wire-level age status requires a separately versioned contract.
- 2026-10-06: The owner supplied registration form version 1.1 and requested a fix. Create a derived version 1.2 review draft aligned with SRS v1.9/B33; include the current package/payment proposal only with a clear owner-review label. This is not approval of final prices, quotas, payment methods, provider, or renewal/refund/tax policy.

- 2026-10-06: Derived `Phieu_FA26SE225_v1.2_review_draft.docx` from the owner-attached v1.1 source. The review copy updates under-9 scope and topic/age discovery; package prices and entitlements are prominently provisional. Preserve the attached source unchanged and defer final package/SRS adoption until the owner reviews the terms.

- 2026-10-06: The owner requested monthly credit targets of about 10 / 30 / 120 for Free / Family / Classroom. Historical v1.3 captured those provisional values while preserving v1.2 and source v1.1.

- 2026-10-06: Owner approves the capstone-trial packages: Free 10 credits/month; Gia đình 99,000 VND/month, 30 pooled credits, up to 3 profiles; Lớp học 499,000 VND/class/month, 120 pooled credits, one Guide and up to 25 assigned profiles. One-time top-ups: 10/49,000 VND, 30/129,000 VND, 60/239,000 VND. One credit is charged for the full adult-approved experience after successful handoff; reserve at session start, release on failure/cancellation, and make same-session retries idempotent. Monthly paid plans renew manually; verified backend payment precedes entitlement/credit grant. Use a clean v1.4 form and SRS v2.0. No provider or live billing implementation is selected.
- 2026-10-06: Owner correction supersedes v1.4's user-facing layout. Keep the supplied v1.1 form structure, derive current v1.5 directly from v1.1, retain its three original tables and signature blocks, and put the approved package terms in the existing Other Comments slot. Remove internal review/draft/waiting-for-owner-approval notes. Preserve v1.4 unchanged as a superseded presentation iteration.
- 2026-10-06: Following the owner's request for more detail based on the SRS, derive v1.6 from preserved v1.5. Expand existing form fields with SRS v2.0 workflow, Gates A/B/script approval, B33 discovery, age-aware GenAI/story/video, safety/privacy/recovery, trial plan/payment/credit and research details. Keep all original sections, tables and signature blocks, with no internal approval/status notes or new package table.

## Owner decision — replace prior form target with SRS v3.1 (2026-10-12)

- The direct owner request to update FA26 authorizes a new derived registration form aligned to canonical Master SRS v3.1 and FEAT-039's owner answers.
- For the current form, the confirmed child population is 36–155 completed months inclusive, with experience bands 3–5, 6–8, and 9–12. The pilot target is one school and one class of up to 40 children. School personnel collect/record guardian-consent evidence and permitted purposes under the authority described by SRS v3.1.
- The current product actors are Child, Teacher, and Super Admin. Children use Teacher-managed profiles and QR/session-code admission without separate login accounts. Class/group sessions, individual/shared drawing, Teacher-reviewed AI suggestions, reviewed knowledge/video, off-screen activity, reflection, assessment, privacy, and recovery form the current registered direction.
- SRS v3.1 supersedes the earlier under-9 product target, Parent portal, capstone trial packages/payment/credits, fixed 10-minute screen limit, 40–60-second video requirement, and exact-script-before-generation requirement for the current form. Earlier approvals remain historical evidence.
- Session and artwork data use the owner-confirmed default retention period of 90 days after session end. This duration is not applied to other data classes.
- Derived form v1.7 uses the extant v1.5 artifact because the v1.6 evidence note's named DOCX output is absent from the repository. The supplied v1.1 source and every earlier derivative remain unchanged. The original section structure, three tables, class/duration fields, and signature blocks are preserved.
- Approval and execution records: plan revision 8 and the evidence note `evidence/notes/FORM_V1_7_ALIGNMENT_20261012.md`.

## Owner correction — use the selected v1.2 source file (2026-10-12)

- The owner clarified that the updated FA26 form must use `artifacts/Phieu_FA26SE225_v1.2.docx` as its base. This replaces the previous v1.7 task's source-selection assumption only; v1.7 and all earlier versions remain preserved.
- Current artifact v1.8 is based on the v1.2 DOCX package, keeps its 159 paragraphs and exact three-table content and shapes (2×5, 5×6, 1×2), and aligns existing form text with Master SRS v3.1 and FEAT-039 owner-approved answers.
- v1.7 remains historical and was derived from v1.5. v1.8 is the current FA26 form.
- Approval and verification: plan `plan/PLAN_FORM_V1_8_20261012.md`, approval in `approvals/TASK_APPROVAL.md`, and `evidence/notes/FORM_V1_8_ALIGNMENT_20261012.md`.