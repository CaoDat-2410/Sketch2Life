# StoryRun-lite on the main backend — local synthetic UI handoff

For Windows setup, Modal CLI and model resources, ClamAV, database configuration and the live demo procedure, see [MODAL_BE_UI_SETUP_20261103.md](MODAL_BE_UI_SETUP_20261103.md).

This is a **local synthetic demo**, not Parent authentication or a production API. The actor is the fixed synthetic Parent; use no real child data. With `STORYRUN_LITE_MAIN_DEMO_ENABLED=1`, the combined `sketch2life.main:app` exposes the routes below only in local/test mode. Requests are accepted only from loopback to a loopback server with a local Host; forwarded-client headers are rejected. The feature is off by default. No CORS policy was added, so a browser UI must use the same origin; do not assume a remote UI or reverse proxy is supported.

The owner-approved local target is PostgreSQL 17 `127.0.0.1:5433/sketch2life`, with the connected user also the database owner. Both `SKETCH2LIFE_DATABASE_URL` and `STORYRUN_LITE_DATABASE_URL` must explicitly point at the same target; provide secrets through local process configuration, never in the UI or source. Real ClamAV, worker limits and a configured Vision path are required for image admission/analysis. Modal live mode additionally requires the run UUID to be pinned and the bearer held server-side. The Modal app and local test processes from the smoke were stopped after the test; they must be set up again for another demo. Do not retry an ambiguous request after `SENT`/`UNKNOWN`.

With the opt-in enabled, the main app's `/openapi.json` includes the namespaced StoryRun contract. The original standalone contract is `openapi.json` beside this file; the example requests are in `bruno/`.

Use `GET /v1/story-runs/readiness` to monitor this demo runtime: 200 means its configured runtime currently owns the pinned singleton lock; 503 means it cannot accept StoryRun work. It is available in both standalone and opt-in main apps. `/health` remains main backend liveness and is not StoryRun readiness. If readiness latches lock loss, restart that instance rather than treating a still-healthy `/health` as permission to continue.

| Step | Method and route | UI behavior |
| --- | --- | --- |
| Create | `POST /v1/story-runs` | Send an `Idempotency-Key`; retain `run_ref`, revision and response ETag. |
| Begin upload | `POST /v1/upload-sessions` | Send purpose, target, media type, size and SHA-256 with an idempotency key; retain upload ref and ETag. |
| Send part | `PUT /v1/upload-sessions/{upload_ref}/parts/{part_no}` | Supply content length and `Content-SHA256`; respect server part limits. |
| Complete | `POST /v1/upload-sessions/{upload_ref}/complete` | Send aggregate size/hash, `If-Match` and idempotency key; poll the upload. |
| Upload status | `GET /v1/upload-sessions/{upload_ref}` | Wait for `READY` and use the admitted `asset_ref`; surface failure states. |
| Attach | `POST /v1/story-runs/{run_ref}/assets` | Send `asset_ref`, expected revision, `If-Match` and idempotency key; a response can wait for Vision. Do not blindly replay an ambiguous live attempt. |
| Run status | `GET /v1/story-runs/{run_ref}` | Read the result at `SUBJECT_REVIEW` and retain the new ETag and understanding revision. |
| Confirm | `POST /v1/story-runs/{run_ref}/subject-confirmation` | Confirm the current understanding revision with `If-Match` and an idempotency key; use Bruno `11-get-run-after-confirm` to check `PREPARATION_REVIEW` and refresh the ETag/revision. |
| Cancel / demo closeout | `POST /v1/story-runs/{run_ref}/cancel` | Cancel an eligible unfinished run or explicitly close the demo after `PREPARATION_REVIEW`; use the current revision/ETag and an idempotency key. `202` / `DELETE_PENDING` releases the active-owner slot and preserves the prior admitted assets, result and receipts. |
| Abort upload | `DELETE /v1/upload-sessions/{upload_ref}` | Abort an eligible upload using the contract's preconditions and idempotency rules. |

The smoke on 2026-11-03 reached `PREPARATION_REVIEW` after confirmation. This result does not cover later story/video stages. To repeat the demo on the same DB, read the confirmed run with request 11, close it explicitly with request 09, and start the next run using fresh idempotency keys. Follow the setup guide to re-pin the new run UUID before live attach. Keep the old run, assets and receipts; do not delete or reset the DB. The earlier live smoke is historical evidence, not proof that the revised repeat-run procedure has been rerun against Modal.
