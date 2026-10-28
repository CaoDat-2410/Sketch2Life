# EV-063-23 — Local Docker, MinIO and S3-compatible storage example

- Reviewed: 2026-10-28.
- Approved scope: FEAT-063 Plan Rev30, SHA-256 `F6BD755CBC543374AC9091BB7603C2A9EB83DC20F2EDCA92B2A10158AB88C794`.
- Approval: owner direct instruction recorded in `approvals/TASK_APPROVAL.md` at 2026-10-28 22:21:18 Asia/Saigon.
- Evidence type: source/configuration review; runtime behavior has not been demonstrated.

## Implemented local path

`api (FastAPI) -> StorageExampleService -> ObjectStoragePort -> Boto3S3CompatibleObjectStorage -> private MinIO bucket`

The application port contains no MinIO/Boto3 types. The adapter accepts an endpoint override and path-style addressing for local MinIO. With the endpoint omitted, Boto3 uses its standard credential chain, which supports a later AWS IAM role configuration without changing application use cases.

The development-only routes are:

- `POST /api/dev/v1/storage-examples/lesson-source-documents` — bounded PDF/DOCX/PPTX upload, generated object ID and SHA-256 receipt.
- `GET /api/dev/v1/storage-examples/lesson-source-documents/{object_id}` — stream from private storage through the backend.
- `DELETE /api/dev/v1/storage-examples/lesson-source-documents/{object_id}` — remove the example object.

The router is mounted only for `env=local`, the explicit example flag, and the combined local app. Compose publishes the API/MinIO ports on loopback. The Docker build context excludes actual environment and secret files. No actual `.env` file was read, created, or modified.

## Files changed

- `compose.yaml`: backend API, pinned local MinIO image, bucket initializer, loopback ports and health/start ordering; existing Postgres/Redis/MinIO data volumes are retained.
- `.env.example` and `backend/.env.example`: local S3-compatible endpoint, region, bucket, placeholder credentials and example limits/flag.
- `backend/.dockerignore`: prevents ignored environment/secret files and test/runtime artifacts from entering the image build context.
- `backend/src/sketch2life/application/ports/object_storage.py`: provider-neutral port and object result types.
- `backend/src/sketch2life/application/services/storage_example.py`: bounded example upload, generated key, allowlisted extensions, safe filename and checksum.
- `backend/src/sketch2life/infrastructure/storage/s3_compatible.py`: Boto3 S3-compatible put/get/delete adapter and client factory.
- `backend/src/sketch2life/infrastructure/storage/ensure_local_bucket.py`: local-only retrying private-bucket initializer.
- `backend/src/sketch2life/interfaces/http/routers/storage_examples.py` and `interfaces/http/app.py`: local-only example routes and storage composition.
- `backend/src/sketch2life/interfaces/http/middleware/bounded_image_upload.py`: request-body cap for the new multipart route.
- `docs/setup/LOCAL_DEVELOPMENT.md`: local env, Compose, endpoint and AWS/IAM transition notes.

## Source review and limitation

The official MinIO Community repository now says its Community distribution is source-only, and the GitHub repository is archived. Its release history identifies `RELEASE.2025-10-15T17-29-55Z` as the final tagged security release found during this review. The Compose image is pinned to that tag for the requested local synthetic demo only. This is not a maintained production image recommendation.

Sources:

- <https://github.com/minio/minio>
- <https://github.com/minio/minio/releases/tag/RELEASE.2025-10-15T17-29-55Z>
- <https://min.io/docs/minio/container/index.html>

## Evidence limits and follow-up

- No tests, builds, security validator, Docker pulls, `docker compose config`, or Compose services were run, per the exact Rev30 plan.
- No PostgreSQL metadata, resumable upload session, S3 multipart upload, malware scan, document parsing/OCR, lesson CRUD, Manager review, Parent share, production authorization, AWS account, or real child data is included.
- The local image tag's availability and the S3-compatible operations remain runtime-unverified. A later verification request should use synthetic files and exercise Compose startup plus upload/read/delete before expanding to durable LessonSourceDocument records.
