# Plan Rev36 — UI component patterns and interaction states

- Feature: FEAT-063 — whole-repository architecture redesign.
- Status: APPROVED for generated visual drafts and feature-local documentation only, based on the project owner's direct request on 2026-10-30.
- Authority: owner asked to add modal, toast and other UI patterns needed by the SRS alongside the Rev35 screen mockups.
- Approval record: `approvals/TASK_APPROVAL.md` (this plan's SHA-256 is recorded there).

## Goal

Create a reusable visual reference set for the common components and response states needed across Parent Android, Teacher web, School Manager and Platform Admin surfaces. Each component group gets its own folder, image, prompt brief and motion note. The visuals must reflect the current SRS/API boundaries, including the difference between APIs implemented in Rev31 and SRS target flows that are not mounted yet.

## Source baseline

- `artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md`, especially §3 (roles), §20 (permissions), §21.5–§21.6 (client screens and error recovery), §22.4 (truthful job status), §31.2–§31.7 (lesson sharing, authoring, Parent history/feedback, quota and usage flows).
- `artifacts/LESSON_LIBRARY_API_CONTRACT_DRAFT_REV29_20261028.md`, Rev31 reconciliation: lesson visibility/grants, upload/extraction review, Manager decisions, Parent lesson access and Platform Admin moderation.
- `artifacts/API_INVENTORY_FEAT063_REV31_20261028.md` and `artifacts/API_PURPOSE_CATALOG_FEAT063_REV32_20261028.md` for mounted/current versus target API boundaries.
- Existing generated screens in `assets/generated/ui-mockups-rev35-20261030/` for visual continuity.
- Existing Parent assets and Teacher/Admin UI source as secondary visual references.

## Component board inventory

Generate one landscape component-board image per group, with several clearly separated component specimens/states on the board. Labels are Vietnamese. Examples are fictional and contain no real child data.

| ID | Group | Required specimens and SRS/API purpose |
|---|---|---|
| UI01 | Foundations and controls | Color/type/spacing/radius tokens; primary, secondary, destructive and disabled buttons; text field, select, chips, switch, checkbox, badge and focus/hover states. |
| UI02 | Parent dialogs and bottom sheets | Adult confirmation for exact script revision; subject correction/confirmation; cancel/delete confirmation; permission explanation with camera-to-gallery and microphone-to-text fallback. |
| UI03 | Teacher, Manager and Admin decision dialogs | Public request review/return-for-changes; hide/reopen content with reason; destructive archive; clear role-specific actor and target version. |
| UI04 | Toasts, snackbars and inline notices | Success, info, warning and failure; persistent actionable error; safe permission/not-found copy; stale-revision reload notice. |
| UI05 | Loading, empty, unavailable and conflict states | Skeleton/loading; first-use empty state; safe not-found/unavailable; action forbidden; stale revision; retryable provider error; non-retryable validation error. |
| UI06 | Upload and extraction states | File selected, actual byte transfer, scanning, deterministic extraction, `READY_FOR_REVIEW`, missing-field correction, unsupported/encrypted/oversize/scanned-PDF rejection. |
| UI07 | Quota and AI job states | Video quota summary and top-up entry; `VIDEO_QUOTA_EXCEEDED`; pre-admission `AI_COST_LIMIT_REACHED`; discrete named job stages, failure/safety hold and ready state. |
| UI08 | Sharing and access grants | Public/School/Selected Audience choices; invite named Parent or Parent group; child-profile share scope/purpose/expiry; revoke confirmation and revoked/unavailable state. |
| UI09 | Feedback and notification components | School-scoped text-only Parent–Teacher feedback thread, Manager/Admin reply context, in-app notification row/unread badge, send success/failure states. |

## Design and behavior rules

- Parent components use the existing calm mobile palette; web components use the existing light neutral/blue Teacher/Admin surfaces.
- Modal actions must identify what will change and which exact lesson/version/grant/run is affected. Sensitive actions require explicit confirmation; no action occurs merely because a modal was viewed.
- Toasts and banners must use SRS-safe copy. Never leak whether a resource exists outside the actor's scope; use the same not-found/unavailable presentation.
- Job status changes only from API responses. Do not animate invented percentages, ETAs or success. Upload percentage may be shown only when based on transferred bytes.
- `VIDEO_QUOTA_EXCEEDED` and `AI_COST_LIMIT_REACHED` are distinct. The former may offer a permitted purchase path while preserving existing playback; the latter is a temporary admission rejection and must not appear as a provider failure or consume quota.
- Upload original files remain private. Only filtered, Teacher-reviewed fields can proceed to AI. Use deterministic `READY_FOR_REVIEW` and validation/error states.
- Lesson grants and child-profile grants are different permission resources. Show audience/scope, purpose, expiry and revoke distinctly; never imply a lesson share grants child-media access.
- Feedback is text-only and school-scoped. Do not add chat, image/video attachment or a completion toggle.
- Each motion note lists trigger, state source, timing, reduced-motion behavior and any interaction guard. These are recommendations, not implemented animations.
- Component boards are visual drafts; keep all outputs under `assets/generated/` until owner visual approval.

## Execution

1. Generate nine component boards with the built-in image-generation tool, one call per board.
2. Save each image and its `PROMPT.md` and `MOTION.md` under `assets/generated/ui-components-rev36-20261030/<component-group>/`.
3. Create an index mapping each group to SRS/API sources and marking current versus target API behavior.
4. Review the nine outputs for role/scope clarity, accessible interaction, state accuracy, visual continuity and accidental child-identifying data; regenerate any unusable draft.
5. Update FEAT-063 context, decisions, source register, status and feature-local evidence. Do not modify application code or promote generated images to approved/applied assets.

## Acceptance criteria

- AC1: All nine groups in the inventory have a separate folder and a generated image board.
- AC2: Each group folder contains a prompt brief and motion note; motion notes include reduced-motion behavior and API-confirmed state requirements.
- AC3: The index maps each group to SRS/API contracts and explicitly distinguishes Rev31 runtime APIs from SRS-only/not-mounted target behavior.
- AC4: Modal, toast, upload, quota, sharing, feedback, permission and failure states respect the SRS role/data boundaries and use fictional data only.
- AC5: Job/progress and request errors are truthful; no invented percentage, ETA, access, confirmation, quota charge or visibility transition is shown.
- AC6: All assets remain in FEAT-063 `assets/generated/`; no product implementation, API, schema, database or runtime behavior is changed.
- AC7: Feature-local evidence records prompts, tool/source provenance, image hashes, review observations and remaining visual-approval status.

## Explicitly excluded

Frontend component code, design tokens in app source, executable animation/prototype, API/schema/database changes, AI/provider/model calls, tests/builds, deployment, real child data, Git commit/push, and promotion into `assets/approved/` or `assets/applied/` before visual approval.
