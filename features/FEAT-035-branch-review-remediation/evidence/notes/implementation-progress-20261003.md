# FEAT-035 implementation progress — 2026-10-03

- Evidence ID: FEAT-035-EV-002
- Related: C-01, H-01..H-05, H-06, M-01, M-08, M-09, M-10, L-05, L-09, L-14
- Type: offline implementation, synthetic tests, static checks, local build configuration validation
- Branch/baseline: `codex/pixi-ai-show-20261001`, unchanged HEAD `7a65890`; changes are uncommitted.
- Provider/model calls: none. No user/child media, credentials, live services, or asset promotion used.

## Implemented in this work package

1. **Pixi subject-only show (C-01/M-02 partial).** Added ADR-0013 plus additive planner request V2, show plan V2, renderer envelope V3, and renderer command V5. A valid source-subject plan can contain zero companion assets; each beat still targets the source subject, source/rig/behavior validation remains required, V1/V2 are unchanged, and the flow does not silently fall back to PIXI_V2. Empty asset reads remain valid only for an empty selected-asset plan. The composed backend default now points to `/v3/pixi/show-plan` (a stale V2 setting was found and corrected); a settings regression test protects this wiring. Covered by `backend/tests/unit/test_pixi_show_planner.py`, `backend/tests/unit/test_pixi_show_assets.py`, `backend/tests/unit/test_settings_security.py`, and renderer `tests/pixiShowContracts.test.ts`.
2. **Subject labels (H-06).** Whole-token alias matching handles Vietnamese labels including cà rốt, hóa thạch, con gà, ô tô, chim, and bướm; conflicting alias claims resolve to `UNKNOWN` rather than substring misclassification. Covered by planner unit tests.
3. **Image preflight (H-04 partial).** Mobile permits up to 16 MP with a 6,000-pixel edge before bounded normalization; downstream backend output/decode limits are unchanged. Regression coverage accepts 4032×3024 and 5000×3000, rejects 6000×4000 and 5000×3500. This is not a measurement of peak memory, EXIF orientation handling, or an Android-device decode run.
4. **Session contention/event loop (H-01/H-02 partial).** Added a weak per-session lock pool, replaced global locks in the two workflow services, and moved synchronous upload admission/service work off the ASGI loop. Different sessions no longer serialize behind one global lock. Same-session workflow operations still hold their lock across provider/GPU work; there is no stale-version fencing or slow-provider health-latency benchmark yet.
5. **ASR transport mapping (H-03 partial).** Direct connection reset/OS transport errors map to a typed retryable response for an explicit user retry; no automatic retry is issued. Adapter unit tests use a fake transport.
6. **Idempotency expiry (M-01 partial).** Added deletion of every receipt scoped to the expired session without matching similarly prefixed session IDs; covered by storage and session HTTP tests.
7. **Android/mobile quality (H-05/M-08/M-10 partial).** Added the Expo AV permission disclosure and Android `RECORD_AUDIO`, removed the incorrect picker microphone setting, wired mobile Vitest into the default package test command, added fail-closed release signing properties (no debug-key release signing), aligned SDK defaults to the recorded ADR baseline, and taught the skeleton validator to inspect `apps/ui-mobile`.
8. **Small security/reliability checks (L-09/L-14).** Lightning development auth comparison uses `hmac.compare_digest`; production application-service `assert` statements in the touched scope were replaced with explicit invariant/error paths.

## Verification run

Commands were run from the repository root on Windows PowerShell. Pytest used a local temporary base directory under the ignored backend venv because the default user Temp path returned `PermissionError`.

| Check | Command / result |
|---|---|
| Changed Python Ruff | `backend/.venv/Scripts/python.exe -m ruff check` on changed Python files — `All checks passed!` |
| Full backend suite | PowerShell: `$env:PYTHONPATH = 'backend/src;vendor/sam2'`; `backend/.venv/Scripts/python.exe -m pytest backend/tests --basetemp <backend/.venv temp> -q --tb=short -p no:cacheprovider -rA` — reached `[100%]`, process exit 0, no failures. Six skips were explicit: one live-AI E2E requires `SKETCH2LIFE_RUN_REAL_AI_E2E=1`; five Phase-B input cases are covered by an attempt-zero row. Pillow emitted deprecation warnings in an existing mask test. |
| Mobile tests | `pnpm --filter sketch2life-mobile test` — 2 files, 22 passed; UI validator printed `UI_COPY_AND_RECOVERY_VALID`. |
| Mobile TypeScript | `pnpm --filter sketch2life-mobile exec tsc --noEmit --pretty false` — exit 0. |
| Renderer TypeScript | `pnpm --filter @sketch2life/art-renderer typecheck` — exit 0. |
| Renderer tests | `pnpm --filter @sketch2life/art-renderer test` — 13 files, 58 passed. |
| Security | `python tools/validate_repository_security.py` — `REPOSITORY_SECURITY_VALID`, 1,911 publishable files scanned; secrets, environment files, seed data, external originals, and absolute machine paths absent. |
| Architecture | `python tools/validate_architecture.py` — `ARCHITECTURE_VALID`; dependency direction, mobile isolation, asset gate, mobile AI boundary, and Firebase data-product prohibition pass. |
| Skeleton | `python tools/validate_skeleton.py` — `SKELETON_VALID`; inspected active `apps/ui-mobile`, reported min 29 / target 36 / compile 37 and Firebase Auth only. |
| Harness | Initial run reproduced FEAT-026/033/034 missing evidence locations. Added README-only location notes in the three owning features, explicitly stating no evidence was added. Final `python tools/validate_harness.py` — `HARNESS_VALID`; FEAT-026 SRS artifact and all existing feature evidence were preserved. |
| Strict mypy | Baseline archive of `HEAD` run with the same local interpreter/config: 149 errors in 15 files (182 source files). Current tree after this work: 139 errors in 13 files (183 source files), exit 1. This is still a failing gate, although current total is 10 lower than the measured baseline. Remaining errors include Pydantic/camel-alias typing, catalog parsing types, missing optional AI package stubs, and workflow/provider strictness; remaining current errors are not all FEAT-035-owned. |
| Diff whitespace | `git diff --check` — no errors. |

## Remaining gates and accurate disposition

- The code/test result does not prove a real drawing yields a correct subject-only animation or acceptable masks. No image/provider invocation was made.
- After the full-suite run, final typing/config refinements were rechecked with the Pixi planner/catalog/settings/session/idempotency focused tests (all passed), changed-file Ruff (passed), and `git diff --check` (passed).
- Same-session backend locks still span slow operations; version fencing, race/stale-write tests, GPU semaphore bounds, and latency measurements remain open.
- Image memory/time/EXIF profile acceptance remains unmeasured; the 16 MP mobile admission budget is only a bounded preflight change.
- Android SDK/Gradle/ADB were unavailable in this task environment; generated/merged manifest, actual permission denial UX, release signing, emulator launch, Metro connectivity, and Android playback were not verified. `expo config` resolution alone is not merged-manifest evidence.
- Firebase token verification and identity-to-owner authorization remain unimplemented. Deployment configuration cannot be substituted for this security boundary.
- Docker/wheel resource-root and `/renderer` installed-package smoke remain open.
- Harness now validates all feature paths; the empty README-only evidence locations are structural placeholders, not test evidence. All unresolved finding IDs must still be dispositioned before FEAT-035 can complete.
- No commit, push, restart, deployment, production credential change, asset rights change, or asset promotion was performed.

## Approval-integrity stop

A final governance check found the current `plan/PLAN.md` raw SHA-256 is
`DCA28C79763AF55C6CC083CD500F19655EEB760D4206928E8334DEE5DEE94A1E`; `approvals/TASK_APPROVAL.md`
records `ACCD6B6D7B0645CC334CB7AE7350765C2075A482EA431C780189B909FFA26229`. The current file is LF
text; LF normalization, CRLF, CR-only, and UTF-8 BOM hash checks did not produce the recorded value.
The plan and approval files were not changed to mask the discrepancy. Further implementation is
paused until the owner approves the exact current contents/hash or provides the previously approved
plan copy. Existing code/test changes and results above remain uncommitted and unchanged.
