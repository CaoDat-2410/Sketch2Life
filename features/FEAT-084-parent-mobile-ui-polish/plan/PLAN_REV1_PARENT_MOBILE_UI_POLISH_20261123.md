# FEAT-084 Plan Rev1 — Parent mobile UI review and polish

**Date:** 2026-11-23
**Status:** APPROVED; scoped source changes applied, device verification not run.
**Worktree:** `<LOCAL_ROOT>\.codex-worktrees\fe`
**Branch:** `feature/fe-mobile-remediation`

## Goal

Review all Parent mobile screens, answer whether topic/object suggestion UI exists, and make the necessary UI refinements so the suggestion cards are visually clear and the main drawing flow avoids repeated or overly technical copy. Keep the app's existing visual language and child-friendly illustrations.

## Current findings

- The topic suggestion UI already exists in `TopicScreen`; it renders the API-provided cards, has a shuffle action and a separate custom-topic input.
- The drawing-subject suggestion UI already exists in `DrawingSubjectScreen`; it renders API-provided cards, supports a separate custom-subject field, and shows validation state. The cards currently have no subject artwork and the screen repeats explanatory text.
- Topic cards reused existing artwork for only part of the catalog; some IDs without a fitting image fell back to nature artwork, which could show the wrong topic.
- Activity cards show useful adult-facing instructions and safety information, but repeat explanatory copy and expose an internal lesson-version UUID.
- Capture shows repeated explanation about image selection/recognition.
- Other Parent mobile screens were source-reviewed. Preserve full review, safety, consent, account, error, and state information where the copy is necessary to the workflow; no broad redesign is justified from source review alone.

## Allowed code changes

1. `apps/ui-mobile/src/parent/presentation/components/topicVisuals.ts` — new shared topic-visual metadata; keep existing artwork paths and add topic/subject icon fallbacks for the rest of the catalog.
2. `apps/ui-mobile/src/parent/presentation/screens/TopicScreen.tsx` — shorten repeated instructions, improve topic card/custom-entry hierarchy, keep API cards, shuffle, input and all current actions.
3. `apps/ui-mobile/src/parent/presentation/screens/DrawingSubjectScreen.tsx` — add topic-aware visual cues to the topic header and subject choices, reduce repeated prose, preserve all three API cards, custom-subject validation, errors and confirmation actions.
4. `apps/ui-mobile/src/parent/presentation/ParentExpoApp.tsx` — pass the selected topic ID to the drawing-subject presentation screen only.
5. `apps/ui-mobile/src/parent/presentation/screens/ActivityScreen.tsx` — compact the intro/result copy and remove internal lesson-version identifiers from visible source labels; keep adult review details, safety notes, selection persistence state, and all actions.
6. `apps/ui-mobile/src/parent/presentation/screens/CaptureScreen.tsx` — remove duplicate explanatory copy while keeping image-upload transparency, locked-photo state, analysis states, errors, and required actions.

Feature-plan and evidence records under this FEAT-084 folder are also in scope.

## Explicit exclusions

- No changes to other mobile screens unless a necessary defect is found; record review findings instead.
- No behavior/state-machine, flow ordering, API, backend, Modal, AI, catalog-content, quota, consent, safety, or SRS changes.
- No new or generated bitmap assets and no changes to `assets/approved/` or `assets/applied/`.
- No Android/emulator launch, tests, typecheck, API/inference calls, security validation, commit, or push.

## Acceptance criteria

1. Topic and drawing-subject suggestions remain API-driven; the UI does not hardcode card content or imply a suggestion is the confirmed subject of the child's drawing.
2. The topic screen still has exactly the API-supplied cards, a separate custom-topic input, refresh/shuffle, skip, loading/error states, and its existing continue behavior.
3. The subject screen still has API-supplied catalog cards when available, a separate custom-subject input, topic/object validation, loading/error/success states, and the existing continuation guard.
4. The topic and subject cards include clear, child-friendly visual cues drawn from existing artwork/icons and use the current creative palette/component style.
5. Activity source labels do not display internal version IDs; activity instructions, required adult review, materials and safety details remain visible.
6. Capture continues to explain when the selected drawing is sent for analysis; photo locks, error states, and recognition actions are unchanged.
7. No Teacher Web/backend/business behavior changes are made.
8. Every Parent mobile screen component and the bottom bar are represented in the evidence audit with a disposition; source review is clearly distinguished from emulator visual verification.

## Review procedure

- Compare the affected screens against the shared Parent UI components, palette and topic assets already referenced by the app.
- Review the full diff for accidental workflow or API changes.
- Run only `git diff --check` as a whitespace/static diff check. Do not run tests, typecheck, API/AI, or emulator work under this plan.

## Risks

- A local visual metadata map can become stale as catalog topic IDs evolve. Keep it display-only and provide a safe generic icon fallback.
- Shortening copy must not hide the adult confirmation, safety, data-transfer or error details required by the flow.
- Source review cannot prove actual device layout, touch behavior, or visual fidelity; emulator verification remains a separate task.
