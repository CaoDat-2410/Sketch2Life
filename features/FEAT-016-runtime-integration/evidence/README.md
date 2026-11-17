# Evidence index

Runtime implementation evidence is stored here and linked to the bounded FEAT-016 scope. Live providers, production API, Android release and real data remain excluded.

## EV-016-01 — Fixture-only runtime integration

- Date: 2026-09-05
- Scope implemented: framework-free session aggregate, versioned transport envelope, local job store, P2/P1 Gate state transitions, identity locking, stale-version rejection, command idempotency and fixture-only E2E tests.
- Command: PYTHONPATH=features/FEAT-016-runtime-integration/src python -m pytest features/FEAT-016-runtime-integration/tests -q -p no:cacheprovider --basetemp=<workspace-temp>
- Result: 7 passed.
- Limitations: no FastAPI deployment, cloud infrastructure, Android release, live provider or real data.

## EV-016-02 — Deep review and regression

- Date: 2026-09-05
- Full command: PYTHONPATH=features/FEAT-015-integration-readiness-review/src;features/FEAT-016-runtime-integration/src python -m pytest features/FEAT-015-integration-readiness-review/tests features/FEAT-016-runtime-integration/tests -q -p no:cacheprovider --basetemp=<workspace-temp>
- Result: 32 passed.
- Static checks: Ruff passed; Python compileall passed; harness, architecture and repository security validators passed.
- Review finding fixed: replaying an already processed command previously assigned the historical snapshot back to the aggregate, allowing state rollback. Replay now returns the prior command result without mutating current state; regression coverage verifies this after state progression.
- Additional contract checks: invalid artifact hash, invalid Gate A confirmation, invalid Gate B identity/version and unsupported transport version are rejected.
- Limitations: no HTTP server, Android device lifecycle, live provider, cloud or real data.

## EV-016-03 — Fixture UI and renderer lifecycle harness

- Date: 2026-09-05
- Scope implemented: Android-facing React Native fixture screen with capture, deterministic P2 AI proposal, Gate A, P1/Gate B identity display, Pixi-style whole-drawing preview, P4 cache/fallback state, activity handoff and feedback completion. The state machine is framework-free and the renderer lifecycle rejects duplicate/out-of-order events.
- Mobile tests: `pnpm --dir apps/mobile exec jest --runInBand`
- Mobile result: 2 suites, 6 tests passed.
- Mobile static checks: `pnpm --dir apps/mobile typecheck`; `pnpm --dir apps/mobile lint` passed.
- Cross-feature regression: PowerShell `$env:PYTHONPATH='features/FEAT-015-integration-readiness-review/src;features/FEAT-016-runtime-integration/src'; python -m pytest features/FEAT-015-integration-readiness-review/tests features/FEAT-016-runtime-integration/tests -q -p no:cacheprovider --basetemp=tmp/test-ui-regression` — 32 passed.
- Governance/security checks: `validate_harness.py --feature features/FEAT-016-runtime-integration`, `validate_architecture.py`, and `validate_repository_security.py` passed.
- Limitations: no Android SDK/device screenshot or APK build was available; the UI harness is fixture-only and intentionally does not call a live provider or reference production visual assets.
- Android bundle composition: from `apps/mobile`, `pnpm exec react-native bundle --platform android --dev false --entry-file index.js --bundle-output ..\tmp\mobile-fixture.bundle --assets-dest ..\tmp\mobile-fixture-assets` completed and emitted `apps/tmp/mobile-fixture.bundle`. Metro reported only workspace cache permission skips and one React Native package exports fallback warning; no application bundle errors remained.
- Environment note: the Metro config now declares pnpm workspace `nodeModulesPaths` and `watchFolders` so the mobile app resolves the locked React Native dependency from the monorepo.
