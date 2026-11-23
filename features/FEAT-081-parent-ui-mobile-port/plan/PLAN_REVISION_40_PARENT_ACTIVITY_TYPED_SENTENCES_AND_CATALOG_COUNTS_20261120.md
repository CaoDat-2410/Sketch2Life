# FEAT-081 — Plan Revision 40: typed activity sentences and catalog diagnostics

- **Status:** APPROVED under the owner's continuing direct instruction on 2026-11-20 to keep fixing the real Parent workflow until it runs.
- **Feature/worktree:** FEAT-081, `feature/fe-mobile-remediation`, `<local-machine-path>
- **Product authority:** FEAT-063 v2.7-draft, §§1–31; catalog-first Parent activity selection is recorded in Rev63 and cross-referenced by Rev71. The SRS remains unsigned.
- **Relationship:** follows Plan Revision 39. Its single real activity request completed in 114.611s, but the output failed the existing punctuation check at `fallback_activities[0].objective`; this was not a timeout. The catalog-backed code path ran, but the exact catalog/candidate counts were not logged.

## 1. Goal

Make the Parent activity fallback response reliably satisfy its existing sentence-ending rule by representing sentence bodies and their terminators as separate typed values in the **internal Qwen worker output**, then compose the existing worker/backend response shape and run all current validators. Add privacy-safe counts proving how many accessible lessons and activity candidates were considered and sent to Qwen.

## 2. Evidence and diagnosis

- Rev39 used the existing synthetic StoryRun `ec455bbb-8211-49d5-8cef-9889df809de2`, backend request `c340d429-1cb1-4b1e-a19f-7a917fc074ed`, and Modal call `fc-01M7VC15RQPD9XKX454Y9ZJ3RH`.
- Qwen3.5-9B generated 681 tokens in 91.015s; model load took 19.140s and total worker time was 114.611s. JSON completion, EOS allowance, and parser completion passed. The terminal parser rejected `fallback_activities[0].objective` with `MODAL_MODEL_OUTPUT_INCOMPLETE_TEXT`. No suggestion was persisted, and no activity selection, story, or video was attempted.
- Rev39 blocked 46,644 quote-ending candidates, but this did not guarantee the final JSON string had accepted punctuation. The token-level workaround is therefore not a sufficient invariant.
- The actual no-pinned-lesson route constructs `LessonLibraryParentActivityCatalogAdapter`, reads Parent-accessible published/shared lesson versions, applies age/access/renderability/relevance filtering, and passes the selected top candidates to Qwen. If there is no catalog match, the worker is asked to produce exactly three fallback activities. Runtime logs did not record lesson or candidate counts, so the count for Rev39 is unknown.
- Detailed evidence: `evidence/PARENT_API_AUTH_FULL_E2E_REV24_20261119/REV32_AUTH_RECOVERY_AND_E2E/32-rev39-activity-failure-analysis.md` and `32-rev39-modal-activity-sanitized.json`.

## 3. Authorized implementation

### M1 — typed punctuation for generated fallback text

- Change only the internal JSON schema emitted by the Parent activity worker. Represent `objective`, `preparation_text`, and `safety_notes` as a bounded sentence object with `content` and a required `terminator` enum fixed to the existing requested ASCII period (`.`). Represent `instructions_text` internally as exactly two such sentence objects.
- The parser must reject missing/extra keys, empty bodies, an unsupported terminator, body text that already ends in a sentence terminator, an instruction list whose length is not exactly two, or any composed field that exceeds its existing maximum length.
- Compose these typed values into the same existing normalized worker result fields: `objective`, `preparation_text`, `instructions_text`, and `safety_notes`. Do not change the backend request/response contract or persisted activity schema.
- Run the existing language, length, shape, age-band, catalog-selection, activity-kind, and Parent activity quality gates against the composed strings unchanged. Keep the requirement for exactly three fallback activities when no candidate matches.
- Remove the Rev39 quote-ending-token filter and its helper/counters; punctuation is now explicit in the typed structure and still checked after composition. Keep the existing backslash and non-Latin protections.
- Keep prompt/checkpoint/revision, provider, token limit, timeout, candidate limit, punctuation policy, and soft/hard quality thresholds unchanged. Do not add output repair or retries.

### M2 — privacy-safe catalog counts

- Extend the prepared application result with integer-only diagnostics: accessible lessons read, age/access-eligible lessons, renderable non-excluded activities in those lessons, relevance-matched activities before the top-12 cap, and candidates actually sent to the worker.
- Count a lesson as eligible only when its age range and allowed access source pass. Count an activity as eligible only after renderability and explicit exclusion checks. Count a relevance match only after the existing overlap rule. Preserve deterministic ranking and the top-12 cap.
- Emit these counts once in the backend's structured `parent_activity_suggestions_catalog_prepared` log before Modal dispatch. For the worker, log only the received candidate count and resulting decision/counts.
- Never log lesson/profile identifiers, titles, activity text, child context, image/audio, prompts, model output, tokens, secrets, or credentials. For pinned lessons, retain the current no-Modal direct-selection path; do not report it as an unpinned catalog query.

### M3 — offline verification

- Add tests for typed sentence schema bounds, exactly two instruction sentences, period composition, malformed/double terminators, final composed-length limits, and unchanged normalized response shape.
- Add application tests proving each catalog count is computed at its specified filter stage, including age/access rejection, non-renderable/excluded activities, relevance misses, ranking/top-12 truncation, and zero candidates.
- Add safe worker/backend log assertions that counts are present while content and identifiers are absent.
- Run the focused Modal worker contract tests and `backend/tests/unit/test_parent_activity_suggestions.py`; run Python compilation for changed Python files and `git diff --check`. Existing unrelated failures must be reported and not broadened into this amendment.

### M4 — deploy/readiness and one real UI attempt

- Deploy only Modal app `sketch2life-srs23-language-audio-dev` to `dev`; perform CPU-only readiness without loading model weights or warming a GPU.
- Reuse the authenticated synthetic Parent/profile/drawing/context and StoryRun `ec455bbb-8211-49d5-8cef-9889df809de2` on the real Android emulator. Submit exactly one fresh activity-suggestion action through the real Expo UI, with an eight-minute hard cap and no retry, duplicate tap, direct API/worker call, fixture, or synthetic response.
- Pass only if the real response is persisted and the suggestion cards render in the UI. Capture the safe catalog counts, request/call IDs, terminal status, timings, and UI evidence.
- After activity success, continue one real UI activity selection/persistence and one story generation/adult review only under already active, unconsumed approvals. A single silent LTX-2.5 call remains conditional on the exact pre-existing video authorization being verifiably unconsumed and every earlier gate passing; this amendment adds no video allowance. If that cannot be verified, stop before video.
- If activity fails, preserve sanitized evidence and stop further AI calls until a new amendment is recorded.

## 4. Acceptance criteria

1. The internal worker schema encodes the sentence terminator separately, while the normalized worker result and backend/API contracts remain unchanged.
2. All current schema, language, punctuation, length, catalog, age, consent, safety, and quality checks remain active and pass focused tests.
3. Catalog diagnostics report exact counts at each documented stage and contain no content or identifiers.
4. The single real UI activity attempt returns and persists a valid catalog selection or three gated fallback activities, then displays them. If there is no suitable catalog activity, the trace must show zero relevance-matched candidates and the worker's `NO_MATCH` path before fallback creation.
5. No inference is repeated after a failure under this amendment.

## 5. Explicit exclusions

- No quality-gate relaxation, timeout/token-limit increase, prompt/model/provider/checkpoint change, output repair/translation, retry, parallel inference, or GPU warm-up. No new video authorization or quota/admission bypass.
- No change to lesson visibility/access policy, catalog source, top-12 cap, Parent activity selection semantics, consent/age/safety rules, quota/payment, database schema/data, migrations, SRS, or `.env`/Modal secrets.
- No new account/profile/run, real child data, fixture/mock in the live flow, direct database edit, commit, push, branch/history operation, or unrelated service shutdown.
- Preserve all pre-existing dirty/staged work. Keep the emulator online; stop only task-owned services after evidence capture and leave unrelated Modal apps untouched.

## 6. Exact file boundary

- `deployment/modal/srs_v23/language_audio_app.py`
- `deployment/modal/srs_v23/tests/test_qwen35_lesson_suggestion_contract.py`
- `backend/src/sketch2life/application/services/parent_activity_suggestions.py`
- `backend/src/sketch2life/interfaces/http/routers/parent_ai.py`
- `backend/tests/unit/test_parent_activity_suggestions.py`
- `features/FEAT-081-parent-ui-mobile-port/plan/PLAN_REVISION_40_PARENT_ACTIVITY_TYPED_SENTENCES_AND_CATALOG_COUNTS_20261120.md`
- `features/FEAT-081-parent-ui-mobile-port/approvals/TASK_APPROVAL.md`
- `features/FEAT-081-parent-ui-mobile-port/status/STATUS.md`
- `features/FEAT-081-parent-ui-mobile-port/evidence/PARENT_API_AUTH_FULL_E2E_REV24_20261119/REV32_AUTH_RECOVERY_AND_E2E/`
