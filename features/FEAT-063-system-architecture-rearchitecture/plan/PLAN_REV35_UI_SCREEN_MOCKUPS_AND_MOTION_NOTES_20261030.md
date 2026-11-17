# Plan Rev35 — UI screen mockups and motion notes

- Feature: FEAT-063 — whole-repository architecture redesign.
- Status: APPROVED for the exact visual-draft scope below by the project owner's direct request on 2026-10-30.
- Authority: owner requested UI images based on the current APIs and SRS, organized into a dedicated folder per screen, with animation notes where needed.
- Approval record: `approvals/TASK_APPROVAL.md` (this plan's SHA-256 is recorded there).

## Goal

Create a reviewable set of screen-level visual concepts for the existing Parent and Teacher flows and the additive lesson-platform roles. Keep each generated image in its own role/screen folder, and document interaction motion, triggers, timing, reduced-motion behavior, and API-backed states next to the image.

## Source baseline

- `artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md`, especially §3, §6, §20, §21.5, and §31.1–§31.7.
- `artifacts/LESSON_LIBRARY_API_CONTRACT_DRAFT_REV29_20261028.md`, Rev31-reconciled contract for lesson authoring, filtered upload/review, visibility/publication review, access grants, Parent reads and Platform Admin moderation.
- `artifacts/API_PURPOSE_CATALOG_FEAT063_REV32_20261028.md` and `artifacts/API_INVENTORY_FEAT063_REV31_20261028.md` for current runtime/API boundaries.
- Existing Parent screen artwork under `apps/ui-mobile/assets/images/`; existing Teacher and Admin surfaces under `apps/teacher-ui/src/` and `apps/admin-ui/src/` are visual references only.

## Scope and screen inventory

Generate one standalone, high-fidelity screen image per screen. Parent screens use a portrait Android layout; Teacher, School Manager, and Platform Admin screens use desktop web layouts. Keep UI copy Vietnamese. Use fictional lesson/child examples and no real child data.

| ID | Role | Screen | Source-backed purpose |
|---|---|---|---|
| P01 | Parent | Lesson library | Discover Public or currently shared lessons; age/topic filters and lesson cards. |
| P02 | Parent | Lesson detail | Review learning topic, drawing guidance, age band, script direction and outdoor activities before using a lesson. |
| P03 | Parent | Drawing session with optional guide open | Show the child's paper drawing as primary; line-sketch guide is an explicit, dismissible option during drawing. |
| P04 | Parent | Capture and subject confirmation | Capture/upload artwork, review the proposed subject, and allow the adult to correct it before continuing. |
| P05 | Parent | Context and story review | Review the permitted child context and generated script/story direction before confirming the exact revision. |
| P06 | Parent | Video job progress | Show real named stages and retry/help state without invented percentage progress. |
| P07 | Parent | Video playback and post-video activities | Play the private child-specific video, then show lesson-defined outdoor activities and their materials/instructions. |
| P08 | Parent | Lesson history and feedback | See delivered lessons in the configured history window and provide text feedback in the school-scoped thread. |
| T01 | Teacher | Organization lesson workspace | Browse school-owned, shared and Public lesson presets alongside assigned classes. |
| T02 | Teacher | Structured lesson authoring | Create/edit a lesson version with topic, age band, objectives, drawing steps, subject knowledge, activities, safety and optional script direction. |
| T03 | Teacher | Filtered document import and review | Upload a supported document, inspect deterministic extracted allowlisted fields, correct them, and confirm before any AI assistance. |
| T04 | Teacher | Session presentation with optional Sketch Deck | Prepare an occurrence and explicitly enable/disable the Teacher line-sketch deck; show lesson steps without implying child-profile data is sent to deck generation. |
| M01 | School Manager | Public publication review | Review a Teacher lesson's version and checklist, then approve or return it with feedback before Public visibility. |
| A01 | Platform Admin | Public catalog moderation | Review, publish, hide or disable lesson content and inspect audit metadata without default child-media access. |

## Visual and interaction rules

- Match the existing Parent app's child-friendly blue, sunshine-yellow and mint palette, rounded cards, calm white space and drawing-led visual language. Preserve the Android Parent surface and its adult-guided role.
- Match the existing Teacher/Admin web foundations: light neutral workspace, blue primary actions, restrained status colors, clear data tables/forms and role-specific navigation.
- Keep screens faithful to the source contracts. In particular: no Parent-generated lesson suggestion entry point; no AI request from a whole raw lesson file; no automatic line-sketch generation when disabled; no shared/reused child video; no public Manager approval shortcut; no default child-media pane for Manager/Admin.
- Each motion note states trigger, visible change, suggested duration/easing, reduced-motion behavior and whether the effect is required, optional or intentionally absent. Motion must not imply unmeasured job progress or replace an adult confirmation.
- A still image is a visual draft. Motion is specified in Markdown and is not represented as implemented behavior.

## Execution

1. Generate images with the built-in image-generation tool, one call per screen, using the existing app assets/code only as visual references.
2. Save the PNG and its `PROMPT.md` and `MOTION.md` under `assets/generated/ui-mockups-rev35-20261030/<role>/<screen-id>/`.
3. Create a root index with screen IDs, image paths and review status; record tool/source provenance in feature-local evidence.
4. Inspect generated outputs for role/layout mismatch, missing core controls, obvious text defects and accidental child-identifying information. Regenerate a screen if the draft is visibly unusable.
5. Update FEAT-063 context, source register, status and evidence. Leave all assets in `generated`; do not copy them into `approved`, `applied`, or application source until the owner gives visual approval.

## Acceptance criteria

- AC1: All 14 screens in the inventory have a separate role/screen folder and a generated PNG.
- AC2: Every screen folder contains its generation prompt and a motion note; screens without meaningful animation explicitly say so.
- AC3: The screen index traces each mockup to the SRS/API purpose and identifies the asset as an unapproved visual draft.
- AC4: Parent, Teacher, School Manager and Platform Admin screens follow their server-side scope and consent boundaries; examples use fictional data only.
- AC5: Assets remain under FEAT-063 `assets/generated/`; no product UI, route, backend, database, or API implementation is changed.
- AC6: Feature-local evidence records image-generation tool, source references, output files, review observations, and timestamp.

## Explicitly excluded

Frontend implementation, product API/schema changes, app wiring, interactive prototypes or executable animation, AI/provider/model calls, database changes, tests/builds, deployment, real child data, Git commit/push, and promotion into `assets/approved/` or `assets/applied/` before visual approval.
