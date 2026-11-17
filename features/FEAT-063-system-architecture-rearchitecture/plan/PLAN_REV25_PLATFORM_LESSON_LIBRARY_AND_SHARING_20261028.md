# Plan revision 25 — platform lesson library and cross-role sharing

- Feature: FEAT-063 — Whole-repository architecture redesign.
- Status: documentation amendment authorized by the owner's 2026-10-28 request and answers to the platform-architecture questionnaire; product implementation remains unapproved.
- Scope authority: preserve all existing Parent/Teacher runtime flows and the planned image-to-video pipeline. Extend the architecture with a shared lesson platform; do not wholesale replace or delete prior requirements, records, feature history, or source artifacts. Supersede only the specific requirements the owner explicitly changed.

## Scope

- Update the FEAT-063 full SRS and Data Table Register to add a Vietnamese-first, Montessori-inspired lesson platform for children aged 3–10, with age bands configurable as versioned catalog data until exact ranges are confirmed.
- Keep Parent and Teacher identities/accounts separate. Add a consented, invited, scoped and revocable sharing grant for a child's profile between Parent and the responsible Teacher/school. Preserve organization isolation, least privilege, audit and immediate access revocation.
- Model reusable lessons separately from class/session occurrences. Lessons may be authored by platform Admin or Teacher, versioned, reused as presets, and used by a Teacher or Parent without mutating the published source version.
- Define platform Admin, school Manager and Teacher permission boundaries. Support Private, School, Selected audience and Public visibility. Require school Manager approval before a Teacher's content becomes Public; keep non-public Teacher content within that school. Permit platform Admin moderation/hide/revoke, with organization isolation for ordinary school/Parent/Teacher access.
- Define a structured Teacher authoring form and standardized lesson-document template. Parse and filter documents before AI use; allowlist only fields such as topic, target age band, objectives, materials and activity steps. Keep original uploads tenant-private and out of model input. Teacher reviews/corrects the extracted structured draft before generation/publication.
- Add AI-assisted lesson drafting and activity suggestions as draft artifacts, never auto-published. Preserve the user's requested role boundary as an explicit open item where the answers differ on whether Teacher may initiate lesson suggestions. Keep Parent out of lesson-suggestion prompting by default; Parent may use/adjust a personal copy of an authorized lesson. In-session optional line-sketch generation runs only when the responsible adult has enabled it; do not create a sketch job when disabled.
- Extend reusable lesson content to include drawing subject/how-to guidance, learning notes about the subject, outdoor activities with materials/instructions/notes, optional versioned story/video script direction, and optional generated instructional illustrations/slides. Keep generated assets private, validated, versioned and provenance-tracked. Treat Presenton/FLUX.3 or other named generators as candidates only; do not lock providers/models.
- Preserve the current Parent draw → optional in-session line-sketch → capture the child's drawing → VLM subject review/correction flow and the current Teacher occurrence/teaching flow. Use the lesson's configured outdoor activity list after video generation as specified by the owner.
- Preserve the planned video stages: VLM understanding, structured story, 5–15-scene storyboard, adult review, Character Bible/reference, per-scene LTX-2.5/Modal, consistency checks, FFmpeg, narration/subtitles, output safety and private playback. Generate every video for the selected child's drawing; never reuse another child's video. Support an optional lesson-level/Adult-selected script-guided mode; record unresolved script-mode defaults/allowable deviations as an open question.
- For Teacher's one-child representative sample per teaching slot, record the owner's intent for a random representative child while leaving the precise selection mechanism/consent eligibility as an open question. Parent may separately generate a new personalized video for their own child from an authorized lesson, subject to that Parent account's quota.
- Add Parent access to the current Teacher's delivered lessons and the Public lesson library; support downloading authorized lessons, lesson-scoped feedback and replies, and visibility limited to the responsible school. Do not add direct chat, Parent completion toggles or Parent drawing-photo upload through this feature.
- Add plan-based quota scopes for schools and Parent accounts, school Manager allocation/purchase and Parent add-on purchase. Keep video quota ownership in Billing and AI compute/rate reservations in AI Policy. Record unresolved quota precedence/package rules as open questions.
- Reconcile the source register, context, decisions, ADR, status, feature-local evidence and global source register. Keep FEAT-062 as a superseded redirect/history source.

## Out of scope

- Product source/UI/backend changes, API implementation, database migrations, live database access, provider/model calls, generated visual assets, product tests/builds/benchmarks, deployment, real-child processing, commit or push.
- Deleting prior SRS versions, decisions, approved plan/evidence records or original source artifacts. Preserve provenance and point readers to the new current draft.

## Open clarification items to record in the SRS

- Exact Montessori age-band boundaries within ages 3–10.
- Whether lesson-suggestion generation can be initiated by Teacher, or only by platform Admin, given the owner's answers in items 11 and 13.
- Whether Parent edits only a personal lesson copy, and which fields are editable.
- Whether delivered-lesson history is visible for 30 or 60 days, or is configurable by plan.
- How the Teacher sample child is selected randomly and which consent/eligibility rules apply.
- Default and override behavior for following a lesson's optional script, and what changes are allowed when script-guided mode is enabled.
- Whether school and Parent quota pools are strictly separate and the fallback/charging order when both could fund a Parent-initiated generation.
- Whether Manager approval is required for School-only publication or only for Public publication; owner's explicit minimum is approval before Public.

## Acceptance criteria

1. SRS v2.3-draft states that this is an additive platform architecture update. Existing Parent and Teacher flows and the previously planned video pipeline remain present; no entire baseline or history is removed.
2. The SRS defines platform Admin, school Manager, Teacher and Parent roles, tenant boundaries, grants, revocation, audit and organization isolation.
3. Reusable lesson/template content is distinct from a delivered class occurrence, versioned, reusable as a preset and supports private/school/selected/public visibility with the stated Manager/Public approval rule and Admin moderation.
4. Teacher upload uses a structured form and standardized document format; raw original lesson material is not sent to AI. A filtering/allowlist step and Teacher preview/correction precede AI generation. AI output remains draft until an authorized human publishes it.
5. A lesson version can carry topic/drawing guidance, optional line sketch, subject-learning notes, one or more outdoor activities with materials/instructions/notes, optional video-script direction and optional generated slide/illustration assets with provenance.
6. Parent/Teacher profile sharing is invite-based, consented, scoped and revocable while account identities remain separate. Parent sees delivered lessons for the linked child, authorized Public content, and can download lessons and submit feedback/replies without chat, completion toggles or drawing-photo upload.
7. Existing optional line sketch remains opt-in per live session; disabled means no sketch generation job. Parent and Teacher videos remain child-specific, use the child's drawing, never reuse another child's video, and retain the existing pipeline stages. Lesson script-following is optional and versioned; unresolved mode defaults are recorded as open questions.
8. Age scope is updated to 3–10 years; exact age-band boundaries and 30/60-day history policy are explicitly left open rather than invented.
9. Billing/AI Policy responsibilities remain distinct, with school and Parent quota packages represented and unresolved quota priority recorded.
10. Data Table Register, SRS requirement/acceptance/trace matrices, ADR, context, decisions, status, evidence and source registers agree on the platform model and counts. All new or changed tables/relationships are explicitly enumerated.
11. FEAT-062's old question list remains retired and redirects to FEAT-063. Historical documents remain preserved and marked as superseded where practical.
12. Evidence records this as documentation-only work and does not claim runtime, provider, database or product-test verification.
