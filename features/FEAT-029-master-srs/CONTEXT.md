# Sketch2Life — Master SRS Markdown context

- Status: OWNER_APPROVED_BASELINE — v1.4 scope clarification recorded; implementation and physical deployment remain out of scope
- Owner: Project owner / Codex
- Goal: produce one Vietnamese master Markdown SRS that consolidates actors, scope, use cases, business rules, domain entities, state transitions, functional and non-functional requirements, versioned contracts, traceability, and unresolved decisions.
- Scope: documentation only. The SRS follows the B4–B12 workflow while adding B1–B3 and B13–B19 completeness sections from the supplied reference and the Sketch2Life product journey shown in the supplied workflow image. Current repository evidence and user-confirmed target requirements are labeled separately.
- User-confirmed target choices:
  - The product flow in the supplied image is the intended target workflow.
  - Parent and Guide are adult guardians who observe and participate with the child; include an Admin actor.
  - The digital portion should take about 10 minutes maximum, excluding the physical/off-screen activity.
  - Narration may be edited and recorded again if unclear.
  - A parent/guardian selects a child-data retention period of 30, 60, or 90 days.
  - Include detailed contract families while retaining the current incompatible same-name families as unresolved; do not silently adopt a proposed mapping.
  - Admin may grant a Guide class assignment; existing Parents receive a notification and may petition a change.
  - Admin may view raw child drawing/audio/transcript/observation when needed; Firebase remains the authentication provider/boundary.
- Catalog-derived target coverage: activity records cover age bands 0–3, 3–6, 6–9, and 9–12 years, represented by inclusive completed-month ranges 0–35, 36–71, 72–107, and 108–155 respectively. Exact activity readiness and safety fields remain authoritative.
- Non-goals: application code changes, contract migration/adoption, provider or model execution, cloud changes, frontend asset generation/promotion, release, commit/push, or changes to pre-existing user work.
- Source boundary: the current working tree contains pre-existing modified and untracked files. They may be inspected as current evidence but must not be changed by this feature. Existing external handbooks/workbooks remain contextual references and must not be copied into the SRS.
- Output: artifacts/Sketch2Life_Master_SRS.md

## Owner scope closure — 2026-09-19

- MVP includes personalized animation, narrated story and learning micro-video.
- One Owner Caregiver owns each ChildProfile; one owner can create many ChildProfiles; there is no child account.
- Each ChildProfile may have multiple active/overlapping Guide assignments. Guide share duration is 3/7/15/30 days, effective immediately, and Parent may revoke immediately.
- A Guide can operate one session at a time. A Parent receives notification and live monitoring information when a Guide session starts/ends.
- Revoking a Guide during an active session stops the session immediately and shows an on-screen message.
- Parent live views expose the necessary redacted projection, not every technical metadata field.
- Parent Web is Phase 2 for child management, monitoring and information updates; it uses the same backend authorization and is not implicitly a session runner.
- Retention 30/60/90 applies to all child/session data classes; expired data becomes Parent/Guide-invisible archive data before purge. Audit retention is separate.
- Notification uses combined channels. Grafana is used for redacted metrics/logs/traces and dashboards; durable business and audit records remain authoritative.
- Admin raw child data access is break-glass, reason-required and audited.
- Legal note: Nghị định 13/2023/NĐ-CP was reviewed for child consent, best-interest, deletion and the general 72-hour response rule; it does not itself prescribe a universal 30/60/90 product retention period. Legal exceptions and production privacy review remain TBD.

## Owner media-pipeline clarification — 2026-09-23

- PixiJS remains the interactive drawing-exploration implementation. It keeps tap-to-discover and
  2.5D source-derived layers; it is not converted into whiteboard mode.
- Whiteboard animation is a separate video implementation that runs after Gate B and starts in
  parallel while Pixi is playing. It uses the same approved learning thread and ExperienceSpec.
- Target pipeline: current VLM localization → SAM 2.1 Hiera Small masks → contour/stroke extraction
  → deterministic whiteboard render → FFmpeg/NVENC MP4, with an independent TTS narration track.
- Parent continuation is exposed only after the MP4 is ready. Generation failure is retryable and
  must not be presented as successful video. Current scope is process-local/session-only; auth and
  durable save remain future work.
- Exact codec/size/timeout/retry/TTS voice and exhausted-failure recovery remain OPEN_TBD. See
  `evidence/notes/WHITEBOARD_VIDEO_SCOPE_UPDATE_20260923.md`.

## Completion snapshot — 2026-09-23

- Consolidated Vietnamese SRS v1.4 completed at artifacts/Sketch2Life_Master_SRS.md with B1–B29, target workflow diagram, business rules, domain entities/ERD, relationship/cardinality, logical schemas/data dictionary, API/error surface, state model, FR/NFR, versioned contract families, Parent Web, observability, retention/legal constraints, use cases, verification, traceability and open decisions.
- The v1.4 update separates PixiJS Personalized Drawing Exploration from the parallel whiteboard MP4 job, records the SAM 2.1 Small/mask/stroke/TTS pipeline target, and adds the READY/retry gate without claiming runtime implementation.
- Focused contract/runtime tests passed (27 collected). Markdown structure and catalog checks passed.
- Repository-wide harness/security validators still report pre-existing FEAT-026 issues recorded in evidence/notes/VALIDATION_20260918.md; no unrelated files were changed.

## Expanded scope review — 2026-09-18

The owner supplied Phieu_FA26SE225.docx and directed that the master SRS be longer, cover the full registered scope including authentication, and ask for clarification without inventing requirements. The complete project registration form was text-extracted and its three embedded images were checked; embedded images are university logos/placeholders and add no product requirements. DOCX visual rendering could not run because the bundled renderer could not find LibreOffice; this does not affect text extraction but leaves page-layout review unverified.

The registration adds Guide Console and class-level duties, curriculum knowledge-base administration, recommendation override, account/role/family-classroom administration, model/safety/screen-time configuration, retention/deletion operations, offline tolerance, explicit child-data research dataset and household-trial evaluation, work packages, and minimum-vs-extended scope. Those details are not fully specified in the prior SRS.

Conflicts needing owner direction include: the form's early-childhood population versus the catalog's 0–12-year bands; Parent/Guardian versus Guide as a guardian and as a class-level professional; form's animation/story and minimum-vs-extended statement versus the supplied workflow image's 5–10-second micro-video; and exact scope of human overrides, research data and screen-time enforcement. Do not alter the SRS as if these are resolved until the owner answers.

- Clarification questionnaire: artifacts/SRS_Clarification_Questions.md; unresolved requirements remain open until owner answers.


## Owner clarification responses — 2026-09-18–19

- Target journey: use the supplied workflow image and include a narrated story.
- Target age range: 0–12 years, resolving the prior early-childhood/catalog ambiguity for this SRS.
- Authentication: preserve the current repository authentication approach.
- Role scope: Admin is the highest system role; Parent access is limited to their own children; Guide access covers own children plus Admin-assigned class records. Existing Parents receive a notification and may petition a change; petition/revocation/consent details remain open.
- Admin access: Admin may view raw drawing/audio/transcript/observation when needed; safeguards, audit detail and provisioning remain OPEN_TBD.
- Retention data classes and research protocol: not decided yet; keep explicit OPEN_TBD requirements and ask no fabricated values.
