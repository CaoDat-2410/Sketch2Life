# StoryRun-lite API handoff

This folder contains the OpenAPI 3.1 contract and a Bruno collection for the local synthetic Parent demo. The OpenAPI file is the contract source. The collection defaults to `http://127.0.0.1:8778`; it is not configured for a provider, Modal, GPU, or remote host.

## Flow

1. Start the dedicated `story_run_lite_app` on loopback after creating and migrating a goal-owned disposable PostgreSQL database.
2. In Bruno, select the `local` environment and send `01-create-run`. The response script stores `runRef` for the rest of this collection.
3. Choose a synthetic JPEG, PNG, or WebP image and save its bytes as `synthetic-upload.bin` in the collection root (the folder containing `bruno.json`). The file body uses this collection-relative path. For a clean local workflow, copy the collection to a temporary directory and place the chosen image there. Set `syntheticMediaType`, `expectedSizeBytes`, `expectedSha256`, `contentLength`, and `contentSha256` in the `local` environment from the exact bytes. Do not use real child photos.
4. Send `02-create-upload`; it stores `uploadRef` and the server-advertised part limits. The sample Bruno request sends one part, so use an image of at most 4 MiB. The backend accepts 1–5 contiguous parts; the focused API and PostgreSQL tests cover multipart behavior.
5. Send `04-complete-upload` with the aggregate size and SHA-256. Poll with `05-get-upload` until the upload is `READY`; scanner or worker failures stay fail-closed.
6. Copy the admitted `asset_ref` from the upload response into the local environment. Attach it with `06-attach-asset`, then poll `07-get-run` until `SUBJECT_REVIEW`.
7. Confirm only the current `understanding_revision` using `08-confirm-subject`. A stale revision returns `409 STALE_REVISION`; exact command replay returns the original `202` without a second decision or Vision attempt.
8. Use `09-cancel-run` as an alternative branch on a separate unfinished run before confirmation. Use `10-abort-upload` as an alternative branch on a fresh open upload before sending a part or completing it. They are not appended to the successful `01`–`08` flow. Cancellation never claims that an external provider or GPU stopped.

The local environment keeps each idempotency key in a named variable. Change those keys for a fresh demo run; reuse the same keys only for exact replays of the same requests. Requests `01`–`08` include status assertions so a 4xx/5xx response fails the Bruno CLI run instead of appearing as a successful handoff.

From the collection root, run the main flow with the Bruno CLI:

```text
bru run requests/01-create-run.bru requests/02-create-upload.bru requests/03-upload-part.bru requests/04-complete-upload.bru requests/05-get-upload.bru requests/06-attach-asset.bru requests/07-get-run.bru requests/08-confirm-subject.bru --env local
```

## Limits and safety

The current server target is 20,971,520 bytes total, 4,194,304 bytes per part, at most five contiguous parts, and 40,000,000 pixels. JPEG, PNG, and WebP are accepted for original uploads. The server advertises limits on upload creation; clients must read those values instead of hard-coding part count. Original bytes and their server hash remain distinct from a normalized V2 model-input derivative and its lineage.

ClamAV must return `CLEAN` for the exact immutable quarantine snapshot before any parser or decoder runs. The decoder/normalizer must run in a killable worker with verified OS-enforced RAM and CPU limits. A local scanner stub is for tests only and is never presented as a real `CLEAN` result. If ClamAV or worker limits are not verified, the corresponding readiness remains `NOT VERIFIED` and no image is dispatched to Vision.

S1 uses explicitly fake Vision. S2 uses only the existing A1 guard, ledger, and HTTP transport against a loopback stub. Neither stage authorizes Modal, GPU, remote provider, real child data, or production use.
