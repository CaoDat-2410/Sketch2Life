# Plan Rev87.29 — Parent non-kitten catalog guide verification

**Date:** 2026-11-15
**Status:** APPROVED for the bounded real Modal verification below.
**Requirements authority:** FEAT-063 SRS v2.7-draft, current target §§1–31.
**Purpose:** check whether the generic Qwen/catalog path works for two source topics other than the pinned kitten.

## 1. Approved sample topics

- Initial diagnostic: `con bướm` (one route attempt; it failed before Modal dispatch because a bundled source guide exceeded the Parent API path-count cap).
- Remaining live Modal tests: `con voi` and `con cá`, which do not match the bundled Openclipart/OpenMoji guide aliases and therefore exercise the generic Qwen/catalog path.

Each request uses a synthetic topic only. It must search the real Openclipart catalog on the Modal Volume, use the Qwen3.5 catalog-query expansion and generic draft/review path, and preserve source-path geometry and existing quality/safety gates. No fixture or curated kitten override is used for either topic.

## 2. Execution steps

1. Confirm Modal dev identity and current app state; deploy the current `deployment/modal/srs_v23/language_audio_app.py` to the existing dev app only if required to run the approved code.
2. Call CPU `/health` and confirm pinned Qwen3.5 plus the read-only catalog Volume are ready before GPU work. Health is not an inference.
3. Run at most one Parent route request for each of `con voi` and `con cá`, sequentially. Capture elapsed time, request/Modal IDs, selected catalog asset/hash/license, path/stage counts, API status, hard-gate results and sanitized worker logs.
4. Do not retry a failed or visually rejected topic. Render each successful genuine response locally and inspect every cumulative stage and Vietnamese instruction.
5. Stop the Modal app and verify zero running tasks. Record results, limitations and evidence.

## 3. Acceptance criteria

- `con voi` and `con cá` are attempted at most once each through the real Parent route → Modal Qwen3.5/catalog worker; the catalog Volume is read-only and actual catalog candidates are selected at runtime.
- The earlier `con bướm` API attempt is recorded as a local pre-dispatch failure and is not counted as a Modal inference; it must not be repeated in this plan.
- No fixture, child profile, child artwork, voice, consent, personal data, video, DB writes, seed account or authenticated user identity is used. The test harness uses a synthetic Parent principal and bypasses the HTTP auth guard; this is not Firebase/Android E2E.
- Successful responses pass the existing API/schema, source-geometry, exact path-coverage, safety and quality gates without weakening them. Visual review records each source and step's recognizability/caption alignment.
- Each generic route gets one request maximum. No retry, fallback to another model, or additional topic beyond these two.
- Modal dev app is stopped after evidence capture.

## 4. Limits

Maximum two actual Modal route dispatches, one for `con voi` and one for `con cá`. The earlier `con bướm` route was rejected by local source-guide validation in 0.078 s, had no Modal call ID and did not reach the worker. Each generic request may run query expansion, draft-stage assignment and visual-review inference; no more than these two inference chains. No Docker, UI, Teacher flow, video, database/account/consent/secret/`.env`, Volume write/import/delete, source-code change, SRS §§1–31 edit, commit, push or merge. If either source fails, record the exact phase and safe reason; fixing it requires a follow-up plan.

## 5. Allowed paths

- This plan and `features/FEAT-063-system-architecture-rearchitecture/approvals/TASK_APPROVAL.md`
- `features/FEAT-063-system-architecture-rearchitecture/evidence/EV-063-123_PARENT_NON_KITTEN_MODAL_SMOKE_20261115/**`
- FEAT-063 `CONTEXT.md`, `DECISIONS.md`, `SOURCE_REGISTER.md`, `status/STATUS.md`, `evidence/README.md`
- FEAT-063 SRS §32 only and `docs/context/SRS_AUTHORITY.md`

No other paths may be edited.

## 6. Authorization record

Approved by the owner's direct instruction on 2026-11-15: “test thử với các cái khác xem”. The selected topics and limits above make that request concrete and reviewable.

## Execution amendment after the first topic preflight

The first `con bướm` Parent route attempt returned HTTP 503 in 0.078 s with `SVG_OPENCLIPART_SOURCE_GUIDE_DOCUMENT_INVALID`; no Modal call ID was produced. The route resolves a bundled Openclipart source guide before Modal dispatch, and the bundled butterfly guide declares 39 paths while the API canonicalizer accepts at most 32. The sibling bundled turtle guide has the same boundary mismatch (35 paths), so neither is suitable to test the generic Modal flow as-is. Do not retry those local topics. Preserve the recorded butterfly failure and spend the still-unused two-inference budget on `con voi` and `con cá`, which do not match bundled source aliases. No implementation fix or gate weakening is included.

## Execution closeout — 2026-11-15

- `con voi`: one genuine Parent route → Modal Qwen3.5/catalog call returned HTTP 200 in 147.959 s, 20 paths/8 stages. Existing schema and hard gates passed, but manual visual/pedagogical review rejected the guide: captions add unrelated alternating rear-leg ridge instructions; first-stage marks are disconnected and the source silhouette is crude. No retry.
- `con cá`: one genuine Parent route → Modal Qwen3.5/catalog call returned HTTP 200 in 131.538 s, 9 paths/4 stages. Existing schema and hard gates passed, but manual review rejected it: the selected Openclipart source is a kitchen scale and copy repeats/truncates Vietnamese text with Chinese characters. No retry.
- Both output SVGs were rendered locally and stage-by-stage contact sheets inspected. No child data, fixture, video, UI, Docker or DB was used.
- The Modal app is stopped; `app info` reports `state=stopped` and no servers. The `app list` task field reports `1`; it is recorded as returned and not assumed to mean a live task.
- Acceptance was **not met** for generic non-kitten guide quality. Evidence: `evidence/EV-063-123_PARENT_NON_KITTEN_MODAL_SMOKE_20261115/REPORT.md`. Any implementation correction or additional inference needs a new plan.
