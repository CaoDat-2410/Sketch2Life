# Plan revision 30 — local Docker, MinIO, and lesson-source storage example

- Feature: FEAT-063 — whole-repository architecture redesign.
- Plan status at authoring: AWAITING_APPROVAL. This immutable revision becomes actionable only when `approvals/TASK_APPROVAL.md` records the owner's approval for its exact SHA-256.
- Predecessor: Rev29 remains the approved API-contract proposal for review and is not replaced by this infrastructure example.
- Owner request: set up Docker for the backend, use MinIO locally with an environment setup that can later point to AWS S3, and make one example first.

## Goal

Provide a local Docker Compose stack that runs the existing FastAPI backend beside private MinIO storage, with an environment-driven S3-compatible adapter and one small upload/read/delete example for lesson source documents. This is a storage and runtime vertical slice; it does not implement the complete 28-operation Lesson Library contract.

## Scope

1. Extend the existing `compose.yaml` with the backend API and a local-only MinIO bucket initialization service. Preserve the existing PostgreSQL, Redis, and MinIO data volumes. Add startup ordering/health behavior and bind local MinIO console/API ports to loopback.
2. Pin the local MinIO image to the last upstream security release available before the upstream repository became archived. Keep this local-only and call out its maintenance limitation; do not treat it as a production recommendation.
3. Add placeholder-only storage settings to `backend/.env.example` and the root `.env.example`. Do not read, create, or overwrite `.env`, `backend/.env`, or any secret file. The user will supply local values. The backend receives storage credentials; browser/mobile clients never do.
4. Add a provider-neutral application object-storage port and a Boto3 S3-compatible infrastructure adapter. MinIO uses an endpoint override and path-style addressing. AWS S3 is configured by omitting the endpoint and using the normal AWS credential chain/IAM role; no AWS keys or live AWS access are added.
5. Add a local-development-only demonstration API, disabled by default outside the local Compose profile:
   - `POST /api/dev/v1/storage-examples/lesson-source-documents` — upload one bounded file and return a generated opaque object ID, media type, byte length, and SHA-256.
   - `GET /api/dev/v1/storage-examples/lesson-source-documents/{object_id}` — stream the private object through the backend.
   - `DELETE /api/dev/v1/storage-examples/lesson-source-documents/{object_id}` — remove the example object.
6. Store only bytes and minimal object metadata for this demonstration. Do not add lesson/database entities or claim the sample endpoint is the Rev29 product API. The future `LessonSourceDocument` use case can reuse the same port.
7. Document copy/edit environment steps, Docker startup/shutdown, MinIO Console access, and example requests in the backend/root developer documentation.

## Acceptance criteria

- AC1: `compose.yaml` defines an API service built from `backend/Dockerfile`, MinIO with persistent storage, and a bucket bootstrap that completes before the API example is used.
- AC2: MinIO's API and console are reachable from the developer machine only through loopback-published ports; its bucket is private and no client receives S3 credentials or presigned links.
- AC3: Compose and the API read configuration from named `SKETCH2LIFE_*` variables; example files contain placeholders only. AWS mode requires no code change and supports IAM/default credentials when the endpoint override and explicit keys are absent.
- AC4: The storage port is in the application boundary; Boto3, endpoint configuration, and MinIO details remain in infrastructure/configuration.
- AC5: The three example operations use generated object keys, enforce a configured upload size cap, return safe metadata, stream reads via the API, and are unavailable when the environment is not `local` or the explicit example flag is false.
- AC6: No AI/parser/OCR, authentication bypass on a product route, relational schema/migration, full Lesson CRUD, publication/share logic, deployment, AWS account access, or real child data is introduced.
- AC7: README instructions distinguish this synthetic local storage example from the formal Rev29 Lesson Library API and explain the MinIO upstream maintenance limitation.

## Implementation sequence

1. Record the exact plan hash and this owner's direct authorization in `approvals/TASK_APPROVAL.md`.
2. Implement the application port, Boto3 adapter, configuration, and guarded example router.
3. Add MinIO bucket bootstrap and compose service wiring; preserve existing Compose services and data volumes.
4. Update placeholder environment templates and local setup instructions.
5. Add feature evidence/context/decision/status/source-register entries. Automated tests and running Docker services are not included in this pass; record them as unverified follow-up work.

## Risks and controls

- MinIO Community upstream repository is archived and its community distribution changed to source-only. Pin the last upstream security release for this local synthetic demo, document the limitation, and keep the application port S3-compatible so MinIO can be replaced without changing use-case code.
- A compose-local example without relational metadata is not resumable upload and does not prove production authorization, antivirus scanning, retention, or lesson ownership. Label it as a developer example and do not mount it outside local mode.
- Large uploads can exhaust memory or block the event loop. Enforce a strict byte limit while reading bounded chunks and move blocking Boto3 calls off the async event loop.
- Local credentials and bucket policy must remain private. Do not commit real credentials, use public ACLs, expose the MinIO console beyond loopback, or return storage URLs.

## Verification plan and limits

- Review the Compose and environment wiring statically; inspect the route guard and confirm all object operations use the injected port.
- Do not run tests, builds, repository security validation, Docker pulls, or Docker Compose services in this task. No commit or push is included.
- Record any unavailable runtime proof explicitly. A later owner-requested verification pass can run the Compose stack with synthetic data and exercise upload/read/delete before extending to durable lesson upload sessions.

## References

- `docs/architecture/PYTHON_BACKEND_ARCHITECTURE.md`
- `docs/architecture/DEPENDENCY_RULES.md`
- `docs/adr/ADR-0020-parent-teacher-modal-local-architecture.md`
- `docs/adr/ADR-0021-single-child-parent-teacher-story-architecture.md` (resumable upload/multipart behavior remains a later POC; this plan does not claim that behavior)
- MinIO upstream repository status: <https://github.com/minio/minio>
- MinIO last upstream security release: <https://github.com/minio/minio/releases/tag/RELEASE.2025-10-15T17-29-55Z>
