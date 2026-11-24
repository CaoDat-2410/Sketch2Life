# FEAT-081 — Plan Revision 33: Fix Parent activity inference throughput

- **Status:** APPROVED under the owner's direct instruction on 2026-11-20 (Asia/Saigon): “fix tiếp đi, nào nó chạy đc hết thig dùng”.
- **Feature/worktree:** FEAT-081, `feature/fe-mobile-remediation`, `<local-machine-path>
- **Product authority:** canonical FEAT-063 v2.7-draft SRS in `features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md`; this plan does not amend product requirements.
- **Relationship:** bounded execution amendment after the two activity calls in Revision 25. It permits one further activity call after a specific performance fix; it does not permit repeating drawing, and does not expand story/video limits.

## 1. Goal

Make the existing real Parent `parent.activity.suggest` Qwen3.5-9B request finish through the Android UI and preserve the catalog-first schema, quality, age, safety, and adult-selection rules. Diagnose and remove avoidable language-model memory/latency overhead without changing the model ID/revision or replacing Modal.

## 2. Evidence and current diagnosis

1. First post-kernel activity call, Modal `fc-01M7V4JFQ43TP51RR9CJH4S2N4`, reached `model_inference` and failed immediately with `NameError: StoppingCriteriaList is not defined`. Code inspection found the same path referenced `progress` without binding `GenerationProgress`. Both defects were fixed; the focused activity wiring and L4 workload tests passed (`3 passed`).
2. Second call, submitted from the real emulator at **2026-11-20 07:14:34 +07**, Modal `fc-01M7V4WKRXR151Q8RXR77GJP4G`, loaded the pinned Qwen3.5-9B checkpoint and verified FLA `0.6.0`, causal-conv1d `1.7.0`, Triton `3.3.1`, Torch `2.7.1+cu126`, CUDA `12.6`, compute capability `8.9`. Prompt encoding took 62 ms and constrained-decoder setup 3,733 ms.
3. The inference produced only 104 of 1,000 allowed tokens over 424,778 ms. The backend wait ended with `FunctionTimeoutError` / HTTP 502; Modal then recorded `KeyboardInterrupt` at 450,006 ms. No JSON result or activity selection was persisted. This is a slow inference, not a cold-start failure or missing-kernel fallback.
4. The language/audio app currently loads `AutoModelForMultimodalLM` for text-only lesson/activity/story workloads. GPU model name, device-map placement, cache state and per-callback LMFE time were not logged, so CPU offload and constrained-decoder cost remain hypotheses. Official Qwen3.5 guidance provides a text-only `Qwen3_5ForCausalLM` path; this supports a targeted implementation change while retaining the same checkpoint.

## 3. Approved implementation

### M1 — Text-only Qwen loading and safe diagnostics

- Use Transformers' Qwen3.5 text model class for the language/audio worker's text-only workloads; retain the pinned `Qwen/Qwen3.5-9B` checkpoint and revision. Keep the processor/tokenizer chat template and the existing input/output contracts.
- Log one privacy-safe runtime diagnostic after model load: GPU model name, total/allocated GPU memory, CUDA/CPU module counts from `hf_device_map`, model `use_cache`, and attention implementation. Log prompt token count and constrained-decoder callback count/last/max/aggregate duration at bounded intervals. Do not log prompts, generated text, token IDs, images, profile values, secrets, or full device-map module names.
- Preserve the existing fast-kernel guard and model-generation token heartbeat. Preserve JSON schema enforcement and all existing quality, safety, age, catalog-selection, and confirmation gates. Do not reduce schema constraints to make a pass.
- Update CPU readiness to check the text-only loader symbol without loading weights, acquiring a GPU, or generating tokens.

### M2 — Offline verification and redeploy

- Add focused regression coverage for the text-only model class, safe device/callback diagnostics, activity inference bindings, and readiness behavior.
- Run only the relevant Modal contract/readiness tests and Python compile check. Record unrelated failures separately; do not mass-fix unrelated legacy tests.
- Redeploy only `sketch2life-srs23-language-audio-dev` from this worktree. Check CPU readiness; do not warm or invoke inference during readiness.

### M3 — One bounded real UI attempt

- Submit exactly one new activity-suggestion request by pressing the available action once in the authenticated Android Expo app. Reuse the existing synthetic Parent, profile, confirmed turtle drawing/context, and StoryRun. No API-only or direct worker submission.
- Bound the full UI/API wait to 8 minutes; no worker/API retry. Capture call ID, API result, safe worker stages, GPU/device placement, callback timing, and the activity-screen screenshot.
- On success, verify the returned candidates, select one main activity in the UI, verify the persisted receipt, then continue with one story request and adult review/confirmation under Revision 25. Video remains at most one silent LTX-2.5 request after every preceding gate passes.
- If this attempt fails, retain the exact terminal reason and do not issue another activity request under this amendment. Any further live request needs a new explicit execution amendment.

## 4. Acceptance criteria

1. The text worker loads the same pinned Qwen3.5-9B revision through the text-only class; readiness imports the class without loading model weights.
2. Safe telemetry identifies whether GPU memory placement, CPU offload, or constrained-decoder callback latency explains the slow path, without exposing user content.
3. The one real Android activity request returns an actual Modal terminal success and contract-valid response within 8 minutes; or it records a precise terminal failure and does not retry.
4. Activity selection is accepted by the actual UI and persisted before story generation. Story/video are reported PASS only on real worker terminal output and completed UI gates.
5. No drawing replay, fixture, mock, direct database mutation, real child data, quota/payment mutation or test, secret/`.env` edit, model/provider substitution, scene retry, commit, or push.

## 5. Bounded execution and cleanup

- One additional activity inference only, maximum 8 minutes, retries disabled. No warm-up or duplicate submission.
- Existing Revision 25 caps remain for one story after persisted activity selection and at most one silent LTX-2.5 request after story confirmation and executable admission gates.
- Stop only task-owned Modal language/audio and drawing apps, task Compose services and task Metro after evidence capture. Keep the emulator online and preserve volumes/evidence.
- Append sanitized results to `evidence/PARENT_API_AUTH_FULL_E2E_REV24_20261119/`; update `status/STATUS.md` and the API workflow report. Do not commit or push.

## 6. Authorized paths

- `deployment/modal/srs_v23/language_audio_app.py`
- `deployment/modal/srs_v23/worker_observability.py` only if needed for allowlisted safe metrics
- Focused tests under `deployment/modal/srs_v23/tests/`
- This plan, `approvals/TASK_APPROVAL.md`, `status/STATUS.md`, and evidence under `evidence/PARENT_API_AUTH_FULL_E2E_REV24_20261119/`
- No UI redesign, SRS/DDL/migration, quota/payment, Teacher work, `.env`, direct database write, branch/history change, commit, or push.

## 7. Technical references

- Qwen3.5 official model card: text-only Transformers path uses `Qwen3_5ForCausalLM`; model card also documents the same checkpoint for serving. <https://huggingface.co/Qwen/Qwen3.5-9B>
- Hugging Face Qwen3.5 model documentation: `Qwen3_5ForCausalLM` quickstart and hybrid attention notes. <https://huggingface.co/docs/transformers/main/model_doc/qwen3_5>
- Hugging Face generation docs: `prefix_allowed_tokens_fn` is invoked for each generation step. <https://huggingface.co/docs/transformers/en/internal/generation_utils>
