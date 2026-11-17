# FEAT-033 implementation follow-up — 2026-09-30

This follow-up contains catalog measurements, synthetic API smoke results, and emulator performance
metadata only. It contains no real child profile, drawing, audio, preference text, provider body,
credential, or screenshot.

## Catalog coverage and expansion decision

The reproducible JSON report is `../metrics/CATALOG_COVERAGE_20260930.json`. Generate it from the
repository root with:

```powershell
$env:PYTHONPATH = 'backend/src;.'
backend\.venv\Scripts\python.exe backend/tools/audit_child_profile_catalog.py `
  --output features/FEAT-033-montessori-profile-and-flow-recovery/evidence/metrics/CATALOG_COVERAGE_20260930.json
```

The audit joins the current 300 semantic profiles to their 300 templates and reports concept × age,
objective × age, declared FEAT-022 demand-family × age, authored readiness metadata, prerequisites,
materials, supervision, safety metadata, candidate counts, and distinct activity-family counts.
Demand tiers are an audit-only mapping from FEAT-022 Decision 2; no tier field or matching behavior
was added to runtime records. Each applicable concept-age target is compared using distinct
activity IDs after the static gate simulation; objective coverage separately requires two distinct
activity families.

| FEAT-022 tier | Applicable concept-age slices | Below candidate target | Empty after static gates |
|---|---:|---:|---:|
| A (target ≥5) | 49 | 49 | 35 |
| B (target ≥3) | 29 | 29 | 19 |
| C (target ≥2) | 36 | 27 | 22 |

Across the 61 applicable objective-age slices, 41 had fewer than two distinct activity families
after the static gates and 34 were empty. Across 68 declared demand-family-age rows, 44 had no
surviving candidate; `house/home` has no mapped catalog concept in any age band. The report also
finds 100/300 templates with `AUTHORED` readiness metadata and 200/300 with `UNSPECIFIED`; the
static upper-bound simulation yields 85 candidate profiles if all authored prerequisites are
observed. With child readiness unobserved, 17 otherwise eligible candidates remain because their
authored templates have no readiness IDs; this does not satisfy or bypass any readiness prerequisite.
This is a conservative metadata-coverage simulation, not a live recommendation count: it assumes
age-band midpoints, an adult can provide direct supervision, all materials are available, and no
unobserved activity-history prerequisite is met. It does not evaluate the actual drawing topic,
per-activity context answers, or runtime safety.

The measured gaps are real, but no new activity or readiness statement was inserted. The existing
records require authoritative provenance, a safe age adaptation, observable outcomes, materials,
supervision/safety rationale, and a qualified reviewer; increasing count or marking generated text
as reviewed would violate FEAT-022 and the approved plan. The catalog expansion backlog should start
with readiness metadata review and the empty Tier A/B concept-age slices, especially the missing
house/home family. FEAT-022 groups space with sun/moon; the present concept tags do not isolate
space as its own demand family.

## Current feature verification

- Full backend unit and contract suite from the repository root: passed. Existing Pillow
  `Image.getdata` deprecation warnings remain in unrelated mask tests.
- FEAT-033 catalog-audit helper tests: 2 passed. Targeted Ruff over modified/added backend source,
  tests, the report tool, and Lightning V2 server: passed.
- A broader Ruff scan of all backend source/tests/tools is not clean: it reports nine lint findings
  in five untouched files (`semantic_personalization_v2.py`, `activity_preparation.py`,
  `learning_media.py`, `test_learning_media_scenario_matrix.py`, and
  `benchmark_sam21_synthetic.py`). These unrelated files were left unchanged; all modified/added
  backend files pass the targeted Ruff check.
- Mobile TypeScript `tsc --noEmit`: passed; `npm test` reports `UI_COPY_AND_RECOVERY_VALID`.
- `git diff --check`: passed. Repository security validator: `REPOSITORY_SECURITY_VALID`, 10,952
  publishable files scanned; no credentials or absolute machine paths.
- Emulator: Android `sdk_gphone16k_x86_64` (`emulator-5554`) foregrounded the app; reverse
  `tcp:8081 -> tcp:8081` was active. Metro listened on 8081 (PID 27872); local backend listened on
  8000 (PID 15644) and `/health` returned `ok`.
- The profile screen visibly uses adult-entered free-text interest/avoid fields and an explicit AI
  action. No fabricated progress examples or global readiness checklist are shown. Adult presence is
  confirmed in-session; activity supervision remains a candidate-level decision. No network action
  is bound to text change; the classifier is invoked only by the explicit action.
- A contract review found that the mobile serializer already omitted proposal IDs until the adult
  confirmed them, but the V2 backend contract could not represent or enforce that confirmation. The
  V2 profile now carries `preference_tags_confirmed`; non-empty interest/avoid tags without that flag
  fail with a safe typed 422. The mobile request carries the flag and still sends empty arrays before
  confirmation. Contract coverage verifies both confirmed success and unconfirmed rejection without
  echoing the tag value.
- The phase-one candidate list is now sorted by activity ID after selecting the bounded
  topic/age-compatible set, preventing semantic score order from looking like a recommendation
  rank. The contract regression asserts this stable unranked display order; final ranking remains
  after adult context answers and hard gates.
- After resetting Android graphics counters and performing three controlled profile scrolls,
  `gfxinfo` recorded 130 frames, 3 janky (2.31%), P95 frame duration 19 ms, zero slow-UI-thread
  frames, and 3 slow draw-command frames. This is a scroll/frame sample, not the plan's P95
  text-input-to-paint measure. No valid pre-change baseline or input-to-paint trace is available;
  AC-09 is therefore not claimed as fully met.
- No current `ReactNativeJS` fatal was found in the recent emulator log sample. The activity remained
  foregrounded after relaunch. A later touch-only profiling attempt returned no usable
  input-event-linked framestats and navigated the emulator back to onboarding; it is not included as
  performance evidence. The app was restored to foreground, and the test did not classify or persist
  any profile text.

## Live classifier blocker

A single synthetic preference classification was sent through the local mobile backend contract.
The API returned `ChildPreferenceClassificationFailureV1`, HTTP 502, code
`CLASSIFIER_UNAVAILABLE`, `retryable=true`. The backend log recorded only the bounded request ID,
failure code, and retryability; it did not record the submitted phrase. The Lightning upstream closed
the connection, so no successful AI result, tag confirmation, contextual-readiness round trip, or
Gate-B happy path could be verified. Unit/contract tests verify safe responses, but a live L4 success
requires the deployed Lightning Studio to run the current `/v2/profile/preferences/classify`
implementation with its Qwen worker available. The backend and Metro remain running locally.

## Remaining acceptance evidence

- AC-04/AC-10: repeat one explicit classification and the Android readiness → final-candidate →
  Gate-B path after the Lightning endpoint is available.
- AC-08: a qualified Montessori reviewer must approve source-backed readiness and activity additions;
  the present report is the pre-expansion baseline and no content was fabricated.
- AC-09: capture a valid input-event-to-paint trace on the agreed emulator and compare it to a
  pre-change baseline. The measured scroll result is useful but does not substitute for that trace.

## Continued verification and revision guard — 2026-09-30

Evidence ID: `FEAT033-EV-20260930-02` · Related criteria: AC-03, AC-04, AC-09, AC-10, AC-11.
Environment: Windows PowerShell, Android `emulator-5554` (`sdk_gphone16k_x86_64`), local Expo
Metro and local backend. No preference text was entered for this check, and no screenshot or raw
profile data was retained.

- Code review found that a successful classification left the AI button available for the same
  unchanged draft, allowing duplicate model requests; the UI also discarded the classifier's
  `interest_unmapped` / `avoid_unmapped` flags. Added a session-local revision gate: one successful
  inference completes the current draft revision, editing creates a new revision, failed inference
  remains explicitly retryable up to two attempts per revision, and a stale response cannot
  complete a newer revision. The form now explains unmapped/no-match results and requires editing
  before classifying an already-successful revision again. Revision-gate regression checks run in
  the existing mobile test command.
- `npm test`: `UI_COPY_AND_RECOVERY_VALID`, including duplicate-submit, stale-response, fresh-edit,
  and two-attempt-limit behavior.
- `tsc --noEmit -p apps/ui-mobile/tsconfig.json`: passed.
- Metro virtual Android entry bundle request returned HTTP 200 in 0.05 seconds after the retry-cap
  change. The app was
  relaunched from the dev client; `MainActivity` remained foregrounded, ADB reverse `8081 -> 8081`
  remained active, and the recent React Native log sample had no fatal/unhandled match.
- Backend health returned `{"status":"ok","service":"sketch2life-api"}`. The complete backend
  unit/contract suite passed with an isolated repository-local pytest base directory:
  `backend\.venv\Scripts\python.exe -m pytest backend/tests/unit backend/tests/contract
  --basetemp=backend/.pytest-tmp-feat033-rerun-20260930` → 1,648 passed, 8 skipped, 26 warnings
  (153.57 s). The default Windows pytest temp location was access-denied, so the first attempt had
  setup errors before test bodies; the isolated run removed that environmental failure. Existing
  Pillow deprecation and pytest-cache permission warnings remain.
- `backend\.venv\Scripts\python.exe tools/validate_repository_security.py` returned
  `REPOSITORY_SECURITY_VALID`, 13,237 publishable files scanned, with absolute machine paths absent.
  The test-generated `.vision.env` under the scratch directory was removed after the validator
  correctly identified its synthetic absolute path.
- `git diff --check`: passed. Targeted backend Ruff and the feature catalog-audit helper tests had
  passed in the earlier verification recorded above.
- AC-09 remains incomplete: the existing controlled scroll sample is not a text-input-to-paint
  measurement and there is no valid pre-change baseline. Do not infer input latency from the 19 ms
  frame-duration p95.
- AC-04 / AC-10 remain incomplete: successful Lightning inference and the complete Android
  readiness-to-Gate-B flow are still blocked by the remote upstream connection failure documented
  above. AC-08 still needs source-backed catalog review by a qualified Montessori reviewer.

## Connected AVD input-frame proxy — 2026-09-30

Evidence ID: `FEAT033-EV-20260930-03` · Related criterion: AC-09 (partial evidence only).
Environment: Android `emulator-5554` (`sdk_gphone16k_x86_64`), development client, connected
through Metro reverse `8081 -> 8081`. A short synthetic phrase was entered locally in the
session-only profile field, followed by 24 separate synthetic character changes. The dev-only
instrumentation measured from the JavaScript `onChangeText` callback to the next animation frame;
the Android log reported `event_to_next_frame_ms=40.80` for that sample set. No raw text was logged,
transmitted to the classifier, or retained as evidence. The test draft was cleared afterward, and
the temporary screenshots/UI artifacts were deleted rather than stored in the feature evidence.

This is a useful JS scheduling/render proxy and is below 100 ms for this sample, but it is not a
native keyboard-event-to-visible-pixel latency trace: the timer begins after React Native delivers
`onChangeText`, and the next animation-frame callback does not prove the updated pixels were
presented. No comparable valid pre-change baseline exists. Therefore AC-09 remains incomplete and
the plan's `<100 ms` input-to-paint target is neither claimed as passed nor waived. Emulator stayed
on the profile screen with the synthetic draft cleared; the local app was not asked to classify it.

- `npm test`: `UI_COPY_AND_RECOVERY_VALID`; `npx tsc --noEmit -p tsconfig.json`: passed;
  `git diff --check`: passed (Git emitted only existing CRLF normalization warnings in unrelated
  FEAT-029 files).
- Repository security validator: `REPOSITORY_SECURITY_VALID`, 13,237 publishable files scanned;
  no credentials or absolute machine paths.
- Backend `/health`: HTTP 200, `{"status":"ok","service":"sketch2life-api"}`. Metro
  `/status`: HTTP 200; virtual Android bundle: HTTP 200, 7,889,996 bytes in 204 ms.
- AVD remained connected as `emulator-5554`, app `MainActivity` foregrounded, and ADB reverse
  `8081 -> 8081` active. Recent 1,000-line logcat sample had no fatal-exception or ReactNativeJS
  unhandled/error match. No screenshots or UI dumps are retained.
- Remaining AC-04/AC-10, AC-08, and AC-09 requirements are unchanged: live Lightning classifier
  success and full Gate-B smoke; qualified source-backed catalog review; and a valid native
  input-to-paint trace with a comparable baseline.

## Fresh backend-to-Lightning route probe — 2026-09-30

Evidence ID: `FEAT033-EV-20260930-04` · Related criteria: AC-04 and AC-10 (blocker revalidated).
A bounded synthetic preference request was sent through the currently running local backend
route `/v1/profile/preferences/classify`. The verified response was the backend's typed failure contract with
HTTP 503, code `CLASSIFIER_ENDPOINT_UNAVAILABLE`, `retryable=false`, and the safe message that the
Lightning AI service must be updated/restarted or the profile can proceed without personalization.
No raw input text was included in this evidence. The local route and UI safe-failure mapping are
present; the connected Lightning deployment currently returns not-found for
`/v2/profile/preferences/classify`, before any Qwen inference is run.

Current code inspection confirms that `tools/lightning_vision_v2_server.py` registers that route and
passes the shared `_QWEN_GENERATION_RUNNER` under the existing Qwen request lock, so the committed
design does not create a second Qwen worker. The live 503 means the external Lightning Studio is
running a version predating this route; updating/restarting that remote checkout is required to
prove classification, tag confirmation, and the Android Gate-A → contextual readiness → Gate-B
happy path. This local implementation turn does not push or mutate the remote deployment.

- Focused backend contract/unit run covering the profile material-ID contract, bounded classifier,
  missing-route translation, topic resolver, catalog-audit helpers, P1 hard gates, and the mobile
  session API: 97 passed.

## Stale classifier commit-boundary fix — 2026-09-30

Evidence ID: `FEAT033-EV-20260930-05` · Related criteria: AC-03 and AC-04.
Review found that the backend-owned mobile context function wrote returned AI proposals to the
session profile before `Flow1Screens` checked whether the submitted preference revision was still
current. The text field and child picker are disabled while a request is in flight, which limits the
normal race, but the commit order contradicted the stale-response safeguard and left future callers
unprotected.

The context method now returns the typed proposal without changing profile state. The screen builds
and applies the proposal patch only after both the submitted revision and the active child ID match;
the patch always sets `preference_tags_confirmed=false`. Regression cases cover accepted results,
stale revisions, changed-child responses, duplicate submit, bounded retries, and stale result
rejection. The static mobile validator also ensures the context request method does not mutate the
profile before UI acceptance.

- `npm test`: `UI_COPY_AND_RECOVERY_VALID`.
- `npx tsc --noEmit -p tsconfig.json`: passed.
- Metro virtual Android entry bundle: HTTP 200, 7,890,036 bytes.
- Backend `/health` returned HTTP 200; `emulator-5554` stayed connected with `MainActivity`
  foregrounded and ADB reverse `8081 -> 8081`; the latest 500-line logcat sample contained no
  fatal exception or ReactNativeJS error match.
- `git diff --check` passed. Repository security validator returned `REPOSITORY_SECURITY_VALID`
  with 13,237 publishable files scanned and no absolute machine paths.
- No backend code or remote Lightning deployment changed in this follow-up; prior verified 503
  route-missing status remains the blocker for a live classifier success.

## Repeat connected-AVD input/frame trace attempt — 2026-09-30

Evidence ID: `FEAT033-EV-20260930-06` · Related criterion: AC-09 (partial evidence; not a pass).
The `Pixel_10` AVD (`sdk_gphone16k_x86_64`, 1080×2424) was using Android Emulator OpenGL ES
translated to the host NVIDIA GeForce GTX 1660 SUPER, not SwiftShader. After resetting app graphics
counters, a synthetic 24-character text-input sample was entered in the profile field and cleared.
The dev-only JS callback-to-next-frame display reported p95 23.06 ms across 24 samples.

`dumpsys gfxinfo ... framestats` returned 30 completed frames during the input sample; the
`HandleInputStart` → `FrameCompleted` duration was p50 16.46 ms, p95 22.50 ms, and max 34.27 ms.
However, `InputEventId` was zero for all 30 rows, so the trace could not correlate individual key
events with their resulting frames. These values are frame-processing proxies, not native
input-to-presented-pixel latency. The broader 63-frame interaction/recovery window reported p95
frame duration 18 ms, modern janky frames 53/63 (84.13%), legacy janky frames 3/63 (4.76%), 9 high
input-latency events, 2 slow UI-thread frames, and 46 slow issue-draw-command frames. The modern
and legacy jank counters disagree substantially, and the interval includes keyboard, typing,
clearing, and recovery actions; it is not an app-only baseline. A separate 3-second idle sample had
only 6 frames, too few for a stable comparison.

The synthetic text was cleared; no screenshot, UI dump, or raw text is retained. The old 40.80 ms
and new 23.06 ms JS proxies used the same callback-to-next-frame definition but different emulator
interaction windows, so they are repeat samples, not a before/after code comparison. AC-09 remains
incomplete: there is no comparable pre-change baseline and no event-correlated present trace. The
emulator is hardware-accelerated, but the available evidence cannot cleanly attribute the jank to
the app versus emulator/compositor scheduling.

## API validation/proxy error distinction and current Metro route — 2026-09-30

Evidence ID: `FEAT033-EV-20260930-07` · Related criteria: AC-02, AC-09 (integration check only), AC-10 (partial).
The mobile client no longer reads response bodies with `response.json().catch(() => null)` and then
collapses all untyped responses into “Backend returned an unreadable response.” It now parses the
response text without retaining or logging it and classifies: typed workflow failures; FastAPI
422 `detail` arrays; unrecognized/non-JSON 422 responses; 502/503/504 upstream failures; other
non-JSON API/proxy responses; invalid successful JSON; authorization; missing routes; and other
backend failures. Safe messages contain no server response body or submitted profile values.
Regression cases cover the typed classifier failure, valid validation response, malformed 422,
gateway HTML, non-JSON 200, and JSON `null` success. The mobile test command and TypeScript check
passed.

An initial Metro probe used `/index.bundle`, which returned 404 because this Expo monorepo's actual
app entry is nested under `apps/ui-mobile`. Testing the correct `/apps/ui-mobile/index.bundle`
route on the existing Metro server returned HTTP 200 (8,088,466 bytes); Metro output confirmed
`apps/ui-mobile/index.ts` bundled. The local API health endpoint returned HTTP 200. Android
`emulator-5554` remained connected, `MainActivity` was foregrounded, and ADB reverse `8081 -> 8081`
was present. A temporary second Metro process used to validate the nested route was stopped; the
existing backend, Metro, emulator, and reverse mapping were left running. The earlier 404 was a
probe-path error, not evidence of an app Metro failure.

After this evidence update, `git diff --check` passed (Git emitted only existing CRLF warnings in
unrelated FEAT-029 files), and `python tools/validate_repository_security.py` returned
`REPOSITORY_SECURITY_VALID` with 13,239 publishable files scanned and no absolute machine paths.
AC-04/AC-10 still require the current remote Lightning classifier route and a complete successful
classification → contextual readiness → Gate B run. AC-08 still needs qualified catalog review.
AC-09 still lacks a comparable baseline and a valid native input-to-presented-pixel trace.

## Catalog production-eligibility audit correction — 2026-09-30

Evidence ID: `FEAT033-EV-20260930-08` · Related criterion: AC-08.
Review of the FEAT-022 Decision 3 gate against the loaded catalogs found that the earlier coverage
matrix intentionally included every non-blocked/non-deprecated profile, but its “review eligible”
and “ideal static gate survivor” labels did not make the pre-production status split prominent.
The current 300 semantic profiles and matching P1 templates are 200 `DEMO_ELIGIBLE` and 100
`PROVISIONAL_OWNER_REVIEWED`; both catalogs have zero `PRODUCTION_APPROVED` records and zero
`production_eligible=true` records. Thus the 85 prior static survivors are an upper bound within
the demo/provisional review scope, not production availability.

The audit now reports both catalog status distributions and production-eligible survivors. A
candidate counts as production eligible only when both its semantic profile and matching P1
template are explicitly `PRODUCTION_APPROVED` and marked `production_eligible=true`; the current
post-static-gate production count is zero. Regression coverage verifies that a semantic-only
approval, a provisional pair, or one missing side cannot be counted as production approved. The
coverage report was regenerated; the current catalog itself was not modified and no pedagogical
content was authored. Tier A/B shortages, 200 `UNSPECIFIED` readiness records, and lack of a
qualified reviewer remain visible work rather than being papered over with generated activities.

- `backend/tests/unit/test_child_profile_catalog_audit.py`: 3 passed.
- Ruff on the audit script and focused test: passed.
- Full backend unit/contract suite after the audit correction: 1,649 passed, 8 skipped, 26
  warnings in 149.09 seconds. Warnings were existing Pillow `getdata` deprecations and pytest
  cache-path access denial; tests ran using the isolated repository-local basetemp.
- Generated `evidence/metrics/CATALOG_COVERAGE_20260930.json`: 200 demo-eligible, 100 provisional,
  0 production-approved, 85 pre-production static survivors, and 0 production static survivors.

## Context shortlist ordering and completion verification — 2026-09-30

Evidence ID: `FEAT033-EV-20260930-09` · Related criteria: AC-05, AC-06, AC-07, AC-08.
The final server-flow audit found that phase-one candidates were previously produced by the same
resolver that ranked by topic relevance and limited the result to three. This could hide an
otherwise eligible activity before the adult answered its activity-specific readiness, material,
and supervision questions. Phase one now selects a stable, family-deduplicated shortlist without
using relevance scores. Finalization recomputes that same candidate set on the server, applies the
adult-confirmed hard gates, and only then uses relevance ranking. An adversarial unit test proves
the ranked and unranked bounded selection differ in the failure case and locks the intended order.

The same verification pass made catalog-audit integer fields reject unexpected non-integer JSON
values and made recommendation preparation enums fail closed on unsupported catalog values. The
personalization comparison read model is emitted only when its server-side recommendation exists.
These are validation/safety changes; no activity catalog content, profile retention, or external
deployment was changed.

- Full backend unit/contract suite: **1,650 passed, 9 skipped, 26 warnings** in 150.75 seconds.
  Warnings were Pillow `Image.getdata` deprecations and a pytest cache-path access denial; pytest
  used a unique isolated basetemp. No failures.
- Focused post-change unit tests: **12 passed**; focused profile-flow contracts: **2 passed**.
- Ruff on changed Python sources/tests: passed. Targeted mypy with imported dependencies skipped:
  success for the three audited source files.
- Mobile UI/recovery test: `UI_COPY_AND_RECOVERY_VALID`; TypeScript `tsc --noEmit`: passed.
- `git diff --check`: passed, with only existing CRLF-normalization notices in unrelated FEAT-029
  files. No commit, push, or external deployment update was performed.

The live Lightning classifier/full Android Gate-B happy path, qualified Montessori catalog review,
and AC-09's comparable event-correlated native input-to-presented-pixel trace remain outstanding;
this evidence does not claim those criteria pass.

Subsequent integrated verification added one optional-NumPy SAM runtime regression, which is
skipped in the local backend virtualenv. The latest full suite result is therefore 1,650 passed,
10 skipped; see FEAT-030 `E-030-SAM-QUALITY-012` for the updated command and environment details.

## Android responsiveness safety recheck — 2026-09-30

Evidence ID: `FEAT033-EV-20260930-10` · Related criteria: AC-09, AC-10, AC-11.
The connected Android app remained foregrounded on the child-profile screen. Accessibility
inspection suppressed all `TextInput` contents and found both preference fields already populated
in the current session. The child-picker navigation did not provide a reliable confirmation of a
blank disposable profile, so no typing, field reset, or classifier submission was performed; this
avoids overwriting session-only profile data. The original profile-field viewport was restored and
no profile value was changed. No fresh text-latency sample was collected, and previous JS callback
→ next-frame figures remain proxies rather than AC-09 input-to-presented-pixel evidence.

- Focused backend contract/unit selection reached 100% with no reported failures.
- Mobile UI-copy test: `UI_COPY_AND_RECOVERY_VALID`; TypeScript `tsc --noEmit`: passed.
- `git diff --check`: passed, with existing CRLF-normalization notices limited to unrelated
  FEAT-029 files.
- Local backend `/health` and Metro `/status` both returned HTTP 200; the ADB reverse tunnel remained
  active and the app stayed in `MainActivity`. No fatal exception or uncaught React Native JS error
  matched the recent 1,200-line logcat window.
- AC-09 remains open pending a safely disposable blank profile and a comparable,
  event-correlated Android trace. No backend classifier request or external deployment change was
  made during this check.

## Separate test-AVD profile responsiveness check — 2026-09-30

Evidence ID: `FEAT033-EV-20260930-11` · Related criteria: AC-04, AC-09, AC-10, AC-11.
To avoid touching the existing connected emulator's non-empty session draft, a separate freshly
created `Pixel_10_2` Android API 37.1 test AVD was used. After confirming both preference fields
were blank (accessibility text matched each placeholder), a synthetic 24-character string was
typed into the temporary profile and never submitted to the classifier. At a deliberate 140 ms
per character, the dev-only JavaScript `onChangeText` → next-`requestAnimationFrame` p95 was
21.12 ms. The same callback proxy under a 40 ms/character burst measured 149.92 ms and 166.54 ms
in two 24-sample batches, showing sensitivity to event burst/AVD scheduling. No matching
`/profile/preferences/classify` route entry appeared in the test-device log window; source review
confirms classification is invoked only by the explicit adult button, not the text-change handler.
The temporary text was cleared, both fields were verified blank, and the test app process was
restarted. The original emulator (`emulator-5554`) was not interacted with.

These are JS callback-to-next-frame proxies, not native input-to-presented-pixel traces, and no
comparable pre-change baseline exists; therefore AC-09 remains **open** despite the paced proxy
being under 100 ms. The Android 37.1 image also displayed the platform's 16 KB native-library
compatibility warning for this debug APK; treat that as an environment caveat, not proof of app
performance. AC-04/10 still need a successful live Lightning classification and complete Gate-B
smoke, and AC-08 still needs qualified catalog review. No external service was changed.

The current mobile UI-copy test and TypeScript check pass; `git diff --check` exits 0 (only existing
FEAT-029 CRLF notices). Local backend health and Metro status both returned HTTP 200. The original
`emulator-5554` remained in `MainActivity`, with Metro reverse active and no fatal/uncaught-JS match
in the recent log window. The separate test AVD was shut down after the measurement.

The first repository security scan flagged absolute machine paths in two untracked pytest
`--basetemp` fixture files under `backend/.pytest-tmp-feat033-final-audit-20260930/` and
`backend/.pytest-tmp-feat033-final-flow-20260930/` (`test_env_file_entrypoint_uses_0/.vision.env`).
Their timestamps and fixture directory names identify them as generated test scratch, so a narrow
`/backend/.pytest-tmp-*/` ignore rule was added to root `.gitignore`; both directories/files were
preserved untouched. `git check-ignore` confirms the exact two fixtures match that rule. The
security validator then passed with 1,717 publishable files scanned and no absolute machine paths.

A fresh bounded synthetic request to the currently running local backend
`POST /v1/profile/preferences/classify` returned HTTP 503, contract
`ChildPreferenceClassificationFailureV1`, code `CLASSIFIER_ENDPOINT_UNAVAILABLE`,
`retryable=false`. This confirms the connected Lightning deployment still lacks the classifier
route; no successful model inference or Gate-B smoke is claimed. A focused rerun of the P1,
profile, classifier and catalog contract/unit files completed with **30 passed**.

## Mobile P1 producer regression — 2026-09-30

Evidence ID: `FEAT033-EV-20260930-12` · Related criteria: AC-01, AC-02, AC-11.
Extracted the actual V2 mobile context-options body construction into the pure
`buildP1ContextOptionsRequest` helper used by `api.ts`. The mobile regression now executes that
helper with a synthetic profile and verifies current `MAT_PLANT_TRAY` plus legacy `GMAT-...`
material identifiers pass through unchanged, unconfirmed tags are omitted, raw interest text is
not included, and adult/candidate confirmations remain explicit. Added a backend V2 schema test
that accepts both namespaces. Focused live-image API/profile-contract tests: **24 passed**;
mobile `UI_COPY_AND_RECOVERY_VALID` and TypeScript pass. Metro compiled the Android app bundle
with the extracted helper (HTTP 200, 8,089,290 bytes); local backend `/health` also returned 200.

This ties a regression to the actual mobile producer and backend boundary. The original historical
production request body was never captured, so its exact submitted value still cannot be proven;
the reproduced `MAT_` versus legacy-only schema mismatch is the confirmed current contract defect,
not forensic proof that no other historical issue contributed.

The catalog audit was rerun read-only against the current tree: 300 templates, readiness metadata
100 `AUTHORED` / 200 `UNSPECIFIED`, 85 pre-production static hard-gate survivors, and zero
production-approved/static survivors. This matches the checked-in feature coverage report; it
confirms a real metadata/source-review gap, not a reason to fabricate criteria or add unreviewed
activities.

## SRS age-band UI gap — 2026-09-30

Evidence ID: `FEAT033-EV-20260930-13` · Related criteria: AC-06, AC-10.
Current SRS BR-012 bands are 0–3 (0–35 months), 3–6 (36–71), 6–9 (72–107), and 9–12
(108–155); BR-013 requires a caregiver to be present and directly supervise ages 0–3. The backend
V2 schema accepts 0–155 months and adapts the confirmed adult participant to `DIRECT`, but that
generic adult boolean does not establish that the adult is the child's caregiver. The mobile profile
selector offers only `3–4`, `5–6`, `7–8`, and `9+`, mapping them to 48, 60, 96, and 120 months. It
cannot start an under-three session, and the selected month values do not encode the chosen age
bands accurately. No age input change was made: FEAT-033 revision 3 does not specify exact age vs
coarse-band entry, while SRS OPEN-014 leaves DOB/timezone/snapshot semantics unresolved. Owner
direction is required before changing the selector/month mapping. A separate caregiver-specific
backend gate and SRS-derived direct-supervision display are also needed for any under-three path;
do not claim AC-06/10 verifies the complete 0–12 UI path.

## Under-three caregiver supervision enforcement — 2026-09-30

Evidence ID: `FEAT033-EV-20260930-14` · Related criterion: AC-06.
Closed the backend portion of the BR-013 gap without guessing the unresolved age-entry UX. The V2
finalization schema now requires an explicit `caregiver_participating=true` declaration for ages
0–35 months; ages 36+ retain the existing adult-participation and per-candidate confirmation flow.
The candidate response elevates minimum supervision to `DIRECT` and displays
“Người chăm sóc ở bên và giám sát trực tiếp” for under-three children even when catalog metadata is
weaker. The 35/36-month boundary, missing-caregiver rejection, and direct-supervision override have
focused regression coverage. Targeted profile/API tests: **8 passed**; Ruff passed. The complete
backend unit+contract suite then reached 100% and exited successfully; the repository's configured
quiet mode does not print the final aggregate count. Existing Pillow `Image.getdata` deprecation
warnings remain unrelated to this change.
The final repository security validator passed (1,720 publishable files scanned), mobile UI-copy
validation passed, TypeScript typecheck passed, and `git diff --check` passed.

This does not yet make an under-three session reachable from the mobile UI: its age selector is
unchanged pending the owner's exact-age vs SRS-band decision, and the mobile form/request still needs
the matching caregiver confirmation control. AC-06/10 remain incomplete for the full mobile path.

## Exact-age profile entry and reachable caregiver gate — 2026-09-30

Evidence ID: `FEAT033-EV-20260930-15` · Related criteria: AC-06, AC-10, AC-11.
The initial child-profile screen now edits exact completed age in years and months, bounded to
0–155 months, rather than mapping broad age cards to representative months. Date of birth is not
requested. The age value is held in the app's current volatile state, associated with the selected
child, and changing child/age invalidates stale P1 candidates and options. Accessible increment /
decrement controls display the selected child's current age. A pure helper regression covers 0,
35, 36, and 155-month boundaries, rollover, formatting, and clamping.

For ages 0–35 the same initial profile step requires the adult to confirm that the caregiver will
remain present and directly supervise; that action sets both adult-participation and caregiver
confirmation. Ages 36+ retain the adult-participation question. The main flow continues to request
per-candidate supervision confirmation, and the server enforces authored minimum supervision after
the caregiver gate. `P1ContextV2` is sent only below 36 months; 36+ keeps the frozen `P1ContextV1`
shape. The backend revalidates V2 on downstream loads and rejects under-three legacy V1 contexts.

This is an implementation choice to feed the exact age already used by the SRS/catalog eligibility
filter; it is not a new DOB, timezone, snapshot, or durable-profile decision. SRS OPEN-014 remains
open. No activity/readiness catalog content was added because source-backed review remains
unavailable.

- `npx tsc --noEmit -p tsconfig.json` and mobile `npm test`: passed (`UI_COPY_AND_RECOVERY_VALID`),
  including exact-age helper boundaries, removal of stale age-group references, and caregiver/P1
  serialization checks.
- Focused backend P1/profile/mobile API tests: passed; targeted Ruff for changed backend modules and
  tests: passed.
- Full backend unit+contract command
  `backend\.venv\Scripts\python.exe -m pytest backend/tests/unit backend/tests/contract -q
  --basetemp=backend/.pytest-tmp-feat033-final-20260930 -p no:cacheprovider` exited 0 at 100%.
  Configured double-quiet output suppressed the aggregate count. Existing Pillow
  `Image.getdata` deprecation warnings remain.
- Local backend `/health`: HTTP 200; Metro `/status`: HTTP 200; the Android Expo bundle route
  `/apps/ui-mobile/index.bundle?platform=android&dev=true&minify=false`: HTTP 200, 8,096,813 bytes.
  The current PowerShell environment has no `adb` command, Android SDK environment variable, or
  `adb.exe` at the standard SDK paths, so this run could not install/reload the new screen or
  execute a fresh connected-device flow.
- `backend\.venv\Scripts\python.exe tools\validate_repository_security.py`: passed,
  `REPOSITORY_SECURITY_VALID`, 1,724 publishable files scanned; no credentials or absolute machine
  paths. `git diff --check`: passed.
- No commit, push, or external Lightning deployment change was made.

The backend/mobile under-three path is locally covered, but AC-10 still needs a connected Android
smoke through successful remote preference classification and Gate B. AC-08 still needs qualified
source-backed catalog review, and AC-09 still lacks comparable event-correlated native
input-to-presented-pixel evidence. Feature status remains `IN_PROGRESS`.

## GET P1 validation response and catalog-report freshness — 2026-09-30

Evidence ID: `FEAT033-EV-20260930-16` · Related criteria: AC-01, AC-02, AC-08, AC-11.
Current-state review found that the P1 `POST` validation path returned a typed failure, but invalid
query parameters on the legacy `GET /p1/context-options` route bypassed that handler and returned
FastAPI's generic `detail` response. Extended the same safe `MobileWorkflowResultV1` validation
failure to the GET route and declared its provenance source as `P1ContextOptionsQueryV1`. Query
location/value details are sanitized: a request with `age_months=156` returns HTTP 422 with
`REQUEST_VALIDATION_FAILED`, logs the bounded field path, and does not log `156`. The mobile error
classifier regression also confirms it preserves the backend's typed safe message and non-retryable
status for a 422 envelope.

- Focused GET/POST validation tests: **2 passed**. Targeted Ruff for the HTTP handler and contract
  tests: passed. Mobile TypeScript and `npm test`: passed (`UI_COPY_AND_RECOVERY_VALID`).
- The full backend unit+contract suite, including the new GET validation case, reached 100% and
  exited 0; repository quiet configuration suppresses the aggregate count. Existing Pillow
  deprecation warnings remain.
- Re-ran the catalog audit from current source and compared the parsed live JSON to the checked-in
  `CATALOG_COVERAGE_20260930.json`; normalized reports match exactly. Current state remains 300
  templates, 100 `AUTHORED` / 200 `UNSPECIFIED` readiness, zero activities approved in both
  production catalogs, and zero production static survivors. No content was fabricated.
- Final repository checks: `git diff --check` passed; the targeted HTTP Ruff check passed; the
  repository security validator returned `REPOSITORY_SECURITY_VALID` with 1,724 publishable files
  scanned and no credentials or absolute machine paths.

The validation contract and report freshness are locally verified. The previously recorded external
gates remain: Lightning classifier deployment/full Android happy-path smoke, qualified Montessori
review for catalog expansion, and a comparable event-correlated native input-to-presented-pixel
measurement.

## Dedicated Android profile-boundary smoke and final local regression — 2026-09-30

Evidence ID: `FEAT033-EV-20260930-17` · Related criteria: AC-06, AC-09, AC-10, AC-11.
Used the dedicated Pixel_10_2 API 37 test AVD (`emulator-5556`) so the existing/main AVD
(`emulator-5554`) and its session were not altered. Visually verified the exact-age profile and
under-three caregiver gate at 35 months, then incremented across the boundary to 36 months and
verified that the caregiver-specific requirement is replaced by the ordinary adult-participation
confirmation. The screen continues to state that age is not a date of birth and that free-text
preferences are session-only. The test AVD held only synthetic preference text; it was shut down
after the check, while `emulator-5554` remained online.

- On the test AVD, 24 spaced synthetic text edits reported JS callback-to-next-frame p95 of
  59.73 ms. This is only a development proxy, not native input-to-presented-pixel latency. A fresh
  `gfxinfo framestats` sample contained 120 completed frames and zero nonzero `InputEventId` values,
  so an event-correlated input-to-paint percentile could not be computed. AC-09 remains incomplete.
- Both online AVDs had Metro reverse for TCP 8081 before test cleanup. Backend `/health`, Metro
  `/status`, and the Android Expo bundle route returned HTTP 200; bundle size was 8,096,813 bytes.
  The last 250 test-AVD log lines contained no fatal React Native/JS match. This verifies startup and
  connectivity, not the complete recommendation happy path.
- Final local regressions: backend unit+contract suite reached 100% and exited 0; mobile `npm test`
  returned `UI_COPY_AND_RECOVERY_VALID`; TypeScript typecheck passed; targeted Ruff, `git diff
  --check`, and repository security validation passed (`REPOSITORY_SECURITY_VALID`, 1,724
  publishable files scanned). Existing Pillow `Image.getdata` deprecation warnings remain.
- No classification submit or external deployment change was made in this smoke. AC-04/10 still
  require the Lightning deployment to expose the current classifier route and a successful Android
  classifier → contextual readiness → final-candidates → Gate-B run. AC-08 still requires qualified
  source-backed catalog review; no unreviewed content was added. AC-09 still requires a valid,
  comparable event-correlated native input-to-paint measurement.

## Clear session-scoped activity answers after feedback — 2026-09-30

Evidence ID: `FEAT033-EV-20260930-18` · Related criteria: AC-06, AC-07, AC-10.
Flow review found that after a successful feedback save, the mobile app retained the previous
workflow's adult/caregiver participation, readiness answers, and material availability in the
per-child volatile object. Starting another exploration could therefore show old activity-specific
answers as already selected and reuse the prior adult confirmation. The feedback-success path now
clears those four session-bound answers only after the backend accepts feedback, while retaining
the adult-declared stable preference text/tags, learning-support choices, and selected age for the
current app session. Failed feedback saves do not clear the answers.

- Added a pure reset helper and regression assertions proving that only session-specific
  participation/readiness/material values clear and stable preference declarations remain.
- Mobile UI validation returned `UI_COPY_AND_RECOVERY_VALID`; TypeScript typecheck passed; the
  Android Metro bundle returned HTTP 200 (8,097,656 bytes). The main emulator was not mutated by
  this check.
- The remote Lightning classifier, complete connected Android happy path, qualified Montessori
  catalog review, and comparable native input-to-paint measurement remain open.

## Readiness identifiers and preserve the two-phase P1 shortlist — 2026-09-30

Evidence ID: `FEAT033-EV-20260930-19` · Related criteria: AC-06, AC-07, AC-10.
The full profile-to-Gate-B contract test exposed two catalog/workflow integration defects. First,
legacy catalog readiness slugs were emitted unchanged, but the versioned profile contract accepts
canonical `READY_…` identifiers. The catalog adapter now maps the three authored child-readiness
slugs to their canonical contract identifiers and rejects unknown/colliding values. The legacy
`caregiver_present` marker is treated as an adult supervision/safety gate (and validated against
the under-three age/direct-supervision/policy metadata), not as a child's readiness observation.
No readiness criterion or activity was invented.

Second, after the adult finalized conditions against the bounded, unranked phase-one candidate set,
`RUN_P1_FILTER` recomputed the default ranked top-three and could reject the selected eligible item
as `ACTIVITY_NOT_IN_SEMANTIC_SHORTLIST`. An additive `P1ContextV3` contract now marks this explicit
candidate → adult conditions → final options path. Its P1 filter verifies the selected ID against
the same deterministic server-side phase-one shortlist, resolves only that candidate, and then
runs the existing compiler hard gates. Existing V1/V2 clients keep their legacy ranked-options
behavior. This avoids ranking drift without trusting arbitrary client IDs or relaxing safety,
readiness, material, prerequisite, or supervision rules. The synthetic contract now covers Qwen-tag
proposal → adult confirmation → contextual candidate finalization → P1ContextV3 → P1 filtering →
experience preparation → Gate B, plus injected/stale IDs, legacy-client compatibility, and readiness
normalization. ADR-0011 now documents P1ContextV3 as an additive contract and explicitly preserves
V1/V2 legacy behavior.

The focused contextual-candidate/catalog regressions passed (5); the full backend unit/contract
suite exited 0; mobile UI validation returned `UI_COPY_AND_RECOVERY_VALID`; TypeScript and targeted
Ruff passed. The current Metro Android bundle returned HTTP 200 (8,098,320 bytes); backend health
and Metro status both returned HTTP 200. `git diff --check` passed. Repository security validation
returned `REPOSITORY_SECURITY_VALID` with 1,726 publishable files scanned. The catalog audit was
regenerated from source: 300 templates, 100 with authored readiness and 200 unspecified; 85 remains
only a pre-production static upper bound and production-approved survivors remain zero. ADB was
not available on PATH or at the default local SDK path during this verification, so this run makes
no claim of a fresh emulator interaction. The live Lightning route, qualified catalog review, and
event-correlated native responsiveness acceptance remain external/open gates.

## Enforce one classifier inference per unchanged text revision — 2026-09-30

Evidence ID: `FEAT033-EV-20260930-20` · Related criteria: AC-04, AC-09.
The acceptance criterion says classification runs once per submitted preference revision, but the
revision gate still permitted two requests when the text had not changed. The cap is now one
inference per unchanged text revision. Editing the interest/avoid text opens a new revision and
allows one new explicit submit; success, failure, or timeout cannot trigger an automatic or repeated
request for the same revision. The UI now instructs the adult to edit the text to start a new
attempt, avoiding hidden retries when the upstream is unavailable.

Mobile UI regression validation verifies a failed revision cannot be submitted again and editing
opens a fresh request; TypeScript validation passes. This is a source/UI contract check, not live
classifier evidence. The deployed Lightning route and end-to-end Android happy path remain open.

## Resolve configured Android SDK and recheck the running app/network — 2026-09-30

Evidence ID: `FEAT033-EV-20260930-21` · Related criteria: AC-09, AC-10, AC-11.
The earlier check looked only at the default SDK path and `PATH`; Android Studio's own setting
points to `D:\AndroidStudio`. Using that configured platform-tools directory, ADB found
`emulator-5554` (`sdk_gphone16k_x86_64`) online, package `com.sketch2life.mobile` running with
`MainActivity` focused. The last 1,000 logcat lines had zero matches for fatal exceptions, Metro
connection errors, or the React Native script-load red screen. No profile fields were opened or
edited and no child data was read.

From the emulator, TCP connection checks succeeded to host `10.0.2.2` ports 8000 and 8081, matching
the app's configured backend base URL (`http://10.0.2.2:8000`) and Metro port. Host backend `/health`,
Metro `/status`, and the Android bundle each returned HTTP 200; the bundle was 8,098,258 bytes.
An attempted raw `nc` HTTP probe returned a 400 on the first encoding attempt and no HTTP body from
the backend on a shell-formatted retry, so evidence claims TCP reachability plus host HTTP health,
not a device-originated successful API response. The main app remained running. The one-inference
revision-cap mobile regression and TypeScript checks also pass; no live classifier request was
triggered. Full Gate-A-to-Gate-B success still depends on the deployed Lightning classifier route.

This closes the earlier ADB-path discovery gap and reconfirms startup/port reachability. It does
not close AC-09's comparable before/after native input-to-presented-pixel trace or AC-10's complete
Android happy path.

## One synthetic live preference-classifier probe — 2026-09-30

Evidence ID: `FEAT033-EV-20260930-22` · Related criteria: AC-04, AC-10.
Sent one explicit synthetic, non-child preference-classifier request through the running local
backend to test whether the Lightning deployment had since exposed the approved route. It returned
HTTP 503. The caller did not retain the response body, so this probe records status only and does
not assert a more specific current failure code. No retry was made, no raw phrase was logged or
copied into evidence, and no profile/session was created. A prior sanitized probe identified the
deployment's missing `/v2/profile/preferences/classify` route; this current 503 is consistent with
that blocker but does not alone prove the exact 503 subtype. AC-04's live inference and the full
Android classifier → contextual readiness → Gate-B path therefore remain unverified.

## Isolated baseline bundle attempt — 2026-09-30

Evidence ID: `FEAT033-EV-20260930-23` · Related criterion: AC-09.
Started a separate `Pixel_10_2` API 37.1 AVD and opened the debug app without changing the
existing `emulator-5554` or any profile data. A managed checkout at the pre-change baseline commit
was connected to a dedicated Metro port. The baseline reload returned HTTP 500 before rendering:
Metro could not resolve `@babel/runtime/helpers/interopRequireDefault` from the isolated checkout,
whose `node_modules` were junctioned to the main checkout. This is a measurement-harness/dependency
resolution failure, not evidence of an application regression. That first attempt collected no
timing. The harness was subsequently repaired by giving the managed baseline checkout its own
frozen-lockfile dependency installation; the resulting comparison is recorded separately in
`ANDROID_RESPONSIVENESS_COMPARISON_20260930.md` (EV-24). The failed first attempt remains documented
here so it is not confused with the later valid bundle run.

## Android responsiveness comparison — 2026-09-30

Evidence ID: `FEAT033-EV-20260930-24` · Related criterion: AC-09.
See `ANDROID_RESPONSIVENESS_COMPARISON_20260930.md` for device/build identification, paired proxy
samples, caveats, and cleanup verification. The profile-input JavaScript callback-to-next-frame
proxy improved substantially, but baseline and current fields differ and the metric is not native
input-to-presented-pixel latency. Scroll frame p95 was higher in current samples (32 ms versus
22–25 ms baseline) with different screen content, so this is a follow-up signal, not a proven
regression. The attempted current cold-mount sample was discarded because the expected profile
screen was not reached. AC-09 remains open; do not claim a complete responsiveness pass.

## Current source audit and regression verification — 2026-09-30

Evidence ID: `FEAT033-EV-20260930-25` · Related criteria: AC-01–AC-11.
Re-read the approved revision 3 plan/approval record and audited the current source path. The
context-options validation handler returns a typed `MobileWorkflowResultV1` with bounded field
paths/codes only; synthetic V1, V2 and query-validation contracts pass. The original historical
production payload remains unavailable, so this report distinguishes the reproduced
`MAT_`/`GMAT-` producer/schema mismatch from forensic proof of the exact old request.

The full current backend unit/contract pytest invocation completed with exit code 0. Mobile
`validate-ui-copy.mjs` returned `UI_COPY_AND_RECOVERY_VALID`; TypeScript (`tsc --noEmit`) and targeted
Ruff checks passed. The running app workspace's Android Metro bundle returned HTTP 200 (8,098,258
bytes). A fresh catalog audit written only to a temporary file matched the feature's checked-in JSON
exactly. Repository security validation passed with 1,727 publishable files scanned. The main AVD
remained on `MainActivity`; backend health and main Metro status were HTTP 200.

These local results do not close the unavailable deployed Lightning preference-classifier route,
real Android classification → readiness → Gate B smoke, source-backed qualified catalog approval,
or AC-09's comparable native input-to-presented-pixel and classification-wait measurements.

## Live P1 validation-handler comparison — 2026-09-30

Evidence ID: `FEAT033-EV-20260930-26` · Related criteria: AC-01, AC-02, AC-10.
Sent a synthetic GET with `age_months=156` to the already-running backend at port 8000. It returned
HTTP 422 with the legacy `{detail: "request contract invalid"}` body instead of the current typed
workflow envelope. The process was Python PID 10652, started at 00:54, and its command targets the
backend factory without auto-reload; the source had changed after that process started. The route
was present in OpenAPI, so this was a stale running process, not a missing route.

To verify the current source without interrupting the main process or its in-memory sessions, an
isolated current-code backend was started on localhost port 8001. The same synthetic query returned
HTTP 422 `MobileWorkflowResultV1`, status `FAILED`, code `REQUEST_VALIDATION_FAILED`, and provenance
`P1ContextOptionsQueryV1`. Its sanitized log contained only `fields=age_months` and
`codes=less_than_equal`; the submitted value was not logged. The isolated server was stopped and
port 8001 closed. The main 8000 process was deliberately left untouched; a restart is still needed
before its runtime behavior reflects the fixed source. No session/profile payload was read or sent.

## Clarify unknown-readiness catalog coverage — 2026-09-30

Evidence ID: `FEAT033-EV-20260930-27` · Related criteria: AC-06, AC-11.
An audit wording review found the report's unknown-readiness value was 17 while two prose summaries
incorrectly said zero. The metric counts only otherwise eligible templates with `AUTHORED` readiness
metadata and no readiness IDs: no child-readiness answer is needed for those activities. It never
treats an unanswered child-readiness prerequisite as satisfied. The source now names and tests this
rule explicitly, and the checked-in report includes the same interpretation. The current catalog has
20 authored-empty templates overall; only 17 pass the other static age/material/safety/history gates.
This is an upper-bound audit metric, not a claim that the activities are production-approved or a
live recommendation count. No catalog activities or Montessori readiness criteria were changed.
The focused audit tests passed (4); the complete backend unit/contract suite then exited 0 at 100%
using `backend/.venv/Scripts/python.exe` (the first attempt used system Python, which lacks the
backend's Pillow/PyAV dependencies and failed during test collection). Mobile UI-copy and TypeScript
checks, focused Ruff, `git diff --check`, fresh catalog generation, and the repository security
validator also passed; 1,727 publishable files were scanned.

## Restart the stale local backend and verify the typed validation fix — 2026-09-30

Evidence ID: `FEAT033-EV-20260930-28` · Related criteria: AC-01, AC-02, AC-10, AC-11.
At the owner's request, stopped only the verified stale Uvicorn process tree serving local port
8000 (PIDs 10652 and 8796), then started the current repository source from `backend/.venv` bound
to `0.0.0.0:8000`. The new process is PID 36444; startup completed and `/health` returned
`{"status":"ok","service":"sketch2life-api"}`. A synthetic invalid-age GET returned HTTP 422
with `MobileWorkflowResultV1`, status `FAILED`, and code `REQUEST_VALIDATION_FAILED`. The server log
contains only `route=p1_context_options`, a synthetic request ID, `fields=age_months`, and
`codes=less_than_equal`; no submitted values were logged. The startup/runtime logs are local under
`runtime-output/` and are not part of the commit. This confirms the local typed-validation fix is
loaded; it does not verify remote Lightning classification or the full Android Gate-B journey.

The approved FEAT-033 implementation was committed and pushed as `a22d6a8` to
`origin/codex/feat-018-pixi-exploration`. Independent FEAT-029/030/031 worktree changes were not
staged or included.
