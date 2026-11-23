# FEAT-081 Rev20B Parent Android E2E evidence

**Latest result (2026-11-19): PARTIAL / BLOCKED at drawing worker/API output-contract validation.** The real Expo Android app, local backend, Firebase-authenticated synthetic Parent, generated synthetic turtle artwork, and one live Qwen3.5 Modal inference were used; this was not a fixture or preview-harness run. The worker completed, but its output omitted the confidence field required by the backend and SRS AT-14. Activity/story were therefore not reached. Video, quota, and payment were not called. The earlier decoder failure and its offline fix are preserved as historical evidence below.

## Run environment

- Date: 2026-11-19, Asia/Saigon.
- Android emulator: `emulator-5554`.
- Worktree: `.codex-worktrees/fe`, branch `feature/fe-mobile-remediation`.
- Task-local Compose project: `s2l-feat081-rev20`; API host port configured from the ignored root `.env` (58100 during this run).
- Synthetic pilot was enabled only in `compose.rev20b.override.yaml` for this disposable local API container. The shared Compose defaults were not changed for this purpose.
- Modal drawing app: `sketch2life-srs23-drawing-vlm-dev`; model `Qwen/Qwen3.5-9B`, pinned revision `c202236235762e1c871ad0ccb60c8ee5ba337b9a`.
- Artwork: generated synthetic turtle; SHA-256 `43596C821E6D80B3792F227F684B1C30DEA5D84653BB7D504C873F2F3B3F5A40`.

## Observed workflow and API results

| Step | Real action | Result |
|---|---|---|
| Startup | Started task-local Docker API and Android Metro; checked host and container `/health`. | Healthy. Initial profile-create attempt returned 409 because the disposable API container did not have the synthetic-pilot flag. The task-local Compose override was amended, only the API container recreated, and the next profile create succeeded. |
| Login/profile | Signed in through the actual Parent app and created a synthetic child profile. | Profile POST 201; GET-by-ID 200. No legal consent was fabricated. |
| Topic | Loaded topic cards from backend, chose `Động vật`. | Topic-suggestions API 200. |
| Subject | Loaded the three subject suggestions (`Con bướm`, `Con mèo`, `Chim nhỏ`); entered `turtle`. | Custom-subject validation API 200; accepted and normalized to `con rùa`. |
| Optional SVG guide | Requested the guide from the Parent app and advanced all steps. | Sketch-guide API 200; six progressive catalog SVG steps with curated Openclipart color reference. This did not call Modal. Screenshots show all six steps. |
| Artwork | Selected the generated synthetic turtle through Android Photo Picker and attached it to the new session. | Actual file-picker path; image staged to Modal scratch and upload completed in 2,835 ms. |
| StoryRun | Tapped “Tạo buổi và nhận diện tranh” once at approximately 14:38:03.652 local time. | `POST /v1/story-runs` 201; `GET /v1/story-runs/b3ef10be-6418-40f1-b0c7-0e760d5c0607` 200. |
| Drawing analysis | One live `drawing.analyze` request. | Modal call `fc-01M7SBVYYV1MJEHMZP5M93JXX4`; Parent API returned 502 `DRAWING_OUTPUT_INVALID`; a follow-up StoryRun GET returned 200. The UI showed a safe error and did not claim success or resend the image. |

### Drawing inference diagnostics

- The request was **not a timeout**. The worker finished in 30,197 ms; the model loaded in 16,008 ms, preprocessing took 20 ms, prompt encoding 71 ms, constrained-decoder setup 3,664 ms, and model inference 9,983 ms.
- 125 output tokens were generated; the 512-token limit was not reached. The sequence ended with a model EOS token.
- The terminal parser diagnostics nevertheless reported `json_complete=false`, `json_error_type=OtherJSONError`, `json_error_position=224`, while the constrained decoder's final diagnostics reported that the parser could end and model EOS was allowed.
- The worker emitted the sanitized terminal reason `MODAL_MODEL_OUTPUT_INVALID`; it did not log model text, prompt, image bytes, or credentials. Backend mapped this to `DRAWING_OUTPUT_INVALID` / HTTP 502 rather than the former generic 504.
- This proves the current failure is an output/decoder contract inconsistency, not GPU allocation delay. The exact malformed substring is intentionally unavailable because raw model output is not retained or logged.

## Blocked / not run

- Activity suggestion and activity persistence: not reached; the drawing result was not valid enough to confirm a subject.
- Story generation, story review/revision, and script confirmation: not reached; no activity selection was persisted.
- Video, narration, quota, and payment: not called.
- No second inference or retry was sent.
- The older StoryRun `f9b29982-5472-4456-b2e8-2f44dc900382` was checked once through the authenticated API route using the local seed Parent token. The API returned 401, so no state was disclosed and no cancellation was attempted. The local seed identity/token was not accepted by this API instance; this is not evidence that the old run is absent. Do not modify the database directly.
- `ParentApi.cancelStoryRun` is still an unavailable client method in this worktree, so the app itself cannot yet cancel that run.

## Screenshot index

All captures are emulator screenshots from this run; `00-*` are startup diagnostics and `06-parent-profile-submit.png` is a stray app-drawer capture, not a workflow pass.

| Screenshot | Contents |
|---|---|
| `00-current-screen.png`, `00-after-cold-link.png`, `00-after-metro-link.png`, `00-dev-menu.png`, `00-bundle-location-dialog.png` | Metro/dev-client startup diagnostics. |
| `05-parent-profile-create-error.png` | Initial profile-create 409 before enabling the synthetic-only pilot flag in the task-local API container. |
| `06-parent-resumed.png`, `07-parent-login-result.png`, `08-parent-profile-created.png` | Actual Parent app resume, login, and created synthetic profile. |
| `09-parent-start-options.png` | Parent session entry options. |
| `10-parent-topic-suggestions.png`, `11-parent-drawing-subjects.png`, `12-parent-subject-validation.png` | Real topic, subject-card, and custom-subject validation screens. |
| `13-parent-guide-choice.png`, `14-parent-svg-guide.png`, `14b-svg-guide-step-2.png` … `14b-svg-guide-step-6.png`, `15-parent-guide-approved.png` | Optional guide choice, every progressive SVG step, and guide completion. |
| `16-parent-capture.png`, `17-parent-gallery-picker.png`, `17b-parent-gallery-menu.png`, `17c-parent-gallery-collections.png`, `17d-parent-gallery-folder.png`, `17e-parent-gallery-album.png`, `18-parent-synthetic-image-selected.png`, `19-parent-image-preview.png`, `20-parent-artwork-attached.png` | Camera/gallery and actual Android Photo Picker selection of generated synthetic artwork. |
| `21-parent-drawing-analysis-progress.png`, `22-parent-drawing-error.png` | Real drawing request progress and terminal UI error. |

`current-ui.xml` is the final accessibility/UI hierarchy snapshot. `start_rev20b.log` and `stop_rev20b.log` record task startup/cleanup commands. They must not be augmented with tokens or credential values.

## Next fix target

Review the drawing decoder's token-to-text handling and EOS eligibility. Ensure EOS can only be allowed when the exact decoded prefix parses as a complete object satisfying the output contract. Keep raw output private; add content-free diagnostics for parser state/schema stage if needed. Any new live inference requires a separately bounded approval because this run already consumed the approved one-shot drawing call.

## Offline root-cause analysis and fix (after the Rev20B run, no inference)

- **Cause:** `_build_qwen_tokenizer_data` in `deployment/modal/srs_v23/drawing_vlm_app.py` built the LMFE prefix tree with the same `decode()` that strips a trailing `U+FFFD`. Qwen byte-level BPE splits many Vietnamese characters into byte-fragment tokens; for those, the stripped decode is `""` and the token is marked as a new word. LMFE places empty-string tokens at the prefix-tree root, which `_collect_allowed_tokens` returns in **every** parser state, and applying them adds no characters. The model could therefore emit fragment bytes after the closing `}` while LMFE still reported `can_end` and allowed EOS; the final `batch_decode` then contained trailing characters and `json.loads` failed (classified as `OtherJSONError`, i.e. "Extra data").
- **Reference behaviour:** LMFE 0.11.3 `integrations/transformers._build_regular_tokens_list` and this repo's `language_audio_app.py` build regular tokens from raw `tokenizer.decode`; only the incremental decoder strips `U+FFFD`.
- **Fix:** regular tokens now use raw `tokenizer.decode`; the incremental decoder is unchanged. JSON diagnostics now also classify `ExtraData`, `InvalidControlCharacter`, and `InvalidEscape` without exposing text.
- **Regression test:** `deployment/modal/srs_v23/tests/test_drawing_lmfe_byte_fragments.py` uses real `lm-format-enforcer==0.11.3` with a byte-level toy tokenizer. Fixed code: 4 passed. The same test against the previous builder: 2 failed, reproducing the defect (after `}` the allowed set was `{EOS, 9, 37, 38}` including both fragment tokens).
- **Not yet proven:** a live Qwen3.5 drawing call. The Rev20B bounded inference was consumed; a new bounded call needs separate owner authorization. The existing 29-test contract file was not re-run in this step.

## Latest post-parser rerun — 2026-11-19 (one bounded drawing call)

**Result: real worker inference completed, but Parent drawing analysis still fails at the worker/API output contract.** This rerun used the real Expo Android app, task-local backend, synthetic Parent/profile, and generated synthetic turtle artwork. It did not use fixtures or the preview harness.

| Stage | Result |
|---|---|
| Parser regression suite | `test_drawing_lmfe_byte_fragments.py` + `test_qwen35_lesson_suggestion_contract.py`: 33 passed, 2 warnings. |
| Parent flow | Live topic suggestions returned 200; selected `Động vật`, then `Rùa con`; attached generated synthetic turtle through Android Photo Picker. |
| StoryRun | `POST /v1/story-runs` 201; `GET /v1/story-runs/ca45988b-cde6-4b32-b672-dd0202d93ad4` 200. |
| Drawing request | One `POST /api/parent/v1/ai/drawing-understandings`, started `2026-11-19 16:14:02.148 +07:00`; API returned 502. No retry. |
| Modal | Qwen3.5-9B pinned revision `c202236235762e1c871ad0ccb60c8ee5ba337b9a`; call `fc-01M7SHBPCAKZDBDQ695P6NJ3EW`; worker emitted `worker_succeeded`. |
| UI | Showed the safe message that the image is attached but the server did not return a review result; status GET did not reconcile to a result. |

### Timing and contract diagnosis

- Request job `20a6e5fe7a3dd319`; generation `9d6e7da18ad07b06`; attempt `5bc8a28b5abccc2a`.
- Image upload to Modal scratch: 299,379 bytes, 2,867 ms.
- Worker start approximately `16:14:22 +07:00`; terminal success approximately `16:14:48 +07:00`.
- Model load 13,073 ms; preprocessing 20 ms; prompt encoding 77 ms; constrained-decoder setup 3,661 ms; model inference 7,900 ms; 78 output tokens. The output ended with model EOS below the 512-token limit. This was not a timeout or GPU-allocation failure.
- A read-only inspection of the completed Modal call found the returned result keys `adult_confirmation_required`, `candidate_subject`, `decision`, and `visible_features`; the required `confidence` field was absent. No field values or raw model output were copied into this report.
- The source confirms a deterministic cross-layer schema mismatch: the Modal JSON schema/parser allows exactly `candidate_subject` and `visible_features`, then the worker adds `decision` and `adult_confirmation_required`; it never emits `confidence`. The backend route requires `confidence` to be a finite number in `[0, 1]` and returns `MODAL_OUTPUT_CONTRACT_INVALID` / HTTP 502 otherwise. SRS AT-14 requires candidate/confidence to be shown for adult review. This explains the worker-success/API-failure split. The earlier parser/EOS defect is no longer the observed failure in this rerun.
- Activity selection/persistence and story generation were not reached. No activity/story inference, video, narration, quota, or payment call was sent. No additional live inference was sent after this failure.

### Latest rerun screenshots

These six captures are from the real emulator flow and contain no login/credential screen:

| Capture | Contents |
|---|---|
| `screenshots/33-parent-topic-rerun.png` | Live topic cards; `Động vật` selected next. |
| `screenshots/34-parent-subject-rerun.png` | Live subject suggestions including `Rùa con`. |
| `screenshots/35-parent-turtle-attached.png` | Generated synthetic turtle attached in the actual Parent app. |
| `screenshots/36-parent-drawing-submitted.png` | Single drawing request in progress. |
| `screenshots/37-parent-drawing-contract-error.png` | UI error after the API rejected the result. |
| `screenshots/38-parent-status-after-check.png` | Same safe state after one read-only status check. |

### Cleanup

- Task Compose project `s2l-feat081-rev20` is stopped; its containers are `Exited`.
- Modal drawing and language/audio apps were stopped; Modal video was left untouched.
- The stop script did not terminate its Metro process tree because its PID marker was absent. I then verified the process command line pointed to this exact worktree and port `18081`, stopped only that tree, and verified that port no longer had a listener. Other long-running Docker stacks and unrelated Node processes were left alone.
- No commit or push.

### Next fix

Align the worker output schema/parser with the backend and SRS requirement for candidate plus confidence. Define confidence semantics consistently with the SRS before emitting it; do not invent a placeholder. Add offline worker/API contract coverage first. This one-shot rerun is consumed; another live inference needs a new bounded approval.
