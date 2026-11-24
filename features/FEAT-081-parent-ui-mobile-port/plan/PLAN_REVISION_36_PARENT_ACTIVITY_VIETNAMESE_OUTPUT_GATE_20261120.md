# FEAT-081 — Plan Revision 36: Parent activity Vietnamese output gate

- **Status:** APPROVED under the owner's continuing direct instruction on 2026-11-20 to keep fixing the real Parent workflow until it runs.
- **Feature/worktree:** FEAT-081, `feature/fe-mobile-remediation`, `<local-machine-path>
- **Product authority:** FEAT-063 v2.7-draft, §§1–31; especially BR-08, FR-P-05, §31.21 and NFR-13/21. SRS remains unsigned.
- **Relationship:** follow-up to Plan Revision 35 after its bounded activity request completed generation but failed the language gate.

## 1. Goal

Make Qwen3.5 Parent activity suggestions return valid Vietnamese text without weakening catalog-first selection, age, safety, schema, or quality checks, and verify one actual request from the authenticated Parent Android UI.

## 2. Evidence and diagnosis

- Rev35 call `fc-01M7V7JFVH0RWAMH38VB7G4E74` completed 682 generated tokens in 99.573 seconds; the constrained-decoder callback maximum was 106 ms. Model load was 24.969 seconds. The failure occurred after generation at `output_parse_and_contract_validation` with `MODAL_MODEL_OUTPUT_INVALID_NON_LATIN_SCRIPT`.
- The current worker prompt already requires Vietnamese Latin text. No generated text was retained or logged.
- Inspection of pinned LMFE 0.11.3 source shows `StringParsingState.get_allowed_characters()` always adds a backslash in free-text strings and its parser explicitly accepts JSON `\\uXXXX` escapes. Thus the configured Vietnamese alphabet alone does not prove that decoded JSON string values contain only Latin text. This is the leading, testable cause; the exact escape form from the failed response is unknown.
- The current post-generation script check covers fallback activity fields but does not cover `no_match_reason` or catalog `match_reason` fields.

## 3. Authorized implementation

### M1 — block escaped non-Latin output at generation

- Add an activity-only LMFE allowed-token filter that disallows vocabulary tokens whose decoded output contains a JSON backslash escape. Reuse the existing token-vocabulary scan; do not add a second full-vocabulary scan per generated token.
- Keep other Qwen workloads and their JSON escape behavior unchanged.
- Record only counts for blocked token candidates and any safe decoder dead-end reason; never log generated text, prompt text, image data, or tokens.
- Add a concise prompt instruction asking for natural Vietnamese Latin text and no Unicode escape encoding. The constrained token filter is the enforcement mechanism; prompt text is not treated as a safety gate.

### M2 — close output-language validation coverage

- Apply the existing fail-closed Latin-script check to every user-visible generated text field: catalog match reasons, no-match reason, and all fallback activity prose.
- On a failure, report only the field path and a character count/category; do not include the character, field value, or generated JSON.
- Preserve the existing output contract, length bounds, sentence punctuation, required outdoor setting, age band, catalog IDs, no-duplicate behavior, activity quality checks, and adult selection requirement.
- Add offline regression cases for literal and JSON-escaped non-Latin text, catalog and fallback fields, and activity-only decoder token filtering. Confirm the bounded free-text fast path still applies.

### M3 — offline verification and Modal readiness

- Run Python compilation and the focused Qwen3.5 activity contract tests.
- Deploy only `sketch2life-srs23-language-audio-dev` from the approved worktree and run its CPU-only health/readiness checks. Do not load model weights or send a warm-up inference.

### M4 — one real Parent UI verification

- Use the existing synthetic Parent, profile, StoryRun, confirmed subject/context, and artwork on the Android emulator. Do not create new accounts, profiles, runs, or redraw/re-run drawing understanding.
- Make exactly one fresh activity-suggestion request by tapping the real Parent UI; maximum elapsed worker wait is eight minutes. No direct Modal worker invocation, replay, automatic retry, or duplicate tap.
- Pass requires the authenticated API to return HTTP success, the UI to render the actual model/catalog result, and the server to persist the suggestion set so the existing flow can select and persist one main activity.
- Stop on this request's first success or failure. If it succeeds, continue one activity selection/persistence and one story generation/adult confirmation under existing approvals; a single silent LTX-2.5 request remains conditional on all prior gates and its existing exact authorization. If it fails, preserve diagnostics and prepare a new bounded amendment before any further inference.

## 4. Explicit exclusions

- No weakening or bypassing the language, schema, quality, safety, age, consent, catalog, activity-selection, story-review, or video-safety gates.
- No output post-processing that strips, substitutes, translates, or silently repairs generated text.
- No model/provider/checkpoint substitution; no video retry or warm-up; no quota/payment change or bypass; no database edit/migration; no `.env` or secret change; no real child data or fixtures; no SRS change; no commit or push.
- Keep the Android emulator online. Stop only Docker/Metro/Modal services started or used for this task; do not stop unrelated apps or the video app.

## 5. Exact file boundary

- `deployment/modal/srs_v23/language_audio_app.py`
- `deployment/modal/srs_v23/tests/test_qwen35_lesson_suggestion_contract.py`
- `features/FEAT-081-parent-ui-mobile-port/plan/PLAN_REVISION_36_PARENT_ACTIVITY_VIETNAMESE_OUTPUT_GATE_20261120.md`
- `features/FEAT-081-parent-ui-mobile-port/approvals/TASK_APPROVAL.md`
- `features/FEAT-081-parent-ui-mobile-port/status/STATUS.md`
- `features/FEAT-081-parent-ui-mobile-port/evidence/PARENT_API_AUTH_FULL_E2E_REV24_20261119/REV32_AUTH_RECOVERY_AND_E2E/`

