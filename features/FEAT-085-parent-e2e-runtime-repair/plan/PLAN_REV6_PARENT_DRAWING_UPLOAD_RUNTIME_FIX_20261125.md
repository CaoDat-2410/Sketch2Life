# Plan Rev6 — Parent drawing upload runtime repair

**Status:** APPROVED under the existing Parent real-E2E authorization and Addendum 9.

## Observed failure

- The real Expo app created a Parent run successfully (`POST /v1/story-runs` → `201`) and read it back (`GET /v1/story-runs/{run_id}` → `200`).
- The next request, `POST /v1/upload-sessions`, returned `404 Not Found`.
- The running FEAT-085 API image does not contain `sketch2life.interfaces.http.routers.upload_sessions`; runtime OpenAPI also lacks `/v1/upload-sessions`. Current root source contains the router and mounts it in the combined local app.
- Drawing bytes were not uploaded and no drawing/VLM inference was dispatched. The UI nevertheless locks the image after run creation and reduces the unrecognized HTTP error to a generic message.
- Separately, the Android camera action remains in `busy` after its permission result; the gallery path works after remounting CaptureScreen.

## Scope

1. Rebuild and recreate only `fe085-parent-api-20261123` from the current root checkout using the existing task Compose project and override. Use `--no-deps`; preserve PostgreSQL, Redis, MinIO, ClamAV, their volumes, root `.env`, Firebase data, Modal apps, and all unrelated containers.
2. Verify the rebuilt API is healthy and that the upload-session endpoint is mounted before retrying the drawing flow.
3. Resume the existing run `ed6bf408-743b-4bc9-92dd-470d36120468` from the existing authenticated emulator UI, using the already-selected generated butterfly image. Retry upload/recognition once after route verification; do not create another run or send a duplicate inference.
4. Capture HTTP access logs, worker result/error, and UI evidence in this feature's evidence folder.

## Exclusions and safeguards

- No migration or database reset; no seed/account changes; no credentials in logs or evidence.
- No quota/admission/safety bypass. No video request in this repair.
- Do not alter unrelated Docker stacks or stop Modal apps.
- Do not change app code in this task. Record the camera busy defect and its gallery workaround separately; fix it only under a separately scoped approved task if it remains reproducible after runtime repair.
- No commit or push.

## Acceptance criteria

- Only the FEAT-085 API container is rebuilt; existing data services and volumes remain running.
- Runtime API exposes `POST /v1/upload-sessions`.
- The existing run accepts the selected drawing, completes upload, and reaches a drawing-analysis result or a specific terminal diagnostic from the worker.
- UI no longer reports the generic pre-upload failure for this run; evidence distinguishes upload acceptance from AI recognition completion.
