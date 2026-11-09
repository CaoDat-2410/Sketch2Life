# FEAT-036 plan revision 3 — Parent UI findings

- Revision: 3
- Status: `APPROVED`
- Prepared: 2026-11-09
- Type: bounded Parent UI implementation
- Source review: `evidence/notes/PARENT_UI_UX_REVIEW_20261109.md`
- Product baseline: FEAT-063 SRS v2.7-draft Rev57, unsigned

## Objective

Fix the seven prioritized Parent UI findings recorded in the 2026-11-09 Parent UX/SRS review.
The current request authorizes this bounded implementation batch. Broader visual redesign, general
copy reduction, and remaining Teacher, School Manager, and Platform Admin optimization are deferred
until the owner requests that next scope.

## Scope

1. Move Parent activity presentation after the video is playable. Remove the pre-video activity
   gate and show all activities from the selected lesson after the video, including their materials,
   instructions, and safety notes. Do not invent a global catalog behavior for runs without a
   lesson preset; that SRS decision remains open.
2. Enforce the 36–120 month child age range in create/edit controls and Parent context mutations.
   Invalid values must not be silently clamped or saved; explain the allowed range in Vietnamese.
3. Remove Parent activity completion state, progress, and completion wording. Keep activity content
   as guidance. Parent run completion remains a story-level action and must not imply that an
   activity was completed.
4. Remove background-music controls from portrait and landscape playback. Keep controls only for
   supported playback and captions.
5. Require login email and password, prevent submission when the authentication bridge is absent,
   and replace provider/backend jargon in the Parent-facing warning with plain Vietnamese and a
   useful next action.
6. Expose flow-step/current-step and any retained selection states semantically to assistive
   technology, consistent with FEAT-063 NFR-20.
7. Raise frequently used Parent touch controls to at least 44 CSS px where practical, using the
   existing design tokens and interaction patterns.

## Out of scope

- General visual redesign, information-architecture changes, and broad text reduction.
- Changes to Teacher, School Manager, or Platform Admin portals.
- Backend/API/authentication implementation, video runtime, external providers, credentials,
  deployment, real child data, and generated assets.
- Resolving the open product decision for Parent Web as a supported target client, or the SRS
  behavior for Parent runs without a lesson preset.

## Acceptance criteria

1. The Parent context step continues directly to story review. No activity is displayed as a
   pre-video requirement or included in the script-confirmation gate.
2. After the playable-video screen, the Parent can see every activity provided by the selected
   lesson, with its materials, instructions, and safety notes. No activity is required to start or
   finish the video.
3. Profile creation and editing accept integer ages from 36 through 120 months inclusive. Values
   outside the range remain unsaved and receive clear Vietnamese validation; Parent context methods
   reject invalid values as a second guard.
4. Activity guidance contains no completion toggles, completed-count progress, or language that
   claims the Parent marked an activity complete. Any run completion action is explicitly
   story-level.
5. Neither portrait nor landscape playback offers a background-music toggle. Caption controls and
   supported playback controls remain usable and accessible.
6. Login fields are required. Empty values receive field validation. When no auth bridge exists,
   login cannot submit and the notice states the limitation and next action in ordinary Vietnamese.
7. The flow stepper announces its label and current step; retained selected controls announce their
   state. Visible keyboard focus is preserved.
8. Back, compact, and chip buttons used on the Parent touch flow meet a 44 px minimum target where
   layout permits. Main actions remain at least 44 px.
9. The local preview remains available on `127.0.0.1:5271`. Manually inspect changed Parent screens
   at the existing 430×932 viewport and run `git diff --check`. Automated tests/builds are not part
   of this approval.
10. No unrelated visual restyle or broad text reduction is included.

## Implementation sequence

1. Record this revision and the owner's explicit approval in `approvals/TASK_APPROVAL.md`.
2. Implement the flow, age, activity, video-control, login, accessibility, and target-size changes.
3. Inspect the changed Parent preview screens; store updated evidence and record remaining limits.
4. Keep FEAT-036 active for later all-portal review/optimization; do not mark the broader UI effort
   complete from this Parent batch alone.
