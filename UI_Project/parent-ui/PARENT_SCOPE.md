# Parent Android UI coverage

Source of current product intent: FEAT-063 SRS v2.7-draft Rev60, located on branch docs/feat063-diagram-readiness-20261107 at d77ad86c. It remains unsigned and is not merged into dev. The local dev baseline is 1431ef81; the latest BE feature branch is feature/feat063-be-foundation at 4b7f07cc, which is not merged into dev. See PARENT_FLOW_AUDIT.md for branch evidence and target API gaps.

## Implemented in the local UI prototype

| Parent capability | Prototype coverage |
| --- | --- |
| Account access | Login, signup, recovery and password-change forms; service integration is pending. |
| Child profiles | List, detail, add/edit and preview-only deletion. Age uses years plus extra months, constrained to 36–120 months. Interests, observations, achievements and external experiences can be entered. Revision/provenance and server purge status are not implemented. |
| Create a story | Choose one child, optionally pin a lesson, capture/select artwork, provide text and/or audio. No activity is selected before video. |
| Voice idea | Recording limit 2 minutes; imported audio limit 20 MB. Transcript review is editable and requires adult confirmation. ASR is not connected. |
| Image subject review | Adult can confirm or correct the suggested subject. Revision numbering is simulated; VLM is not connected. |
| Profile context | Adult reviews a minimal per-run context; private profile fields are excluded by default and age is opt-in. |
| Script review | Parent may request up to 3 rewrites; no direct scene editing; final script/storyboard confirmation precedes video in the prototype. Content is fixture data. |
| Video run | Stage-based progress, return/resume, cancel, unsuitable-video retry and finish are simulated. No real job/admission/safety/quota state is connected. |
| History and playback | Story list/status filters, illustration player with CC and full-screen control, and delete confirmation are present. Playback token, true video/captions and private media service are not integrated. |
| Lessons and activities | Lesson catalog/detail and activities are represented; with a pinned lesson, activities appear after video-ready. No-preset catalog policy stays unresolved. |
| Lesson feedback | Parent feedback and Teacher reply are displayed as a lesson thread; not general chat. Backend permissions and notification delivery are not connected. |
| Session feedback | Optional post-video stars, quick tags and note, separate from lesson feedback. Stored only in preview memory; no confirmed session-feedback API. |
| Notifications | Inbox and navigation are simulated; notification API is not connected. |
| Teacher sharing | Invite/revoke states are represented; server grant, permission, expiry and history rules are not integrated. |
| Quota and top-up | Prices and quota are treated as server-sourced; purchase is unavailable until Billing integration. |
| Optional sketch guide | Separate from child profile/story run. Current result is text-only fixture, not validated line-art; it is not a blocker to capture in the prototype flow. |

For a screen-by-screen gap inventory, see `PARENT_COVERAGE_RECHECK_20261111.md`. The preserved local SRS v2.2 asks Parent to select an outdoor activity before video; the newer Rev60 explicitly removes that gate. Rev60 governs this prototype until the project owner approves a later contract.

## Target backend contract

The SRS §21.2 target for Parent includes profile CRUD with revisions; resumable upload sessions; one-child story run creation; image/audio/text input; ASR and subject confirmation; context and script revision confirmation; bounded rewrites; video admission/generation; unsuitable-video retry; async jobs; playback-token issuance; completion/cancel/deletion; plus quota, lesson and notification reads as required. These are target contracts, not claims that all routes are currently implemented.

The current BE evidence does not show the complete target API mounted:

- Main dev composition does not mount the AI Jobs router.
- The newer BE feature branch is mainly Teacher/organization M2 and contains a StoryRun-lite route only behind a local/test synthetic demo flag. The demo is unauthenticated and loopback-only.
- Parent profile phase S1a-P and Parent StoryRun phase S2 are documented as separately gated; do not treat their planned routes as implemented.
- Durable job admission, outbox/reconciliation, real Parent identity/authorization, production media upload/playback and full video lifecycle remain integration gaps.

## Decisions still open in the SRS

- Whether a Parent run without a pinned lesson queries the global activity catalog after video, and its permission/filter/order/version/empty/revoke behavior.
- Lesson-history retention and default degree to which a story follows a lesson.
- Versioned age-band boundaries within the 36–120-month target; handling legacy ages 121–155.
- Parent/Teacher profile-sharing fields, invitation acceptance and revocation history.
- Quota units, packages, prices and school allocation.
- Other items explicitly marked OPEN-OWNER in SRS §31.

The prototype should not invent a decision for these items.

## Platform and integration boundary

parent-ui is a React/Vite Android-sized interaction prototype, not the native Android app. The intended Parent Android target is apps/mobile (React Native 0.87 + TypeScript) per the SRS/source notes. Fixture state does not validate Android camera/microphone permissions, upload resume, background recovery, API authorization, durable job polling or server lifecycle behavior.
