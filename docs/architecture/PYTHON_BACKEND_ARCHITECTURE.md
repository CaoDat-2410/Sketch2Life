# Python backend architecture guide

## Goal

Keep business rules testable without FastAPI, PostgreSQL, Redis, Lightning AI, or an external network. The backend is a modular monolith first; workers and provider adapters are replaceable edges.

## Directory contract

```text
backend/src/sketch2life/
├─ domain/
│  ├─ session/                 # lifecycle, commands/events, version rules
│  ├─ understanding/           # meaning artifacts and uncertainty rules
│  ├─ recommendation/          # candidate policies and hard constraints
│  └─ experience/              # plan, art, learning asset, handoff invariants
├─ application/
│  ├─ commands/                # state-changing use cases
│  ├─ queries/                 # read use cases
│  ├─ ports/                   # repository, queue, storage, AI interfaces
│  └─ services/                # orchestration across domain modules
├─ contracts/
│  ├─ http/                    # request/response DTOs
│  ├─ events/                  # event envelopes and versioned payloads
│  └─ schemas/                 # JSON Schema/Pydantic boundary definitions
├─ interfaces/
│  ├─ http/routers/            # thin FastAPI route adapters
│  ├─ http/dependencies/       # auth, request context, composition root
│  └─ events/                  # queue/event consumers
└─ infrastructure/
   ├─ persistence/             # SQLAlchemy models and repository implementations
   ├─ object_storage/           # S3/MinIO implementation
   ├─ queue/                    # Redis/RQ implementation
   ├─ ai/                       # Lightning AI client adapters
   ├─ config/                   # environment/config loading
   └─ telemetry/                # redacted logs, traces, metrics
```

## Layer responsibilities

### Domain

Contains entities, value objects, policies, domain services, and state transitions. It may use Python standard-library types, but must not import FastAPI, transport-only Pydantic models, SQLAlchemy, Redis, cloud SDKs, or model SDKs.

### Application

Coordinates use cases and transactions. It depends on domain and abstract ports. It decides when to load an aggregate, validate a command, call a port, and persist an outcome. It does not know whether a port is backed by PostgreSQL, RQ, MinIO, or Lightning AI.

### Contracts

Defines versioned boundary shapes. Pydantic is appropriate here for parsing/serialization, but a contract object is not automatically a domain entity. Every external/model response is rejected or converted before domain use.

### Interfaces

Translates HTTP/queue/CLI input into application commands and translates results into transport responses. Routes stay thin; business branching belongs in application/domain code.

### Infrastructure

Implements ports and owns framework/provider details. Repository code maps ORM rows to domain objects. AI clients map provider results to validated contracts. Queue workers carry `expected_session_version` and cannot directly mutate domain state without an application completion command.

## Request flow

```text
HTTP request
 -> FastAPI router
 -> transport validation
 -> application command/query
 -> domain policy/state transition
 -> port interface
 -> infrastructure adapter
 -> mapped result/contract
 -> response
```

## Async flow

```text
command creates job + expected version
 -> queue adapter
 -> worker/provider adapter
 -> validate output contract
 -> application completion command
 -> discard if session version is stale
 -> persist artifact/job evidence
```

## AI provider boundary

- Application code depends on `application.ports.ai_gateway.AiGateway`, never Lightning/Runpod APIs or credentials.
- The infrastructure adapter is the only provider-aware code. Lightning is fixture/dev; Runpod is production.
- Mobile cannot reach the AI endpoint. It submits authenticated backend commands and reads versioned job state.
- The adapter exchanges artifact references, validates all provider output, redacts sensitive payloads, and returns typed failures.
- Runpod bearer keys are restricted per endpoint and loaded from runtime secret files; no key is present in source/mobile.
- Full controls and the production gate are in `docs/security/PRIVATE_AI_BOUNDARY.md`.

## Managed identity boundary

- Application code depends on `application.ports.identity.IdentityTokenVerifier`, not Firebase Admin APIs.
- The initial infrastructure adapter verifies Firebase ID tokens and maps them to `VerifiedPrincipal`.
- Authentication establishes identity; application/domain policies authorize roles and resource relationships.
- Firebase data/storage products are forbidden. PostgreSQL and the S3-compatible adapter remain authoritative.

## Testing map

- Domain: pure unit tests for allowed/forbidden transitions and hard rules.
- Application: fake ports, command idempotency, stale-version, fallback, and join tests.
- Contracts: schema round-trip and invalid fixture tests.
- Interfaces: route contract tests with dependency overrides.
- Infrastructure: repository/queue/storage adapter tests using disposable fixtures.
- E2E: fixture-only session flow, no real child data.
