# EV-063-87 — Parent non-video API/UI and Rev78 activity suggestions

**Date:** 2026-11-11 (Asia/Saigon)
**Product authority:** FEAT-063 SRS v2.7-draft Rev60, unsigned. The later owner catalog-first clarification is recorded as D-172; the SRS remains unchanged and unsigned.
**Approved scope:** Plan Rev78, SHA-256 `127E471CD737E0E1C2A4FD33FF49B2A7790A814C1F8FD7B85A1BFEBC2C27E408`; Plan Rev78A, SHA-256 `03F777103B23A56FDEC398CA940094A62DF26EDE28B35DA56BE4FBA96C077183`
**Data:** synthetic account/profile and generated butterfly artwork only. No real-child media or identity was used. No video workload was called.

## Result

**PARTIAL.** Parent registration, authentication, consent/profile setup, StoryRun creation, drawing analysis and adult subject confirmation passed in the earlier connected API run. The published/shared Parent lesson gallery returned zero eligible lessons, so only fallback was available; catalog selection could not be exercised against live catalog content. Rev78A's gate changes and local checks pass, but its one live inference was cancelled before producing output, so live quality-gate acceptance remains unknown.

### Earlier Rev78 worker results

The first Qwen3.5 fallback call completed without timeout and returned three schema-shaped drafts in 105.412 seconds. Review found multiple prose fields ended mid-sentence at their character limits; replay through the stricter sentence-completeness gate rejected it with `ACTIVITY_TEXT_INCOMPLETE`.

A later call tested an initial punctuation-constrained schema. Model loading and decoder setup completed, but LM Format Enforcer raised `LMFormatEnforcerException` because its parser does not support a string schema combining `pattern` with `minLength`/`maxLength`. That incompatible schema was corrected before Rev78A.

### Rev78A quality gate and one live retest

Rev78A makes `materials_text` and `observation_notes` concise phrase/list fields without mandatory sentence punctuation. Objective, preparation, instructions and safety remain sentence-complete; their generation budgets were reduced. The backend still enforces age, outdoor suitability, child choice, Montessori exploration, adult support, safety markers/actions, context match, exactly-three count, uniqueness, catalog deduplication, PII and Vietnamese Latin script. Prompt, Modal JSON schema, worker parser and backend response limits were aligned. The schema avoids combining regex patterns with length keywords.

Focused tests passed (**28 passed**); Ruff and `py_compile` passed. The updated `sketch2life-srs23-language-audio-dev` app deployed successfully. One synthetic fallback inference started on Qwen3.5-9B revision `c202236235762e1c871ad0ccb60c8ee5ba337b9a`. Model loading took 12.672 s and constrained decoder setup 2.833 s; the worker then remained in `model_inference` without a terminal event for 976.326 s. Modal logs reported missing `causal_conv1d` and `flash-linear-attention` and fallback to slower reference PyTorch kernels. To limit GPU use, the exact function call was cancelled after more than 16 minutes. It returned no output, so the application quality gate was not reached. No retry was made. The event summary is in `runtime/rev78a-live-inference-review.json`; the raw client failure record is `runtime/rev78-fallback-worker-failure-151251.json`.

## Parent API path exercised

| Step | Result | Timing / note |
|---|---|---|
| Backend registration and Firebase sign-in | Pass | Synthetic Parent only; credentials were not recorded in evidence |
| `/api/auth/v1/me`, consent and profile operations | Pass | Synthetic profile and test consent |
| Parent lesson gallery | Pass, empty | 0 Parent-accessible published/shared lessons in the dev data |
| StoryRun creation and image upload | Pass | Generated butterfly artwork |
| Qwen3.5 drawing analysis | Pass | HTTP 200; approximately 46.2 s; model revision `c202236235762e1c871ad0ccb60c8ee5ba337b9a` |
| Adult subject confirmation / current-run read | Pass | Confirmed drawing context before activity suggestion |
| Initial `POST /api/parent/v1/ai/story-runs/{run_id}/activity-suggestions` request | Fail closed | HTTP 502 quality-gate rejection; the first output lacked explicit outdoor markers and a safe fabric term was falsely matched as fire |
| First worker/service retest after batch 1 | Rejected | Qwen output had weak child-choice wording, repeated procedures, non-Latin characters and clipped fields; safe gate diagnostics were added |
| Synthetic Modal fallback output | Worker completed; output rejected on replay | 105.412 s; call `fc-01M75FQMWZ2CZSXNMT2C65C275`; 0 catalog candidates; decision `NO_MATCH`; exactly 3 drafts; `ACTIVITY_TEXT_INCOMPLETE` |
| Punctuation-grammar compatibility check | Worker failed before token generation | 33.829 s; call `fc-01M75GCGV1E4CFPX3EPXJ1EJWT`; model loaded, then LM Format Enforcer rejected `pattern` combined with min/max length |
| Rev78A Modal deployment | Pass | Language/audio app deployed with shorter core prose limits and fragment allowances for materials/observation |
| Rev78A single synthetic fallback inference | Cancelled before output | 976.326 s; call `fc-01M75HS5EDVSVC60CJ33KGPCY6`; last worker stage `model_inference`; no gate verdict; missing optimized kernels reported |

The first worker's exact three drafts and retrospective gate result are preserved in `runtime/rev78-fallback-successful-worker-output.json`; its offline replay diagnostic is in `runtime/rev78-final-fallback-gate-review.json`. The grammar compatibility failure is in `runtime/rev78-final-worker-schema-failure.json`. The successful worker log summary contained 20 structured events and identified Qwen3.5-9B at the pinned revision. Model load took 19.701 s and constrained-decoder setup 4.510 s. That call did not time out. Modal log indexing initially missed its terminal event, although the worker returned successfully; later logs showed the exact LM Format Enforcer exception and terminal worker failure for the schema compatibility call.

## Rev78 implementation and checks

- Parent suggestions now query only versions from published/shared lessons the Parent may access, preserve exact version/hash provenance, and send bounded candidates plus minimized context to Qwen3.5. The ACT demo catalog is excluded.
- When no candidate is eligible or suitable, the worker may draft exactly three temporary activities. The API returns canonical catalog content for matches and never lets AI rewrite a catalog item.
- The backend gate rejects incomplete core sentences and still enforces age, outdoor, child-agency, safety, context, duplication and schema rules. Materials/observation fields now allow concise fragments; their content remains subject to the same safety, language, PII and context checks. Rejected output remains skippable and is not saved to the catalog or pinned lesson.
- The worker prompt and response budgets are shorter. Only the four core sentence fields use bounded punctuation patterns; materials/observation use `maxLength` only. Worker parser and Pydantic response limits match. The language/audio app was deployed successfully after a zero-task check; all three existing Modal dev apps remained deployed and later showed 0 tasks after scale-down.
- Rev78A focused tests: **28 passed** across the Parent activity service and worker-contract suites. Ruff and `py_compile` passed. Pytest emitted only a cache-permission warning after the passing run.
- The live Rev78A call reached model inference but was cancelled after 976.326 s with no terminal worker event. Missing optimized kernels and reference PyTorch fallback are evidenced in Modal logs. The deployed schema was therefore not validated on a completed generation, and no API/UI E2E was run after this change.

## UI and acceptance limits

- The evidence folder contains screenshots from the earlier Parent workflow up to activity review, but none demonstrates a successful Rev78 catalog match or a post-fix activity result.
- ADB is unavailable in the current environment, so no fresh Android-connected UI run was completed for the catalog-first change. The optional microphone/transcript screens in the Expo shell call audio-transcription routes that are not part of this Rev78 branch; use typed idea input for the verified activity/story contract. The voice path remains unverified.
- The live dev catalog had no eligible published/shared activity. Automated tests cover candidate selection and versioned hydration, but the deployed catalog-match path remains unverified.
- The Docker API container was not rebuilt/restarted after the final quality-gate change, and the authenticated Parent endpoint was not re-run after the worker fix. The final test was a direct Modal worker call followed by the actual application service and an offline replay, not a post-fix full HTTP/UI E2E.
- The isolated test DB contains only synthetic test data. A test-only Firebase identity from the earlier failed harness may remain in the dev Firebase project; no credentials were saved or printed. No `.env` or Modal secret was inspected or changed.
- During the runtime test, no video API or Lightning adapter was used, and no Modal app stop was performed. Git publication was completed afterward: commit `34b92194867e915040aae1a1178dee0e526a60c3` is verified on both `origin/codex/feat063-parent-catalog-20261111` and `origin/dev` after a fast-forward merge. The `dev` push included its 21 pre-existing local commits; GitHub reported that the pull-request-only rule was bypassed for the owner-authorized push.

## Publication-scope local verification

- Backend Parent activity service/worker tests: 28 passed.
- Expo Parent tests: 26 passed; TypeScript typecheck passed with the full workspace dependency graph installed from the local pnpm store.
- Python compilation passed; Alembic reports 20261110_parent_lesson_pin as the single joined head across the existing migration branches.
- Ruff passes on the new catalog service/port and focused tests. A broader check of touched legacy modules still reports lint diagnostics in those modules; this closeout does not claim the whole legacy codebase is Ruff-clean.
- Repository security validation passed before publication: 7,223 publishable files scanned; environment files, seed accounts, credentials, signing keys and external reference documents excluded; no absolute machine paths found.
- The Alembic migration was not applied to PostgreSQL. No live Parent HTTP/UI retest was run after Rev78A because its sole approved Modal inference returned no output and the catalog was empty; no video was called.
