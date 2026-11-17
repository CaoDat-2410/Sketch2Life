# Sketch2Life implementation workspace

This repository starts with a delivery harness before product code. The harness protects context, architecture, evidence, visual approvals, and implementation approvals while the project scope and final technology choices are being confirmed.

## Start here

- Read the [complete current-system baseline](docs/SYSTEM_BASELINE.md) for the product boundary, frozen stack, architecture, security model, delivery workflow, team split, and implementation status.
- Read [project context](docs/context/PROJECT_CONTEXT.md).
- Read the [source register](docs/context/SOURCE_REGISTER.md) to distinguish reference material from user-authorized instructions.
- Follow the [workflow](docs/governance/WORKFLOW.md).
- Read the [Python backend guide](docs/architecture/PYTHON_BACKEND_ARCHITECTURE.md) and [React Native guide](docs/architecture/REACT_NATIVE_ARCHITECTURE.md).
- Use the [context management guide](docs/context/CONTEXT_MANAGEMENT.md) and [evidence management guide](docs/governance/EVIDENCE_MANAGEMENT.md).
- Use the [feature template rules](features/README.md) for every feature.
- Follow the [repository security policy](SECURITY.md); never commit environment files, seed accounts, service credentials, or signing keys.
- Run `python tools/validate_harness.py` before review or handoff.

## Current state

- Harness: active and enforced per feature.
- Product implementation: backend/mobile foundations and scoped workflows exist. FEAT-063 Rev31 adds the persistent no-AI Lesson Library API; database migration and runtime verification remain to be performed locally.
- Tech stack: Python/FastAPI backend and Android-only React Native 0.87 foundation remain the current product foundation. Existing AI adapters are not replaced by this backend slice; the Modal-hosted AI pipeline remains a separate proposal pending its own approval and prototype.
- Frontend assets: no generated asset is approved or applied yet.

## Foundation commands

- `python tools/validate_harness.py`
- `python tools/validate_skeleton.py`
- `python tools/validate_architecture.py`
- `python tools/validate_team_allocation.py`
- `python tools/validate_repository_security.py`
- `docker compose up --build -d`

See [local development setup](docs/setup/LOCAL_DEVELOPMENT.md) and the [project skeleton map](docs/setup/PROJECT_SKELETON.md).

For the complete backend route inventory, including mounted, conditional and candidate APIs, see [FEAT-063 API inventory Rev31](features/FEAT-063-system-architecture-rearchitecture/artifacts/API_INVENTORY_FEAT063_REV31_20261028.md).
