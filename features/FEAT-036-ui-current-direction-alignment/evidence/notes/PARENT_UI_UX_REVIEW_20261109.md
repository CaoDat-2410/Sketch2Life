# Parent UI/UX and SRS review — 2026-11-09

## Scope and method

- Reviewed Parent in `origin/FE_UI_Project`, commit `c384dcc6705b54005eea5e3ce21ecccf349498d5`.
- Used the `ui-ux-pro-max` skill for flow, hierarchy, feedback, accessibility and touch-target review, and `code-reviewer` for source-backed, prioritized findings.
- Compared the captured Parent routes at 430×932 with the canonical FEAT-063 SRS v2.7-draft Rev57 in the main repository, especially §5.1, FR-P-05, FR-PL-25, BR-24/55/57, AC-52/62, NFR-13 and NFR-20.
- Visual evidence is in `evidence/screenshots/fe-ui-project-20261109/parent/`. The local app runs in synthetic preview mode; this is not a backend-authenticated production walkthrough.
- This is a read-only review. No product code was changed. FEAT-036 remains `AWAITING_APPROVAL`.

## Findings

### P1 — The Parent must choose exactly one activity before video, then sees only that activity

`apps/parent-ui/src/pages/ParentScreens.tsx:1162-1257` routes the context step to P05b, preselects the first activity, requires a selection, and sends the user to script review. After the video, P08 only offers “Tiếp tục: Khám phá hoạt động ngoài đời” (`ParentScreens.tsx:1728-1737`); the layout resolves and displays the single `selectedActivityId` (`apps/parent-ui/src/components/MobileLayout.tsx:90-91`). The P05b screen even says the activity is for after the video, while making it a prerequisite before script review.

This reverses §5.1 steps 9–11 and conflicts with FR-P-05, BR-55 and AC-52: the story/video must run first and the Parent should then receive the activity list from the pinned lesson version. It also hides the other activities when a lesson has several. Remove the pre-video chooser; after playable video, show all eligible activities with materials, instructions and safety notes. For a run without a preset, follow the still-open decision in §31.10 instead of inventing catalog behavior.

Evidence: `P05b-activity-selection.png`, `P08-video-and-activities.png`, `P08b-outdoor-activity.png`.

### P2 — Child profile controls accept ages outside the target range

The create and edit controls label the range as 36–155 months and clamp values to that range (`apps/parent-ui/src/components/MobileLayout.tsx:244-283`; `apps/parent-ui/src/pages/ParentScreens.tsx:2280-2293,2353-2361`). This accepts ages 121–155 months, above the 36–120-month range in FR-PL-25 and BR-57; AC-62 explicitly accepts the boundary values 36 and 120. The screenshot also shows a “9+ tuổi” quick band without communicating the 10-year upper bound.

Set UI bounds and context validation to the approved 36–120 range, and keep any legacy 121–155 transition policy explicit rather than accepting those values as current.

Evidence: `P10-child-profile.png`.

### P2 — The Parent activity screen records completion, which the SRS excludes

P08b stores three completion booleans, exposes checkable steps and a progress count, and clears the active run when the Parent presses “Hoàn tất hoạt động & Tiếp tục” (`apps/parent-ui/src/pages/ParentScreens.tsx:1756-1779,1812-1853`). §5.1 step 13 and FR-PL-22 explicitly exclude a Parent completion toggle. Keep materials, instructions and safety guidance; remove completion recording and completion language.

Evidence: `P08b-outdoor-activity.png`.

### P2 — Video controls expose background music even though the product requires it to stay off

Portrait and landscape video layouts expose a “Bật/Tắt nhạc nền” control (`apps/parent-ui/src/pages/ParentScreens.tsx:1636-1644,1695-1702`). Its state changes only the icon; the preview does not control an audio track. BR-24 requires background music to remain disabled. Remove the control and expose only playback controls that operate on supported media.

Evidence: `P08-video-and-activities.png`.

### P2 — Login validation and the backend warning are not parent-friendly

The email and password inputs are not marked required (`apps/parent-ui/src/pages/ParentScreens.tsx:2559-2593`), so the form can submit empty credentials and rely on a backend failure instead of immediate field guidance. In backend mode, the warning explains “Firebase ID token”, “Backend” and role selection, but gives the Parent no next action. NFR-13 requires plain Vietnamese for non-specialists; the Parent persona also requires errors to offer a next action (§2). Add field validation and keep provider diagnostics out of parent-facing copy; state the available action in ordinary language.

### P2 — The activity choice and progress stepper do not fully expose their state to assistive technology

The P05b single-choice buttons change only their visual class and check icon; they do not expose a pressed/checked state (`apps/parent-ui/src/pages/ParentScreens.tsx:1224-1243`). The progress component puts an `aria-label` on a generic `div`, while each visible step is a `span` with a `title` and no current-step semantic (`apps/parent-ui/src/components/Kit.tsx:185-201`). NFR-20 requires semantic labels for the critical Parent flow. Expose the activity selection as a radio group or pressed state, and make the stepper a semantic list/progress indicator with the current step announced.

### P3 — Several mobile controls are smaller than the UX skill’s 44 px touch-target guidance

The main action buttons are 48 px and the bottom tabs are 44 px, but the back/icon button is 40 px; small primary and secondary buttons are 40 px and 38 px; chips have only 6 px vertical padding (`apps/parent-ui/src/styles/tokens.css:207-220,345-367,374-388`). Increase frequently used small controls to at least 44 px where the layout permits, especially on the Parent touch-first surface.

## What is working well

- The visual hierarchy is consistent, and the main action is prominent.
- Main buttons meet the 48 px target; bottom navigation meets 44 px.
- Global visible keyboard focus and reduced-motion handling are present (`tokens.css:111,1172-1174`).
- Form fields generally have visible labels and illustrations have alt text.
- Script review is a clear, required gate before video generation, matching §5.1 and FR-P-08. Preview video-progress copy also says it does not create a real video job.

## Scope and verification limits

- The canonical SRS describes Parent Android and Teacher Web as the client surfaces (§§2–3); it does not establish Parent Web acceptance criteria. Confirm whether this Parent Web portal is an intended product surface before using web-specific behavior as an acceptance baseline.
- In backend mode, several Parent routes are replaced with API-unavailable views because their product APIs are not connected. The local preview is useful for visual review but cannot prove authenticated end-to-end behavior. The separate FE_UI_PROJECT review records the Firebase session restoration/sign-out issue and other integration blockers.
- This pass reviewed source and the 430×932 screenshots. It did not run an automated accessibility scan or a manual keyboard, screen-reader, contrast, browser-zoom, or smaller-viewport walkthrough; no tests or builds were run.
- The root repository authority points to v2.7-draft Rev57. The branch-local authority copy still refers to v2.5-draft; retain the previously recorded authority-drift item.
