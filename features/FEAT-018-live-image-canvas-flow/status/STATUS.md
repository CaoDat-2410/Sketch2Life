# FEAT-018 status — subject recall and Pixi main-flow hardening

Status: IN_PROGRESS — approved offline implementation verified; live rig/Pixi visual acceptance pending
Updated: 2026-10-21

## P2-T4 diagnostic acceptance rebase — 2026-10-21

- State: `DIAGNOSTIC RUN COMPLETE; TASK 4 OPEN — FINAL GATES AND INDEPENDENT REVIEW PENDING`.
- Person 2 approved Revision 3 at source commit `b39a9f2f56509b0543184876eb538fc9faf0e1aa`.
  The 2026-10-21 acceptance rebase is also recorded in `approvals/TASK_APPROVAL.md`.
- The synthetic manifest has 120 primary and 43 separately counted supplemental cases. The initial
  local preflight lacked `Pillow>=11,<13`; the later owner-run Modal Notebook focused suite completed
  with 368 passed and one Pydantic deprecation warning. The regenerated report records B1/B2/B3
  COMPLETE for all 120 primary cases and all 43 supplemental cases COMPLETE. Requirements remain
  60 primary UNRESOLVED, 5 supplemental UNRESOLVED and 10 supplemental EXPECTED_BLOCKED; see the
  sanitized metrics report for row-level evidence.
- Scoped Ruff 0.16.4 passed. Local mypy 1.20.2 still terminates with `INTERNAL ERROR`; the default
  cache reports `OperationalError: unable to open database file`, and a separate ignored cache path
  reports `PermissionError: [WinError 5]`. Neither constitutes a type-check result. The latest
  focused test result and current final gate results are recorded in the evidence note below. Do not
  count mypy `INTERNAL ERROR` as a pass.
- Architecture, repository security, and skeleton validators pass. The repository harness validator
  remains `HARNESS_INVALID` due to missing evidence paths under FEAT-045, FEAT-046, and FEAT-047;
  those unrelated feature directories were not changed.
- The amendment allows acceptance of the diagnostic deliverable while preserving all 60 primary
  and 5 supplemental `UNRESOLVED` results as product gaps. Follow-ups are recorded separately and
  are not assigned to Task 5. No runtime/schema/catalog edits or Lightning/model calls were made.
- The provenance contract-name check is documented with a follow-up. Task 4 is not complete until
  all final gates have valid results and an independent reviewer reviews the final handoff state.
- Plans: `plan/P2_T4_MAPPING_DIAGNOSTICS_PLAN_DRAFT_20261020.md` and
  `plan/P2_T4_MAPPING_INPUT_REVIEW_DRAFT_20261020.md`. Evidence:
  `evidence/notes/P2_T4_MAPPING_DIAGNOSTICS_20261020.md` and
  `evidence/metrics/P2_T4_MAPPING_DIAGNOSTICS_20261020.json`.

## Supported-age amendment — 2026-10-06

- Current supported product age is `<9` / 0–107 completed months. Mobile selection and supervised-flow/P1 application services reject ages from 108 months onward before selection, Gate B media resolution, or renderer localization. Existing versioned DTOs continue to accept historical/catalog values.
- Source catalog bands 9–12 remain unchanged; they are not requested by supported sessions.
- The cross-feature change is approved and tracked under FEAT-037. Automated checks were not run for this amendment.

## FEAT-035 integration follow-up — 2026-10-03

- Added an additive subject-only Pixi show contract/runtime path for the reviewed empty-companion
  case; legacy V1/V2 contracts remain intact, the original source remains available, and essential
  rig/subject failure does not downgrade to PIXI_V2. No asset approval or rights gate was changed.
- Renderer contract tests (58), renderer typecheck, mobile tests (22), and mobile typecheck pass;
  complete backend suite passed before final focused Pixi typing refinements. No live drawing or
  provider result was used, so visual playback acceptance remains pending.
- Cross-feature evidence: `../../FEAT-035-branch-review-remediation/evidence/notes/implementation-progress-20261003.md`.

- Approved plan: `plan/SUBJECT_RECALL_AND_PIXI_MAIN_FLOW_HARDENING_PLAN_20260930.md`.
- Approved plan SHA-256 remains
  `6EF237C0117AED6C8A4B513D69F084131FAB5E8B5C6C29DB2157E6607D92F65F`.
- Subject recovery now retains unknown valid labels, prioritizes reviewed whole-animal claims over
  part labels, supports adult edit/add, exposes one explicit shared-budget re-query, and permits
  adult-confirmed continuation with versioned provenance and no fabricated AI claim ID.
- Pixi now keeps preparation visible until actual playback data arrives, applies finite
  handshake/preparation/startup/playback watchdogs, forwards typed terminal playback failure for
  legacy and V2 renderer commands, and destroys player resources idempotently on failure/exit. The
  audit also fixed a preparation-failure spinner that never ended and a late-preparation path that
  failed to advance the session version. Original-source preservation and no-auto-fallback policy
  remain unchanged.
- Focused checks: backend subject/re-query/Gate-A/P1/renderer-contract tests 100 passed; renderer
  tests 48 passed;
  renderer TypeScript check/build passed; mobile UI-copy/recovery validation and TypeScript check
  passed; backend Ruff lint passed; repository security validation passed; `git diff --check` passed.
- Android connectivity evidence: `emulator-5554` is connected, ADB reverse `tcp:8081 -> tcp:8081`
  is active, Metro `/status` returns `packager-status:running`, and Expo's Android virtual-entry
  bundle returns HTTP 200 (7,900,918 bytes). A bare `/index.bundle` is not this Expo app's entry
  route and returns 404; this was not a Metro failure.
- No recent matching Pixi/React Native fatal error was found in the bounded logcat sample. The
  emulator was not foregrounded into a new Pixi launch; actual rig/mask playback requires the
  backend result path and remains operator-run. No Qwen/SAM/provider request or image was used.
- Ruff formatting check is not a clean repository gate for these already-dirty files: the same
  files fail formatting on `HEAD`. `ruff check` passes; broad formatting was intentionally avoided
  to prevent unrelated diffs.
- `tools/validate_harness.py` is currently blocked by missing pre-existing evidence directories in
  FEAT-026 (`evidence/raw`, `evidence/metrics`) and FEAT-033 (`evidence/raw`, `evidence/screenshots`);
  those unrelated feature folders were not changed. `tools/validate_architecture.py` and
  `tools/validate_repository_security.py` pass; security scanned 1,742 publishable files.
- Evidence: `evidence/notes/SUBJECT_RECALL_AND_PIXI_MAIN_FLOW_HARDENING_IMPLEMENTATION_20260930.md`.
- Follow-up to `MASK_BACKGROUND_RECONSTRUCTION_FAILED`: backend source/package/four-mask reads
  returned HTTP 200, while synthetic reproduction isolated the defect to a saturated outline beyond
  the local donor radius. FEAT-030 now seeds only masked-pixel reconstruction from credible
  same-image paper when local donors are absent. Renderer tests (49), typecheck/build, mobile
  typecheck/UI-copy checks pass; backend serves the rebuilt renderer assets with HTTP 200. Fresh
  Android visual playback remains unverified because `adb` is unavailable in this shell. Evidence:
  `evidence/notes/PIXI_RENDERER_DIAGNOSTIC_PARTIAL_20260930.md` and FEAT-030 `E-030-FIX-014`.
- 2026-10-06: Product age boundary aligned to under 9 / 0–107 completed months in mobile input and FEAT-018 application guards. Existing versioned DTOs remain able to represent historical 9–12 catalog/session records; age-sensitive session progression is rejected before selection, Gate B media resolution, or renderer localization. Automated checks were not run for this amendment.
