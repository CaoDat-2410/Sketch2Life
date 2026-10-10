# FEAT-036 plan — current UI audit and alignment fixes

- Revision: 2
- Status: `AWAITING_APPROVAL`
- Prepared: 2026-10-05
- Type: UI review and proposed remediation task

## Objective

Make the existing Sketch2Life UI truthful, usable on Android, and consistent with the current
owner-approved product flow. Record separate follow-up tasks for required surfaces that do not yet
exist. No implementation is authorized by this plan's preparation.

## Baseline and authority

- Current screen code: `apps/ui-mobile/src/screens/Flow1Screens.tsx`,
  `apps/ui-mobile/src/screens/Flow2Screens.tsx`, `apps/ui-mobile/BaoApp.tsx`, and
  `apps/ui-mobile/src/context/AppContext.tsx`.
- Runtime snapshot: synthetic Android `Pixel 10` emulator captures plus four preserved screenshots
  from FEAT-035-EV-003, all recorded under this feature's `evidence/screenshots/`. Five of 15 active
  routes have runtime evidence; the remaining routes were not fully navigated.
- Product requirements: FEAT-029 master SRS B21 (Parent Web and Guide Console), B30–B32 (40–60s
  illustrated story video, adult script gate and READY requirement), B33 (all topic+age matches),
  ADR-0012, and ADR-0013.

## Findings and proposed work

| ID | Priority | Finding | Proposed fix / task |
|---|---|---|---|
| UI-01 | Verify; fix only if reproduced | A preserved FEAT-035 screenshot suggested Home inset overlap, but the current Pixel 10 runtime shows the greeting below the status bar and tabs above the gesture area. | Keep safe areas in the cross-screen/device matrix. Do not implement an inset change from the stale screenshot alone. |
| UI-02 | P1 | Activity suggestions are rendered with `slice(0, 3)` until the user taps to expand, although ADR-0012/B33 call for the complete topic+exact-age set in the normal chooser. | Show the complete returned set by default. Use pagination only if a measured transport/display constraint exists and the UI retrieves every page; preserve ranking without suppressing matches. |
| UI-03 | P1 / dependency | The current “Video Placeholder” explicitly says the main video comes later and immediately offers physical-activity handoff. The SRS requires an adult-approved illustrated video of 40–60 seconds to reach validated `READY` before Parent continuation; Pixi remains a separate experience. | Open a separate video UX/runtime task once the versioned API contract is approved. It must cover script review/approval, job progress, recoverable failure, playable READY media, and the handoff gate. Do not fake READY or merge this with Pixi. |
| UI-04 | P1 / separate task | There is no Parent Web or Guide Console UI; the README in `apps/parent-web` labels the web surface inactive, while the current SRS makes Parent Web and desktop Guide Console required product surfaces. | Create separately approved/scoped UI tasks. Cover responsive Parent child/profile/consent/feedback management and desktop Guide assigned-child/session, observation, and review workflows. Parent Web must not create sessions without a separately approved command contract. Reconcile context and record any web stack decision in an ADR first. |
| UI-05 | P1 | The active app initializes fixed mock children and the Home greeting hard-codes “chị Lan”; there is no sign-in/owner or Guide assignment surface in the active screen map. This reads like an operational account rather than an explicitly labeled fixture demo. | Keep fixture mode visibly identified. For operational flows, bind the adult identity and child list to authenticated/backend-authorized data; add adult sign-in and role-appropriate child selection/assignment entry points. UI role checks are presentation only; backend remains authoritative. |
| UI-06 | Not reproduced | The current Pixel 10 runtime shows the fish and robot story-card artwork; the flat-color image in the preserved screenshot appears stale. | No image fix is proposed from current evidence. Reopen only if it recurs on another supported device. |
| UI-07 | P2 / verify | Story Preview artwork and scene thumbnails look washed out in the default demo state, but the screenshot has no selected drawing. | Compare with a synthetic selected-drawing flow; adjust contrast only if the fade persists in the intended state. |
| UI-08 | Capture tooling gap | Android's React Native Dev Menu opens but has no app-route selector. The 15-screen selector and `?screen=<id>` route are Web-only; Expo Web leaves the root empty. | Approve a capture path: repair the Web root bootstrap or add a dev-build-only native route selector, then capture the ten remaining routes. |
| UI-09 | Development setup blocker | The app initially displayed React Native's missing-bundle screen until Metro/ADB reverse was available and it was relaunched. | Document the supported emulator startup command and port mapping. This does not require a product UI change. |

### Existing alignment to retain

- The profile screen currently uses completed years/months rather than collecting date of birth and
  exposes caregiver participation in the session profile.
- The screen flow has separate Gate A, Gate B, Pixi, off-screen activity, and feedback steps.
- Current activity selection uses the server's topic/age result path; keep safety, age, topic, and
  adult confirmation visible and do not reintroduce readiness/history/material filtering.
- Renderer failure copy must continue to preserve the original drawing and remain distinct from video
  generation state.

## Scope

### In scope after approval

1. Verify Android safe-area and gesture-bar layout across the screen matrix; fix only if a current
   runtime capture reproduces overlap.
2. Make complete activity recommendations visible in the normal selection experience.
3. Make fixed data unmistakably demo-only and define the authenticated adult/linked-child UI handoff.
4. Establish a capture path for the remaining app routes before claiming full visual coverage.
5. Produce and approve separate, dependency-aware follow-up plans for video UI/runtime and the Parent
   Web / Guide Console surfaces; no default person allocation is implied.

### Out of scope

- Backend/provider implementation, new contracts, live model calls, cloud services, credentials,
  real-child content, release/publishing, deployment, and asset-rights changes.
- Implementing Parent Web, Guide Console, or video runtime as an unapproved expansion of this mobile
  task.
- Creating or promoting new product artwork before provenance and visual approval.

## Acceptance criteria

1. Every finding is dispositioned as fixed, accepted with rationale, or linked to a separately named
   approved task; each disposition has feature-local evidence.
2. On the agreed Android device-size matrix, app content, headers, bottom navigation, dialogs, and
   keyboard actions do not overlap status, navigation, or gesture insets; screenshots cover the
   checked screens and states.
3. The activity chooser displays every returned matching activity by default, or implements measured,
   complete pagination; preference ranking never removes a matching topic+age activity.
4. The normal flow does not ask child readiness, completion history, or material availability as
   discovery filters. Activity materials remain preparation information after selection; Gate B keeps
   exact approved identity/version.
5. Pixi exploration and illustrated video are visibly separate. No UI reports video `READY` without
   a current validated artifact and approved script; Parent continuation respects the video/hand-off
   prerequisites once the owning contract exists.
6. Synthetic/mock personas and sample stories/activities are clearly marked as examples. Operational
   screens do not present a hard-coded adult identity or unlinked child as authenticated account data.
7. Parent Web and Guide Console have approved separate scopes, exact user journeys, responsive
   targets, backend authorization boundaries, owners, and any required ADR before their
   implementation begins.
8. Any generated frontend art follows the generated → provenance → visual approval → approved/applied
   asset gate. No new visual art is required by this review itself.
9. All visual and behavior evidence uses synthetic data and is stored in this feature or its owning
   feature; no task is marked complete using only source inspection.

## Work sequence

1. Obtain approval for a specific implementation scope and plan hash.
2. Fix safe areas and verify the existing Android screen matrix.
3. Correct complete-list selection and truthfully label demo content.
4. Recheck artwork on device and repair only a reproducible asset failure.
5. Write separate owner-approved plans for web surfaces and video after their contract/architecture
   dependencies are resolved.
6. Capture feature-local screenshots and run only the gates authorized by the approved plan.

## Risks / dependencies

- Existing device evidence covers onboarding, Home, and the child profile, not every screen. Device
  validation is required before declaring visual acceptance.
- Video and web UI depend on unsettled/versioned backend contracts and architecture decisions. Keep
  these as explicit dependencies instead of showing false capabilities.
- The product notes contain an older “mobile-only” statement alongside later SRS scope closure for
  Parent Web and Guide Console. Record the controlling decision before implementation.

## Verification plan (after approval)

- Inspect synthetic Android screenshots for top/bottom insets, long-form scroll, profile form,
  capture/voice, Gate A, full activity list, Pixi, video-ready/failure states, handoff, and feedback.
- Exercise responsive behavior on the agreed phone sizes and Android API/gesture configurations.
- Verify every recommendation from an API response can be reached; verify empty/no-match and loading
  recovery states without external provider calls.
- Run the exact code/test/security/UI gates named by the eventual approved revision. No tests were run
  as part of this review-only preparation.
