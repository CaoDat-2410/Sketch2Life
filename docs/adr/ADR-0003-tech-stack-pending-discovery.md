# ADR-0003: Mobile-first technology stack proposal

- Status: ACCEPTED WITH ADR-0004 CONSTRAINTS
- Mobile: React Native + TypeScript, with a controlled WebView/bridge boundary for the PixiJS + GSAP original-art renderer.
- Backend: Python 3.12 + FastAPI + Pydantic, PostgreSQL, SQLAlchemy/Alembic, S3-compatible object storage, Redis/RQ, and Docker.
- AI plane: provider-neutral `AiGateway`; Lightning AI for fixture development and Runpod Serverless for production per ADR-0005. Exact model profiles remain benchmark-gated.
- Development data: fixture/synthetic data only.
- Deployment posture: backend and data plane remain provider-agnostic and can later target AWS managed services; AI remains isolated on Lightning AI.
- Decision rule: Android/native/security details are frozen by ADR-0004. Model profiles and managed cloud services still require benchmark/provisioning evidence.
- Consequence: Foundation scaffolding is allowed; product behavior and live provider integration remain separately feature-gated.
