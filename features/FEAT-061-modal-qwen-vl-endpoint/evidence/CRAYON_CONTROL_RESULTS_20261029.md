# Three synthetic crayon controls — bounded live observations

## Authorization and execution

- The owner asked for three childlike synthetic controls, then requested continuation. The assistant prepared actual local admission and stated that the owner would start serve before a maximum of three sequential requests, stopping on error. The owner supplied `Serving...` for App `ap-VsvYKHb4tQVOROYFZJSLf4`. The assistant then sent exactly those three prepared requests, in house-only, sun-only, combined order; there were no automatic probe retries or additional model requests.
- Before calling the endpoint, all request/source/admission bytes were checked against the preparation manifest's SHA-256 values. Actual ADMITTED receipts, PASS provenance, image base64 and source identities matched; no narration was added. Prompt/model/profile/config/adapter remained unchanged.
- Correct auth came from the existing locally encrypted backup through stdin. No credential was printed or stored. A temporary probe was removed after execution. Raw generation/response bodies and predicted labels were not saved; selected typed synthetic labels were displayed transiently for the owner's requested content review.

## Results actually returned

| Asset ID | HTTP / typed status | Entities | Client wall seconds | Attempt / repair |
| --- | --- | ---: | ---: | --- |
| crayon-house-only-v1 | 200 / SUCCEEDED | 1 | 24.955 | 1 / true |
| crayon-sun-only-v1 | 200 / SUCCEEDED | 1 | 4.611 | 1 / true |
| crayon-house-and-sun-v1 | 200 / SUCCEEDED | 4 | 8.026 | 1 / true |

All three passed response schema, source/correlation, profile/catalog, exact model/revision, config/adapter and attempt checks, with policy execution PASSED. Model: `Qwen/Qwen3-VL-8B-Instruct`; revision `0c351dd01ed87e9c1b53cbc748cba10e6187ff3b`; profile `QWEN3_VL_8B_INSTRUCT_BF16_V1`; adapter `qwen3-vl-local-adapter-v2-b1`.

The metadata JSONL is `crayon-controls-20261029-v1/content-metrics-20261029T054340220933Z.jsonl`, containing a run header and three result rows. Correlation suffix is `19c4ae7a18`. First request began `2026-10-29T05:43:40.226448+00:00`, or 12:43:40 Asia/Saigon. Preparation `manifest.json` remains the historical preparation-time record and still says inference was not yet executed at that moment; later execution is recorded separately here and in the result JSONL.

## Bounded manual interpretation

- Comparison of the validated typed entities with the visible sources found the intended subject in each single-subject case. The combined source explicitly identified both intended subjects and additionally reported two visible building parts. Only closed comparison flags and counts are persisted in `crayon-controls-20261029-v1/manual-observations-v1.json`, not predicted text.
- These observations show that the deployed path can return multiple entities and both intended subject categories for this crayon sample. They do not establish why the earlier geometric sample omitted its smaller secondary subject, nor isolate a prompt/model/normalizer cause.
- Each case has one example and one request. The AI-edited controls are not guaranteed pixel-identical. No quality benchmark, calibrated confidence claim, pass threshold, Lightning L4 comparison, backend integration or production-readiness claim follows. The earlier FEAT-003 quality result is unchanged.
- No GPU peak, exact billed duration/cost, same-container identity or model-cache continuity was measured for this run. Do not label these client times a controlled cold/warm benchmark.
- After result recording, the owner supplied all three successful server logs and keyboard-interrupt shutdown ending in `App aborted` for `ap-VsvYKHb4tQVOROYFZJSLf4`. This confirms this temporary session stopped. No further request or retry was made, and no commit/push is performed by this test step.

## Subsequent owner-supplied server timing

The ordered server logs match the prepared house-only, sun-only and combined sequence by status and entity counts. These server durations differ from the client wall times above and do not measure exact billing or instantaneous GPU peak.

| Request in sequence | Server HTTP duration seconds | Server execution seconds | Status / entities |
| --- | ---: | ---: | --- |
| House only | 24.3 | 18.9 | SUCCEEDED / 1 |
| Sun only | 3.96 | 3.85 | SUCCEEDED / 1 |
| Combined | 7.40 | 7.28 | SUCCEEDED / 4 |
