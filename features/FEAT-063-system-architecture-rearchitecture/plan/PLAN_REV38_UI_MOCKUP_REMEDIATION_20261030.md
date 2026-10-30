# Plan Rev38 — UI mockup remediation and workflow coverage

- Feature: FEAT-063 — whole-repository architecture redesign.
- Status: APPROVED for generated visual drafts and one narrow SRS consistency correction; application implementation and visual promotion are not approved.
- Authority: project owner replied “Ok, ấy lại dfi” to the recommendation to correct the mockups against the current FEAT-063 source and add missing workflow screens. Interpreted as approval to revise the visual set.
- Approval record: `approvals/TASK_APPROVAL.md`; this plan's SHA-256 must be recorded before work begins.

## Goal

Replace the inconsistent Rev35/Rev36 visual drafts with a consistent, reviewable candidate set that reflects FEAT-063's current v2.3-draft requirements, makes the Parent and Teacher flows easier to follow, and adds the missing role screens identified in the review. Preserve Rev35/Rev36 files unchanged as historical drafts.

## Source baseline

- Current FEAT-063 SRS: `artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md` v2.3-draft, especially BR-13, BR-42/45/48/59, FR-P-05/08, FR-T-16/18, FR-AI-04/15 and §31.2–§31.6.
- Historical comparison only: `artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS_V2.2_PRESERVED_20261028.md`.
- Rev31 Lesson Library API contract, Rev31/32/37 API inventories and catalogs for current-versus-target API boundaries.
- Rev35/Rev36 visual source directories and evidence; project-owner UI review supplied 2026-10-30.
- FEAT-029/039 SRS v3.5 is a separate authority that states a broader age range. Do not resolve that conflict in this visual revision; use a five-year-old fictional example and keep age-band labels illustrative.

## Approved scope

1. Correct the contradictory AC-33 wording in the unsigned FEAT-063 v2.3-draft so it agrees with the already-recorded Parent optional generic line-sketch guide and Teacher optional Sketch Deck. Preserve the no-preselected-subject rule, capture-before-VLM order, adult confirmation, and no-child-data input to sketch generation. This is a consistency correction only; it does not sign off the SRS.
2. Create a new set of 23 screen drafts under `assets/generated/ui-mockups-rev38-20261030/`:

| ID | Role | Screen |
|---|---|---|
| P01 | Parent | Lesson library and child/profile selection entry |
| P02 | Parent | Lesson detail and use-with-child action |
| P03 | Parent | Drawing session with optional, dismissible line-sketch guide |
| P04 | Parent | Camera/gallery capture and uncertain subject suggestion |
| P05 | Parent | Child context snapshot, text/voice idea and transcript confirmation |
| P06 | Parent | Story review: 5–15 scenes, AI rewrite suggestion counter (0–3), final confirmation |
| P07 | Parent | Background video-job stages, resumable return, failure and automated safety-blocked states |
| P08 | Parent | Private video, captions, finish/retry actions, then lesson outdoor activities |
| P09 | Parent | Lesson history, delete action and school-scoped feedback thread |
| P10 | Parent | Child profile list and create/edit/archive flow |
| P11 | Parent | Sign-in/register entry and authentication recovery states |
| P12 | Parent | Numeric quota summary, exhausted state and optional top-up choices |
| T01 | Teacher | Organization lesson workspace |
| T02 | Teacher | Structured, multi-activity lesson authoring and submit-for-review action |
| T03 | Teacher | Filtered upload, supported-file limits, extracted-field correction and confirmation |
| T04 | Teacher | Occurrence preparation with optional Sketch Deck and one consistent enable/disable control |
| T05 | Teacher | Class and assigned-child roster/profile workspace |
| T06 | Teacher | Teacher sample run: select the eligible representative child, capture/confirm subject, review context and script |
| T07 | Teacher | Sample-video preview and explicit class-presentation confirmation |
| M01 | School Manager | Version-aware Public publication review with disabled decision until checklist passes |
| M02 | School Manager | School organization: teacher/parent groups, classes/slots and school quota |
| A01 | Platform Admin | Public lesson catalog moderation with state-dependent actions |
| A02 | Platform Admin | Platform operations for organizations, activity catalog and policy/quota oversight |

3. Create nine revised component boards under `assets/generated/ui-components-rev38-20261030/`: foundations/controls, Parent dialogs, web decision dialogs, notices/toasts, loading/error/safety states, upload/extraction, quota/jobs, separate lesson/profile grants, and school-scoped feedback/notifications.
4. Each screen/component directory contains a PNG, exact generation prompt, and motion note. Root indexes state role, purpose, SRS/API mapping, API implementation status, and visual-approval status.
5. Keep one proposed brand treatment and navigation per role across the set. Use a blue primary action on mobile and web, yellow as an accent/secondary action, mint for supportive information, and red only for destructive/error states. Treat all colors, logo treatment, wording, and layout as visual proposals—not app token or brand approval.
6. Reuse one fictional child name, one five-year-old age example, one butterfly drawing, one Teacher name, and one school/date set wherever those appear. Do not include real personal data. Avoid dense paragraphs and specification/privacy banners in user-facing screens.
7. Preserve the product boundaries: feedback is lesson-scoped, not general chat; profile sharing is invited/scoped/revocable and separate from lesson grants; Teacher manages groups, not ownership of Parent accounts; activities appear after video; automated safety is not a human review gate; Teacher Deck and Parent guide are opt-in and produce no job when off; only AI rewrite suggestions may revise script scenes.
8. Record extra workflow gaps that remain outside the 23-screen visual set rather than implying an API/UI behavior that is not in the current SRS. Clearly label SRS-only target flows versus mounted Rev31/Rev37 APIs.

## Acceptance criteria

- **AC1 — Source consistency:** AC-33 no longer denies the Parent guide and aligns with BR-42/46, FR-P-11, FR-T-18 and the existing owner decision. No age-band policy is silently changed.
- **AC2 — Screen coverage:** the 23 listed screens each have a dedicated PNG, prompt, motion note, SRS/API mapping and accurate mounted-versus-target label.
- **AC3 — Component coverage:** all nine component groups have a dedicated board, prompt and motion note with state-dependent controls and accessible failure/recovery actions.
- **AC4 — Cross-screen consistency:** the proposed logo/wordmark, primary/secondary colors, role navigation, fictional names, date style and child artwork are consistent throughout the new set.
- **AC5 — Product rules:** no direct scene editing; storyboards show 5–15 scenes; only adult-confirmed script passes the pre-video human gate; job stages show no fake percentage; video safety is automatic/fail-closed; activities follow playback; sharing and feedback obey organization/profile scope.
- **AC6 — Visual quality:** inspect every generated image for legibility, clipped controls, text/spec leakage, sample-data drift and workflow contradictions; regenerate visibly unusable images and record remaining ImageGen text limitations.
- **AC7 — Provenance and lifecycle:** preserve Rev35/Rev36 unchanged; store all Rev38 visuals under `assets/generated/`; record prompts, tool, input references, output paths, hashes, review observations, context, decisions, status and evidence. Do not copy/reference assets from `approved/` or `applied/` or application source before separate owner visual approval.
- **AC8 — Scope:** no frontend/backend/API/schema/database changes, executable animation, tests/builds, external provider calls, real child data, commit or push.

## Execution steps

1. Freeze the relevant source baseline and preserve the existing working tree and Rev35/Rev36 artifacts.
2. Apply the single AC-33 consistency correction in the unsigned FEAT-063 SRS draft; statically confirm referenced requirements still agree.
3. Generate the 23 screens and nine component boards into the new Rev38 directories using the built-in image generator; save each prompt and motion note beside its image.
4. Inspect every image, including cross-screen branding, sample artwork/name/date continuity, action-state logic and role scope; regenerate defects within this plan.
5. Produce indexes and EV-063-31 with provenance, hashes, visual review, API boundary notes, limitations and remaining product decisions.
6. Update FEAT-063 context, decisions, source register, evidence index and status. Keep visual approval pending.

## Risks and limits

- The FEAT-063 SRS v2.3 and FEAT-029/039 age ranges conflict; this plan avoids age-policy resolution and uses only an illustrative five-year-old example.
- Image generation may render small Vietnamese text imperfectly. Keep copy short and record any remaining defects instead of treating PNG text as an implementation contract.
- New Parent/Teacher AI, video, quota, occurrence, profile-share and feedback screens may depict SRS-target APIs not mounted today; the indexes must make this explicit.
- The workspace already contains unrelated staged, modified and untracked files. Do not reset, clean, or rewrite them.

## Excluded

Application code or tokens, product API/schema/database changes, executable animation, live AI/model/provider calls, tests/builds, deployment, real child data, Git commit/push, owner sign-off of either SRS, a final age-band decision, and promotion of visuals into `assets/approved/` or `assets/applied/`.
