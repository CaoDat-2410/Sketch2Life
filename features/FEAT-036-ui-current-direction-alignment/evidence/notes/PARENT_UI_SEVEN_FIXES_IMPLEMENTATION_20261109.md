# Parent UI seven-fix implementation — 2026-11-09

## Scope and authority

- Implemented the owner-approved revision 3 plan in
  `plan/PLAN_REV3_PARENT_UI_SEVEN_FIXES.md` (SHA-256 recorded in `approvals/TASK_APPROVAL.md`).
- Applied the canonical FEAT-063 v2.7-draft Rev57 as the product baseline. No SRS requirement,
  Parent Web target-client decision, backend contract, or no-lesson-preset decision was changed.
- Changes are limited to the Parent UI and FEAT-036 records. Broad redesign/copy reduction and the
  Teacher, School Manager, and Platform Admin portals remain deferred.

## Changes

1. Context confirmation now opens story review directly. Removed the pre-video activity chooser,
   selected-activity state, and activity details from the pre-video confirmation/lesson detail.
   After playback, the Parent sees every activity in the selected lesson with materials, guidance,
   and its safety note. Activity presentation has no per-step completion or progress state. The
   final action is explicitly “Hoàn tất câu chuyện”.
2. Profile creation and editing accept integer ages from 36 to 120 months inclusive. Both forms
   show Vietnamese validation and never clamp an invalid value. Parent context mutations reject
   invalid ages as a second guard. The last quick-age option is “9–10 tuổi”.
3. Removed activity completion checkboxes, completed count/progress, and “Hoàn tất hoạt động”. The
   story-level completion action still leads to session feedback.
4. Removed background-music toggles from portrait and landscape playback. Captions and playback
   remain available. The local-preview banner is hidden while the player is in landscape so it
   does not push controls below the visible player frame.
5. Login email and password are required. Submission is disabled when the Firebase bridge is
   missing. The warning and unavailable-registration message use parent-friendly Vietnamese and
   offer a next step.
6. The flow stepper is an ordered list with labeled steps and `aria-current="step"`. Retained
   age-chip and caption selections expose their state with `aria-pressed`.
7. Back/icon, compact buttons, chips, and video control buttons have 44 px minimum touch targets
   where their layout permits.

## Manual preview evidence

Screenshots and capture metadata are stored in
`evidence/screenshots/parent-ui-seven-fixes-20261109/`.

- Inspected P05 context, P06 story review, P07 video status, P08 portrait playback, P08 landscape
  playback, P08b activities, P10 profile edit, and P13 profile creation at 430×932; landscape
  playback was inspected at 932×430.
- The post-video page rendered both activities. The captured invalid value of 121 months showed
  the same clear range error in both profile editing and profile creation. After an attempted
  create save, the dialog remained open, the field still contained 121, and the profile was not
  added.
- The portrait and landscape playback captures contain no background-music control/copy. The
  landscape capture shows the player controls inside the visible frame.
- No JavaScript runtime errors were observed during the captured route sequence. `git diff
  --check` passed.
- Automated tests and builds were not run, per the approved plan. The preview uses synthetic data;
  it does not verify backend authentication or backend-backed Parent activity retrieval. The
  current backend UI does not provide an end-to-end Parent Story Run API.

## Remaining scope

FEAT-036 remains active for the broader UI effort. Parent Web acceptance scope and the SRS behavior
for runs without a lesson preset remain open. General restyling and reducing text are deferred to
the owner's next request.
