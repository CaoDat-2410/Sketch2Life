# ADR-0022: Additive Montessori lesson platform and scoped sharing

- Date: 2026-10-28
- Status: PROPOSED — the owner approved this documentation amendment only; SRS content sign-off and implementation remain pending.
- Authority: owner request and answers 1–49 recorded as Q147–Q195 in FEAT-063 SRS v2.3-draft.
- Scope: lesson library, school tenancy, role/access model, Parent–Teacher profile grants, filtered lesson authoring, delivery/feedback, quotas and integration with existing Parent/Teacher media flows.
- Technology boundary: no final stack, model/provider, deployment, physical schema or migration is selected by this ADR.

## Context

Sketch2Life already has separate Parent Android and Teacher web flows, a single-child drawing-to-video pipeline, a Teacher occurrence/sample workflow, quota and safety rules. The owner wants a Montessori-inspired platform that supplies reusable lessons while keeping those flows and the planned image-to-video stages. This platform is an additive architecture layer; it does not replace the existing product baseline or erase its history.

The platform needs reusable lesson content, school-private authoring, public discovery, controlled sharing, and a way for Parents and Teachers to coordinate around a child without merging accounts or profile ownership. Lesson uploads may contain content outside the allowed AI input, so a filter and human review step must precede any model request.

## Decision

### Product and role boundaries

- Add a Vietnamese-first lesson platform for children aged 3–10, Montessori-inspired, child-centered and supporting adults as guides, observers and helpers. Exact age-band boundaries remain configurable/open.
- Provide Platform Admin, School Manager, Teacher and Parent roles with scoped permissions, deny-by-default access, audit and revocation. Each school is one organization/tenant.
- Keep Parent and Teacher accounts and profile ownership separate. A Parent may invite a responsible Teacher/school to receive a consented, field-scoped child-profile grant. Pending invitations grant no access. Revoke must invalidate new reads, downloads, tokens, caches and not-yet-accepted AI work.

### Reusable lessons and publication

- Separate a reusable lesson and immutable lesson versions from each teaching occurrence or Parent use. Preset/reuse/remix pins a version; Parent/Teacher may ask AI for edits to a selected lesson, with the result kept as a draft/personal copy. Edits create a new version/copy and preserve source lineage.
- Lesson versions can define the drawing subject/steps, subject knowledge, age target, one or more outdoor activities with materials/instructions/notes, optional video-script direction, and optional visual/slide assets.
- Support PRIVATE, SCHOOL, SELECTED_AUDIENCE and PUBLIC visibility. Selected audiences may be a Parent group or individually invited recipients. Non-public Teacher lessons remain in the school tenant.
- A Teacher lesson can become PUBLIC only after a School Manager approves it. School-only content needs no public approval. Platform Admin can moderate/hide content under platform permissions. Hiding/unpublishing removes library access while preserving versions and usage history.
- If a lesson has been used and is later unpublished, keep the pinned version, occurrence and history metadata. Lesson content becomes available again only after republication or a new valid grant.

### Authoring and AI boundary

- Provide Teacher authoring fields and a standardized lesson document format. Quarantine, malware-check, parse and map uploads into an allowlisted structured draft before any AI request. Keep the original private and preserve its hash/provenance.
- Never send a full lesson upload, raw extracted text, embedded image or unrelated metadata to a model. Teacher previews, corrects and confirms the filtered fields before AI assistance.
- AI lesson, plan, activity, illustration and slide outputs begin as drafts and require an authorized human to review and publish. No AI draft becomes public automatically.
- The role allowed to initiate lesson suggestions is unresolved because owner answers 11 and 13 need reconciliation. Keep that permission explicit and configurable in this draft; do not infer it from an editor role.
- Parent and Teacher line-sketch guidance is a session option. Generate only after the responsible adult enables it; when disabled, do not create a job or asset.

### Existing learning and video flows

- Parent flow remains: child draws; while drawing an adult may enable a line-sketch guide; after drawing, capture the child artwork; run the existing VLM/story/storyboard/review/image-to-video/safety pipeline; then show the lesson outdoor activity list.
- Teacher retains the existing class/occurrence and one-child sample flow. Teacher may use a reusable lesson as a preset. For a sample slot, select one eligible child at random and pin one approved activity; a maximum of one successful sample per occurrence remains. Exact random-selection and consent eligibility rules remain open.
- Every Parent or Teacher video is newly generated from the selected child’s drawing and approved profile context. Never reuse another child’s video. A lesson’s script direction can be enabled or disabled; when enabled it guides the story, while generated video remains specific to the child drawing/profile.
- If subject recognition appears wrong, ask the adult to confirm, correct the subject and request a new suggestion. Do not silently change the subject.

### Feedback, history and quota

- Parents with an active profile share can see lessons delivered to that child and authorized public/shared lessons, download permitted lesson content, and submit lesson-scoped feedback. Teacher, Manager and Platform Admin may review/reply within the school thread; feedback is not general chat and is not visible to other organizations.
- Do not add Parent completion marks or drawing-photo attachments to feedback. Parent lesson history uses a configurable 30/60-day window until the exact policy is settled.
- The platform pays provider costs. Billing owns product video quota scopes for school, Teacher and Parent packages; Managers may allocate/buy school quota and Parents may buy their own package/top-up. AI Policy remains responsible for compute reservation. Package values and charging precedence remain open.

### Architecture and data boundary

- Add logical platform entities only where the SRS requires them. FEAT-063 v2.3 proposes 11 new logical tables, bringing the target to 51 new + 38 retained/refactored = 89 active, plus 48 legacy/read-only = 137 projected physical tables. These are design counts, not a live database inspection.
- Cross-feature operations use versioned contracts and owner ports. Do not add cross-owner database coupling, silently replace original assets, or overwrite source lesson versions.
- Existing technical proposals remain subject to their original review gates. Firebase remains Authentication-only; no Firebase Storage/Firestore/Realtime Database. Mobile receives no storage or inference credentials/endpoints. Final technology/provider selection remains open under ADR-0003 and related records.

## Consequences

- Parent/Teacher flows and the existing video pipeline remain part of the product baseline while lesson discovery and reuse become shared platform capabilities.
- School tenant isolation, grant lifecycle, lesson versioning and content filtering are architectural requirements, not UI-only checks.
- The architecture grows by the 11 logical platform tables documented in the current Data Table Register. Physical schema and migrations require a separate approved plan.
- SRS v2.3 and the Data Table Register remain drafts. This ADR does not authorize implementation, provider calls, generated assets, product tests, deployment or real-child processing.

## Open decisions

- Exact Montessori age-band boundaries.
- Which role may initiate AI lesson/activity suggestions, resolving owner answers 11 and 13.
- Exact profile fields and invitation expiry/renewal policy.
- Parent lesson-history window: 30 or 60 days.
- Teacher sample child randomization, eligibility, consent and guardian notice.
- Default and allowed deviation for lesson script-following.
- Public approval/moderation process for Platform Admin-authored lessons.
- Asset ownership, review and approval for AI-generated lesson visuals/slides.
- Quota allocation, package values, purchase and charge/fallback order.
- Exact policy details for the owner’s short answer 46.

## References

- FEAT-063 SRS v2.3-draft: `features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md`, especially §31.
- FEAT-063 Data Table Register v2.3-draft: `features/FEAT-063-system-architecture-rearchitecture/artifacts/DATA_TABLE_REGISTER.md`, especially §14.
- FEAT-063 Plan Rev25 and approval record; approval is documentation-only.
- ADR-0003 and ADR-0021 remain in force where not explicitly extended here.
