# Modal live recheck — 2026-11-02

## Scope

The owner directly requested a fresh check that the existing Modal Vision
service was still usable. This was one direct authenticated `POST /v2/vision`
with an existing synthetic house-and-sun PNG. It did not exercise the new
StoryRun S1/S2 flow, the A1 guard/ledger, a database, the UI, or any later AI
stage.

To avoid uploading unpublished A2 working-tree changes, the temporary Modal
serve used only the relevant files archived from clean commit
`a88de875ff92e9b4d4fa5cc2f5f8d5fc1f626f58`: the FEAT-061 deployment file,
committed backend source/manifest, and existing Vision V2 server. No source
file or configuration in the repository was changed for this run.

## Result

- Modal CLI authentication succeeded. A first serve attempt stopped before any
  inference because the Windows console could not encode a Unicode status
  character. A read-only app listing found no active app from that attempt.
- The retry with UTF-8 console settings created temporary app
  `ap-TN7uEfXGowwQNf1LLxJZvi`.
- `GET /health`: HTTP 200, `{"status":"ok","service":"modal-qwen3-vl-vision-v2"}`.
- Exactly one inference request was sent to `/v2/vision`. Its fixture was the
  existing synthetic PNG with SHA-256
  `504a0d0c03a4183f25608138bf8dc46a6779155b4fa5015e9c4e89ce10103f89`.
- Result: HTTP 200, `VisionUnderstandingResultV2` version `2.0`, status
  `SUCCEEDED`, fresh correlation ID matched, and one entity was returned. The
  server log recorded `attempt=1`, `repair_attempted=True`, and HTTP duration /
  execution of 20.7 / 20.6 seconds. No retry or redirect was followed.
- The token was read from its local file only into process memory. The raw
  response and generated text were not printed or persisted. The sanitized
  client check did not capture profile/revision fields, so this recheck makes
  no new provenance claim. Modal billing was not queried.
- The temporary app was explicitly stopped. Modal later reported
  `state=stopped`, `tasks=0`, at 2026-11-02 16:50:38 Asia/Saigon.

## Conclusion and limits

The existing FEAT-061 Modal Qwen Vision V2 endpoint accepted a synthetic image
and returned a successful typed result during this check. This confirms the
legacy direct endpoint was reachable and functional at that time. It does not
prove the new S1/S2 backend flow is integrated with Modal, establish recognition
quality or production readiness, or authorize another provider call.
