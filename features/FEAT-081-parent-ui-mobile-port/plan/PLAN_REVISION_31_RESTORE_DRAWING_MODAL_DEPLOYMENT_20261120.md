# FEAT-081 — Plan Revision 31: restore the missing drawing Modal deployment

- **Status:** APPROVED under the owner's active 2026-11-20 instruction to keep fixing and run the Parent flow until it works.
- **Feature/worktree:** FEAT-081, `feature/fe-mobile-remediation`, `<local-machine-path>
- **Authority:** FEAT-063 canonical SRS v2.7-draft through the current local amendments; unsigned.
- **Relationship:** execution amendment to Plan Revision 25, continuing from Revision 30. All existing per-workload limits and safety gates remain in force.

## 1. Evidence and cause

- The real Parent UI uploaded the selected synthetic turtle image and called the drawing-understanding API.
- Backend logs show `MODAL_FUNCTION_UNAVAILABLE` / Modal `NotFoundError` at `function_spawn`, with no Modal call ID. This is a pre-worker dispatch rejection; model loading and inference did not begin.
- Modal `dev` inventory has no deployed `sketch2life-srs23-drawing-vlm-dev` app. The existing Qwen3.5 pinned checkpoint directory is present in the model Volume, and the existing `huggingface-secret` is present. Do not read or copy secret values.

## 2. Authorized recovery

1. Deploy the existing `deployment/modal/srs_v23/drawing_vlm_app.py` to Modal environment `dev`; do not alter model, code, checkpoint, or secret.
2. Verify that Modal registers `analyze-drawing` and that the pinned checkpoint files are present. Use deployment/CPU inspection only; do not warm a GPU or invoke a direct worker request.
3. Use supported Parent UI/API behavior to reconcile and close the unresolved run. If a new run is required, use the current synthetic profile and existing synthetic turtle image through the real Android UI.
4. Submit at most one actual drawing inference after the function is available. The earlier `function_spawn` rejection is recorded as a failed dispatch, not a worker inference. If this one model request fails, do not resend the drawing.
5. If drawing succeeds, continue under Revision 25's existing limits: up to two activity calls only after an actionable code/deploy fix (8-minute hard cap each), one story after the persisted activity selection, and at most one silent LTX-2.5 video after every prior gate passes. No automatic retries.

## 3. Boundaries

- Synthetic Parent/profile/artwork only; real Expo Android UI and real local backend. No fixtures, mocks, preview harness, direct worker invocation, direct database writes, real child data, or fake success.
- No model download, GPU warm-up, extra topic request, topic-subject AI call, quota/payment changes or bypass, secrets/`.env` edits, migration, Teacher changes, commit, push, branch/history operations, or unrelated service shutdown.
- Keep the emulator online. Record sanitized request IDs, Modal call IDs when present, timings, terminal phases and relevant UI evidence in the existing FEAT-081 evidence folder.
- Stop only task-used Modal apps, Metro and the task Compose project after evidence capture; preserve Volumes and unrelated services.

## 4. Acceptance

- Modal `dev` contains the expected drawing app/function and Qwen3.5 pinned checkpoint is available without downloading it again.
- The single UI-driven drawing request reaches the worker and produces either a valid adult-review candidate or a precise terminal failure; the app must not silently retry.
- If drawing succeeds, continue Parent activity selection/persistence, story review/confirmation, and eligible video under Revision 25. Report every gate that was reached and any failure boundary.
