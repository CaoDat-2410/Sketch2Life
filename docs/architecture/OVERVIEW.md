# Clean architecture overview

The repository uses a modular monolith boundary first. Modules can become independently deployed services later only when evidence justifies that cost.

```text
apps / interface adapters
        |
application use cases + ports
        |
domain entities, policies, state machines
        |
contracts / versioned schemas
        ^
infrastructure adapters: DB, object storage, queue, model providers, telemetry
```

## Planned repository boundaries

```text
apps/
  mobile/           React Native mobile app: child, parent, and guide modes
  api/              thin inbound HTTP/command adapter
backend/
  src/sketch2life/  modular monolith: domain, application, contracts, adapters
services/
  understanding/    ASR/VLM/fusion adapters and use cases
  recommendation/   retrieval, deterministic constraints, selector boundary
  experience/       planner, three-phase compiler, validators
  media-worker/     media processing and cache operations
  gpu-orchestrator/ AI-plane scheduling boundary
packages/
  contracts/        language-neutral versioned schemas and fixtures
  domain-session/   domain boundary reference and shared contracts
  domain-montessori/domain boundary reference and catalog fixtures
  domain-experience/art, learning asset, handoff rules
  application/      use-case and port boundary reference
  infrastructure/   adapter boundary reference
  telemetry/        redacted logs, traces, metrics conventions
data/                reviewed catalog, assets, evaluation manifests
infra/               containers, migrations, deployment
tests/               unit, contract, integration, e2e, eval
```

The mobile app contains presentation and device adapters only. Business truth stays in the backend domain/application layers and crosses the mobile boundary through versioned contracts.

## Dependency rules

- Domain packages do not import web frameworks, ORM models, queues, SDK clients, or UI code.
- Application code depends on domain and port interfaces, not concrete infrastructure.
- Adapters translate external formats into contracts and domain commands at the boundary.
- Database models and provider responses never cross into the domain unvalidated.
- Features communicate through versioned contracts and explicit events/commands.
- Every derived or generated artifact references its source artifact IDs, version, configuration, and reason.
