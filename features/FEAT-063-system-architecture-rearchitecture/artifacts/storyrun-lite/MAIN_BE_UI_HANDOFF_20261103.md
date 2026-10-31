# StoryRun-lite on the main backend — local synthetic UI handoff

For Windows setup, Modal CLI and model resources, ClamAV, database configuration and the live demo procedure, see [MODAL_BE_UI_SETUP_20261103.md](MODAL_BE_UI_SETUP_20261103.md).

This is a **local synthetic demo**, not Parent authentication or a production API. The actor is the fixed synthetic Parent; use no real child data. With `STORYRUN_LITE_MAIN_DEMO_ENABLED=1`, the combined `sketch2life.main:app` exposes the routes below only in local/test mode. Requests are accepted only from loopback to a loopback server with a local Host; forwarded-client headers are rejected. The feature is off by default. No CORS policy was added, so a browser UI must use the same origin; do not assume a remote UI or reverse proxy is supported.

The owner-approved local target is PostgreSQL 17 `127.0.0.1:5433/sketch2life`, with the connected user also the database owner. Both `SKETCH2LIFE_DATABASE_URL` and `STORYRUN_LITE_DATABASE_URL` must explicitly point at the same target; provide secrets through local process configuration, never in the UI or source. Real ClamAV, worker limits and a configured Vision path are required for image admission/analysis. Modal live mode additionally requires the run UUID to be pinned and the bearer held server-side. The Modal app and local test processes from the smoke were stopped after the test; they must be set up again for another demo. Do not retry an ambiguous request after `SENT`/`UNKNOWN`.

With the opt-in enabled, the main app's `/openapi.json` includes the namespaced StoryRun contract. The original standalone contract is `openapi.json` beside this file; the example requests are in `bruno/`.

| Step | Method and route | UI behavior |
| --- | --- | --- |
| Create | `POST /v1/story-runs` | Send an `Idempotency-Key`; retain `run_ref`, revision and response ETag. |
| Begin upload | `POST /v1/upload-sessions` | Send purpose, target, media type, size and SHA-256 with an idempotency key; retain upload ref and ETag. |
| Send part | `PUT /v1/upload-sessions/{upload_ref}/parts/{part_no}` | Supply content length and `Content-SHA256`; respect server part limits. |
| Complete | `POST /v1/upload-sessions/{upload_ref}/complete` | Send aggregate size/hash, `If-Match` and idempotency key; poll the upload. |
| Upload status | `GET /v1/upload-sessions/{upload_ref}` | Wait for `READY` and use the admitted `asset_ref`; surface failure states. |
| Attach | `POST /v1/story-runs/{run_ref}/assets` | Send `asset_ref`, expected revision, `If-Match` and idempotency key; a response can wait for Vision. Do not blindly replay an ambiguous live attempt. |
| Run status | `GET /v1/story-runs/{run_ref}` | Read the result at `SUBJECT_REVIEW` and retain the new ETag and understanding revision. |
| Confirm | `POST /v1/story-runs/{run_ref}/subject-confirmation` | Confirm the current understanding revision with `If-Match` and an idempotency key; a 202 is followed by GET. |
| Alternatives | `POST /v1/story-runs/{run_ref}/cancel`; `DELETE /v1/upload-sessions/{upload_ref}` | Cancel or abort using the contract's preconditions and idempotency rules. |

The smoke on 2026-11-03 reached `PREPARATION_REVIEW` after confirmation. This result does not cover later story/video stages. The current synthetic run and its assets remain in the local DB; do not delete or reset them to start a new test without an owner-approved lifecycle action.
