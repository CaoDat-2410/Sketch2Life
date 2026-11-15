# EV-063-96 — Rev86 Teacher SVG dataset-pack correction and live comparison

**Date:** 2026-11-13 (Asia/Saigon)<br>
**Plan:** Rev86, approved SHA-256 `144EA85E3314A9CC86659D749DDFDD9D317C306C5C134BFE6035F975C395696D`<br>
**Outcome:** Dataset validation and one real UI → API → Modal → sanitized SVG → browser-render request passed. **Visual-quality objective: NOT PASSED** for the deer topic. This is one bounded sample, not a benchmark.

## Scope and input

- Used the existing local synthetic Teacher account, Firebase Auth Emulator, Docker API, and actual Teacher Web form. The non-personal request was `con hươu sao`, target age `60` months, style `warm_storybook`.
- No fixture, canned output, previous SVG, real child profile/data, video, FLUX, or additional AI request was used.
- Preserved the pinned dataset source snapshot `yoavf/svg-animal-illustrations@d7ab3149308746a4b17e7cbee30f1f054f6c49df` byte-for-byte. Source snapshot SHA-256: `62e79601cf0e8709b71d7bcafd323b09a9aed91f1304bf049091015c36660fef`.
- Removed `prompet-sample-cat` only from the active preview pack. The preserved raw record remains in `source-examples.jsonl`; the manifest records the exclusion because `path-026` has `stroke_width=20`, above the unchanged worker maximum `12`.
- Active pack contains the dog/quadruped and rabbit/lagomorph examples. Its byte count is 9,716 and SHA-256 is `319d25932c8d4bc8c362b6af19ecded75cb1015d7f8cc19387c9685a74349af0`.
- Static preflight used the exact deployed worker parser: dog sample, 22 paths, PASS; rabbit sample, 18 paths, PASS. Pack JSON, byte count/hash, manifest and worker pin matched. This was the plan-required preflight, not a product test-suite run.

## Runtime execution

| Step | Result |
|---|---|
| Update existing Modal app | One update of `sketch2life-srs23-language-audio-dev`, completed in approximately 14.81 s |
| CPU `/health` | HTTP 200 in 4.749 s; pinned Qwen3.5-9B revision ready; `gpu_allocated=false`, `inference_executed=false` |
| Teacher UI request | Exactly one POST; HTTP 200. The browser runner counted the preflight CORS OPTIONS and POST as two network events, but API logs show one POST and one inference. No retry. |
| API elapsed | 225.822 s; worker wait 223.907 s |
| Worker phases | input envelope 0 ms; scratch reload 138 ms; manifest read 162 ms; reference selection 1 ms; checkpoint check 46 ms; model load 18,348 ms; prompt encoding 65 ms; constrained decoder setup 3,738 ms; model inference 192,176 ms; parse/contract validation 1 ms |
| Result | `TeacherSvgIllustrationDraftV1`, HTTP 200, `DRAFT`, `review_required=true`, `persisted=false`, 19 paths |

Request ID: `a371d8a9-2de0-485e-a844-a58328ce29b8`<br>
Modal call ID: `fc-01M799DWAHN9XGNRRTX4NFE2X4`<br>
Model: `Qwen/Qwen3.5-9B@c202236235762e1c871ad0ccb60c8ee5ba337b9a`<br>
Canonical document SHA-256: `9de4dc5936682e79b3e288229256f84f9564025ec14f3d1bed17b4caebcc8ac7`

The active lookup supplied the dog/quadruped structural reference (`prompet-sample-dog`). Its source record has no paired source prompt and its composition hint explicitly says to create the requested subject, not a rabbit. The model output nevertheless reads as rabbit-like, so the retrieved structural example did not preserve deer-specific identity in this sample.

## Visual comparison with Rev84

Compared the actual browser render with `EV-063-94/teacher-svg-draft.png` using the five criteria already approved in Rev86:

| Criterion | Rev86 result | Comparison / finding |
|---|---|---|
| Recognizable deer anatomy | **Fail** | The two long, unbranched upright shapes read as rabbit ears, not deer antlers. The output is more rabbit-like than the Rev84 sample. |
| Coherent body/head proportions | **Partial** | The body is more quadruped-like; the compact head and front/neck joins still look crowded and stylized. |
| Connected, grounded limbs | **Improved** | Four legs are visibly attached to the torso and reach the baseline; Rev84 had detached triangular leg/ground shapes. |
| Markings/details attached to subject | **Partial** | White spots appear on the torso, but several are oversized and overlap body/neck boundaries. |
| No detached/unrelated objects | **Improved** | No obvious floating grass or prop shapes remain; Rev84 had detached green triangles and an unrelated-looking green cluster. |

Overall the result is **mixed and not suitable as a deer illustration without revision**. Three structural aspects improved or partly improved, but species recognition—the central requirement for this request—failed. One output cannot establish general dataset benefit. Do not mark the SVG quality gate passed or enable this workload broadly.

## Diagnostics and cleanup

- All logged worker phases completed and the API returned HTTP 200. The API summary nevertheless recorded `worker_terminal_event=None` and `worker_failure_boundary=worker_started_without_terminal_event`; this is an observability inconsistency requiring separate follow-up. It did not change this request's HTTP result.
- Modal remains deployed as the shared language/audio app. Its source configuration has `min_containers=0`; a post-run live-container query was not verified because the current PowerShell environment has no `modal` command. Do not claim scale-to-zero was observed.
- The local Rev86 API container was recreated with `SKETCH2LIFE_SVG_ILLUSTRATION_GENERATION_ENABLED=false` without editing `.env`. It remains in Docker `Created` state because startup could not bind `127.0.0.1:8000`, already occupied by the separate `sketch2life-api-1` container. That existing container was left running and untouched; its health remained `healthy`. No alternate port or extra API container was introduced.
- The task Vite server and private headless Chrome session were closed; ports `5173` and `62597` had no listener at cleanup check.
- No database migration/seed, test suite, secret access/output, commit, push, or merge occurred. The task API's failed bind means local API health was not restored; this is recorded rather than hidden.

## Artifacts

- [Actual API response](generated-svg-draft.json)
- [Sanitized SVG serialized from that response](generated-svg-draft.svg)
- [Actual browser-rendered SVG screenshot](teacher-svg-draft.png)
