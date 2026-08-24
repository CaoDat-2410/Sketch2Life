# Backend modular monolith

The backend owns session truth, domain policies, application use cases, contracts, and infrastructure adapters. Keep provider and framework details at the outer boundary.

The backend is a Python package organized as a modular monolith. It is not a collection of route handlers that directly call the database or model providers.

See:

- [Python backend architecture](../docs/architecture/PYTHON_BACKEND_ARCHITECTURE.md)
- [Backend layer map](src/sketch2life/README.md)
- [Contract and integration rules](../docs/architecture/CONTRACTS_AND_INTEGRATION.md)
