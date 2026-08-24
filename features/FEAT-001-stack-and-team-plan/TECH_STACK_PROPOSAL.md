# Proposed implementation stack

| Area | Proposed choice | Why | Validation before lock |
|---|---|---|---|
| Mobile | React Native + TypeScript | One mobile codebase, broad team familiarity, suitable for capture/playback flows | Device matrix, audio/image capture, bridge ergonomics |
| Original-art renderer | PixiJS + GSAP inside a controlled WebView/bridge | Preserves handbook renderer contract while staying mobile-only | FPS, startup latency, memory, asset/provenance bridge tests |
| API/orchestration | Python 3.12 + FastAPI + Pydantic | Matches handbook contracts and AI/data workflow | Contract tests, lifecycle/state-machine tests |
| Persistence | PostgreSQL + JSONB + SQLAlchemy/Alembic | Durable session, domain, audit, versioning model | Migration/replay tests and fixture isolation |
| Object storage | S3-compatible storage, MinIO locally | Original/derived/generated asset lineage | Signed-reference and deletion workflow tests |
| Async/cache | Redis + RQ/simple workers | Enough for MVP fan-out and cache-first resolution | Retry, stale-version, queue, and fallback tests |
| AI hosting | Lightning AI for fixture development; Runpod Serverless for production | Fits current low-credit development access while preserving a production adapter target | VRAM, latency, queue, cost, region, security, and failure benchmark on fixtures |
| AI models | Whisper large-v3-turbo, Qwen3-VL-8B Instruct, Wan2.2-TI2V-5B | Matches handbook baseline | Fixture accuracy, schema validity, safety, media integrity |
| Packaging | Docker; backend provider-agnostic, AWS-compatible later | Reproducible local and cloud deployment | Build, migration, smoke, and deployment checks |
| Observability | OpenTelemetry-compatible logs/metrics; Prometheus/Grafana later | Trace session/job/version without raw child data | Redaction and job metrics tests |

## Explicitly deferred

- Real child data.
- Graph database and mandatory vector search.
- Generative replacement of child artwork.
- Independent microservices before measured need.
- Final backend cloud/region and managed S3 provider selection.
- Vietnamese TTS until fixture benchmarks show it is needed for MVP.
