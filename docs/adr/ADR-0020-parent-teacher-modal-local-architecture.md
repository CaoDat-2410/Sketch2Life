# ADR-0020: Parent and Teacher flows with local Docker and Modal AI

- Date: 2026-10-26
- Status: ACCEPTED for FEAT-062 under approved Plan revision 2.
- Authority: Project owner's direct request to restore the flows and follow-up decisions selecting Parent Android + Teacher web, no product file export, Docker local, and Modal for AI hosting.
- Scope: FEAT-062 only. This decision changes the product path in ADR-0019 and the provider/deployment assumptions in ADR-0003, ADR-0005, and `docs/security/PRIVATE_AI_BOUNDARY.md` only for the Parent/Teacher flows. Other approved features retain their historical contracts until separately migrated.

## Context

The repository contains a legacy Parent flow in `apps/ui-mobile`, an active Android foundation in `apps/mobile`, and a separate Teacher console in `apps/teacher-ui`. ADR-0019 described collaborative classroom learning as the current product target and kept Parent/Guide flows in demo entrypoints. The owner now requests two role-specific primary flows and explicitly says not to connect the FEAT-060 collaborative flow yet.

The application backend has no production host selected. Local Docker Compose already provides PostgreSQL, Redis, and MinIO. The owner selects Modal for AI hosting and Docker for local application development. The app should preserve the child's paper drawing, personalize generated results, restore animated original-art playback and story video, and support teacher lesson preparation and one-child-at-a-time generation.

## Decision

### Product flows

- Parent uses the Android client. The active implementation target is `apps/mobile`; `apps/ui-mobile` is the behavior reference. Parent selects a child, captures a paper drawing, reviews/corrects subject understanding, then chooses an outdoor activity and approves the personalized story.
- Teacher uses the separate `apps/teacher-ui` web console. Teacher manages a class and multiple saved child profiles, imports a PDF/PPTX/DOCX lesson, reviews extracted text while retaining the original file, prepares the scenario, and selects/approves the outdoor activity before starting an individual child run.
- Each generation run and all associated inputs/results/artifacts are bound to exactly one authorized child profile. A teacher repeats the run to process another child.
- Both roles can view animated original artwork and story video in the product. Original-art animation remains a deterministic PixiJS/GSAP renderer flow with explicit provenance. AI story-video generation uses the backend-owned Modal adapter.
- Product file export/download is excluded. The original lesson and drawing are retained as source artifacts; generated media is a separate derivative.
- Neither flow requires a shared tablet drawing canvas. Input is a camera photo of paper artwork.
- FEAT-060 group sessions, QR/numeric admission, shared strokes, and nine-stage collaborative workflow are not connected.

### Selected stack

| Area | Selection |
|---|---|
| Parent Android | React Native 0.87 + TypeScript (`apps/mobile`); reuse the shared PixiJS/GSAP art renderer |
| Teacher web | React 19 + Vite 8 (`apps/teacher-ui`) |
| Backend | Python 3.12 modular monolith, FastAPI, Pydantic, SQLAlchemy 2, Alembic |
| Database | PostgreSQL 17, Docker Compose locally |
| Object storage | S3-compatible MinIO locally, accessed only through backend ports |
| Queue and rate limits | Redis 8 + RQ 2; Redis-backed distributed rate limiting and job admission |
| AI | Modal inference over an authenticated backend-owned provider port/adapter; no provider calls from clients |
| Local containers | Docker Compose runs API, worker, PostgreSQL, Redis, MinIO, OpenTelemetry Collector, Prometheus, and Grafana |
| Monitoring | `structlog` redacted JSON logs; OpenTelemetry traces/metrics; Prometheus scrape/storage; Grafana local dashboards and alert rules |
| Authentication | Firebase Authentication only; backend checks roles, class assignment, and parent-child ownership |

Mobile and Teacher clients use local device/browser dev runtimes for hot reload and call the Docker-hosted API. Docker Compose is local development hosting; no public/production app host or deployment is selected by this ADR.

### AI boundary and job lifecycle

```text
Parent Android / Teacher web
              |
              | authenticated versioned HTTP contracts
              v
FastAPI application (authorization, policy, limits, provenance)
     | PostgreSQL   | Redis/RQ    | MinIO
     |              |              |
     +--------------+-- worker ----+---- Modal AI endpoint
                                      (backend credential only)
```

Application use cases depend on provider-neutral AI ports. The Modal adapter handles network requests, authentication, timeouts, retries, typed errors, and result validation. Worker results return through an application completion command and must match the expected child, job, and source-artifact versions. A deterministic fake adapter is the default for local flow development. Live Modal calls require a configured endpoint/profile, synthetic input, and a separate approved spend limit.

Lesson sources (PDF/PPTX/DOCX) are size/type checked, preserved unchanged in MinIO, and parsed with bounded `pypdf`, `python-pptx`, and `python-docx` extraction for text only. Teacher reviews the extracted text before the lesson is used in a run. Scanned-page OCR and export/download are excluded.

Original artwork animation and AI story-video are distinct derivatives. Every derivative stores source artifact ID/hash, child profile ID, model/config version where applicable, renderer version where applicable, adult approval, and timestamps. Raw media, extracted lesson text, prompts, signed URLs, and identity data are excluded from logs and metrics.

### Monitoring and rate limits

- API/worker emit request IDs, structured redacted logs, OpenTelemetry traces, and low-cardinality metrics.
- Local dashboards cover API traffic/error/latency, queue depth/age, worker failures, Modal calls/latency, and rate-limit rejections.
- Redis enforces sliding-window limits by authenticated account and source IP plus stricter AI submission and concurrency budgets. Limits are server-side and configurable by operation; excess requests receive HTTP 429 and `Retry-After`.
- Initial local synthetic defaults: 60 general authenticated API requests/minute/account, 20 unauthenticated requests/minute/source IP, 3 AI submissions/minute/account, and at most one active generation job per child. These are development safeguards, not production capacity claims; record measurements and revise before any public deployment.
- Alerts/rules flag sustained API failures/latency, stale/deep queues, provider failures, unusual request volume, and security events without labeling child content.

## Consequences

- FEAT-062 owns the role-specific workflow contracts, activity planning state, lesson-import boundary, profile binding, and local observability/rate-limit configuration.
- Domain rules stay independent of FastAPI, PostgreSQL/Redis/MinIO, Modal, and UI frameworks. Cross-boundary calls use versioned contracts.
- The implementation ports user-facing behavior from `apps/ui-mobile` into the active `apps/mobile` client; legacy demo API fallbacks are not product success paths.
- Local monitoring is observable and reproducible, but does not establish production alerts, data retention approval, backup/recovery, public host, or capacity.
- `apps/ui-mobile` and existing ADRs/evidence remain unchanged as historical material. No FEAT-060 integration is implied.

## Open gates

- Modal endpoint/profile, authentication method, model/version/license, GPU, timeout/retry, scaling, endpoint secret, provider spend cap, and measured latency/quality.
- Consent/purpose and retention/deletion rules for real child profiles, source art, lesson uploads, and generated media.
- Production application hosting, production object storage, backup/recovery, and incident-response policy.
- Review of the new FEAT-062 HTTP/data contracts before connecting any separately owned BE2 card or live provider.
