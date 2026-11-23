# FEAT-081 — Plan Revision 38: Parent activity punctuation and safe diagnostics

- **Status:** APPROVED under the owner's continuing direct instruction on 2026-11-20 to keep fixing the real Parent workflow until it runs.
- **Feature/worktree:** FEAT-081, `feature/fe-mobile-remediation`, `<local-machine-path>
- **Product authority:** FEAT-063 v2.7-draft, §§1–31; especially BR-08, FR-P-05, §31.21 and NFR-13/21. SRS remains unsigned.
- **Relationship:** follows Plan Revision 37. The Unicode filter passed its language check, but the real response failed the existing sentence-punctuation contract.

## 1. Goal

Keep the existing Parent activity content-quality rule intact and make Qwen3.5 reliably emit complete Vietnamese sentences. If it fails again, record only the failing field path so the failure is diagnosable without retaining generated text. Verify one fresh suggestion through the authenticated Parent Android UI.

## 2. Evidence and diagnosis

- Revision 37 UI request used StoryRun `ec455bbb-8211-49d5-8cef-9889df809de2`; Modal call `fc-01M7V9SVGD1WXFXD4FS07TSYA2` generated 746 tokens in 111.629 seconds and returned a JSON-complete response. The Unicode gate did not fail.
- The worker rejected the response with `MODAL_MODEL_OUTPUT_INCOMPLETE_TEXT`. The current parser raises this when any nonempty `objective`, `preparation_text`, `instructions_text`, or `safety_notes` field does not end with an accepted sentence terminator. The exact field was not logged; model text was not retained.
- The prompt already generally requests punctuation. Rev38 makes the requirement field-specific and asks for a final ASCII period before each closing JSON quote. This is an instruction change only; it does not weaken the parser gate.
- The API observed a generic Modal terminal error before Modal's specific terminal log was indexed. The client allows 450 seconds for this workload and no inference timeout was observed; do not modify timeout settings.

## 3. Authorized implementation

### M1 — clearer field-level generation instruction

- State that `objective`, `preparation_text`, and `safety_notes` each contain one concise Vietnamese sentence ending with ASCII `.` as the final non-whitespace character before the JSON quote.
- State that `instructions_text` contains two short Vietnamese sentences, each ending with `.`, and its last character before the closing quote must be `.`.
- Keep all current length limits, outdoor requirement, child-led wording, adult role, catalog-first choice, fallback count, age and safety rules.
- Keep the Rev37 activity-only non-Latin/backslash token filter and final parser checks.
- Do not add regex patterns to the LMFE schema, increase output-token limits, post-process/repair text, or relax punctuation checks.

### M2 — privacy-safe field diagnosis and offline regression tests

- Introduce a dedicated parser error carrying only the failing schema field path and the existing safe code `MODAL_MODEL_OUTPUT_INCOMPLETE_TEXT`.
- Emit `invalid_text_field_path` for that error in the worker's structured invalid-output event. Do not include the field value, character, generated JSON, prompt, image, or token IDs.
- Add unit tests for each required sentence field, ensuring the unchanged punctuation rule rejects missing terminators and that diagnostics contain only the field path/code. Add a prompt regression check for the explicit final-period instruction.
- Run Python compilation and focused Parent activity parser/decoder tests using a task-local temporary directory if needed.

### M3 — deploy and verify the worker build

- Deploy only `sketch2life-srs23-language-audio-dev` to Modal `dev` from this worktree.
- Run only the existing CPU readiness function; do not load model weights, warm GPU, or send a direct worker request.

### M4 — one UI-driven activity verification

- Reuse the authenticated synthetic Parent, profile, artwork, confirmed context, and StoryRun `ec455bbb-8211-49d5-8cef-9889df809de2` on the Android emulator.
- Submit exactly one fresh activity-suggestion request from the real UI, with an eight-minute hard cap and no retry, replay, direct API/worker call, or duplicate tap.
- Pass requires HTTP success, the actual suggestion set rendering in the UI, and backend persistence that permits selecting one primary activity.
- If it passes, continue one UI activity selection/persistence and one story generation plus adult review under existing approvals. One silent LTX-2.5 request remains conditional on all current gates and its exact prior authorization. No quota/payment work.
- If it fails, save sanitized evidence and stop AI requests until another amendment is approved.

## 4. Explicit exclusions

- No weakening or bypassing language, schema, punctuation, quality, safety, age, consent, catalog, activity-selection, story-review, or video-safety gates.
- No output repair/translation, model/provider/checkpoint substitution, regex-based decoder constraints, generation-token-limit increase, timeout increase, new account/profile/run, drawing inference, real child data, or fixture in the live flow.
- No direct database edit/migration, `.env`/secret change, quota/payment change or bypass, SRS edit, commit, or push.
- Keep the Android emulator online. Stop only task-used Docker/Metro/Modal services after final evidence capture; do not stop unrelated Modal apps or the video app.

## 5. Exact file boundary

- `deployment/modal/srs_v23/language_audio_app.py`
- `deployment/modal/srs_v23/tests/test_qwen35_lesson_suggestion_contract.py`
- `features/FEAT-081-parent-ui-mobile-port/plan/PLAN_REVISION_38_PARENT_ACTIVITY_PUNCTUATION_DIAGNOSTICS_20261120.md`
- `features/FEAT-081-parent-ui-mobile-port/approvals/TASK_APPROVAL.md`
- `features/FEAT-081-parent-ui-mobile-port/status/STATUS.md`
- `features/FEAT-081-parent-ui-mobile-port/evidence/PARENT_API_AUTH_FULL_E2E_REV24_20261119/REV32_AUTH_RECOVERY_AND_E2E/`
