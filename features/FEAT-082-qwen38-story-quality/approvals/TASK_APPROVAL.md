# FEAT-082 task approval

## Plan Rev1 — Qwen3.8-27B-FP8 and Parent story prompt

- **Status:** APPROVED
- **Approver:** Project owner, direct instruction in this conversation: “thử chuyển sang luôn đi, kèm cả tối ưu prompt luôn”.
- **Approval date:** 2026-11-22 (Asia/Saigon)
- **Approved scope:** Exact scope, file list, constraints, and acceptance criteria in `plan/PLAN_REV1_QWEN38_FP8_STORY_PROMPT_20261122.md`.
- **Plan SHA-256 (current after Amendment I):** B3530A1BF227949EE7A0F8C470DB58B556CEC6156E843359D48E878ACFC91D6E
- **Cost/runtime authorization:** One pinned public model download to the existing Modal volume and at most one synthetic Parent story inference on L40S; stop the language/audio app afterward. No video, real child data, or repeated GPU retry.
- **Out of scope:** Any code or runtime changes beyond the approved file list; do not use the working-tree approval as authorization to modify or commit unrelated existing changes.

### Amendment A

- **Date:** 2026-11-22
- **Change:** Narrow Plan Rev1 to exclude unrestricted free-text profile interests from Modal input; allow only topic and exact approved lesson snapshot fields. No new file or capability was added.
- **Basis:** Repository inspection showed the persisted interests field is free text and is not normalized to the SRS allowlist. This narrows the owner-approved AI data scope to preserve the SRS privacy rule.
- **Updated plan SHA-256:** `1A28FE47C7FA7C7749F7932298E5C30629722B7DAE0D22A70C0D627025076B0B`

### Amendment B

- **Date:** 2026-11-22
- **Change:** Corrected stale checklist text about interests and recorded the official Transformers FP8 kernel extra as part of the approved model-loader implementation.
- **Basis:** The existing field is unrestricted free text and is excluded; official Transformers documentation requires the fine-grained FP8 kernel extra for this checkpoint format.
- **Updated plan SHA-256:** `B7DF0FF0D045AE85F8559FED9392F77892496AD9F7196585C08785199823A030`

### Amendment C

- **Date:** 2026-11-22
- **Change:** Added Teacher text API provenance alignment to the approved implementation file list.
- **Basis:** Teacher lesson-plan and Sketch Deck endpoints compare output model metadata with the Qwen3.5 drawing model; after the shared text checkpoint switch, that would cause false model-revision failures.
- **Updated plan SHA-256:** `382749C9A4774AD3CBB586024F3043611096D37364B026BD44C6C4720BEF9B3E`

### Amendment D

- **Date:** 2026-11-22
- **Change:** Within the already approved Modal worker file, preload the exact Hugging Face fine-grained FP8 kernel from a pinned commit using a repository-specific allowlist, validate its required functions, and place it in Transformers' kernel cache. Keep the one-inference cap unchanged; another inference needs separate owner approval.
- **Basis:** The sole approved synthetic story inference failed at the kernel publisher lookup before any story tokens were generated. Official Hugging Face documentation confirms Transformers 5.22.1 uses the `kernels-community/finegrained-fp8` version 4 integration and the kernels API supports an exact repository allowlist. The repository is marked Trusted publisher and Apache-2.0.
- **Updated plan SHA-256:** AEF66FC78900DADE44640C402B388561864B2BEA1001F5CA308822148F396EB9

### Amendment E

- **Date:** 2026-11-22
- **Change:** Extend the story test cap by exactly one fresh story-generation request, initiated through the real Parent Android UI and routed through the local backend to Modal. Allow relevant fixes in the Parent UI paths listed in Plan Rev1. Keep synthetic-only data, normal admission/safety/business gates, no video, no fixture, and no repeat after a terminal worker error.
- **Basis:** Owner direct instruction in this conversation: “chạy thử trên UI đi, fix nếu có bug”.
- **Evidence:** Capture Parent UI screenshots and sanitized backend/Modal request timing/logs in this feature's evidence folder; stop the language/audio Modal app after the attempt.
- **Updated plan SHA-256:** 21C21747DE6C44C76C2E1DEE91C5B3FBA7625F3A80140A4DA578F4320008A0A3

### Amendment F

- **Date:** 2026-11-22
- **Change:** Fix the Parent mandatory activity-selection gap across UI, API, persistence, and Qwen story input. Store suggestion sets and adult selections with run/owner/input/understanding revision binding; recheck exact lesson access; block story generation until a valid selection exists.
- **Basis:** Owner request to run on the real UI and fix bugs; source review found a bypassable UI step and a story contract that omitted the required selected activity, contrary to FEAT-063 Rev67 FR-P-05 and §31.17.
- **Runtime limit:** One activity-suggestion inference and one fresh Android UI story inference; synthetic data, normal auth/consent/access/quota/safety gates, no video, no repeat after terminal worker failure.
- **Updated plan SHA-256:** EE46DF48EE1FC3F2EA477AC736F0E99AFC474B77E00694DBE898AA7FEC9450CD

### Amendment G

- **Date:** 2026-11-22
- **Status:** APPROVED by the owner's direct request: “chạy thử trên UI đi, fix nếu có bug”.
- **Approved plan SHA-256:** `8F3737F8D2F9DE8E1A10D35C7F3E4263A960135FAE1EF07AAF028212864477BC`.
- **Execution target:** the current `feature/fe-mobile-remediation` worktree, which supplies the Parent UI and mounted API container.
- **Finding and scope:** this worktree already contains persisted activity suggestion/selection and exact selected-activity snapshots. Reuse them; add no duplicate schema, route, or migration. Port the already approved Qwen3.8-27B-FP8 story/text model and prompt update into this worktree, align backend/Teacher text provenance, and update focused contract tests and the workload record. Version the story worker input as v3 with only bounded server-owned topic and the exact pinned lesson's subject-learning notes; exclude free-text profile interests and profile identity. Preserve the activity selection contract, Parent parser, and safe worker progress logs. Drawing VLM stays Qwen3.5; video stays out of scope.
- **Runtime cap:** reuse an existing synthetic activity selection when valid; otherwise at most one activity-suggestion inference. Send at most one new story request through the real Android UI. No fixture/real-child data, direct worker/API inference, quota or safety bypass, video call, or retry after a terminal worker failure. Capture sanitized runtime/request/call/timing evidence and Android screenshots; stop the language/audio Modal app afterward.
- **No commit or push.**

### Amendment H

- **Date:** 2026-11-22
- **Status:** APPROVED by the owner's direct response: “Cho phép sửa riêng stack test (Recommended)”.
- **Scope:** Use a temporary Compose override outside the repository to change only the FEAT-082 ClamAV service host publication from `127.0.0.1:3310` to `127.0.0.1:53310`. Recreate only this project's ClamAV container, preserve the existing signature database volume, leave the older stack untouched, and remove the temporary override afterward. Do not change tracked Compose files.
- **Verification:** Confirm network attachment and service DNS from the API container; scan the existing synthetic artwork and require `CLEAN`; retry the already failed Parent UI artwork-analysis action once. The prior request failed before AI dispatch, so Amendment G's AI inference caps remain unchanged.
- **Updated plan SHA-256:** `A1B494D9303C53C5E7F83742F9CC32C5FDC71F1951AD7177CE59EE7593439594`.

### Amendment I

- **Date:** 2026-11-22
- **Status:** APPROVED under the owner's direct instruction to run the real UI flow and fix bugs found in it.
- **Scope:** Fix the pinned FP8 kernel bootstrap's malformed Hugging Face user-agent in the already approved Modal worker; temporarily allow only generic package/runtime metadata for that exact bootstrap call and restore telemetry-disabled state in `finally`. Add focused offline tests for the fixed repository/revision/allowlist and restoration on success/failure.
- **Runtime:** Offline tests/static checks and health/readiness only. Do not send another AI inference; the one activity inference ended in a terminal failure, so another request requires separate explicit approval. Preserve the no-video, synthetic-only, no quota/safety bypass, no commit/push, and app cleanup rules.
- **Technical scope:** Existing approved `deployment/modal/srs_v23/language_audio_app.py` and focused Modal contract test; update FEAT-082 status/evidence.
- **Updated plan SHA-256:** `B3530A1BF227949EE7A0F8C470DB58B556CEC6156E843359D48E878ACFC91D6E`.

### Amendment J

- **Date:** 2026-11-22.
- **Status:** APPROVED by the owner's direct instruction: “chạy adb, emulator và fix lỗi tiếp đi, gọi cả vid và mấy cái kia luôn, làm luồng end to end đi, check nào hết lỗi thì ấy”.
- **Scope:** Full real synthetic Parent Android → backend → Modal activity/story → UI adult review → Modal LTX-2.5 video candidate/status/playback flow, including minimal fixes in the exact source paths listed in Plan Rev1 Amendment J. Reuse current dev models and real APIs; no fixtures/direct worker calls/database state mutation.
- **Limits:** Synthetic account/profile/art only; preserve auth, consent, malware, age, ownership, activity, story review, video safety and quota/payment behavior. No production quota bypass or ledger falsification. One fresh live request per distinct defect after its fix; no blind retries. Video is silent; no narration. No commit/push.
- **Cleanup/evidence:** Save timestamped screenshots and sanitized per-stage request/call/timing evidence in the FEAT-082 evidence folder; stop only test-specific emulator, Expo, Docker, and Modal processes/apps. Leave unrelated services and persistent volumes untouched.
- **Approved plan SHA-256:** `48EE903B5E5097458E99959333778BDCE9532876242AEE65A715934C5F3DAF7E`.

### Amendment K — Align FP8 kernel runtime with Triton TensorDescriptor — 2026-11-22

- **Status:** Included under the owner's already approved Amendment J instruction to fix distinct live defects in the Parent-to-Modal flow.
- **Evidence prompting this change:** Activity call `fc-01M820QHK486RV7GGZYAHFNGYN` (backend request `def15576-132c-4670-b4e6-bc69662f315a`) loaded the pinned Qwen3.8 model but failed before generation with `ModuleNotFoundError: triton.tools.tensor_descriptor`. The allowlisted Hugging Face FP8 kernel imports `TensorDescriptor`; Triton 3.3.1 does not ship that API, while Triton 3.4.0 does. The previous compatibility shim repaired Python import locations but could not supply the missing compiler/runtime implementation.
- **Scoped implementation:** Align the text worker to PyTorch 2.8.0 / torchvision 0.23.0 / Triton 3.4.0, and the official causal-conv1d 1.7.0 CUDA 12 Torch 2.8 CPython 3.11 wheel pinned by SHA-256. Keep the exact Qwen checkpoint, FP8 kernel repository/revision/allowlist, Modal GPU, API contract, and hard workflow gates unchanged. Remove the temporary autotuner monkey-patch; fail with a stable diagnostic if `TensorDescriptor` is unavailable.
- **Verification gate:** Run focused offline contracts and static checks, deploy the worker, confirm runtime package versions and descriptor import through readiness, then make at most one fresh UI activity request for this distinct runtime defect. Continue the Amendment J per-defect cap only after recording each outcome. No direct worker call, fixture, quota/safety bypass, commit, or push.

### Amendment L — Emit runtime telemetry without context-manager use — 2026-11-22

- **Status:** Included under the owner's already approved Amendment J instruction to fix distinct live defects in the real Parent-to-Modal flow.
- **Evidence prompting this change:** After deploying from the correct `feature/fe-mobile-remediation` worktree and confirming Torch 2.8.0 / torchvision 0.23.0 / Triton 3.4.0 / TensorDescriptor readiness, the one fresh Parent UI activity request loaded Qwen3.8 and the allowlisted FP8 kernel, then failed with `TypeError: 'NoneType' object does not support the context manager protocol` at `_load_text_model` while using `worker_runtime_verified`.
- **Scoped fix:** Call the telemetry emitter directly instead of using it in a `with` statement; retain the existing allowlisted runtime fields. Add a focused regression assertion. No runtime stack, model, schema, or hard gate change.
- **Runtime cap:** One fresh real UI activity request after the fix for this newly discovered defect, consistent with Amendment J. Continue synthetic-only, no fixture/direct worker call, no gate/quota bypass, no commit/push.

### Amendment M — Remove unsupported `use_cache` model constructor kwarg — 2026-11-22

- **Status:** Included under the owner's already approved Amendment J instruction to fix distinct live defects in the real Parent-to-Modal flow.
- **Evidence prompting this change:** The single post-Amendment L Android UI activity request passed checkpoint verification, Qwen3.8 model load, FP8 runtime compatibility, and allowlisted kernel load, then failed in `AutoModelForMultimodalLM.from_pretrained` with `TypeError: Qwen3_5ForConditionalGeneration.__init__() got an unexpected keyword argument 'use_cache'`.
- **Scoped fix:** Remove `use_cache=True` from the model constructor call and preserve the checkpoint's own generation/cache configuration. Add a focused regression check that the unsupported keyword is not forwarded to this model constructor. No model, runtime stack, output schema, or hard gate changes.
- **Runtime cap:** One fresh real Parent Android UI activity request after this fix, consistent with Amendment J. No fixture/direct worker call, no gate/quota bypass, no commit/push.

### Amendment N — owner authorization to publish completed synthetic E2E work

- **Date:** 2026-11-23.
- **Status:** APPROVED by the owner's direct instruction: “commit và push”.
- **Scope:** Commit and push the completed Parent Android → backend → Modal E2E implementation and sanitized synthetic evidence in this branch, together with the related FEAT-063 SRS/register changes.
- **Overrides for publication:** The no-commit/push limits in Amendment J and the associated follow-ups are superseded only for publishing this completed work.
- **Exclusions:** Environment files, credentials, seed account material, pytest temporary/model fixtures, deployment-local pytest output, and any real child data. Keep the video candidate's safety/product-quality status explicitly unverified.
- **Validation:** Run the repository security validator immediately before commit and immediately before push. No new AI inference is authorized by this amendment.
