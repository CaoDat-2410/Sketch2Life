# FEAT-081 — Parent UI mobile first-wave plan

- Status: APPROVED
- Plan revision: 1
- Implementation status: NOT_LAUNCHED
- Owner: Person 2 (AnhKhoaa157)
- Baseline: feature/fe-mobile-remediation at 1f5bb0b5b1ab501a7120598a7e6e0de75217ddb3; its tree matches local origin/dev.

## Objective

Port the approved first-wave P01/P02 Parent home and lesson-gallery presentation behavior into apps/ui-mobile. Extract pure catalog view-model logic and cover it with Vitest synthetic fixtures. Keep the work offline and presentation-focused, and preserve the existing API and workflow boundaries.

## Authority and context

The current product baseline is the unsigned FEAT-063 v2.7-draft SRS identified by docs/context/SRS_AUTHORITY.md and docs/context/SOURCE_REGISTER.md. It defines Parent behavior and target architecture; it remains a draft, not formal SRS sign-off. Do not import requirements from historical feature records or the sibling web sample. Record any missing or conflicting requirement as open.

The target is apps/ui-mobile on Expo SDK 52, React Native 0.76.9, and React 18.3.1. The sibling .worktrees/ui checkout at feature/fe-ui-full-remediation / 30c94342 is external read-only reference material. The first wave uses synthetic records only and does not call APIs. No Modal action is authorized (OWNER_MODAL_CALL_APPROVED=NO).

## Scope

Wave 1 is P01/P02 only:

- Add a pure TypeScript catalog view-model module for filter, sort, and empty-state derivation from injected records.
- Add Vitest tests using synthetic fixtures only.
- Edit only HomeScreen.tsx and LessonGalleryScreen.tsx among existing app files, integrating the view model.
- Use the alternative allowlist in approvals/TASK_APPROVAL.md. Do not edit components/ui.tsx.
- Preserve package.json, pnpm-lock.yaml, ParentApi.ts, controller, workflow types, authentication, navigation, native configuration, and assets byte-for-byte.

The exact approved E/N/H/R file pins are in approvals/TASK_APPROVAL.md. No file outside that allowlist may be changed.

## Non-scope

- No backend/API/client, controller, workflow type, authentication, navigation, native config, package manifest, lockfile, asset, shared components/ui.tsx, or apps/mobile change.
- No sample image, avatar, icon, font, CSS, or web component copy. Any future visual asset must pass the generated/provenance/visual approval gate first.
- Waves 2-5 are outline only and require separate feature approval before implementation. P08c, P14, and P15 remain held until a product requirement is recorded.
- No Android applicationId / validate_skeleton CI repair, backend-route wiring, package installation, publishing, or runtime/provider operation.

## Wave outline

1. **Wave 1 — P01/P02 home and lesson gallery (detailed, approved but not launched).** Implement only the approved alternative allowlist. Derive catalog filter/sort/empty states in a pure function module with synthetic-only tests. Do not edit shared components/ui.tsx or connect to an API.
2. **Wave 2 — P03/P04 drawing guide and subject confirmation (outline only).** Consider a native guide-step presentation and keep media picking/normalization behind application ports. Requires a separate approval and contract review.
3. **Wave 3 — P05-P08 idea/transcript/story/video flow (outline only).** Consider audio-recorder and external-browser ports, adult transcript/script review, job states, and playback gated on safety-approved VIDEO_READY. Requires separate approvals and backend-contract coordination.
4. **Wave 4 — P08b/P09/P10 activities, history, and profiles (outline only).** Place activities after playable video, preserve history rules, and resolve profile lifecycle contracts. Do not add completion toggles. Requires a separate approval.
5. **Wave 5 — P11-P13 auth, quota, and settings (outline only).** Keep auth behind ports, quota read-only until billing decisions, and settings within approved policies. P08c, P14, and P15 remain held. Requires a separate approval.

## Acceptance criteria

- **AC1:** catalogViewModel.ts is a pure function module deriving filter, sort, and empty-state results from injected records. It uses no network, browser, or Expo globals.
- **AC2:** tests/catalogViewModel.test.ts uses Vitest and synthetic fixtures only, makes no network access, and passes offline through both pnpm run test and pnpm exec vitest run tests/catalogViewModel.test.ts.
- **AC3:** HomeScreen.tsx and LessonGalleryScreen.tsx use the view model. There is no change to the API client, controller, workflow types, authentication, navigation, native configuration, assets, or components/ui.tsx.
- **AC4:** apps/ui-mobile/package.json and pnpm-lock.yaml remain byte-identical to the approved baseline pins.
- **AC5:** pnpm run typecheck introduces no new diagnostic compared with the pre-edit baseline.
- **AC6:** The harness, repository-security, and architecture validators pass after implementation. On dev, validate_skeleton.py has the known applicationId failure; report it without fixing it in this feature.
- **AC7:** The owner-run Android manual checklist covers initial, filtered, and empty states; active-child label; detail and back; text wrapping and scrolling; Android back behavior; accessibility labels and touch targets. Use synthetic data only; tests make no network access.

## Command ceilings and execution boundaries

- Vitest / pnpm test: at most 2 invocations total, one baseline before app edits and one post-implementation.
- pnpm run typecheck: at most 2 invocations total, one baseline before app edits and one post-implementation.
- Each of validate_harness.py, validate_repository_security.py, and validate_architecture.py: at most 2 invocations.
- git diff --check: at most 2 invocations.
- No Codex command may require network access, package installation, Gradle, adb, or an emulator.
- Test and Android runs are owner/coordinator-run outside the Codex sandbox. The sandbox stalled on an unrelated pytest TestClient run today; Codex must not run long test commands unless the owner explicitly says so.

## Risks and merge coordination

D-002 authorizes the owner to edit the Parent UI without per-file reservations. CaoDat may later edit these same files on dev, so the merge risk is acknowledged: reconcile and review overlapping changes before merging. The git history is not an in-flight ownership tracker.

## Implementation status

APPROVED / NOT LAUNCHED. This plan records a bounded Wave 1 allowlist approval only. No implementation has started. Launching implementation, owner-run Vitest and Android checks, every later wave, and the move to apps/mobile are separate gates.