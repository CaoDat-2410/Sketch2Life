# Parent AI content and parser audit — Rev117

**Date:** 2026-11-22  
**Scope:** Offline parser/content repair and read-only audit of the approved Parent AI paths. No inference was sent after the repair.

## Observed real result

The approved Parent Android activity request (fc-01M7ZDS0J0Q7YBAKVYHM9M88VJ, API request c96c1b75-e01f-4cca-9e65-af472f8482b5) completed with HTTP 200 using Qwen3.5-9B and returned three fallback activities in 104.515 seconds. Review found one displayed materials field cut at the worker's constrained JSON field limit. The worker/backend accepted it as valid, so this was a content-completeness defect after successful inference, not a timeout. Raw model output is not included here.

The pre-repair UI evidence is retained at ../PARENT_ACTIVITY_PARSER_REV116_20261121/parent-activity-result.png; it does not demonstrate the repaired wording.

## Repairs completed

- Parent activity fallback fields now use internal typed markers and complete, bounded Vietnamese templates for titles, objectives, materials, preparation, instructions, observation notes, safety notes, and match explanations. The external API schema is unchanged.
- Parent topic and topic-subject model JSON parsers reject duplicate keys instead of silently accepting the last value.
- Backend catalog context now validates text fields and cuts excerpts at word boundaries. It leaves the stored lesson unchanged and logs only an aggregate count of shortened fields.
- Updated one silent-video contract-test fixture to include the media metadata required by the existing contract. No video worker or video inference was changed.
- Existing safety, age, topic/context, catalog, Montessori, uniqueness, privacy, and adult-review gates were preserved.

## Parser audit

| Path | Result |
|---|---|
| Drawing/VLM | The authoritative candidate parser rejects duplicate keys and validates subject, features, and confidence. The separate json.loads diagnostic helper reports shape-only diagnostics; it does not accept or return a candidate. |
| Topic and subject suggestions | Duplicate-key rejection is now applied to the model-output parsers; output shape and topic/age checks remain in place. |
| SVG guide | The backend catalog/resolution contract suite passes. This path resolves validated guide assets; no separate Qwen-authored JSON output parser defect was found in this pass. |
| Lesson suggestion and Teacher guide | Existing authoritative parsers reject duplicate keys and enforce exact root/step shapes and field bounds. |
| Parent activity | Duplicate keys are rejected; internal markers are mapped to complete bounded copy before the public result is returned. |
| Story | Existing authoritative parsers reject duplicate keys and enforce story shape, scene count, Vietnamese fields, and sentence/content gates. Diagnostic parsers that use ordinary json.loads only report safe shape metrics; they do not accept story output. |
| Silent video | The worker consumes backend-produced story/scene manifests and validates exact fields, schema versions, hashes, ranges, and media lineage. These input manifests currently use ordinary json.loads (no duplicate-key hook); they are not LLM-authored output. This was recorded as a follow-up hardening opportunity and left unchanged because the approved Rev117 file allowlist does not include video_app.py. |
| Speech/audio | TTS and ASR produce audio/text payloads rather than structured LLM JSON; no JSON-output parser defect was identified in this audit. |

## Verification

- Modal output-contract suites: 184 passed, 2 dependency deprecation warnings.
- Backend parser/service/contract suites: 278 passed, 2 dependency deprecation warnings.
- Python compile checks for all changed Python sources and tests: passed.
- git diff --check for the approved changed source/test paths: passed.
- Task API container image s2l-feat081-rev23-api:parent-ai-parser-rev117: running; /health returned ok for sketch2life-api.
- Modal language/audio app: deployed; CPU readiness returned ready_for_gpu_worker_validation. This does not validate GPU allocation, model weight loading, or inference.
- Modal app inventory showed zero active tasks at review time.

## Limits

No post-repair model inference was run: Addendum 117's single real activity inference was already consumed. Therefore the new deterministic wording and parser behavior are verified offline and deployed, but the repaired output has not been confirmed by a second live UI response. No video request, quota/payment operation, gate bypass, account/run mutation, commit, or push occurred.
