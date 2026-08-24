# Base project structure

This is the first codebase skeleton. It deliberately contains boundaries and documentation, not product behavior.

```text
apps/
├─ mobile/                         # React Native presentation + device adapters
│  ├─ src/
│  │  ├─ app/                      # navigation, providers, startup composition
│  │  ├─ features/                 # capture, Gate A/B, experience, bridge, feedback
│  │  ├─ bridge/pixi/              # narrow WebView/JS bridge boundary
│  │  ├─ shared/                   # UI primitives and client utilities
│  │  └─ infrastructure/           # HTTP, secure storage, device APIs
│  └─ assets/                      # generated -> approved -> applied visual gate
└─ api/                            # thin HTTP entrypoint; no domain logic

backend/
└─ src/sketch2life/
   ├─ domain/                      # entities, value objects, policies, state machines
   ├─ application/                 # commands, queries, use cases, ports
   ├─ contracts/                   # boundary schemas and serializers
   ├─ interfaces/                  # HTTP/CLI/event inbound adapters
   └─ infrastructure/              # DB, object storage, queue, AI, telemetry adapters

services/                          # replaceable provider/worker modules
├─ understanding/
├─ recommendation/
├─ experience/
├─ media-worker/
└─ gpu-orchestrator/

packages/contracts/                 # JSON Schema + fixture manifests
data/fixtures/                      # synthetic inputs only
tests/                              # unit, contract, integration, e2e, eval
infra/                              # Docker, migrations, deployment templates
features/                           # plan, approval, evidence, and feature-local context
```

## Import direction

```text
mobile/api interfaces -> application use cases -> domain
infrastructure adapters ----------------------^ (implements ports)
contracts sit at boundaries and are versioned
```

## Base scaffold rule

The scaffold may be created now because it is the explicitly requested base-project setup. Product behavior, model calls, real schemas, and UI visuals remain separate approved feature work.
