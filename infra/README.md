# Infrastructure skeleton

Local infrastructure is defined in the root `compose.yaml`: PostgreSQL, Redis, and MinIO. Deployment templates remain provider-neutral until an approved cloud feature selects AWS or another provider.

Never place Lightning AI tokens, storage keys, or production credentials in this repository.
