# Rev39 Parent activity attempt — result

- **Date:** 2026-11-20 (UTC).
- **Existing synthetic StoryRun:** `ec455bbb-8211-49d5-8cef-9889df809de2`.
- **UI request:** one tap at `2026-11-20T02:19:25.425114Z`; backend request `c340d429-1cb1-4b1e-a19f-7a917fc074ed`.
- **Modal call:** `fc-01M7VC15RQPD9XKX454Y9ZJ3RH`, workload `parent.activity.suggest`, Qwen3.5-9B pinned revision `c202236235762e1c871ad0ccb60c8ee5ba337b9a`.
- **Outcome:** failed; no suggestion set was persisted. No activity selection, story, or video was attempted. No retry was sent.

## Worker evidence

- GPU capability 8.9. Model load 19.140s, prompt encoding 54ms, constrained decoder setup 4.119s.
- Inference completed 681 tokens in 91.015s (7.482 tokens/s); worker elapsed 114.611s. This was not a timeout.
- JSON completion, EOS allowance, and parser completion passed. The unchanged final punctuation parser rejected only `fallback_activities[0].objective` with `MODAL_MODEL_OUTPUT_INCOMPLETE_TEXT`.
- The Rev39 token filter was active and blocked 46,644 quote-ending candidate tokens over 681 callbacks. The failure shows this token-level condition did not guarantee the external prose-field terminator. No generated text was retained.
- The backend observed `ExecutionError` before the terminal worker event was indexed and returned HTTP 502 `MODAL_WORKER_FAILED_TERMINAL`; Modal logs subsequently exposed the specific safe worker failure.
- Sanitized fields and timing: [32-rev39-modal-activity-sanitized.json](32-rev39-modal-activity-sanitized.json).

## Catalog path verification

- This was a topic-based run with no pinned lesson. The route reached the catalog-backed path before starting Modal: it creates `LessonLibraryParentActivityCatalogAdapter`, calls `ParentActivitySuggestionService.prepare`, then invokes `parent.activity.suggest` with that prepared input.
- The adapter requests Parent-accessible lesson versions from Lesson Library (maximum 500); the application service filters for age/access and relevance and sends the top 12 activity candidates to Qwen. When no candidate is suitable, the worker contract asks Qwen for three fallback activities. This matches the catalog-first business rule.
- The existing request and worker logs do not record the accessible-lesson or candidate counts. The exact candidate count for this attempt therefore cannot be confirmed from runtime evidence. Rev40 will add privacy-safe counts at the service/worker boundary before another inference.

## UI and checks

- Result screen and XML: `31-rev39-activity-result.png` / `.xml`; the UI showed a generic retryable error.
- Focused worker tests: 21 passed, 40 deselected. Python compilation and `git diff --check` passed.
- Full worker contract module: 60 passed, 1 unrelated drawing parser test failed because its expected response omits the now-required `confidence` property. No drawing code/test was changed.
- API `/health` and emulator remained online. No fixture, direct AI request, quota/payment mutation, database edit, or video call occurred.

## Follow-up

Rev40 should represent required punctuation as typed model output: each required sentence supplies bounded text plus a one-character terminator enum; `instructions_text` supplies exactly two such sentence components. The worker will compose them into the existing response fields and run the unchanged length, language, quality, and punctuation validators. Also log only accessible lesson count, age-eligible lesson count, eligible activity count, and candidate count; never log lesson IDs or content. If the next UI request fails, stop AI calls until a new amendment is approved.
