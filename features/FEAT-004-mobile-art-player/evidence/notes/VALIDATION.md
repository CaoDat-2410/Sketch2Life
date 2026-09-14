# Person 3 POC validation

- Timestamp: 2026-08-26
- Branch: `plan/person-3-art-animation-poc`
- Fixture data: synthetic SVG and JSON plans under `packages/art-renderer/fixtures/butterfly/`; no child data.

## Commands and results

| Command | Result | Interpretation |
|---|---|---|
| `corepack pnpm --filter @sketch2life/art-renderer typecheck` | passed | Closed contracts and browser renderer compile under TypeScript strict mode. |
| `corepack pnpm --filter @sketch2life/art-renderer test` | passed: 6 tests | Validates butterfly flow, provenance propagation, Motion DSL rejection cases, fallback preservation, and benchmark sample shape. |
| `corepack pnpm --filter @sketch2life/art-renderer build:demo` | passed | Vite bundled the standalone browser deliverable successfully. |
| `corepack pnpm --filter @sketch2life/mobile typecheck` | passed | Renderer changes do not break the mobile TypeScript skeleton. |
| `corepack pnpm --filter @sketch2life/mobile test` | passed: 2 tests | Existing bridge-protocol behavior remains intact. |

## Limitation

The repository root scripts invoke `pnpm` directly. In this execution environment only `corepack pnpm` is available on PATH, so root `pnpm typecheck` and `pnpm test` cannot invoke their recursive child command. The equivalent package-level checks above passed. `build:demo` output was removed after validation; no generated build artifact is retained in source control.

Browser FPS and optional heap data are emitted by the player during fixture playback. This POC build verification is not a physical Android WebView performance measurement; that must be repeated in the Integration Sprint on the agreed device matrix.

## Final pre-push audit

- Re-ran all package checks after the final demo change: renderer typecheck passed, renderer fixture suite passed (6/6), demo build passed, mobile typecheck passed, and mobile Jest suite passed (2/2).
- Inspected the generated bundle: the synthetic SVG is inlined as a Vite asset and the demo replaces the JSON fixture's development URI with that bundled URL before `Assets.load` runs. This prevents a production build from attempting to fetch an unbundled `fixtures/` path.
- `git diff --check` passed. Temporary `dist-demo/` output was removed before commit; no build output is retained.
