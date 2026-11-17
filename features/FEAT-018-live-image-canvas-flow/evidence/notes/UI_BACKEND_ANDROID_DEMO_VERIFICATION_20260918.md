# Android UI/backend demo integration verification — 2026-09-18

## Scope and safety

- Branch: `codex/feat-018-contract-plan`.
- FEAT-018 Shared Integration Addendum Rev 2 remains the approved scope. The owner clarified an
  aggregate ceiling of at most 25 existing Lightning credits for personally initiated synthetic
  image tests; no top-up. The owner, not Codex, monitors balance and runs any live request. No live
  provider request was sent during this implementation or verification.
- App workflow is image-only. It accepts an explicitly confirmed synthetic/non-child PNG/JPEG up
  to 5 MB, has no microphone/camera/video path, and does not auto-retry. Authentication and durable
  save remain seams only; session and image state are ephemeral.
- Pixi receives a versioned launch contract and an expiring, read-limited source capability. It
  renders the retained original drawing only; FEAT-028's 144 review-pending frames are not passed
  into runtime.

## Verification

- Backend FEAT-018 focused API/contract/storage/provider-adapter suite: 53 passed.
- Broad backend suite: passed with `tests/unit/test_semantic_personalization_v2.py` excluded because
  its seven tests require the absent local-only file
  `backend/data/activity-catalog/golden/v1/semantic-anchor-profiles.v1.json`; five other tests were
  skipped by the suite. A workflow-dependency architecture check initially identified an
  application-to-infrastructure exception import in the new session service; the exception types
  were moved to the application storage port and the broad suite then passed.
- Pixi renderer: TypeScript check passed; 8 unit tests passed; Vite mobile/demo bundle built.
- Android app: TypeScript check passed; Expo SDK compatibility check is clean. Metro successfully
  bundled the Android app (1,368 modules; 6.55 MB JS bundle) using `expo export --platform android
  --no-bytecode --no-minify`. Bytecode/minification were disabled only for this static bundle
  check; this is not a native build or emulator run. Expo config introspection reports `INTERNET` as the only
  requested permission and blocks camera, microphone, legacy storage, and image/video media
  permissions. Android package remains `com.sketch2life.mobile` per ADR-0005; debug cleartext is configured only through
  the debug-manifest plugin. The renderer TypeScript entry point is declared for Metro workspace
  resolution, and Expo packages are aligned with SDK 52.
- Changed backend Python modules: Ruff and focused mypy passed. Whole-tree Ruff still reports four
  findings in untouched semantic-personalization/learning-media files; whole-tree mypy still reports
  three existing literal-type errors in untouched learning-media resolver/fallback files.
- `git diff --check` passed. Repository security validation no longer flags the new integration
  documentation, but still reports two pre-existing out-of-scope publishable items: an absolute
  machine path in FEAT-029 `SOURCES.md` and a PDF under FEAT-026 artifacts. They were not changed.

## Not yet verified

- Android Studio/SDK/emulator is unavailable in the current environment. The app has not been
  installed or visually/device-tested on an emulator.
- No real Lightning request has been made. The owner must configure the endpoint/token privately on
  the backend, build/install the Expo development client, monitor the balance, and press the single
  explicit analysis action if desired.
- The unauthenticated debug API must remain on a trusted local network; do not expose it publicly.

## Operator entry point

See [`apps/ui-mobile/BACKEND_INTEGRATION.md`](../../../../apps/ui-mobile/BACKEND_INTEGRATION.md) for
the host/emulator run steps and manual smoke sequence. No provider endpoint or credential is stored
in this evidence.
