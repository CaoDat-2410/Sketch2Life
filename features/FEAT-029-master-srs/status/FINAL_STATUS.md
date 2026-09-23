# FEAT-029 milestone history

## Initial delivery milestone — 2026-09-18

The first Vietnamese master SRS draft was completed against repository context, the supplied workflow images, and the owner's initial answers.

## Expanded registration-aligned revision — 2026-09-18

After receiving Phieu_FA26SE225.docx, the registration was reviewed and compared against the initial SRS. The owner clarification set contains 58 questions; answers received so far are recorded in feature-local decisions and the question set. Master SRS version 1.2 now includes the confirmed 0–12 target age, image workflow and narrated story, Firebase authentication boundary, top-level Admin role with raw child-content access when needed, Parent own-child scope, and Admin-assigned Guide class scope with Parent notification/petition path, plus registered Guide Console, admin, offline, research and evaluation scope. Unresolved decisions remain OPEN_TBD. The same Markdown artifact now also includes B13–B19 relationship/cardinality, logical schema/data dictionary, API/error/idempotency, use-case, quality/operations, verification and schema review-gate sections.

Current state: awaiting focused owner answer on MVP/extended classification, Guide assignment petition/revocation/consent details, Admin raw-content safeguards/provisioning, account lifecycle, retention scope and research protocol. Do not mark the expanded SRS complete until the owner resolves these or explicitly leaves them TBD.

The bundled DOCX renderer could not find LibreOffice, so page layout of the registration form was not visually verified. Body text, tables and embedded images were inspected; the source form was not modified.

## Owner-approved scope closure — 2026-09-19

The owner approved the v1.3 target baseline. The master SRS now records:

- MVP animation, narrated story and micro-video.
- One Owner Caregiver per ChildProfile, many ChildProfiles per owner, no child account.
- Multiple Guide assignments, 3/7/15/30-day sharing, immediate assignment and immediate Parent revoke.
- Immediate stop and on-screen notification when a Guide session is revoked.
- One active session per Guide and overlapping assignments across different Guides.
- Parent live monitoring with a necessary redacted projection.
- Parent Web as Phase 2 management/monitoring surface using the same backend policy.
- Full child/session retention classes, archive-before-purge and separate audit retention.
- Durable business/audit logs, Grafana observability and break-glass Admin raw access.

The legal note records the reviewed Nghị định 13/2023/NĐ-CP child-data constraints and does not invent a statutory 30/60/90 retention period. Remaining deployment, legal-policy and account-lifecycle questions remain explicitly TBD. No runtime, provider, cloud or pre-existing user files were modified.

## Pixi/whiteboard media clarification — 2026-09-23

The owner clarified that PixiJS remains the interactive Personalized Drawing Exploration layer,
including tap-to-discover and 2.5D source-derived layers. Whiteboard video is a separate MP4
implementation that starts while Pixi is playing, uses the same learning thread/ExperienceSpec, and
targets VLM localization → SAM 2.1 Small → contour/stroke extraction → deterministic render →
FFmpeg/NVENC with independent TTS. Parent continuation is offered only after video READY; failure
is retryable and must not be shown as success. Current media is session-local; the next planned
implementation task is MP4 generation. Exact encoding, TTS, worker, retry and quality gates remain
TBD. No runtime/provider/cloud change was made in this documentation update.
