# EV-063-112 — Parent API to Modal guide runtime failure

**Date:** 2026-11-15<br>
**Plan:** Rev87.17<br>
**Environment:** local Docker API + Firebase Auth Emulator, Modal `dev` Qwen3.5 worker and Openclipart Modal Volume v2

## Result

The real Parent request reached Modal and the worker completed successfully, but the API returned HTTP 502 with `MODAL_SVG_SOURCE_GUIDE_OUTPUT_REJECTED`. The sanitized API reason was `SVG_SOURCE_GUIDE_SCHEMA_UNSUPPORTED`. This was a schema-version mismatch at the API boundary, not a GPU timeout, model failure, invalid source SVG, or path-coverage failure.

The worker payload correctly used `SvgTopicStrokeGuideContentV1`; the API validator compared it with `SvgTopicStrokeGuideV1`, the version for the API's assembled guide entity. Rev87.18 separates those schema constants and verifies the corrected flow with one fresh request.

## Request and worker evidence

- Topic: `con mèo`; no child profile, photo, voice, consent, or real personal data was sent.
- Temporary synthetic Parent authenticated through Firebase Auth Emulator; role check passed.
- Modal call: `fc-01M7E09QD3E3MWW107GSA56Q2E`; worker status `worker_succeeded`.
- Modal worker duration: 86.670 s; API worker wait: 95.394 s.
- API: HTTP 502, terminal schema rejection; no retry was sent under Rev87.17.
- The worker result and the API rejection were retained only as sanitized metadata. No account identifier, token, or raw credentials are included.

## Cleanup and scope

The emulator identity was deleted and one backend identity row was removed. No child entity or consent was created. No video, Android UI, Teacher presentation, extra inference, Modal deployment, secret change, unrelated service restart, commit, or push occurred.

## Follow-up

Rev87.18 fixes the schema boundary. Its successful API → Modal → API result and output artifacts are recorded in [EV-063-113](../EV-063-113_PARENT_MODAL_API_GUIDE_SCHEMA_FIX_20261115/REPORT.md).
