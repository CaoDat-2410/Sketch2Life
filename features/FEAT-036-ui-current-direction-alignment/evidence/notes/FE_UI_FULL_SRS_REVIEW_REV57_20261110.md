# Whole FE review against FEAT-063 SRS Rev57 — 2026-11-10

## Authority and review method

- Canonical source: `F:/Github/Sketch2Life/features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md`, v2.7-draft Rev57 dated 2026-11-09, SHA-256 `BE0D656966FDE91BA7CD5C914C319EF301D137985EF5CC91B94F36FEBCF61FB5`.
- The SRS is the current working baseline, but remains a draft pending formal owner sign-off. §§1–31 define target requirements; §32 is dated, environment-specific source evidence only.
- The feature worktree copies of `docs/context/SRS_AUTHORITY.md` and `docs/context/SOURCE_REGISTER.md` still point to v2.5-draft. Per the repository's root instructions, this review used Rev57 from the main checkout and records that authority drift without changing the source register.
- Scope: `apps/mobile`, the `apps/ui-mobile` reference client, Parent web (`apps/parent-ui`), Teacher, School Manager, Platform Admin, shared auth/API UI, and the extra `apps/admin-ui` surface.
- Method: static route/state/API-source review plus representative visual review from the existing 37-screen FE portal archive. That archive is synthetic preview evidence captured at commit `c384dcc6705b54005eea5e3ce21ecccf349498d5`, one viewport per route. It is historical for Parent screens changed afterward; current Parent source and Rev14/Rev16 evidence were used for those areas. No live backend or provider was called. No tests or builds were run.
- This is a current-state review, not a claim that every finding was introduced by the latest tablet change. No product code was changed.

## Findings

### SRS-UI-01 — P1: Required Parent Android client is still a fixture shell

`apps/mobile/src/app/AppRoot.tsx:3-8` mounts only `FixtureFlowScreen`; `apps/mobile/README.md:55` describes it as a fixture harness, not a production client. The fuller Parent UI under `apps/ui-mobile` is reference material under FR-P-01, while the branch's full demo is a web app. The target SRS names Parent Android and requires profile, capture/audio, review, job, playback, history, quota, cancellation, and deletion surfaces (§2.3, FR-P-01, §21.5). Parent web must not be treated as a substitute without a product decision.

**Direction:** implement the approved Parent Android client in its own scoped work; keep the deterministic fixture visibly separate from production readiness.

### SRS-UI-02 — P1: Required Teacher run and Sketch Deck flows remain preview-only

`apps/teacher-ui/src/App.tsx:54-56` wraps T04 Sketch Deck, T06 sample Story Run, and T07 presentation confirmation in `ApiOrPreview`. With a real backend session those routes render unavailable-state notices. These are required Teacher web surfaces in FR-T-10–16, FR-T-18–19, and §21.5. The unavailable-state behavior is appropriately fail-closed, but the target workflow cannot be used with the product backend.

**Direction:** finish the versioned Story/Sketch Deck and playback-confirmation contracts before exposing those routes as connected product screens. Do not make preview state look authoritative.

### SRS-UI-03 — P1: School Manager backend UI covers only part of the required organization workflow

`apps/school-manager-ui/src/pages/ManagerScreens.tsx:393-478` loads the assigned organization's classes and creates a class. In backend mode `M02OrganizationManagementPage` returns that page (`:480-488`). The richer local preview contains illustrative slot/quota/billing content but is explicitly marked non-persistent. The connected page does not cover the SRS-required capacity enforcement and downgrade, Teacher assignment, roster administration, billing/invoice/subscription, quota purchase, or notification inbox (§21.5; FR-T-02–03; FR-B-01–09).

**Direction:** connect each required operation to its approved organization-scoped API and keep preview-only billing/capacity values out of authenticated backend mode.

### SRS-UI-04 — P1: Platform Admin content moderation cannot be used in backend mode

`apps/shared/backendApi.tsx:459-464` rejects Platform Admin login because role/permission discovery is unavailable. `apps/platform-admin-ui/src/pages/AdminScreens.tsx:94-109` consequently shows an unavailable state for the moderation queue; A02 only checks `/health` and explicitly lists missing organization, catalog, quota, policy, and audit data (`:53-90`, `:270-280`). The fail-closed behavior respects the SRS rule that Content Admin is a permission of Platform Admin and that child media remains denied (§3, §20, §21.5). The required content moderation/operations surfaces are nevertheless blocked.

**Direction:** add permission-aware role discovery and the approved catalog/operations read models before enabling actions. Keep child-media access denied; this is an integration gap, not evidence of an authorization bypass.

### SRS-UI-05 — P2: Teacher preview lets the user choose the sample child and can fall back outside the class

`apps/teacher-ui/src/pages/T06T07T08Screens.tsx:50-57,121-128` displays a free child dropdown. If the selected class has no active roster entries, `eligible` falls back to all active roster rows. FR-T-10 and FR-PL-20 require the system to select one child from the owner-approved eligible set and Teacher to review/confirm it; exact eligibility and no-eligible behavior remain open under Q-01, but free selection is not open. The route is preview-only today, so this is a misleading demo workflow rather than proof of a backend access leak.

**Direction:** replace the picker/fallback with a single system-selected candidate and explicit review/confirmation; show a no-eligible state without cross-class fallback.

### SRS-UI-06 — P2: Teacher profile rows assert consent without joining the returned purpose/state

`apps/teacher-ui/src/pages/T05ClassesScreen.tsx:99-106,124-129` loads profiles and consents independently with `Promise.allSettled`, then renders every returned profile with a green `Consent effective` chip. Consent rows contain child, purpose, state, and effective fields, but the profile chip is not joined to them; profile rows can also render when the consent request fails. This can imply a purpose-specific grant that the UI has not established. Server authorization remains authoritative; the finding does not claim the UI itself bypasses backend permission checks (§3, FR-T-10, §20).

**Direction:** associate the badge with the exact child and purpose response, or show consent as unknown and avoid asserting access when the consent state is missing.

### SRS-UI-07 — P2: Teacher lesson upload cannot resume after a reload

`apps/teacher-ui/src/pages/TeacherApiImportPage.tsx:36,110-142` stores the upload session and accepted parts only in React component state. The shared client exposes create/part/complete/abort operations (`apps/shared/backendApi.tsx:392-414`) but no authorized session read/list operation. After refresh the browser loses the session reference and selected `File`, so the user cannot resume the durable server session. This misses FR-C-12 and the resume scenarios in AC-29/AT-10.

**Direction:** add an actor-scoped session recovery path and require the user to reselect and hash-check the same file before resuming; do not persist file contents or storage credentials.

### SRS-UI-08 — P2: Parent logout changes UI state without ending the Firebase session

`apps/parent-ui/src/App.tsx:65` replaces Settings with an unavailable screen outside local preview. The only visible Parent logout handler (`apps/parent-ui/src/pages/ParentScreens.tsx:3084-3092`) only calls `setIsAuthenticated(false)` and navigates. It does not call the Firebase bridge's `signOut`; the Parent context can obtain the same token again on reload (`ParentContext.tsx:205-230`). A signed-in user therefore has no working logout path in backend mode, and the preview action is only a local state change (FR-C-01).

**Direction:** keep logout available independently of settings APIs and await the Firebase bridge sign-out before clearing the route state.

### SRS-UI-09 — P2: School Manager notification control is inert and its unread marker is unconditional

`apps/school-manager-ui/src/components/ManagerLayout.tsx:86-89` renders a notification button without an action and an unconditional dot. The Manager screen catalog requires an inbox (§21.5; FR-B-08–09). Platform Admin has the same inert shell control, but the Manager inbox is the explicit SRS requirement.

**Direction:** connect the control to an organization-scoped inbox and derive unread state from data, or remove the affordance until that surface exists.

### SRS-UI-10 — P3: Parent UI README still documents the superseded age range

`apps/parent-ui/README.md:15` says 24–155 months while the current SRS BR-18/FR-PL-25 requires 36–120 months and the current UI/context validation already uses 36–120. Correct the README so it cannot be mistaken for an active contract.

## Confirmed alignment and scope caveats

- The current Parent web code now shows preset activities after video and has no pre-video activity-selection route (`ParentScreens.tsx:617`; compare FR-P-05). The former UIR-01 finding is closed in current source.
- Parent profile validation is 36–120 months; the activity-completion controls and BGM controls from the prior review are absent. The current refresh guard starts signed out and validates the Firebase token plus Parent API access before restoring a protected route. The remaining logout finding above is separate.
- `apps/ui-mobile` still contains its older Pixi and activity-first reference flows. FR-P-01 designates it as a reference client and §2.2 excludes Pixi; do not use it as the current Parent target or ship those flows as the SRS implementation.
- Parent registration behavior and Parent Web as a supported target are not established by the current SRS. The requested registration page is clearly visual-only; do not infer account creation approval from its presence. Parent no-preset activity catalog policy and Teacher child eligibility details remain open; preserve them as open questions.
- The 37-screen archive demonstrates local synthetic previews only, not authenticated production behavior. It predates recent Parent fixes and cannot validate current Parent screens; current Parent responsive screenshots in FEAT-036-EV-009 are separate local evidence.

## Review disposition

The current branch has useful, clearly labeled local preview UI and several Parent corrections now align with Rev57. It is not yet a complete SRS client set: the required Android Parent app remains fixture-only, Teacher run/Deck flows are disconnected in backend mode, School Manager and Platform Admin have substantial backend-screen gaps, and the specific Teacher/Parent issues above remain. No source fixes, tests, builds, backend calls, approvals, deployment, commit, or push were performed in this review.
