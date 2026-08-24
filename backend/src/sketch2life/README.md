# Backend layer map

```text
interfaces/      FastAPI routers, CLI, event consumers
      |
application/     commands, queries, use cases, ports
      |
domain/          entities, value objects, policies, state machines
      ^
infrastructure/  DB, storage, queue, AI, telemetry adapters
contracts/       versioned boundary schemas at the edges
```

Allowed direction: interfaces/infrastructure -> application -> domain. Contracts are used only at explicit boundaries and are validated before entering domain logic.
