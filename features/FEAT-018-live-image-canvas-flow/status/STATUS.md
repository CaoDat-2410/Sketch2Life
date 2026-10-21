# FEAT-018 status — subject recall and Pixi main-flow hardening

Status: IN_PROGRESS — approved offline implementation verified; live rig/Pixi visual acceptance pending
Updated: 2026-10-21

## Candidate-stage Gate 3 snapshot — 2026-10-21 (historical)

Person 2 issued `W2_FEAT018_P2_T4_GATE3_HARNESS_DISPOSITION_01`: `HARNESS_INVALID` remains the
repository-wide result, not a pass or waiver, and is outside the P2-T4-specific closure gate. Person 2
then issued `W2_FEAT018_P2_T4_CONTINUATION_AND_FINAL_GATE_SCOPE_01`. Its new candidate Ruff run
with `--no-cache --no-fix --no-fix-only` passed (exit 0, `All checks passed!`); the earlier cache-denied
run is preserved as a separate no-verdict attempt. The other six passing candidate results remain
applicable to unchanged source/config/tools based on HEAD `4310fcbf`.

State: `CANDIDATE_CHECKS_PASS; TASK 4 OPEN; FINAL COMMIT VERIFICATION AND INDEPENDENT REVIEW PENDING`.
The JSON candidate annotation now references `W2_FEAT018_P2_T4_POST_COMMIT_GATE_RECORD_01`; the
final Gate 3 verdict must come from that chat record bound to the full handoff commit SHA. The C/D
amendment permits this candidate synchronization before commit. No stage/commit/push is currently
authorized. Product gaps and FU-01..FU-10 remain OPEN and unassigned, APP hold remains in force, and
Security remains PENDING. See the diagnostics note for commands, provenance and limitations. This
candidate snapshot superseded earlier candidate gate summaries at that time.

## Latest P2-T4 handoff update — 2026-10-21

Person 2 subsequently authorized the handoff commit and push. Commit
`c54b5a5a4a0dfe8f5c494cd47cd9f432e115f61b` (parent
`4310fcbfafa48a14e5fce31f38a2089e24079e52`) is the pushed handoff. The coordinator's post-commit
chat record reports all seven P2-T4 gates passing on that exact commit. A fresh-session Claude review
reports `PASS WITH NOTES` and independently reran the same seven gates in Linux. Person 2 accepts
session-level independence while the same-Claude-model-family limitation remains explicit.

State: `FINAL GATES PASS; REVIEW PASS WITH NOTES; TASK 4 OPEN — OWNER CLOSURE PENDING`.
`HARNESS_INVALID` remains a separate repository-wide result, not a pass or waiver, and outside the
P2-T4 gate set. The earlier “commit/push not authorized” text above is an issuance-time snapshot;
Person 2 accepted the chronology in chat. Product gaps and FU-01..FU-10 remain OPEN and unassigned,
APP hold remains IN FORCE, and Security remains PENDING. See the diagnostics note for gate and review
provenance, dispositions and limitations.

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
- The Modal run is attributed to checkout `5c79741f9e3806626c1dc5c586fe409b2e9370a1`. The diff from
  that checkout to HEAD `54d482d55b570e17b224a3a3506970b0970759f7` contains only governance/evidence
  files and does not change the Task 4 manifest, tests, or runtime source. The current uncommitted
  candidate contains typing-only fixes in the two approved test files. After installing the declared
  `Pillow>=11,<13` dependency (12.3.0) into the ignored local `.venv`, the focused suite passed
  368 tests; the earlier 238 passed / 129 skipped / 1 failed result was the pre-install environment.
- Scoped Ruff 0.16.4 and mypy 1.20.2 pass on the current candidate. Mypy used a per-command cache
  under `%TEMP%`; it first exposed ten typing issues in the approved tests, which were fixed without
  changing test behavior. Architecture, skeleton, and repository security validators pass. The
  repository harness validator remains `HARNESS_INVALID` due to missing evidence paths under FEAT-045,
  FEAT-046, and FEAT-047; those unrelated feature directories were not changed. Exact commands and
  outcomes are recorded in the evidence note.
- The amendment allows acceptance of the diagnostic deliverable while preserving all 60 primary
  and 5 supplemental `UNRESOLVED` results as owner-designated product gaps. All 60 primary rows have
  static hypotheses; 40 also have runtime findings. Of the five supplemental rows, two have static
  hypotheses and four have runtime findings (six finding entries), with one row in both groups. Do not describe every row as a
  separately measured runtime defect. Follow-ups are recorded separately and are not assigned to
  Task 5. No runtime/schema/catalog edits or Lightning/model calls were made.
- The provenance contract-name check is documented with follow-up `P2T4-FU-01`, which remains OPEN;
  the contract-name gap is not resolved. Task 4 is not complete until artifacts are synchronized,
  validation evidence is bound to the final commit, all final gates have valid results and an
  independent reviewer reviews the final handoff commit.
- Person 2 disposition of the independent working-tree review (2026-10-21, recorded in
  `DECISIONS.md`, not in `approvals/TASK_APPROVAL.md` while the APP write hold is in force): the
  typing-only edits in the two approved test files are authorized and limited to call forms and
  types, with no change to test behavior, fixtures, runtime, schema or manifest. `HARNESS_INVALID`
  stays the recorded result and is not a pass; the missing FEAT-045/046/047 evidence paths are a
  separate repository-wide issue outside P2-T4, and those features are not changed under Task 4.
  Security remains PENDING.
- The initial local Claude `PASS WITH NOTES` did not verify the diff, exact file tuples, or all JSON
  rows. A later re-review by the same Claude reviewer checked the prior candidate but did not rerun
  gates and is not independent; the coordinator then applied its findings. Neither review covers the
  current working tree or satisfies the independent final-review gate. The evidence note records
  both reviews, their limits, gate provenance, and remaining blockers.
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
