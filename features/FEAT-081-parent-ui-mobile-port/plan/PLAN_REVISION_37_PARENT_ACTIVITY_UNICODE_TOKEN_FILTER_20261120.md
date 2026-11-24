# FEAT-081 — Plan Revision 37: Parent activity Unicode token filter

- **Status:** APPROVED under the owner's continuing direct instruction on 2026-11-20 to keep fixing the real Parent workflow until it runs.
- **Feature/worktree:** FEAT-081, `feature/fe-mobile-remediation`, `<local-machine-path>
- **Product authority:** FEAT-063 v2.7-draft, §§1–31; especially BR-08, FR-P-05, §31.21 and NFR-13/21. SRS remains unsigned.
- **Relationship:** follows Plan Revision 36 after its one activity request failed the existing Vietnamese-script output gate.

## 1. Goal

Prevent the Parent activity worker from generating non-Latin letters in user-visible text while preserving Vietnamese Latin letters, the existing schema and quality gates, catalog-first matching, and the current model. Verify one fresh activity suggestion from the real authenticated Parent Android UI using the existing synthetic run.

## 2. Evidence and diagnosis

- Revision 36 UI request used existing StoryRun `ec455bbb-8211-49d5-8cef-9889df809de2`; Modal call `fc-01M7V8T2VAQ488YP3GP9ENJEVM` generated 682 tokens and ended with `MODAL_MODEL_OUTPUT_INVALID_NON_LATIN_SCRIPT`. The safe parser diagnostic identifies `no_match_reason` and one non-Latin letter. No generated text was retained.
- The worker already blocks vocabulary tokens decoding to a backslash, so JSON `\\uXXXX` escapes are not the remaining demonstrated cause. The worker needs an activity-only token filter for direct non-Latin letter tokens.
- The failure was not established as a 120-second client timeout. The live API container source reports no per-client timeout override; the activity workload default is 450 seconds. The API observed a Modal `ExecutionError` before terminal worker logs were indexed; Modal later recorded the worker's language-gate failure. Do not change timeouts without new evidence.

## 3. Authorized implementation

### M1 — detect and block non-Latin token candidates

- Extend the existing single tokenizer-vocabulary scan in `_build_lmfe_tokenizer_data`; do not add another full vocabulary scan per generated token.
- Collect IDs whose decoded token text contains an alphabetic Unicode character whose Unicode name is not Latin, checking both the token's standalone decode and its decode after the existing prefix context.
- Store the IDs in cached tokenizer data. For Parent activity only, filter both backslash-escape tokens and non-Latin-letter tokens from LMFE's allowed-token list. Other Qwen workloads retain their current behavior.
- Keep the final parser language gate. If filtering leaves no allowed candidates, fail closed with the existing safe decoder error; do not repair, translate, substitute, or retry the output.
- Add aggregate, privacy-safe decoder diagnostics for whether the filter is enabled and how many candidates it blocks. Never log model text, tokens, prompts, images, or Unicode characters.

### M2 — focused offline regression coverage

- Verify a direct CJK token is filtered from the Parent activity candidate list.
- Verify Vietnamese Latin letters and diacritics remain allowed.
- Verify the filter remains opt-in and does not change other Qwen workload decoder behavior.
- Keep parser checks for literal/escaped non-Latin text and catalog/fallback fields; verify failures expose only field path and count.
- Run Python compilation and focused activity decoder/parser tests. Use a task-local pytest temporary directory if the Windows default temp path still denies access. Test doubles are limited to offline unit tests; the real UI run must use the existing synthetic account/run and actual Modal worker.

### M3 — deploy and verify the exact worker

- Deploy only `sketch2life-srs23-language-audio-dev` to Modal `dev` from this worktree.
- Run the CPU-only Qwen3.5 readiness check. Do not load GPU weights, warm a model, or send a direct worker request.

### M4 — one real Parent UI activity attempt

- Reuse the authenticated synthetic Parent, profile, artwork, confirmed context, and StoryRun `ec455bbb-8211-49d5-8cef-9889df809de2` on the Android emulator. Do not create a new account, profile, run, artwork, or drawing inference.
- Submit exactly one activity suggestion from the actual Android UI, with an eight-minute hard cap and no replay, direct worker/API request, automatic retry, or duplicate tap.
- Pass requires an HTTP success, the UI showing the actual Qwen/catalog result, and a persisted suggestion set that permits selection of one primary activity.
- If it passes, continue one UI activity selection/persistence and one story generation plus adult review/confirmation under the existing approved limits. A single silent LTX-2.5 request remains conditional on every existing gate and its exact prior authorization. Do not touch quota/payment.
- If it fails, save sanitized diagnostics and stop inference under this plan. Prepare another amendment before any further AI request.

## 4. Explicit exclusions

- No weakening or bypassing language, schema, quality, safety, age, consent, catalog, activity-selection, story-review, or video-safety gates.
- No prompt/output post-processing that strips, substitutes, translates, or silently repairs generated text; no model/provider/checkpoint substitution.
- No drawing inference, new account/profile/run, real child data, fixture/mock in the live flow, direct database edit/migration, `.env`/secret change, quota/payment change or bypass, SRS edit, commit, or push.
- Keep the Android emulator online. Stop only task-used Docker/Metro/Modal services after evidence capture; do not stop unrelated Modal apps or the video app.

## 5. Exact file boundary

- `deployment/modal/srs_v23/language_audio_app.py`
- `deployment/modal/srs_v23/tests/test_qwen35_lesson_suggestion_contract.py`
- `features/FEAT-081-parent-ui-mobile-port/plan/PLAN_REVISION_37_PARENT_ACTIVITY_UNICODE_TOKEN_FILTER_20261120.md`
- `features/FEAT-081-parent-ui-mobile-port/approvals/TASK_APPROVAL.md`
- `features/FEAT-081-parent-ui-mobile-port/status/STATUS.md`
- `features/FEAT-081-parent-ui-mobile-port/evidence/PARENT_API_AUTH_FULL_E2E_REV24_20261119/REV32_AUTH_RECOVERY_AND_E2E/`
