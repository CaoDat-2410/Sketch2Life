# StoryRun-lite API handoff

This folder contains the OpenAPI 3.1 contract and a Bruno collection for the local synthetic Parent demo. The OpenAPI file is the contract source. The collection defaults to `http://127.0.0.1:8778`; it is not configured for a provider, Modal, GPU, or remote host.

Before the flow, send `12-get-readiness` (`GET /v1/story-runs/readiness`). A configured runtime that still owns its pinned singleton session returns `200` with `status: ready`; missing runtime or lost ownership returns `503 SERVICE_NOT_READY`. The main backend's `/health` checks infrastructure liveness and may remain `ok` when StoryRun is unready. After lock loss the old process must be restarted; the readiness check does not reconnect or reacquire the lock.

## Flow

1. Start the dedicated `story_run_lite_app` on loopback after creating and migrating a goal-owned disposable PostgreSQL database, or follow `MAIN_BE_UI_HANDOFF_20261103.md` to enable the same routes in the main backend. Use the base URL of the API you started.
2. In Bruno, select the `local` environment and send `01-create-run`. The response script stores `runRef` for the rest of this collection.
3. Choose a synthetic JPEG, PNG, or WebP image and save its bytes as `synthetic-upload.bin` in the collection root (the folder containing `bruno.json`). The file body uses this collection-relative path. For a clean local workflow, copy the collection to a temporary directory and place the chosen image there. Set `syntheticMediaType`, `expectedSizeBytes`, `expectedSha256`, `contentLength`, and `contentSha256` in the `local` environment from the exact bytes. Do not use real child photos.
4. Send `02-create-upload`; it stores `uploadRef` and the server-advertised part limits. The sample Bruno request sends one part, so use an image of at most 4 MiB. The backend accepts 1–5 contiguous parts; the focused API and PostgreSQL tests cover multipart behavior.
5. Send `03-upload-part` to transfer the image bytes. For this one-part example, use `partNo=1`, `contentLength=expectedSizeBytes`, and `contentSha256=expectedSha256`; these values must describe the exact bytes in `synthetic-upload.bin`. The request must return `200` before completing the upload.
6. Send `04-complete-upload` with the aggregate size and SHA-256. Poll with `05-get-upload` until the upload is `READY`; scanner or worker failures stay fail-closed.
7. Copy the admitted `asset_ref` from the upload response into the local environment. Attach it with `06-attach-asset`, then poll `07-get-run` until `SUBJECT_REVIEW`.
8. Confirm only the current `understanding_revision` using `08-confirm-subject`. A stale revision returns `409 STALE_REVISION`; exact command replay returns the original `202` without a second decision or Vision attempt. Send `11-get-run-after-confirm` to assert the final `PREPARATION_REVIEW` state and refresh the run ETag/revision. Request 07 deliberately asserts the earlier `SUBJECT_REVIEW` state; do not use it as the post-confirm test.
9. To end the successful demo before starting another run, explicitly send `09-cancel-run` after request 11. It uses the current ETag/revision and must return `202` with `DELETE_PENDING`, releasing the active-owner slot while preserving the prior run, admitted assets, result and receipts. It can also cancel an eligible unfinished run. `10-abort-upload` is an alternative branch on a fresh open upload before completing it. Cancellation does not prove that an external provider or GPU stopped.

The local environment keeps each idempotency key in a named variable. Change those keys for a fresh demo run; reuse the same keys only for exact replays of the same requests. Requests `01`–`08` and `11` include status assertions so a 4xx/5xx response fails the Bruno CLI run instead of appearing as a successful handoff.

From the collection root, run the main flow with the Bruno CLI:

```text
bru run requests/01-create-run.bru requests/02-create-upload.bru requests/03-upload-part.bru requests/04-complete-upload.bru requests/05-get-upload.bru requests/06-attach-asset.bru requests/07-get-run.bru requests/08-confirm-subject.bru requests/11-get-run-after-confirm.bru --env local
```

To demonstrate a second image on the same database, first close the prior successful run with request 09. Keep its records; do not delete or reset the database. Use fresh idempotency keys, select the next synthetic image and calculate its size/hash, then repeat 01–08 and 11. For Modal live mode, stop before the next request 06, restart the API with the newly created run UUID in `STORYRUN_LITE_MODAL_RUN_ID`, and follow `MODAL_BE_UI_SETUP_20261103.md`. Do not reuse the previous run pin or attempt.

## Limits and safety

The current server target is 20,971,520 bytes total, 4,194,304 bytes per part, at most five contiguous parts, and 40,000,000 pixels. JPEG, PNG, and WebP are accepted for original uploads. The server advertises limits on upload creation; clients must read those values instead of hard-coding part count. Original bytes and their server hash remain distinct from a normalized V2 model-input derivative and its lineage.

ClamAV must return `CLEAN` for the exact immutable quarantine snapshot before any parser or decoder runs. The decoder/normalizer must run in a killable worker with verified OS-enforced RAM and CPU limits. A local scanner stub is for tests only and is never presented as a real `CLEAN` result. If ClamAV or worker limits are not verified, the corresponding readiness remains `NOT VERIFIED` and no image is dispatched to Vision.

S1 uses explicitly fake Vision. S2 uses only the existing A1 guard, ledger, and HTTP transport against a loopback stub. Neither stage authorizes Modal, GPU, remote provider, real child data, or production use.
