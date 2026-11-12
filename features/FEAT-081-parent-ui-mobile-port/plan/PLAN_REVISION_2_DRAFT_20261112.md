# FEAT-081 Plan Revision 2 — Draft

**Status:** DRAFT / NOT APPROVED / NOT LAUNCHED  
**Revision date:** 2026-11-12  
**Purpose:** Propose the owner's updated mobile application target and source boundary for review.

This draft does not modify or supersede the approved `plan/PLAN.md`, `DECISIONS.md`, or `approvals/TASK_APPROVAL.md`. The current approval remains pinned to Plan Revision 1 and authorizes no implementation until the owner launches the work. This revision takes effect only after its architecture conflict and approval record are resolved through the repository's append-only decision and approval workflow.

## 1. Owner-directed application target

For FEAT-081 and its staged Parent UI follow-on waves, keep the mobile implementation in `apps/ui-mobile`. Do not plan or perform a later move of these screens into `apps/mobile`. Keep `apps/mobile` unchanged and outside this feature's scope.

The owner gave this direction in chat on 2026-11-12. It is an implementation-location direction; it does not change product behavior, API contracts, package manifests, or native configuration by itself.

## 2. Architecture authority and required reconciliation

The canonical working product source remains the unsigned FEAT-063 v2.7-draft Rev60 SRS routed by `docs/context/SRS_AUTHORITY.md`. This plan does not amend the SRS.

The requested target differs from the current SRS and ADR-0020: the SRS names `apps/mobile` as the Parent Android target and `apps/ui-mobile` as a behavior/reference source; ADR-0020 likewise identifies `apps/mobile` as the active implementation target. FEAT-081's existing D-006 and D-008 also describe a later move to `apps/mobile`.

Before this revision can replace the current plan for implementation, record the owner's updated target direction in an append-only decision/ADR and append an approval addendum that pins the adopted plan and resolves the conflicting target statements. Do not silently change the canonical SRS or rewrite the pinned Revision 1 records.

## 3. UI source and porting boundary

Use the sibling `.worktrees/ui` snapshot on `feature/fe-ui-full-remediation` at commit `30c943422637d30465d56b0cf902b3c825f91c8d` as read-only UI feature and interaction reference. Its Parent web application uses React, Vite, and browser-oriented libraries.

Port approved user-facing behavior into native React Native/Expo screens in `apps/ui-mobile`. Do not copy Vite setup, React DOM components, browser-only dependencies, or web CSS into the mobile app. The web reference does not override the FEAT-063 SRS or owner-approved feature requirements. Preserve the generated-asset, provenance, and visual-approval gate for any sample-derived image, avatar, icon, or font.

The source checkout is a pinned local snapshot. If its HEAD changes, stop and re-pin the intended reference before using it.

## 4. Wave 1 source-to-destination map

Paths in the destination column are relative to the mobile worktree `D:\GitHub\Sketch2Life\.worktrees\mobile`. The table mirrors the approved alternative allowlist; it makes no additional file eligible for editing.

| Web UI source or feature | Mobile destination | Mode | Port boundary |
|---|---|---|---|
| P01 home surface in `.worktrees/ui/apps/parent-ui/src/pages/ParentScreens.tsx` | `apps/ui-mobile/src/parent/presentation/screens/HomeScreen.tsx` | E | Port the approved home behavior into the existing native screen. Do not copy the React DOM component. |
| P01 lesson filtering and P02 gallery/detail surface in `.worktrees/ui/apps/parent-ui/src/pages/ParentScreens.tsx` | `apps/ui-mobile/src/parent/presentation/screens/LessonGalleryScreen.tsx` | E | Port the approved gallery and detail behavior into the existing native screen. |
| Filter, sort, and empty-state behavior informed by `.worktrees/ui/apps/parent-ui/src/data/mockParentData.ts` | `apps/ui-mobile/src/parent/presentation/screens/catalogViewModel.ts` and `apps/ui-mobile/tests/catalogViewModel.test.ts` | N | Derive behavior from injected records and test with synthetic fixtures. Recreate the needed fixture shape; do not import web data, browser state, or API calls. |
| `.worktrees/ui/apps/parent-ui/src/components/Icon.tsx`, `Kit.tsx`, `MobileLayout.tsx`, `.worktrees/ui/apps/shared/ui.tsx`, and `.worktrees/ui/apps/parent-ui/src/styles/tokens.css` | No direct source-file destination | R only | Use as behavior/appearance references. Use existing native primitives; do not copy React/Vite components, CSS, phone-frame layout, or assets. Do not edit `apps/ui-mobile/src/parent/presentation/components/ui.tsx`. |
| `.worktrees/ui/apps/shared/backendApi.tsx` | No Wave 1 destination | R only | API wiring is outside Wave 1. Keep `apps/ui-mobile/src/parent/infrastructure/http/ParentApi.ts` byte-identical. |
| Existing mobile `apps/ui-mobile/package.json` and worktree-root `pnpm-lock.yaml` | Same files; no destination change | H | Preserve both byte-for-byte; add no package or dependency. |
| Any source path under `apps/mobile/` | No destination | Outside scope | Leave `apps/mobile/` unchanged. FEAT-081 does not transfer or duplicate screens there. |

## 5. Wave scope

Wave 1 remains limited to P01 home and P02 lesson gallery, using the alternative allowlist already recorded in `approvals/TASK_APPROVAL.md`. This revision changes the intended long-term app location and source boundary; it does not expand Wave 1 to every page in the web reference.

Waves 2–5 remain outline-only and require separate feature plans and approvals. P08c, P14, and P15 remain held until their product requirements are recorded. No API wiring, backend work, package changes, migration, publishing, or Android applicationId repair is included.

## 6. Revised location acceptance criterion

- **AC8 — Stable mobile target:** FEAT-081 Wave 1 and any separately approved Parent UI follow-on wave implement screens only in `apps/ui-mobile`; they do not copy or migrate those screens into `apps/mobile`. The implementation uses React Native/Expo-native components and ports selected UI behavior from the pinned read-only web reference.

Existing Wave 1 acceptance criteria and the exact E/N/H/R file allowlist remain unchanged unless a separately approved revision says otherwise.

## 7. Open gates before launch

1. Resolve the `apps/ui-mobile` versus `apps/mobile` conflict in the current SRS/ADR record as described in section 2. Keep the SRS unchanged unless the owner separately requests an SRS revision.
2. Resolve AC2's test-command ambiguity in an append-only approval addendum. The approved ceiling is two test invocations total, one baseline and one post-implementation, while AC2 names both the full-suite and focused Vitest commands. The owner must select and record a compliant command plan before any test run.
3. Obtain an explicit owner launch instruction for Wave 1. Until then, implementation, tests, typecheck, Android app runs, and later waves remain NOT LAUNCHED.

`OWNER_MODAL_CALL_APPROVED=NO` remains unchanged.
