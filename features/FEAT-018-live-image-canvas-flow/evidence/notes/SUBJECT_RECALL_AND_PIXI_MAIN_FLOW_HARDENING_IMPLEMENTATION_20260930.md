# Subject recall and Pixi main-flow hardening — implementation evidence

Date: 2026-09-30

Plan: `../../plan/SUBJECT_RECALL_AND_PIXI_MAIN_FLOW_HARDENING_PLAN_20260930.md`
Approved plan SHA-256: `6EF237C0117AED6C8A4B513D69F084131FAB5E8B5C6C29DB2157E6607D92F65F`

## Implemented

- Backend/mobile label handling keeps unknown valid labels visible rather than replacing them with
  a generic phrase that topic filtering removes. Reviewed bird/animal aliases are consistent, and a
  grounded whole-animal claim outranks branch/leaf/part claims without creating claim IDs.
- Gate A supports a separate adult-entered subject representation. The server binds it to the
  admitted source artifact/hash and adult assertion provenance; AI claim IDs remain empty when the
  AI produced no usable claim. Existing V1 confirmation remains supported.
- Zero-claim and failed-requery responses lead to an explicit recovery state. Only a user action can
  re-query, at most once per image session; the entered subject remains available for confirmation.
- Pixi loading is not hidden merely because the renderer reports `READY` with zero duration. A
  finite watchdog covers bridge handshake, preparation, startup, and playback heartbeat. WebView
  playback failure reaches the app as a safe typed event for both V1 and V2 launch contracts.
  Player destruction is idempotent on failure and page exit; no automatic retry or silent downgrade
  was added.
- The audit found and fixed two additional transition bugs: failed renderer preparation previously
  left the loading overlay visible over the explicit retry action, and late successful renderer
  preparation did not store the returned session version. The overlay now terminates on preparation
  failure, and the version is advanced before response status handling.

## Validation

- `corepack pnpm --filter @sketch2life/art-renderer test` — 48 passed.
- `corepack pnpm --filter @sketch2life/art-renderer typecheck` — passed.
- `corepack pnpm --filter @sketch2life/art-renderer build:demo` — passed; Vite transformed 826
  modules.
- `corepack pnpm --filter sketch2life-mobile test` — `UI_COPY_AND_RECOVERY_VALID`.
- In `apps/ui-mobile`, `corepack pnpm exec tsc --noEmit --pretty false` — exit 0.
- Focused `test_topic_activity_matching.py`, `test_p1_experience.py`,
  `test_live_image_demo_api.py`, and `test_renderer_contracts.py` — 100 passed. The installed local
  runtime lacks PyAV; an import-only `av` stub was used for this offline test run, whose tested image
  paths use injected decoders. No media decoding, model, or provider was invoked.
- `py -3.14 -m ruff check` on changed backend files — passed.
- `py -3.14 tools/validate_repository_security.py` — `REPOSITORY_SECURITY_VALID`, 1,740 publishable
  files scanned.
- `git diff --check` — passed; Git emitted only existing CRLF normalization warnings in dirty
  FEAT-029 documents.
- `py -3.14 tools/validate_harness.py` — blocked by existing missing evidence directories in FEAT-026
  (`evidence/raw`, `evidence/metrics`) and FEAT-033 (`evidence/raw`, `evidence/screenshots`); these
  unrelated feature records were not modified.
- `py -3.14 tools/validate_architecture.py` — passed all dependency direction, mobile isolation,
  asset-gate, mobile AI boundary, and Firebase data-product checks.
- Final `py -3.14 tools/validate_repository_security.py` — `REPOSITORY_SECURITY_VALID`, 1,742
  publishable files scanned.
- `ruff format --check` reports existing unformatted layout in these already-dirty files; checks
  against corresponding `HEAD` versions also fail. No whole-file formatting rewrite was applied.

## Device/runtime observation and remaining limit

- ADB reports `emulator-5554` connected; `adb reverse --list` reports `host-10 tcp:8081 tcp:8081`.
- Metro `/status` returns `packager-status:running`. The Expo Android entrypoint
  `/.expo/.virtual-metro-entry.bundle?platform=android&dev=true&hot=false&lazy=true&minify=false&transform.engine=hermes`
  returned HTTP 200 with 7,900,918 bytes. The bare `/index.bundle` path returned 404 because it is
  not the configured Expo virtual entry route; the correct route compiled successfully.
- A bounded recent logcat query found no matching Pixi bridge failure, React Native fatal exception,
  or unable-to-load-script message. No screenshot or user artwork was collected into evidence.
- No fresh Pixi launch was performed: reproducing playback requires an available rig/mask response.
  Therefore offline state/bridge correctness and Metro bundle delivery are verified, but actual
  on-device visual playback and live SAM output are not claimed. No live Qwen/SAM/Lightning call was
  made by Codex.

No commit, push, backend restart, or emulator reset was performed.
