# Parent Android two-run E2E — 2026-11-25

## Result

**NOT COMPLETE.** The requested two successful end-to-end runs were not achieved. Run 1 reached the real Parent Android UI, API, object-storage staging, and Modal dispatch boundary. Modal rejected job creation with `RESOURCE_EXHAUSTED` and no call ID. After that stop, the owner separately approved one bounded request under Addendum 20 to distinguish the CPU Sandbox notice from this failure. Run 2 reached Parent UI subject selection and image attachment, but its single UI submit was also rejected by Modal before a call ID. No inference was accepted in either 2026-11-25 run.

No story script, activity result, or video was generated in these runs. No video request was sent.

## Run 1 — transport / bicycle

| Stage | Result | Evidence |
|---|---|---|
| Synthetic Parent sign-in and profile | Passed; existing synthetic account/profile only | Earlier Android flow evidence in this folder |
| Topic and intended subject | Parent chose transport; intended subject was bicycle | Android screen/evidence `run01-bicycle-*` |
| Child-style drawing | Independently generated synthetic crayon drawing, 1,658,679 bytes | [drawing-2-bicycle-synthetic.png](drawing-2-bicycle-synthetic.png) |
| Android picker and attach | Passed; image is shown attached to the real run | [run01-status-after-10s.png](run01-status-after-10s.png) |
| API create-run | First attempt exposed repository signature mismatch; fixed under Rev12. Rebuilt API health is `ok`. | Plan Rev12 and API runtime logs |
| Modal staging | Passed; normalized drawing and manifest staged to the Modal scratch Volume | `input_size_bytes=884847` |
| Modal worker dispatch | **Failed before acceptance**. Two SDK spawn attempts returned `ResourceExhaustedError`; `modal_call_id=None`. | job ref `a2605c60a254a4b3`, generation ref `263efce6a251c5e6`, attempt ref `bc4f6bcc0452b53b` |
| Drawing analysis / activity / story / video | Not reached | No accepted Modal call, no script or video artifact |

### Timing for the diagnostic resume

- Scratch upload: **2,897 ms**.
- First spawn rejection: **3,423 ms** elapsed from invocation start.
- Second and final spawn rejection: **4,687 ms** elapsed.
- Scratch cleanup: **411 ms**.
- Input staged: **884,847 bytes**.
- Modal call ID: **none**; worker/model never started.

An earlier pre-diagnostics dispatch for this attached synthetic input also received no call ID. No accepted/ambiguous call was observed. The one resume after the safe diagnostic build was approved and recorded under Addendum 19.

## Run 2 — insects / butterfly

This was one separately approved, real Android Parent UI attempt with a different topic and a second synthetic crayon drawing. It is **not a successful E2E** because Modal rejected the drawing job before worker acceptance.

| Stage | Result | Evidence |
|---|---|---|
| New topic path | Passed; custom topic `con trung` was normalized by the topic catalog to `Côn trùng` | [run02-before-drawing-submit.png](run02-before-drawing-submit.png) |
| Subject suggestions | Catalog returned rotating subject cards; butterfly was not among the cards shown during this selection | [run02-photo-picker.png](run02-photo-picker.png), [run02-photo-picker-album.png](run02-photo-picker-album.png) |
| Custom subject check | Passed deterministically: `butterfly` matched the catalog alias for `con bướm`, returned `ON_TOPIC`, and normalized to `con bướm`; no AI call was made for this check | [run02-before-drawing-submit.png](run02-before-drawing-submit.png) |
| Child-style drawing | Independently generated synthetic crayon butterfly | [drawing-1-butterfly-synthetic.png](drawing-1-butterfly-synthetic.png) |
| Android photo picker and attach | Passed; the selected image remained displayed in the real run | [run02-photo-picker.png](run02-photo-picker.png), [run02-modal-rejected.png](run02-modal-rejected.png) |
| Modal worker dispatch | **Rejected before acceptance.** One UI submit caused two bounded `Function.spawn` attempts; both raised `ResourceExhaustedError`, with no `modal_call_id`. | job `61d8772fcbf7c484`, generation `2cba30d96d979116`, attempt `bb90bb4ed0d3986c`; [run02-modal-rejected.png](run02-modal-rejected.png) |
| Activity, story, video | Not reached | No worker result, selected activity, script, or video was produced |

The UI settled to an actionable failure state and retained the synthetic drawing; it did not remain in an indefinite spinner. The Addendum 20 stop condition is met, so no more inference was sent.

Run 2 dispatch timing from the sanitized API telemetry: first rejection **3,432 ms**, second/final rejection **4,691 ms** from invocation start; both had no Modal call ID.

## How custom topics and subjects are checked by the backend

- `GET /api/parent/v1/topics/suggestions` rotates three topic cards from the curated Vietnamese catalog.
- `GET /api/parent/v1/topics/{topic_id}/drawing-subject-suggestions` rotates three catalog subject cards for a known topic. If the adult typed an uncatalogued topic, the response has `generation_source=CUSTOM_INPUT_REQUIRED` and an empty card list; the UI asks the adult to type the intended subject. The catalog is not treated as exhaustive.
- `POST /api/parent/v1/topics/custom-subject-validation` receives `topic_id`, `topic`, and `subject`. Backend first checks normalized catalog names/aliases. A known match returns deterministically; a known alias belonging to another topic returns `OUT_OF_TOPIC`. An unresolved free-text topic/subject is sent to the separate Modal workload `parent.topic-subjects.validate`, if enabled, with only the generic topic and subject strings (no child profile or image). It must return one strict decision: `ON_TOPIC`, `OUT_OF_TOPIC`, or `NEEDS_CLARIFICATION`.
- AI validation is fail-closed and is not an exhaustive encyclopedia: if its capability is disabled, the API returns `PARENT_TOPIC_SUBJECT_AI_NOT_ENABLED`; worker/contract errors also stop the path. `ON_TOPIC` lets the UI continue; `OUT_OF_TOPIC` or `NEEDS_CLARIFICATION` asks the adult to change the topic or subject. The final drawing is still analyzed after capture and the adult confirms the recognized subject.

In this Run 2, `butterfly` was already a catalog alias, so this test proved catalog normalization, not the Modal fallback for an unseen object. The fallback exists in source and is wired through the mobile controller, but this E2E did not exercise it. Generating three fresh AI subject cards for every uncatalogued topic is not currently implemented; that is separate from validating an adult-entered item and is not required for the custom-input path.

## Modal diagnosis

- Active Modal profile: `hieuptse184252`, environment `dev`.
- Drawing app `sketch2life-srs23-drawing-vlm-dev` is deployed; `analyze-drawing` is configured for one L40S container.
- Safe API diagnostic: `provider_status=RESOURCE_EXHAUSTED`, `provider_reason_category=ACCOUNT_QUOTA_OR_LIMIT`, detail length 65, fingerprint `266187c22b681ff7`. Raw provider detail was intentionally not logged.
- For the earlier Run 1 diagnostic window, Modal function statistics showed **0 accepted inputs and 0 containers started**. For Run 2, both spawn attempts were rejected before a call ID, so that request did not reach a model worker either.
- Modal worker logs for the attempt: none.
- Current-month billing summary reports metered cost `$3.66`, credits applied `$3.26`, free storage `$0.30`, network egress `$0.10`, billed cost `$0.00`. This summary does **not** disclose remaining workspace credit or identify the exact account limit, so it is not evidence that sufficient compute quota remains.

Modal documents `ResourceExhaustedError` as a server-side resource rejection that can represent a quota or rate limit; function inputs may also be rejected when platform queue/rate limits are exceeded. The current safe response identifies the account/limit category, but the dashboard/API does not expose a more specific reason in the evidence collected. See [Modal Python SDK errors](https://modal.com/docs/sdk/py/latest/exception) and [Modal function invocation methods](https://modal.com/docs/guide/function-invocation-methods).

### Workspace-limit screenshot supplied after the retry

The owner later supplied a Modal limits screenshot showing current usage of **0/100 concurrent containers**, **0/10 concurrent GPUs**, **0/s** container/GPU creation rate, and **0/5,000 CPU sandboxes**. Assuming this is the same workspace and was captured near the failed call, the visible workspace concurrency/creation counters were not saturated. This makes “the workspace hit its displayed concurrent-container/GPU/sandbox ceiling” an unsupported explanation. It does not identify whether the rejection came from a billing/payment/account entitlement, a function queue/placement restriction, or a transient provider-side resource condition. The app code's `ACCOUNT_QUOTA_OR_LIMIT` is a privacy-safe text-pattern category over the gRPC detail, not Modal's exact root-cause code; the detail is intentionally not retained verbatim. The screenshot has no visible workspace identifier or capture time, so its exact correlation to the failed attempt is unverified.

## Separate accepted-call failure in the log supplied by the owner

The pasted Modal log is from a different, previously accepted drawing call (`fc-01M87K036T39JSN0XF0B2ZYX60`). Qwen/Qwen3.8-27B-FP8 on L40S completed inference in **81,191 ms**, emitted JSON, then failed application validation with `BOX_INVALID`; the worker failure was logged at **177,669 ms**. This is a post-startup output-contract failure, separate from the current pre-call `RESOURCE_EXHAUSTED` rejection and from CPU Sandbox admission.

The local worker source now makes box geometry explicit and classifies shape/type/range/order/area violations separately without weakening validation. Offline test: `pytest deployment/modal/srs_v23/tests/test_drawing_understanding_v2.py -q` — **24 passed**. This verifies local source only; deployment of that source was not verified, and no new inference was sent to test it.

## Repairs and verification performed

- Fixed the missing `intended_drawing_subject` forwarding/persistence in both fresh and replay create paths; API container rebuilt without recreating dependencies. The authenticated Android create/attach path then succeeded.
- Added privacy-safe Modal gRPC status/reason diagnostics. The API health endpoint returned `{"status":"ok","service":"sketch2life-api"}` after rebuild.
- Direct diagnostic assertions passed for five categories in the API container.
- Focused unit tests passed in a disposable container: **7 passed, 64 deselected**.
- Python syntax compilation passed.
- Repository security validator ran but returned `REPOSITORY_SECURITY_INVALID` for pre-existing absolute Windows paths in six FEAT-085 historical documents; it did not report a secret/token. Those unrelated records were left untouched.
- The Android UI settles from its short polling state to an actionable failed-analysis screen. The synthetic drawing remains attached; the screen offers the existing close/restart lifecycle action.
- Cleared stale Parent idea text when starting a new topic path. Focused mobile regression test passed (**2 passed**); the butterfly path showed `con bướm` rather than carrying the bicycle idea from the previous path.
- Confirmed the custom-subject backend path from source and this UI attempt: check catalog aliases first, then invoke the topic-validation AI only for unresolved input. In this run, `butterfly` matched a catalog alias, so the validation did not consume an AI request.

## Stop condition and next dependency

No more inference requests were sent after the Addendum 20 request was rejected. Before continuing, inspect the same workspace's billing/payment/plan state and the failed Function's Modal-side rejection detail; the visible concurrency counters are not saturated in the supplied screenshot. Do not raise generic container/GPU limits based on this evidence. The safe diagnostic does not expose the exact underlying cause, and the CPU Sandbox notice alone does not explain a GPU `Function.spawn` rejection. Do not paste credentials or provider error payloads into chat. Resume with a new bounded authorization only after the cause is understood or cleared, using the normal Parent UI and gates.

## Run 3 — updated Modal environment and activity handoff — 2026-11-25

**Result: drawing analysis passed on the real Android Parent flow; the run stopped at activity selection because the task database contains no Lesson Library records. Story and video were not requested.** This run does not count as a complete Parent E2E.

| Stage | Result | Evidence |
|---|---|---|
| API environment reload | Rebuilt and force-recreated only `api` using the root Compose `.env`; health returned `{"status":"ok","service":"sketch2life-api"}` and the service reported healthy. No dependency service or volume was recreated. Secret values were not printed. | Compose result and health check, 2026-11-25; container `fe085-parent-api-20261123` |
| Android Parent run | Existing real UI run `c1004974-7634-4399-a55f-3d4fc1cbee62`, topic insects, confirmed subject `butterfly`; synthetic crayon drawing, no fixture response. | `run03-analysis-result-poll.png`; `run03-subject-confirmed.png` |
| Drawing worker | **PASS.** Modal accepted and completed one call: `fc-01M882PWWJ36ADWJHG24XVK7W5`; job `8eac219ba549ff07`, generation `dc83485e9f0de6f6`, attempt `50bac87fa45aaa48`; `Qwen/Qwen3.8-27B-FP8`, L40S; reported elapsed `182,881 ms`. The UI received `butterfly`, 100% confidence, and visible-feature descriptions. No retry was sent. | Modal call reference above; `run03-analysis-result-poll.png` |
| Adult confirmation and run read | Confirmation returned HTTP 202. Persisted state was `PREPARATION_REVIEW`, revision 5, understanding revision 1, job `SUCCEEDED`; the stored decision is `SUBJECT/CONFIRM`. | Prior read-only DB verification and `run03-subject-confirmed.png` |
| Rev17 activity handoff | After rebuilding only API, one UI retry reached both `GET /v1/story-runs/{run_id}` and `GET /v1/activities?story_run_id=...`; each returned HTTP 200. The earlier “profile changed” error cleared. The UI then reported no matching activity. | `run03-api-activity-access.log`; `run03-after-activity-retry.xml`; `run03-activity-catalog-empty.png` |
| Lesson Library source | Read-only count in the task database: `lesson.library_items = 0`; `lesson.library_versions = 0`. Therefore the Parent-visible published/shared lesson catalog has no source records to rank for this run. This is a missing catalog-data precondition, not a Modal inference failure or an HTTP/API transport failure. | Read-only PostgreSQL count, 2026-11-25 |
| Story/video | **NOT REACHED.** The UI has no selectable activity and exposes only the stop-session action. No activity selection, story request, or video request was sent; no quota/safety bypass occurred. The run and drawing are retained. | `run03-activity-catalog-empty.png` |

### Run 3 conclusion

The edited environment is sufficient for the real Qwen3.8 drawing workload: Modal accepted the call and the UI received a valid result. The remaining blocker is an empty Lesson Library in the isolated FEAT-085 database. The current Parent activity-list route reads accessible published/shared lesson versions and, for this run, returned an empty list. Do not fabricate a selection or write a lesson directly into the database. To continue end to end, first provide an approved published/shared lesson through the normal Teacher/Manager/Admin workflow, or approve a separate implementation for the documented AI-generated fallback when no catalog activity matches. The current run is preserved; no additional AI calls were sent after the activity-list response.

