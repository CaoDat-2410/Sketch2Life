# FEAT-018 status — subject recall and Pixi main-flow hardening

Status: IN_PROGRESS — approved offline implementation verified; live rig/Pixi visual acceptance pending
Updated: 2026-09-30

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
