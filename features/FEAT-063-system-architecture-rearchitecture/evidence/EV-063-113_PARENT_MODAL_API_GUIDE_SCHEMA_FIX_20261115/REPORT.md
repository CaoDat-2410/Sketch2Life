# EV-063-113 — Parent API to Modal SVG guide schema fix

**Date:** 2026-11-15<br>
**Plan:** Rev87.18<br>
**Environment:** local Docker API + Firebase Auth Emulator, Modal `dev` Qwen3.5 worker and Openclipart Modal Volume v2

## Result

**PASS — one real Parent API request completed through Modal and returned a valid guide.** The API returned HTTP 200 in 102.946 seconds. The Modal worker completed in 87.860 seconds; the API waited 96.766 seconds for its result.

The failure in EV-063-112 was caused by checking Modal's worker-content contract against the API entity schema. The validator now expects `SvgTopicStrokeGuideContentV1` at the worker boundary and continues to use `SvgTopicStrokeGuideV1` for the assembled API guide object.

## End-to-end request

- Route: `POST /api/parent/v1/ai/sketch-guides`
- Synthetic account: registered in the local Firebase Auth Emulator; `/me` confirmed role `parent`.
- Topic/difficulty: `con mèo`, beginner. No child profile, child image, voice, consent, or real personal data was supplied.
- API result: HTTP 200, request `c2c6ec7d-1fa5-46a3-93d2-c5e62db604bb`.
- Modal call: `fc-01M7E0Z2386EH7TP37PRGEMKWS`, status `worker_succeeded`.
- Model: `Qwen/Qwen3.5-9B`, pinned revision `c202236235762e1c871ad0ccb60c8ee5ba337b9a`.
- API contract: `SvgTopicStrokeGuideSourceDraftV1`; generation source `QWEN_SOURCE_PATH_DERIVATION`.
- Result: private `DRAFT`, not persisted, adult review required.

## Source and guide validation

- Source: `openclipart-friendly-kitten-icon`, Openclipart, CC0-1.0; immutable catalog revision `df38e5ef633be067d397df7da19a9f009e69b3bd`.
- Source SHA-256: `a5b74eed392104ff9baa2a335b5e8dde9aef40ca7775949a7fbc4a29b7f36594`.
- 11 source paths were assigned exactly once across six ordered Vietnamese stages. The renderer retained source geometry; the matching color illustration is a separate reference view.
- All eight source/provenance, safe-SVG, exact-geometry, exact-coverage, adaptive-stage, color-match, and private-review gates passed.
- All seven saved SVG files (six cumulative stages and the color reference) parsed as XML with an `<svg>` root.
- Artifacts: [API response](parent-guide-response.json), [HTML preview](guide-preview.html), [stage SVGs](stage-01.svg), and [color reference](color-reference.svg). The individual cumulative stages are `stage-01.svg` through `stage-06.svg`.

## Test limits and cleanup

The API/container integration and real Modal inference passed, and Python compilation in the API image passed. The focused pytest was attempted but collection stopped before the test because the host Python environment lacks `sqlalchemy`; this is an environment dependency gap, not a test assertion failure. The pytest suite is therefore **not claimed as passed**.

The synthetic Firebase Auth Emulator user was deleted; one backend identity row was removed. No child data or consent was created. No Android UI, video, Teacher presentation, or additional Modal inference was run. This evidence does not establish educator approval or suitability for children.
