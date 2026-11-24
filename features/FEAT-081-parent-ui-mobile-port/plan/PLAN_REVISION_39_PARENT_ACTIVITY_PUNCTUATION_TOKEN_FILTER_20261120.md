# FEAT-081 — Plan Revision 39: Parent activity punctuation token filter

- **Status:** APPROVED under the owner's continuing direct instruction on 2026-11-20 to keep fixing the real Parent workflow until it runs.
- **Feature/worktree:** FEAT-081, `feature/fe-mobile-remediation`, `<local-machine-path>
- **Product authority:** FEAT-063 v2.7-draft, §§1–31; especially BR-08, FR-P-05, §31.21 and NFR-13/21. The SRS remains unsigned.
- **Relationship:** follows Plan Revision 38. Rev38 produced a JSON-complete response but the unchanged punctuation gate rejected `fallback_activities[0].objective`; no activity was persisted. The failure was not a timeout.

## 1. Goal

Make the Parent activity decoder require a terminal punctuation mark before closing quotes in the four prose fields already checked by the worker, while preserving LMFE's bounded free-text fast path and all existing post-generation validation.

## 2. Evidence and technical diagnosis

- Rev38's one real Android UI request used the existing synthetic StoryRun `ec455bbb-8211-49d5-8cef-9889df809de2` and Modal call `fc-01M7VAJFS2C69SNHZSZA3J0FQ1`. Qwen3.5-9B completed 693 tokens in 112.178 seconds. The safe failure path was `fallback_activities[0].objective`; no suggestion set was stored.
- The pinned Modal image uses LM Format Enforcer 0.11.3. Its JSON free-text fast path reuses a cached allowlist that includes tokens ending in a JSON quote. Removing `"` from the character parser alone would therefore not enforce this contract.
- Correctly apply the punctuation condition in the existing Parent-activity-only token filtering pass. During the existing tokenizer vocabulary scan, collect token IDs whose decoded token ends in a JSON quote. For an active free-text value whose nearest object key is one of `objective`, `preparation_text`, `instructions_text`, or `safety_notes`, exclude those token IDs while the parsed value does not yet end (after trimming whitespace) in `.`, `!`, `?`, or `…`.
- Keep the existing activity-only backslash and non-Latin token filters. Reuse their existing per-callback candidate scan; do not add a regex schema, second vocabulary scan, output repair, or a new full-vocabulary decoder traversal.
- LMFE 0.11.3 primary source: [tokenenforcer.py](https://raw.githubusercontent.com/noamgat/lm-format-enforcer/v0.11.3/lmformatenforcer/tokenenforcer.py), [jsonschemaparser.py](https://raw.githubusercontent.com/noamgat/lm-format-enforcer/v0.11.3/lmformatenforcer/jsonschemaparser.py), and [tokenizerprefixtree.py](https://raw.githubusercontent.com/noamgat/lm-format-enforcer/v0.11.3/lmformatenforcer/tokenizerprefixtree.py).

## 3. Authorized implementation

### M1 — bounded punctuation constraint in the activity decoder

- During the existing tokenizer scan, record IDs for tokens whose decoded form ends in `"`; preserve all existing tokenizer metadata and filtering.
- Add a small safe state-inspection helper that identifies an active free-text value and its nearest schema object key from the LMFE parser state. Only the four already-required prose fields activate this rule. Key-name strings, catalog reasons, titles, materials, and all non-activity workloads remain unaffected.
- Extend the existing activity-only token-filter pass to block trailing-quote tokens only while the active required field lacks one of the same accepted terminal punctuation characters used by the post-generation parser.
- Keep the post-generation parser check unchanged as the second validation gate. Log only a boolean/count for punctuation-filter activity; never log model text, prompt, image, token IDs, or credentials.
- Do not change prompt text, model/provider/checkpoint, schema bounds, field limits, punctuation policy, timeout, token budget, language filter, or quality/safety rules.

### M2 — focused offline regression tests

- Verify the active required prose field blocks a quote-ending token before punctuation and allows it after punctuation.
- Verify the filter does not affect JSON key strings, non-required prose fields, or decoder instances outside Parent activity.
- Verify the vocabulary metadata is collected in the existing scan and the callback still applies the existing backslash/non-Latin filters.
- Run the focused worker test module selection, Python compilation, and `git diff --check`; use task-local temporary output only.

### M3 — worker deployment/readiness

- Deploy only Modal app `sketch2life-srs23-language-audio-dev` to environment `dev` from this worktree.
- Run its CPU-only readiness endpoint/function. Do not load model weights, warm a GPU, or make a direct worker/API request.

### M4 — one real Parent UI activity request

- Reuse the authenticated synthetic Parent, profile, drawing, confirmed context, and StoryRun `ec455bbb-8211-49d5-8cef-9889df809de2` on the online Android emulator.
- Make exactly one fresh activity-suggestion request through the real UI, capped at eight minutes. No retry, duplicate tap, direct API/worker call, new account/profile/run, drawing inference, fixture, or synthetic result.
- Pass requires the actual suggestion set to render in the UI and be persisted so a primary activity can be selected. Preserve catalog-first selection and all existing language, schema, punctuation, quality, age, consent, safety, and ownership gates.
- If activity succeeds, continue one UI activity selection/persistence and one story generation/adult review under existing unconsumed approvals. A single silent LTX-2.5 request is conditional on the exact existing authorization and every prior gate; this amendment adds no video-call allowance. If a gate is not executable, stop before that call.
- If the activity request fails, capture sanitized evidence and stop AI calls until a new bounded amendment is recorded.

## 4. Explicit exclusions

- No relaxing or bypassing language, schema, punctuation, quality, safety, age, consent, catalog, activity-selection, story-review, quota/admission, or video-safety gates.
- No regex-based LMFE constraint, output repair/translation, new model/provider, prompt/schema/limit/timeout change, or broad decoder rewrite.
- No new account/profile/run, real child data, live fixture/mock, direct database edit/migration, quota/payment mutation or bypass, `.env`/secret edit, SRS edit, commit, push, or unrelated service shutdown.
- Keep the emulator online. Stop only services started for this task after evidence capture; leave unrelated Modal apps and the video app untouched.

## 5. Exact file boundary

- `deployment/modal/srs_v23/language_audio_app.py`
- `deployment/modal/srs_v23/tests/test_qwen35_lesson_suggestion_contract.py`
- `features/FEAT-081-parent-ui-mobile-port/plan/PLAN_REVISION_39_PARENT_ACTIVITY_PUNCTUATION_TOKEN_FILTER_20261120.md`
- `features/FEAT-081-parent-ui-mobile-port/approvals/TASK_APPROVAL.md`
- `features/FEAT-081-parent-ui-mobile-port/status/STATUS.md`
- `features/FEAT-081-parent-ui-mobile-port/evidence/PARENT_API_AUTH_FULL_E2E_REV24_20261119/REV32_AUTH_RECOVERY_AND_E2E/`
