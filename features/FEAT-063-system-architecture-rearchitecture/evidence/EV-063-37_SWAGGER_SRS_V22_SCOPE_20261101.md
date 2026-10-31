# EV-063-37 — FE Swagger scope aligned to SRS v2.2

- Date: 2026-11-01, Asia/Saigon.
- Branch: `dev` (started clean and synchronized with `origin/dev`).
- Feature: FEAT-063; approved Plan Rev45 SHA-256 `5D1DBABE161F92F08DE7FE8C1B81B1E5D57CFA3C2B8D57CBA6BE76ACADB0FD06`.
- Owner instruction: “giờ cập nhật lại swagger trên nhánh dev theo srs 2.2 đi”.
- SRS baseline: repository SRS v2.2-draft SHA-256 `D1C4AF0D42A160AAA08D1EC33F1FFD746C4EB33CA75C5D802616A5DD4502E4DE`. The owner selected it for this Swagger task; its draft/sign-off status is unchanged. §9.6 labels target route groups as proposals.

## Result

The FE-facing Swagger publishes exactly 24 existing operations across 17 paths and four tags:

- Organization/class/profile/consent: 11 operations.
- Teacher lesson preparation and authoring: 6 operations.
- Teacher and School Manager lesson read/archive: 3 operations.
- Lesson document upload sessions: 4 operations.

All other currently mounted operations remain registered in the backend and retained in `app.state.runtime_openapi_schema` for full contract inventory. The FE projection omits 100 operations: collaborative classroom/session/device/artifact flows (35), gallery/records (8), local/demo capture/session/renderer/video flows (35), lesson sharing/invitations (14), dev storage examples (3), health (2), access-grant create/revoke operations (2), and platform moderation (1). The 11 unmounted candidate operations remain absent.

The Swagger overview states that Parent profile/story/activity, Teacher lesson-occurrence/Sketch Deck/sample-video/projection, job/playback, quota/subscription/payment, and notification APIs are not available in this FE surface. No target route was invented from SRS §9.6. Public tags and failure descriptions avoid the internal `BE1` label. The common error model is presented as `ApiError`; it retains the current `code`, `message`, and `request_id` fields. Runtime paths and payloads are preserved.

## Verification evidence

- Export command: `$env:SKETCH2LIFE_ENV='local'; $env:SKETCH2LIFE_STORAGE_EXAMPLE_ENABLED='true'; & backend/.venv/Scripts/python.exe features/FEAT-063-system-architecture-rearchitecture/scripts/export_openapi_rev37.py`.
- Export result: `OPENAPI_VALID: 17 FE paths / 24 SRS v2.2 operations; preserved 124 full runtime operations and excluded 11 unmounted candidates`.
- The Swagger overview was shortened to 50 words; each of the four tag descriptions is 5–7 words.
- Snapshot: `artifacts/OPENAPI_FEAT063_REV45_20261101.json`; SHA-256 `C61D3ADD7FF906AC9E5B018A9CE428AF7B162D67510FEEE7B202B53DA05D74A2`.
- The default Python had no FastAPI installed; rerunning with the project `backend/.venv` succeeded.
- Live `http://127.0.0.1:8000/docs` and `/openapi.json` returned HTTP 200. Served document equals the generated snapshot and contains 24 operations, 17 paths, and four tags.
- The exporter checked full runtime Rev37 contract parity, exact FE allowlist, operation metadata preservation, referenced schemas, and zero custom `x-` extensions. `git diff --check` passed.
- Backend tests were not run. No database, provider, deployment, commit, or push operation was performed.

## Interpretation and limits

The projection documents currently implemented, SRS-related FE operations. It does not make the draft SRS a signed-off contract and does not imply that omitted Parent video, Teacher occurrence/Sketch Deck/sample, quota/payment, or notification flows have been implemented. Paths remain as currently mounted, even where they differ from logical route patterns in SRS §9.6. Runtime routes, handlers, authorization, and payloads are unchanged.
