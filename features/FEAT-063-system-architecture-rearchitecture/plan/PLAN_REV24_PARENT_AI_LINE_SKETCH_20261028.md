# Plan revision 24 — optional Parent AI line-sketch guide

- Feature: FEAT-063 — Whole-repository architecture redesign.
- Status: documentation amendment directly requested by the project owner on 2026-10-28; SRS/Data Table Register content sign-off remains pending.
- Authority: the owner clarified that the optional Parent sketch suggestion should be a visual line-sketch generated with AI (for example, a butterfly), and asked whether to offer it to Parents. This resolves the visual-vs-text interpretation of the prior starter request.

## Scope

- Amend the FEAT-063 SRS and Data Table Register to make the Parent sketch starter an optional AI-generated line-sketch guide, available before the child's drawing. Do not keep a separate text-only starter as the defined feature.
- Let the adult choose a generic topic from an approved subject set and a simple difficulty level. Generate one child-friendly guide with 3–5 progressive line-art steps. The guide explains how to draw a generic subject; it is not a completed sample of the child's artwork.
- Keep request and skip paths non-blocking. Skipping, generation failure, timeout, or a limit refusal must return to the existing Parent drawing/capture flow. Subject confirmation remains after the child's drawing is captured and analyzed.
- Do not send a child profile, profile attributes, voice, photo, or existing child artwork to the sketch model. The generation input is limited to the generic selected topic, difficulty and versioned drawing-guide instructions.
- Keep generated guide output temporary, private, provenance-tracked and subject to a bounded cleanup/expiry policy. Do not associate it with the child's profile, StoryRun, or video output; do not charge the video quota. Use separate sketch compute/rate limits and safe output validation.
- Keep Teacher's occurrence-wide AI Sketch Deck as a main-flow step after the approved lesson plan. Parent's guide remains a separate, optional capability and does not replace or reuse the Teacher Deck.
- Reconcile Q145, FR-P-11, relevant AI job/asset contracts, business rules, acceptance criteria, edge cases, traceability, architecture decisions/context/status/evidence and source registers. Retire Q146 as an open question and remove the obsolete Q145 text-only description.
- Retain the existing table-count baseline unless the document review finds an unavoidable new entity. Prefer the current AI Job, Core Asset and AI Policy owners; record any required new field/retention behavior in the target contract. No live database inspection is in this scope.
- Keep FEAT-062 as a clearly superseded redirect/history record; do not delete provenance needed by existing links. Update references that still describe its old questions as current.

## Out of scope

- Product/UI/backend code, database migrations, live database access, model/provider calls, generated images, benchmark/test/build, deployment, real-child data, or Git commit/push.
- Final sign-off of the full SRS/Data Table Register, selection of a specific model/provider, exact cost/rate numbers, and a production retention duration. These remain later gates.

## Acceptance criteria

1. SRS v2.2-draft identifies Parent's AI line-sketch guide as optional and separate from the Teacher Deck; Teacher Deck remains in the main Teacher flow.
2. The Parent flow has a clear example sequence: adult picks a generic subject/difficulty, may request a 3–5-step line-sketch guide or skip, then child draws and the adult captures the drawing; post-capture VLM subject review is unchanged.
3. Requirements prohibit sending child profile, voice, photo or artwork to the Parent sketch generator; only generic topic/difficulty and versioned guide instructions are permitted.
4. Failure/timeout/rate refusal and skip do not block the existing drawing flow. Generated output is private, temporary and provenance-tracked; it is not attached to the profile/StoryRun and does not use video quota. Sketch compute/rate limits remain separate.
5. SRS acceptance and edge criteria cover request, skip, failure/limit refusal, unsafe or invalid output, output expiry/cleanup and prevention of child-data leakage.
6. Data Table Register and architecture documents agree on AI job target, asset lineage/temporary lifecycle and resource accounting. No new table count is claimed unless the plan/evidence explicitly justifies it.
7. Q146 is closed by the owner clarification and no current document describes AI Parent line-sketch as unapproved/open. Old Q145 text-only records are superseded and FEAT-062 continues to redirect to FEAT-063.
8. Feature-local evidence records document reconciliation and states that no runtime, provider, database or product test was performed.

## Evidence

Store a reconciliation note and static cross-document checks under this feature's `evidence/` directory. This amendment is documentation-only; do not claim runtime validation.
