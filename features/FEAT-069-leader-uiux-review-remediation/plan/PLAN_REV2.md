# FEAT-069 leader review UI/UX completion — Plan Rev2

- **Status:** APPROVED for this exact UI-only scope.
- **Feature:** FEAT-069.
- **Revision:** 2.
- **Branch:** `FE_UI_Project_Ver2`.

## Goal

Close the remaining action items in the owner-provided leader review across Parent mobile and Teacher web UI. Treat the leader review as the requested review-prototype target while keeping the FEAT-063 SRS v2.5-draft as the canonical product baseline. Do not silently amend the SRS: explicitly document the UI sequences that differ from it, and keep unsupported API/AI behavior labeled as preview.

## Sources

- `docs/context/SRS_AUTHORITY.md` and FEAT-063 SRS v2.5-draft §§5, 7, 31–32.
- FEAT-063 `DATA_TABLE_REGISTER.md` for profile fields.
- FEAT-068 `evidence/notes/API_UI_CROSSWALK.md` and current mounted API client/routes.
- FEAT-069 Rev1 execution evidence and the user-provided leader transcript.
- Rev38 design references in `UI_Project/design-references/ui-mockups-rev38-20261030/` and `ui-components-rev38-20261030/`, treated as generated visual proposals rather than product/API authority.

## Scope

### Parent mobile

1. Retain the in-flow lesson library, public/shared grouping and in-place detail modal. Verify sample image controls remain absent.
2. Improve the optional pre-capture guide so each of its three steps has a distinct visible sketch illustration and the selected lesson topic. Keep the static/no-AI disclosure and skip path.
3. After capture and subject review, provide a conditional mismatch-choice modal in a clearly simulated preview state. The modal must offer both leader-requested directions and continue behavior, without claiming that a real AI analysis occurred.
4. Keep microphone errors in a concise modal. Let the adult review or type transcript text directly in the story-idea field. Do not claim speech-to-text; keep the recording/transcript local to the preview session.
5. Remove the standalone context-selection step. Show the context snapshot and required adult confirmation inside script review before the video request, preserving FR-P-06.
6. Add the leader-requested outdoor-activity selection before the preview video request, tied to the selected lesson and represented honestly as local preview data. Record that this presentation order conflicts with SRS §5.1 / FR-P-05 / FR-PL-16; do not edit the canonical SRS.
7. Add a gender selector to the local preview child-profile form and display the chosen value. Do not claim that gender is persisted or transmitted; the field is absent from the current SRS/API model.
8. Preserve the compact home, center create action and global settings gear.

### Teacher web

9. Keep the darker contrast, the single top-bar notification entry and the centered lesson-detail modal.
10. Review dashboard data against existing API contracts. Use a connected call only if a real principal, organization context, and supported route are already available; otherwise keep the dashboard clearly labeled as fixture preview and document the exact missing integration.
11. Present the review-requested session sequence as a navigable preview: select class → lesson → start → step through Show Slide/Sketch → complete the activity interaction → enter the separate sample-story capture step. Show explicit consent/eligibility boundaries before any child sample step. No class media is attached to the reusable occurrence.
12. Keep generated slides, occurrence persistence, photo analysis and sample video clearly marked as preview-only while their mounted APIs are unavailable.

### Evidence and delivery

13. Update feature context, decisions, open questions, execution evidence, screenshots, status and root source register.
14. Build the five UI workspaces, Parent Android typecheck, and debug APK. Visually inspect Parent and the three web roles. Do not add or run automated tests.
15. Run `git diff --check` and `python tools/validate_repository_security.py` before each commit/push, then commit and push normally to the previously authorized `origin/FE_UI_Project_Ver2` if fast-forwardable.

## Acceptance criteria

- **AC1:** Lesson groups/detail modal remain in the Parent story flow; no sample-image test button is present.
- **AC2:** The guide visibly changes illustration and instruction through three steps, remains optional/skippable and clearly static.
- **AC3:** A post-capture simulated mismatch state opens a two-choice modal; no real AI result is implied.
- **AC4:** Audio error is concise; the adult can review/edit transcript text in the same idea field; ASR is not claimed.
- **AC5:** There is no standalone context-selection step; the script screen contains the context snapshot and required adult confirmation.
- **AC6:** A lesson-tied outdoor activity can be selected before the preview video step; its conflict with canonical SRS is documented.
- **AC7:** Child-profile UI includes gender as local preview data only, with no persistence claim.
- **AC8:** Parent home, central create action, global gear and bottom navigation remain compact and usable.
- **AC9:** Teacher contrast is readable, dashboard has no duplicate notification card, and lesson details are centered.
- **AC10:** Teacher session preview presents the ordered slide/Sketch → interaction → separate sample capture sequence with explicit preview/consent boundaries.
- **AC11:** Dashboard shows live data only when supported auth and organization context exist; fixture mode remains unmistakably preview-only.
- **AC12:** Builds/typecheck/APK packaging, visual screenshots, repository security validation and publication state are recorded under FEAT-069.

## Product/API conflicts and guardrails

- Leader-requested pre-video activities contradict SRS §5.1 / FR-P-05 / FR-PL-16. Rev2 authorizes a review-prototype UI sequence only; it does not change the canonical SRS or claim signed product approval.
- Gender is not in the current profile model. Rev2 authorizes a local preview field only, not backend/schema/API changes or transmission.
- The mismatch modal is a user-triggered simulated result because no mounted VLM analysis response/contract exists.
- The Teacher auth bridge, `/api/auth/v1/me`, organization context for the current user, full occurrence/deck/story-photo flow, ASR and Parent story/video APIs remain unavailable in this checkout.
- Never invent a tenant ID, transmit profile/child media, call a live AI/provider, or report fixture data as backend data.

## Exclusions

Backend/API/auth/schema/database/SRS/provider/deployment changes; live ASR/AI calls; API writes; persistent child gender; real child data/media; release signing; modifying Child Expo; force push/history rewrite; automated tests.
