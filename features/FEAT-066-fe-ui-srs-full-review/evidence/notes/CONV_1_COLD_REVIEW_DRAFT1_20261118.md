# CONV-1 Draft 1 — cold review record (round 1, 2026-11-18)

- **Artifact:** `plan/PLAN_CONV1_BE_IMPLEMENTATION_APPROVAL_PACKAGE_DRAFT1_20261118.md`, 18,780 B, SHA-256 `7B638AE320AAFBEDA4FBF1FACDE3AE3F0984E571897EA1D35571D9DA23483972`.
- **Reviewer:** a separate subagent started by the coordinator session. Model Sonnet 5.5 (`claude-sonnet-5-5`), reasoning effort high, both set explicitly. It was read-only: no repository edits, tests, validators, database or network.
- **Pin check:** PASS for the package, the conventions contract (13,999 B, `1F41B74A…`), the SRS (701,157 B, `B9B1F42D…`) and the source base `08439b22`.
- **Verdict:** **NOT READY**. P1 = 1, P2 = 8, P3 = 7.
- **Coordinator spot-check:** the coordinator re-read the source for F1, F2, F4 and F5 and confirmed all four:
  - `be1_runtime.py` raises `SCOPE_DENIED` for a class or organization mismatch;
  - `openapi_contract.py` is generated from the Rev37 catalog;
  - `lesson_library.py:91` raises 422 for a malformed `If-Match`;
  - `parentWorkflowApi.ts:268-270` reads only `payload.detail`.

## Findings

| ID | Sev | Finding (short) | Fix planned for Draft 2 |
|---|---|---|---|
| F1 | P1 | The 404/403 split sends every policy refusal to 403. `SCOPE_DENIED` (class or organization not covered) would then reveal that another class exists. This contradicts C-D4 and §9.8 | Map per refusal code. Scope mismatches (`ADULT_NOT_ASSIGNED`, `SCOPE_DENIED` for organization or class) give 404. A role refusal inside an assigned scope gives 403. One test per branch |
| F2 | P2 | `openapi_contract.py` is generated (Rev37 catalog). The 422 logic lives in `openapi_contract_amendments.py`, and `openapi_srs_v22.py` renames `Be1Error`. Neither file is allowlisted. Families with no `responses=` get FastAPI's automatic 422 | Allowlist both modules and `test_openapi_schema_catalog_mapping.py`. Declare the 400 and the envelope through the amendments layer. Leave the generated file untouched |
| F3 | P2 | `middleware/bounded_image_upload.py` emits a 413 for Lesson Library without the envelope or `X-Request-ID`. 500s on legacy paths come from `ServerErrorMiddleware` | Allowlist the middleware. State that the `Exception` handler adds the header. Narrow AC5 to responses produced inside the app stack |
| F4 | P2 | The §2 claim is wrong: a malformed `If-Match` gives 422, not 400. Many `HTTPException(422, INVALID_REQUEST)` sites exist in Lesson Library, plus other 422 codes in `teacher_ai` and `parent_ai` | Correct §2. The handler remaps HTTP 422 with `INVALID_REQUEST` to 400. Classify the remaining 422 codes |
| F5 | P2 | CV-1's premise is false: the mobile parser reads only `payload.detail`. Two `/api/parent/v1/ai` paths are already enveloped through the story-runs branch. `test_parent_ai_late_result_guards.py` pins `{"detail"}` on sibling paths | Reframe CV-1 and ask the owner again. Option A needs a mobile parser change in lockstep. Allowlist or regression-guard that test |
| F6 | P2 | Copying the story-runs branch would give 400 `INVALID_IDEMPOTENCY_KEY` for a missing key. C-D5 and §21.4 reserve that code for key reuse with a different payload | Missing or malformed key: 400 `INVALID_REQUEST` with field code `REQUIRED` or `INVALID_FORMAT`. `INVALID_IDEMPOTENCY_KEY` only for a payload mismatch |
| F7 | P2 | The CV-2 table is incomplete. It maps `REQUEST_TOO_LARGE` to `MEDIA_TOO_LARGE`, but §9.8 has `LESSON_FILE_TOO_LARGE`. The upload codes are missing, and about 30 `*_NOT_FOUND` codes conflict with C-D4's uniform 404 | Complete the table, or limit CV-2 to the generic codes and list the exceptions. Ask the owner how far CV-2 goes |
| F8 | P2 | The message table has no fallback and no coverage list | A status-based Vietnamese fallback, and a coverage test |
| F9 | P2 | The `field_errors` vocabulary is unspecified. The story-runs reduction can echo unknown keys | Use the Parent code set, with a whitelist-or-`<unknown>` rule for field names, in a named module |
| F10 | P3 | Tests 15 and 17 do not pass through the app handlers. `backend/tools/be1_api_smoke.py` is missing from the list | Drop 15 and 17. Allowlist the smoke tool |
| F11 | P3 | The mount table omits the conditional `pilot_assistance` | Add the row |
| F12 | P3 | The `story_run_lite` `X-Correlation-ID` alias from contract C-2 is dropped silently | State that it is outside CONV-1 (a legacy demo family) |
| F13 | P3 | Two envelope variants will coexist. The derivation of `retryable` and `retry_after_seconds` is unstated | State both, and the derivation rule |
| F14 | P3 | The Lesson Library `STALE_REVISION` has no `current_version` or ETag, so C-D7 is deferred silently | State that it is deferred to the Lesson Library slice |
| F15 | P3 | The FE caller list is wrong. `AdminScreens.tsx` is not an error consumer, while `authService.ts`, `userService.ts` and `UsersPage.tsx` are missing | Fix the list |
| F16 | P3 | "An inactive account gives 404" is an interpretation, not a decision | Ask the owner (new CV-5) |

## Owner answers affected

On 2026-11-18, before this review, the owner answered CV-B (local-only branch) and "có hết" to CV-1 to CV-4.
- **CV-1:** that answer rested on the false premise in F5, so it is asked again.
- **CV-2:** asked again for its extent (F7).
- **CV-5:** new (F16).
- **CV-B, CV-3 and CV-4:** stand.

## Next

Draft 2 addresses F1 to F16, then review round 2. The D-171 limit is 5 rounds: stop if a finding class repeats or if P1 + P2 does not fall.
