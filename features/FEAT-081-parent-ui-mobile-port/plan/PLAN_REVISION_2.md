# FEAT-081 Plan Revision 2 — mobile UI target and P01/P02 port

- Revision date: 2026-11-12
- Status: FINAL; approved by the append-only Revision 2 addendum in approvals/TASK_APPROVAL.md.
- Implementation status: NOT_LAUNCHED.
- Owner: Person 2 (AnhKhoaa157).
- Baseline: feature/fe-mobile-remediation at 1f5bb0b5b1ab501a7120598a7e6e0de75217ddb3; HEAD tree matches local origin/dev.

## 1. Objective and revision control

Implement the approved P01/P02 Parent home and lesson-gallery behavior in apps/ui-mobile using a pure catalog view model and synthetic Vitest tests.

This final Revision 2 preserves the original pinned plan/PLAN.md and the original approval entry. After the Revision 2 approval addendum is appended, this plan controls the FEAT-081 app location, source boundary, and AC2 command policy. It does not authorize launch. The original Revision 1 records remain intact as history.

## 2. Target and architecture reconciliation

For FEAT-081 Wave 1 and any separately approved FEAT-081 Parent UI follow-on wave, the implementation location is apps/ui-mobile. Do not move or duplicate these feature waves into apps/mobile. apps/mobile remains unchanged and outside this feature.

This is a feature-scoped implementation-location exception recorded by ADR-0023 and D-009. The canonical FEAT-063 v2.7-draft Rev60 SRS remains unsigned and unchanged. Its §7.2 FR-P-01 and §9.3 describe apps/mobile as the broader Parent Android product target and apps/ui-mobile as the behavior/reference app. ADR-0020 (accepted within FEAT-062 scope) and ADR-0021 (proposed) likewise identify apps/mobile as the broader Parent target. This plan and ADR-0023 do not amend the SRS, claim a global target change, or claim that apps/ui-mobile is now the production Parent target. The owner-directed location decision applies only to FEAT-081 and its separately approved follow-on UI waves. A product-wide or production-target change requires a separate owner decision and SRS/ADR revision.

## 3. Read-only web reference and port boundary

Use the sibling .worktrees/ui snapshot on branch feature/fe-ui-full-remediation at commit 30c943422637d30465d56b0cf902b3c825f91c8d as read-only React/Vite UI behavior reference. If that checkout's HEAD changes, stop and re-pin the intended reference before use.

Do not copy React DOM, CSS, image/avatar/icon/font assets, web API code, or packages. Do not copy Vite configuration or browser-only dependencies. Use the existing native app boundary and synthetic fixtures. Any sample-derived visual asset remains subject to the repository's generated-asset, provenance, and visual-approval gate.

### Wave 1 source-to-destination table

Paths in the destination column are relative to the mobile worktree. The table matches the already approved alternative allowlist and grants no additional edit path.

| Web UI source or feature | Mobile destination | Mode | Port boundary |
|---|---|---|---|
| P01 home surface in .worktrees/ui/apps/parent-ui/src/pages/ParentScreens.tsx | apps/ui-mobile/src/parent/presentation/screens/HomeScreen.tsx | E | Port approved home behavior into the existing native screen. Do not copy the React DOM component. |
| P01 lesson filtering and P02 gallery/detail surface in .worktrees/ui/apps/parent-ui/src/pages/ParentScreens.tsx | apps/ui-mobile/src/parent/presentation/screens/LessonGalleryScreen.tsx | E | Port approved gallery and detail behavior into the existing native screen. |
| Filter, sort, and empty-state behavior informed by .worktrees/ui/apps/parent-ui/src/data/mockParentData.ts | apps/ui-mobile/src/parent/presentation/screens/catalogViewModel.ts and apps/ui-mobile/tests/catalogViewModel.test.ts | N | Derive behavior from injected records and test with synthetic fixtures. Recreate required fixture shape; do not import web data, browser state, or API calls. |
| .worktrees/ui/apps/parent-ui/src/components/Icon.tsx, Kit.tsx, MobileLayout.tsx, .worktrees/ui/apps/shared/ui.tsx, and .worktrees/ui/apps/parent-ui/src/styles/tokens.css | No direct source-file destination | R only | Read-only behavior/appearance references. Use existing native primitives; do not copy React/Vite components, CSS, phone-frame layout, or assets. Do not edit apps/ui-mobile/src/parent/presentation/components/ui.tsx. |
| .worktrees/ui/apps/shared/backendApi.tsx | No Wave 1 destination | R only | API wiring is out of scope. Keep apps/ui-mobile/src/parent/infrastructure/http/ParentApi.ts byte-identical. |
| Existing apps/ui-mobile/package.json and worktree-root pnpm-lock.yaml | Same files; no destination change | H | Preserve both byte-for-byte; add no package or dependency. |
| Any source path under apps/mobile/ | No destination | Outside scope | Leave apps/mobile unchanged. FEAT-081 does not transfer or duplicate screens there. |

## 4. Wave scope

Wave 1 is limited to P01 home and P02 lesson gallery using the alternative allowlist already recorded in approvals/TASK_APPROVAL.md. It edits only HomeScreen.tsx and LessonGalleryScreen.tsx among existing app files, adds catalogViewModel.ts and catalogViewModel.test.ts, and preserves all H-mode files byte-for-byte. Shared components/ui.tsx is not edited.

Waves 2-5 remain outline-only and require separate plans and approvals. P08c, P14, and P15 remain on hold until their product requirements are recorded. No API wiring, backend work, package changes, migration, publishing, or Android applicationId repair is included.

## 5. Acceptance criteria

- **AC1:** catalogViewModel.ts is a pure function module deriving filter, sort, and empty-state results from injected records. It uses no network, browser, or Expo globals.
- **AC2:** tests/catalogViewModel.test.ts uses Vitest with synthetic fixtures only and makes no network access. It passes as part of the full suite run with pnpm run test after implementation. The focused command pnpm exec vitest run tests/catalogViewModel.test.ts is optional diagnostic guidance, not a required acceptance command or an additional invocation. The full-suite script runs vitest run tests and then node scripts/validate-ui-copy.mjs, so the post-implementation full-suite run includes the catalog test and the existing UI-copy validation script.
- **AC3:** HomeScreen.tsx and LessonGalleryScreen.tsx use the view model. There is no change to the API client, controller, workflow types, authentication, navigation, native configuration, assets, or components/ui.tsx.
- **AC4:** apps/ui-mobile/package.json and pnpm-lock.yaml remain byte-identical to the approved baseline pins.
- **AC5:** pnpm run typecheck introduces no new diagnostic compared with its pre-edit baseline.
- **AC6:** The harness, repository-security, and architecture validators pass after implementation. On dev, validate_skeleton.py has the known applicationId failure; report it without fixing it in this feature.
- **AC7:** The owner/coordinator-run Android manual checklist covers initial, filtered, and empty states; active-child label; detail and back; text wrapping and scrolling; Android back behavior; accessibility labels and touch targets. Use synthetic data only; tests make no network access.
- **AC8:** FEAT-081 Wave 1 and any separately approved FEAT-081 Parent UI follow-on wave use apps/ui-mobile as their implementation location and do not move or duplicate those feature screens into apps/mobile. This feature-scoped location decision does not amend the SRS product target.

## 6. Command ceilings and execution boundaries

- Test ceiling: exactly two required pnpm run test full-suite invocations total: one pre-edit baseline and one post-implementation. The baseline establishes existing-suite state; the post-implementation run includes catalogViewModel.test.ts and the UI-copy validation script.
- The focused single-file Vitest command is optional diagnostic guidance, not a required or additional invocation. Do not add it to the two-run sequence. Any later owner-directed focused invocation counts against the same two-invocation ceiling unless the owner separately approves a changed budget.
- pnpm run typecheck: at most 2 invocations total, baseline before app edits and post-implementation.
- Each of validate_harness.py, validate_repository_security.py, and validate_architecture.py: at most 2 invocations. The prior pre-launch governance check used one invocation of each; one post-implementation invocation remains.
- git diff --check: at most 2 invocations. The prior pre-launch governance check used one invocation; one post-implementation invocation remains.
- No Codex command may require network access, package installation, Gradle, adb, or an emulator.
- Test and Android runs are owner/coordinator-run outside the Codex sandbox. The sandbox stalled on an unrelated pytest TestClient run; Codex must not run long test commands unless the owner explicitly says so.

## 7. Risks and merge coordination

D-002 authorizes the owner to edit the Parent UI without per-file reservations. CaoDat may later edit the same paths on dev; overlapping edits carry merge risk and must be reconciled before merging. Git history does not establish in-flight ownership.

## 8. Implementation status and launch gate

APPROVED / NOT LAUNCHED. This plan records the target, source boundary, and bounded Wave 1 acceptance criteria only. It authorizes no implementation. Wave 1 requires a separate explicit owner launch instruction. Android work, tests, each later wave, and any move or product-target change remain separate gates.