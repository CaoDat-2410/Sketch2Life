# Rev87.11-C — Parent progressive SVG guide and finished illustration

Date: 2026-11-14
Plan: `PLAN_REV87_11C_SEPARATE_STROKE_GUIDE_AND_SVG_REFERENCE_20261114.md`
Baseline: FEAT-063 SRS v2.7-draft Rev69, unsigned; §§1–31 unchanged.

## Result

The Parent source-derived route now returns two separate vector documents for the supported chicken topic:

1. A 20-path, six-stage child drawing guide. It is displayed on a plain canvas, with earlier strokes dark, the current step blue and animated in order, and later strokes hidden.
2. The pinned Arcadia full-color illustration, shown only after tapping **Xem hình minh họa hoàn chỉnh**. Returning to the drawing keeps the selected step.

The first visual check showed that placing the completed source image behind the guide confused two different poses and hid the drawing sequence. Rev87.11-C separates the views and revises the stroke drawing to face the same direction as the chicken illustration. The guide is still a private draft requiring adult review.

## Real route result

- Route: `POST /api/parent/v1/ai/sketch-guides`
- Request: `con gà`, beginner
- HTTP: **200**, **0.045 s**
- Contract: `SvgTopicStrokeGuideSourceDraftV1`
- Guide: **20 distinct open paths / 6 progressive stages**
- Source reference: **77 sanitized paths**, all with fills
- Guide document SHA-256: `27bed3626dada9ce68094d7697896d14fa7b7e399ea3b0c34a05f32eed4c5fc7`
- Reference SVG SHA-256: `4f6397d5d32ff7ea58451cb5e5725c87501be155c0eb64f85c5821dfe99cb1ed`
- Reference document SHA-256: `149360115e918a5535616b85564f5ce2c3b9887a6e4908dc671077dd05c0b601`
- Modal dispatch: **false**

The API response preserves both separate documents and provenance. It passes the existing SVG sanitizer, path coverage, source-lineage, and chicken anatomy/topology checks.

## Artifacts

- `parent-chicken-stroke-step-1.png` through `parent-chicken-stroke-step-6.png` — actual guide stages, 1024×1024.
- `parent-chicken-reference-illustration.png` — full-color source illustration, 1024×1024.
- `parent-chicken-source-derived.svg` / `.png` — complete guide document.
- `parent-chicken-stroke-step-1.svg` through `parent-chicken-stroke-step-6.svg` — stage vectors.
- `parent-chicken-reference-illustration.svg` — sanitized full-color source document.
- `parent-svg-guide-response.json` — full actual route response.
- `runtime-attempt.json` — elapsed time, hashes, counts, and Modal-dispatch status.
- `run_source_derived_api.py` — reproducible focused route call.
- `render_svg_evidence.py` — rasterizes those SVG artifacts for review.

## Verification

| Check | Result |
|---|---|
| Backend Docker image build with pinned dataset | Passed (`sketch2life-rev87-11c-api-check:local`) |
| Parent route using the image-packaged source and real builder/sanitizer | HTTP 200; 0.045 s; no Modal call |
| Focused source derivation, route contract, and chicken topology tests | **9/9 passed** in a disposable container; repository tests mounted read-only |
| Focused mobile contract/renderer tests | **5/5 passed** |
| Standalone TypeScript check for changed guide domain/screen/renderer files | Passed |
| Full mobile TypeScript check | Fails on missing `EXPO_PUBLIC_*` declarations in `src/config/apiConfig.ts`, `src/demo/api.ts`, and `src/parent/infrastructure/config.ts`; no diagnostics point to the changed SVG screen/renderer |
| Raster evidence | Eight actual SVG outputs rendered at 1024×1024; guide stages and color reference visually inspected |

The route runner overrides only Parent identity and database dependencies in FastAPI TestClient. It exercises the real route, pinned dataset, guide builder, sanitizer, topology validator, response model, and Docker-packaged source. It does not prove Firebase-authenticated production behavior, database-backed catalog behavior, or Android end-to-end rendering. No Android emulator run was performed.

## Limits and cleanup

Only the pinned chicken aliases use this deterministic source derivation. Unsupported topics retain the existing Qwen/Modal fallback. The generated SVG strokes are an authored educational derivation from Arcadia anatomy reference; Arcadia itself does not contain stroke order. Educator review is still required before catalog approval or publication.

No Modal/GPU call, fixture response, database mutation, child data, account/consent/seed change, `.env` edit, shared-service restart, video generation, commit, push, or merge occurred. The disposable API image was removed after verification; all one-shot containers exited.
