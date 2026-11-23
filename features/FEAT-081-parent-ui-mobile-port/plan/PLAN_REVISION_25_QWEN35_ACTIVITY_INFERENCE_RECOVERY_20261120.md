# FEAT-081 — Plan Revision 25: Recover Qwen3.5 activity inference and resume real Parent E2E

- **Status:** APPROVED by the owner's direct instruction on 2026-11-20 (Asia/Saigon): “fix tiếp đi, nào nó chạy đc hết thig dùng”.
- **Feature/worktree:** FEAT-081, `feature/fe-mobile-remediation`, `<local-machine-path>
- **Product authority:** `docs/context/SRS_AUTHORITY.md` and the FEAT-063 canonical SRS v2.7-draft (Rev67 plus local amendments through Rev71); unsigned. FEAT-081 Rev24 and evidence define implementation/run provenance only.
- **Relationship:** execution amendment to Plan Revision 24. It supersedes Addendum 47's “no further activity request” limit only for the bounded activity recovery below. Other Rev24/Addendum 42–46 boundaries remain active.

## 1. Goal

Fix the Qwen3.5-9B `parent.activity.suggest` worker's 30-minute silent inference stall, then continue the actual Parent workflow on the Android emulator through activity selection, story review/confirmation, and one silent LTX-2.5 video request only if each prior gate and the real video path is operational.

Existing run: `343d11c6-73fe-48e7-913a-069324b63b3d`, created with synthetic Parent/profile/artwork. Reuse its verified drawing understanding and adult-confirmed context through supported UI/API behavior. Do not repeat the drawing request unless the existing run is unusable and a fresh UI run is the only supported recovery.

## 2. Findings that motivate the amendment

- The real activity worker passed envelope, workload, manifest, request, checkpoint, model-load, prompt-encoding and constrained-decoder phases, then remained in `model_inference` for 1,800 seconds without a terminal event or token-progress log.
- Modal logs warned that `causal_conv1d` and `flash-linear-attention` were absent and Transformers had selected its slower PyTorch reference fallback for Qwen3.5's hybrid Gated DeltaNet layers. This is a concrete performance defect and plausible cause; it is not treated as the sole proven cause until a fast-path run is observed.
- The Qwen model and pinned revision remain `Qwen/Qwen3.5-9B` / `c202236235762e1c871ad0ccb60c8ee5ba337b9a`. No model/provider substitution and no schema, safety, business-rule, or quality-gate relaxation.

## 3. Implementation scope

### M1 — Compatible fast kernels and fail-fast readiness

- Add explicitly pinned CUDA-compatible `flash-linear-attention` and `causal-conv1d` dependencies to the shared Modal Qwen image without changing the pinned PyTorch/Transformers/model versions.
- Add an allowlisted, privacy-safe readiness report for package versions, import/callable availability, Torch CUDA build, and GPU capability when available. Never log prompt, generated text, profile/child data, images, or secrets.
- Fail before loading/generating if required Qwen3.5 fast-kernel dependencies are absent. Do not silently accept the reference fallback.
- Do not add a model warm-up request. `/health` or readiness must not load weights or generate tokens.

### M2 — Inference progress and bounded waits

- Add low-volume generation progress events for the Parent activity and story workloads, reporting only generated-token count, maximum-token budget, elapsed milliseconds, and derived tokens/second. Emit at bounded intervals; do not log text/token IDs.
- Keep constrained JSON decoding and the existing output/business/safety gates intact.
- Bound each real activity request at 8 minutes end-to-end, with retries disabled. A timeout must surface a stage-specific terminal/unknown result, must not auto-submit another inference, and must stop the task-used Modal app during cleanup.
- If the first post-fix request reveals a specific fixable worker/runtime defect, one further activity request is authorized after a code/deploy fix; maximum two post-fix activity requests total. No repeat merely to benchmark.

### M3 — Resume through the real Parent UI

- Verify local API health, Modal CPU readiness, Android app/auth state, and current run through supported paths before submitting the single recovery request.
- Submit activity suggestions from the real Expo Android UI using the authenticated synthetic Parent and catalog/context already attached to the run. Require HTTP success, valid schema, catalog-first result/fallback contract, quality/safety gates, and actual worker terminal success.
- Select one returned primary activity in the UI and persist the selection receipt. Then run at most one actual Qwen3.5 story/storyboard request, show the returned result for adult review, and confirm it through the UI.
- Before video, source-review the mounted API and deployed Modal code for the exact silent LTX-2.5 path. If valid and all story/safety/admission gates pass, submit at most one video request and capture the actual output. Do not use another video model or a cached/sample result.
- Quota/payment endpoints are not tested or changed. Any local synthetic-only quota bypass remains server-guarded, default OFF, auditable, and must not alter product quota records.

## 4. Acceptance criteria

1. Focused tests prove the image pins the kernel dependencies and the readiness guard rejects a missing kernel without leaking sensitive values.
2. Readiness reports the actual installed kernel/package state; the deployed worker does not enter model inference with the Qwen reference fallback.
3. The actual Android activity request completes within 8 minutes with a real Qwen3.5 worker terminal event and a schema/quality/safety-valid response, or records a precise failure boundary and no automatic retry.
4. If activity succeeds, the actual UI saves the selected activity. Story and optional video count as PASS only if their real UI/API/worker outputs and required adult/safety gates complete.
5. Every attempted call has a sanitized call/job ID, UTC/local timestamps, elapsed time, worker phase/progress and API outcome recorded in feature-local evidence.
6. No fixture, mock, direct DB write, real child data, secret/env-file edit, quota/payment test, model substitution, scene retry, commit, or push.

## 5. Bounded live execution and cost controls

- Maximum two post-fix activity inference requests total; each hard-limited to 8 minutes and with worker/API retries disabled. The current stale task is not reused as a model warm-up.
- At most one story inference and one silent LTX-2.5 video request, only after prior gates pass. Existing successful drawing analysis is reused; a fresh drawing inference is permitted only if a supported UI recovery requires a new synthetic run, and no successful result is replayed.
- No separate GPU warm-up, benchmark, duplicate submission, direct worker invocation, or scene retry. Check only CPU `/health`/readiness before the UI-driven inference.
- If a path fails, capture enough logs to identify the phase; stop task-owned Modal apps and do not leave a GPU container running while investigating.

## 6. Evidence and cleanup

- Append results to `evidence/PARENT_API_AUTH_FULL_E2E_REV24_20261119/`; preserve existing evidence. Add sanitized dependency/build/readiness diagnostics, worker progress, call timings, API results and only relevant Android workflow screenshots.
- Stop only Modal apps and local processes/services started or used for this amendment. Do not stop unrelated Docker stacks or the emulator. Keep Compose volumes.
- Update FEAT-081 `status/STATUS.md` and the API workflow result after each material result. No commit/push.

## 7. Authorized paths

- `deployment/modal/srs_v23/language_audio_app.py`, `deployment/modal/srs_v23/worker_observability.py`, and focused Modal tests under `deployment/modal/srs_v23/tests/`.
- Only the Parent activity timeout/configuration and error classification code needed for the 8-minute bound, under `backend/src/sketch2life/infrastructure/ai/`, `backend/src/sketch2life/infrastructure/config/`, or the activity route/service, plus focused tests.
- This plan, `features/FEAT-081-parent-ui-mobile-port/approvals/TASK_APPROVAL.md`, `features/FEAT-081-parent-ui-mobile-port/status/STATUS.md`, and evidence under `evidence/PARENT_API_AUTH_FULL_E2E_REV24_20261119/`.
- No other UI redesign, SRS change, schema/migration, quota/payment, Teacher work, `.env` edit, DB mutation, branch/history operation, commit, or push.

## 8. Technical references consulted

- Hugging Face Transformers Qwen3.5 docs: optional `causal_conv1d` and FLA provide fast Gated DeltaNet kernels; without them the model falls back to slower, more memory-heavy PyTorch operations.
- FLA upstream installation docs and `pyproject.toml`: CUDA extra requires PyTorch >=2.7.0 and Triton >=3.3.
- Dao-AILab `causal-conv1d` release/CI matrix includes PyTorch 2.7.1 wheel builds; deployment must still validate the exact Modal CUDA/Python/ABI combination at runtime.

