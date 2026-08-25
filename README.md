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
- Product implementation: foundation only; FEAT-002 Montessori domain fixtures are implemented and awaiting provisional owner content review.
- Tech stack: Python/FastAPI backend and Android-only React Native 0.87 foundation accepted; Firebase Authentication-only identity and Lightning-dev/Runpod-production AI strategy are frozen but live integrations remain gated.
- Frontend assets: no generated asset is approved or applied yet.

## Foundation commands

- `python tools/validate_harness.py`
- `python tools/validate_skeleton.py`
- `python tools/validate_architecture.py`
- `python tools/validate_team_allocation.py`
- `python tools/validate_repository_security.py`
- `python tools/validate_montessori_domain.py`
- `docker compose up -d`

See [local development setup](docs/setup/LOCAL_DEVELOPMENT.md) and the [project skeleton map](docs/setup/PROJECT_SKELETON.md).
