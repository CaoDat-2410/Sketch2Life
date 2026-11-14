# FEAT-069 Plan Rev5 — complete UI preview states from source contracts

- **Status:** APPROVED by the project owner's direct request in this conversation; exact approval is recorded in the root and feature approval registers before implementation.
- **Date:** 2026-11-14 (Asia/Saigon).
- **Branch:** `FE_UI_Project_Ver2` (existing delivery target; no branch switch).
- **Scope:** UI-only updates under `UI_Project/` plus FEAT-069 evidence/status records. Use canonical FEAT-063 SRS v2.5-draft and permitted source/API contracts as business-flow reference. Do not call or connect APIs.

## Source boundaries

- Current product requirements: `docs/context/SRS_AUTHORITY.md` and FEAT-063 SRS v2.5-draft.
- Read-only API source reference: `origin/feature/feat063-m2-parent-teacher-foundation@5c07c94e86826447d975ef2757aa1fefdc876c8c`. Lesson Library summaries and organization assignments inform Teacher Dashboard preview data; Parent workflow contracts inform subject/transcript states. No source is copied from prohibited branches.
- Current delivery target remains `UI_Project/parent-ui`, `UI_Project/shared`, and the existing Parent Android WebView host. Top-level `apps/` and Child Expo remain outside the implementation target.
- No API/auth/network requests, backend/schema/SRS edits, test additions, or real child data.

## Changes

1. **Parent mismatch review:** after image review, present a clearly labeled local analysis fixture. When it reports a lesson mismatch, open the choice modal automatically; allow either the lesson direction or the child's drawing direction and continue in preview. Never claim real AI analysis.
2. **Parent voice-to-text:** make recording, transcribing, editable transcript, retry/error and completion states visible. In this offline preview, a clearly labeled sample transcript is inserted into the idea field; do not call Whisper or any API.
3. **Parent drawing guide:** complete the optional 3–5-step generic-topic guide UI with topic/difficulty context, step navigation, progress, skip and graceful unavailable state. Do not use child/profile/artwork data or call an AI route.
4. **Teacher Dashboard:** derive preview cards from fixture rows shaped after the source contracts for Teacher lessons and assigned classes. Keep counts attributable to returned list rows; remove unsupported topic analytics or invented backend metrics; include useful empty/loading/unavailable presentation and preserve the single top-bar notification entry. Do not connect API.
5. **Parent gender:** add a local preview-only gender field to create/edit profile UI and display the selected value in the child picker. Do not persist it to an API or change the SRS/data model. Track that the current canonical SRS does not define this profile attribute.
6. **Run for review:** build all five UI workspaces, typecheck Parent Android, package the debug APK, start the role previews and visually review the changed Parent and Teacher screens. Record emulator limitations rather than claiming unverified runtime behavior.

## Acceptance criteria

- AC1: The mismatch modal is part of the post-capture/review flow and opens when the local preview result says mismatch; each direction is selectable and its choice is reflected in the next preview step.
- AC2: Recording state and mock transcript state are understandable; the transcript is editable in the same idea field; failure is concise and recoverable; all non-live results remain labeled preview.
- AC3: The Parent drawing guide can be entered/skipped and navigated through three or more ordered generic-topic steps without using child-specific data.
- AC4: Teacher Dashboard preview values are derived only from fixture lesson/assignment rows corresponding to source-supported concepts; no unsupported analytics panel or dashboard notification card is presented.
- AC5: Parent profile creation/editing includes a gender control and the start-story child selector displays the fixture's selected value. This is explicitly local preview data only.
- AC6: `npm run build` passes all five UI workspaces; Parent Android typecheck and debug APK package successfully; the browser previews are running and the changed screens can be reviewed.
- AC7: Repository security validator passes before every commit/push; feature plan, approval, context, decisions, execution evidence, open questions and status are current.

## Approval and limitations

The owner directly authorized this UI-only update, including the Parent gender field. That approval does not sign off or revise FEAT-063 SRS v2.5-draft. The gender field is a UI preview proposal pending product/data-model reconciliation. All AI and ASR outputs in the preview are fixtures; no service behavior or backend readiness is claimed.
