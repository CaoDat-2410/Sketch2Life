# ADR-0001: Modular monolith first

- Status: PROPOSED
- Decision: Start with explicit modules and workers in one repository. Split deployment boundaries only after measured scaling, ownership, or reliability evidence.
- Reason: The handbook explicitly prefers modular monolith + workers for MVP and avoids premature microservices.
- Consequence: Module boundaries and contracts must be real from day one even if deployment is initially simple.
