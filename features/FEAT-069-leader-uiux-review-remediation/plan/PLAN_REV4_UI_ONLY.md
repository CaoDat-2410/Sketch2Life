# FEAT-069 leader UI/UX alignment — Plan Rev4 (UI only)

- **Status:** APPROVED for this exact UI-only scope by the project owner's direct instruction in the current conversation.
- **Feature:** FEAT-069 — Leader review UI/UX remediation.
- **Revision:** 4.
- **Branch:** `FE_UI_Project_Ver2`.

## Goal

Align the Parent mobile and Teacher, School Manager, and Platform Admin web experiences with the leader review. Use API/source inspection only to understand business concepts and role boundaries. Do not wire the UI to backend APIs in this revision.

## Authority and sources

- Current product authority: `docs/context/SRS_AUTHORITY.md` and FEAT-063 SRS v2.5-draft, still unsigned.
- Leader feedback disposition: `features/FEAT-068-project-uiux-coverage/evidence/notes/LEADER_REVIEW_DISPOSITION.md`, reconciled with the owner-provided review transcript already on file.
- Existing UI source and flow: `UI_Project/parent-ui`, `UI_Project/shared`, and `UI_Project/parent-android/apps/mobile`.
- API/source register and FEAT-068 crosswalk are reference material for domain terms and role boundaries only; they do not authorize runtime API calls in this plan.
- Do not use the legacy top-level `apps/`, Child Expo, or the user-excluded branches as implementation sources.

## Scope

1. Keep Parent as a mobile experience under `UI_Project/parent-ui`, packaged by the Parent Android WebView app. Keep Teacher, School Manager, and Platform Admin as web workspaces.
2. Remove the Rev3 conditional API/auth fetching from Parent, Teacher, and School Manager UI. Keep preview data local, visibly identified as demonstration data, and provide usable UI states without login or a live backend.
3. Align the Parent story flow to the leader disposition and canonical SRS: optional static guide; no sample-image shortcut; review the drawing before choosing lesson direction; short audio instructions with editable adult-reviewed transcript; required adult confirmation of context; show lesson activities after a playable story video; no unsupported gender field in child profile.
4. Keep any unavailable AI/media/story service as an honest preview/unavailable state. Do not simulate server success or send child/media data.
5. Keep Teacher contrast and role-specific navigation clear, use a single top-bar notification entry, center lesson details, and make the class → lesson → session → slide/Sketch → activity → separate sample-capture preview navigable with explicit eligibility/consent boundaries.
6. Preserve role-specific School Manager and Platform Admin web workspaces; refine their visual hierarchy and labels without implying unavailable operations completed.
7. Show the Parent Settings entry only on the Family Profile page; remove it from Home, story flow, and other pages while preserving the Settings sheet itself.
8. Update the feature plan/approval, decision, evidence, status, and source register to record this UI-only scope.
9. Build the five UI workspaces, run Parent Android typecheck and debug APK packaging, and visually inspect Parent plus the three web workspaces. Do not add or run automated tests.
10. Run `git diff --check` and `python tools/validate_repository_security.py` before each commit/push. Push normally to the previously authorized `origin/FE_UI_Project_Ver2` only if fast-forwardable.

## Acceptance criteria

- **AC1:** Parent activity selection is presented after a playable story video, consistent with the leader disposition and current SRS.
- **AC2:** Child profile contains no unsupported gender field or false persistence claim.
- **AC3:** Parent retains a compact home, clear create-story action, accessible child/profile context, bottom navigation, and distinct public/shared lesson browsing with centered detail.
- **AC4:** The optional guide is static, skippable, topic-aware, and has no sample-image shortcut; lesson direction is selected after drawing review.
- **AC5:** Audio guidance is concise; any transcript is reviewable/editable by the adult; context confirmation remains explicit before story generation.
- **AC6:** Teacher web meets the contrast, navigation, notification, centered-detail, and review-session requirements above with preview boundaries visible.
- **AC7:** School Manager and Platform Admin remain clearly role-specific web workspaces with no false claim of server-backed actions.
- **AC8:** None of the four role UIs imports or invokes `backendApi`, auth bridges, `fetch`, or another backend client as part of Rev4; all displayed rows are clearly preview/demo data.
- **AC9:** All five web workspace builds, Parent Android typecheck and APK packaging, manual visual review, required records, security validation, and publication state are recorded under FEAT-069.
- **AC10:** Parent Settings entry is visible only on the Family Profile page; it opens the existing settings sheet from that page.

## Exclusions

Backend/API/auth/schema/database/SRS/provider changes; live API/AI calls or writes; invented identity/tenant values; real child data/media; changes to legacy `apps/` or Child Expo; release signing; automated tests; force push/history rewrite.

## Approval basis

The project owner clarified that the task is to build the UI/UX to the leader's requirements and that API information is contextual business-flow reference, not a request to connect the UI to APIs. This plan implements that clarified scope. The canonical SRS remains unchanged.
