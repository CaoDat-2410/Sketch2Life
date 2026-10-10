# Sketch2Life — Master SRS Markdown context

## Canonical replacement — 2026-10-10

Owner explicitly replaced scope and kept Android/FastAPI/React Native. FEAT-039 updates this feature's canonical SRS to v3.1 for ages 3–12, Child/Teacher/Super Admin, classroom/groups/collaborative canvas/adaptive sketch/knowledge video/off-screen/portfolio. Documentation revision 3 adds detailed system-foundation sections B19–B26; owner selected one-school pilot, managed child profiles + QR/code without own login and school-mediated consent evidence/purposes. Exact v2.0 and v3.0 are preserved under FEAT-039. Older decisions below remain historical; conflicting product targets do not override v3.1. Detailed architecture/schema/contracts and unanswered policy remain proposed/TBD; source runtime is unchanged. Approval, source review, analysis, verification and current status are owned by FEAT-039.

Owner also confirmed age 36–155 completed months inclusive, a pilot capacity target of one class/up to 40 children, and default session/artwork retention 90 days after end. Separate portfolio/profile/audit/copy policies and measured device/model/load evidence remain gates.

- Status: OWNER_APPROVED_BASELINE — v1.6 implementation-grade test SRS detail recorded; implementation and physical deployment remain separately gated
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
  - Test authentication uses the owner-controlled real Firebase Authentication project; secrets remain runtime-only.
  - Adult roles are mutually exclusive `PARENT`, `GUIDE` and `ADMIN`; there is no child role or child credential.
  - Parent Web and Guide Console are required operational surfaces, not deferred scope; Parent Web is responsive for mobile and desktop browsers, Guide Console is desktop-first, and Vietnamese is the first UI language.
  - Parent live monitoring is limited to phase, status, progress and update time; backend operational monitoring, rate limits, retry budgets, idempotency and concurrency guards are mandatory test requirements.
- Catalog data covers age bands 0–3, 3–6, 6–9, and 9–12 years, represented by inclusive completed-month ranges 0–35, 36–71, 72–107, and 108–155 respectively. The supported product target is now `<9` / 0–107 months, so the first three bands are in scope and 9–12 records remain preserved source data. Exact activity age/topic and authored safety fields remain authoritative.
- Non-goals for this documentation update: application code changes, contract migration/adoption, provider or model execution, cloud changes, frontend asset generation/promotion, release, commit/push, or changes to pre-existing user work. The SRS target itself includes the required backend monitoring, rate-limit, Parent Web and Guide Console capabilities.
- Source boundary: the current working tree contains pre-existing modified and untracked files. They may be inspected as current evidence but must not be changed by this feature. Existing external handbooks/workbooks remain contextual references and must not be copied into the SRS.
- Output: artifacts/Sketch2Life_Master_SRS.md

## Owner scope closure — 2026-09-19

- MVP includes personalized animation, narrated story and learning micro-video.
- One Owner Caregiver owns each ChildProfile; one owner can create many ChildProfiles; there is no child account.
- Each ChildProfile may have multiple active/overlapping Guide assignments. Guide share duration is 3/7/15/30 days, effective immediately, and Parent may revoke immediately.
- A Guide can operate one session at a time. A Parent receives notification and live monitoring information when a Guide session starts/ends.
- Revoking a Guide during an active session stops the session immediately and shows an on-screen message.
- Parent live views expose the necessary redacted projection, not every technical metadata field.
- Parent Web is a required operational surface for child management, monitoring and information updates; it uses the same backend authorization and is not implicitly a session runner.
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

## Owner requirements closure — 2026-09-23

- v1.5 records the test architecture, real Firebase test authentication, adult-only mutually
  exclusive roles, required Guide Console and Parent Web, Vietnamese-first UI, minimal Parent
  monitoring projection, mandatory backend monitoring and test-stage rate-limit/idempotency guards.
- Lightning connectivity, AI/provider stress testing and production deployment remain outside the
  current stage.

## Completion snapshot — 2026-09-23

- Consolidated Vietnamese SRS v1.6 completed at artifacts/Sketch2Life_Master_SRS.md with B1–B29 plus Annex A implementation-grade test detail: target workflow diagram, business rules, domain entities/ERD, relationship/cardinality, logical schemas/data dictionary, API/error surface, state model, FR/NFR, versioned contract families, required Parent Web and Guide Console, observability, retention/legal constraints, use cases, verification, traceability, synthetic fixtures and implementation sequencing.
- The v1.4 update separates PixiJS Personalized Drawing Exploration from the parallel whiteboard MP4 job, records the SAM 2.1 Small/mask/stroke/TTS pipeline target, and adds the READY/retry gate without claiming runtime implementation.
- Focused contract/runtime tests passed (27 collected). Markdown structure and catalog checks passed.
- Repository-wide harness/security validators still report pre-existing FEAT-026 issues recorded in evidence/notes/VALIDATION_20260918.md; no unrelated files were changed.

## Expanded scope review — 2026-09-18

The owner supplied Phieu_FA26SE225.docx and directed that the master SRS be longer, cover the full registered scope including authentication, and ask for clarification without inventing requirements. The complete project registration form was text-extracted and its three embedded images were checked; embedded images are university logos/placeholders and add no product requirements. DOCX visual rendering could not run because the bundled renderer could not find LibreOffice; this does not affect text extraction but leaves page-layout review unverified.

The registration adds Guide Console and class-level duties, curriculum knowledge-base administration, recommendation override, account/role/family-classroom administration, model/safety/screen-time configuration, retention/deletion operations, offline tolerance, explicit child-data research dataset and household-trial evaluation, work packages, and minimum-vs-extended scope. Those details are not fully specified in the prior SRS.

Conflicts needing owner direction include: the form's early-childhood population versus the catalog's 0–12-year bands; Parent/Guardian versus Guide as a guardian and as a class-level professional; form's animation/story and minimum-vs-extended statement versus the supplied workflow image's 5–10-second micro-video; and exact scope of human overrides, research data and screen-time enforcement. Do not alter the SRS as if these are resolved until the owner answers.

- Clarification questionnaire: artifacts/SRS_Clarification_Questions.md; unresolved requirements remain open until owner answers.


## Historical owner clarification responses — 2026-09-18–19

- Target journey: use the supplied workflow image and include a narrated story.
- Historical target age range: 0–12 years, resolving the prior early-childhood/catalog ambiguity at that time. Superseded by the 2026-10-06 `<9` amendment below.
- Authentication: preserve the current repository authentication approach.
- Role scope: Admin is the highest system role; Parent access is limited to their own children; Guide access covers own children plus Admin-assigned class records. Existing Parents receive a notification and may petition a change; petition/revocation/consent details remain open.
- Admin access: Admin may view raw drawing/audio/transcript/observation when needed; safeguards, audit detail and provisioning remain OPEN_TBD.
- Retention data classes and research protocol: not decided yet; keep explicit OPEN_TBD requirements and ask no fabricated values.

## Owner story/video amendment — 2026-09-28

The owner has now superseded the earlier 2026-09-23 whiteboard-video target for the story-video experience: target duration is 40–60 seconds; illustration redraw is permitted as a derivative; the story retells the adult-confirmed picture and adds age/readiness-appropriate knowledge; the adult can use both quick controls and free-form script edits; an exact full script must be approved before any image-generation request; language and supported voice category are selectable; the current Wan2.2 TI2V-5B baseline is retained. Pixi remains an independent renderer; original image/audio remain immutable; narration is a separate TTS path.

SRS v1.7 B30–B32 is the current product-target authority for this topic. New contracts are `PROPOSED_UNADOPTED`; no runtime schema migration, provider call, implementation, or performance claim is implied. See `evidence/notes/OWNER_CHANGE_STORY_VIDEO_20260928.md`.

## Owner Montessori discovery amendment — 2026-09-30

SRS v1.8 B33 records the owner's direction to show the complete reviewed activity set matching the confirmed drawing topic and exact age, personalize its ordering with adult-confirmed child-profile interests, and remove child readiness/history/material availability as recommendation filters. Authored safety/policy, catalog status, exact age/topic and adult/caregiver supervision remain constraints. This amends product requirements only; FEAT-033 rev6 governs implementation approval and additive contracts/ADR. It does not claim runtime completion.

## Owner age-range amendment — 2026-10-06

The owner changed the supported child population to younger than 9 years: 0–107 completed months inclusive, using bands 0–3, 3–6 and 6–9. Children at 108 completed months or older are outside the supported product target. Preserve the catalog's 9–12 records, but reject such ages before profile/session age-specific generation. FEAT-029 Master SRS v2.0 carries the age and capstone-trial package/credit decisions; FEAT-020 and runtime age boundaries are aligned under FEAT-037, with automated verification pending. Existing versioned DTOs continue to support historical/catalog values. Package and top-up prices are approved assumptions for the capstone trial, not commercial pricing claims; no payment provider or live billing integration is selected.
