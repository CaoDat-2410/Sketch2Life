# AI provider adapter boundary

Implementations in this folder translate provider-neutral application ports. FEAT-017 adds a backend-only Lightning development transport and P2 ASR/VLM adapters for synthetic fixtures. Lightning is development-only; Runpod Serverless remains the production target and requires a separate approved feature.

Required adapter behavior:

- resolve input artifact IDs through an authorized fixture/object-storage port;
- load provider credentials only from runtime secret references;
- use verified TLS outside local development;
- attach contract/session versions and request IDs;
- enforce input/output limits, timeout and one bounded retry;
- validate provider output before creating application artifacts;
- redact media, prompts, credentials, and model output from logs;
- return typed failures and never mutate session state directly.

Do not pass permanent S3 credentials to a provider job. Resolve artifacts through short-lived references or a backend-controlled transfer. Mobile never imports this package or receives provider endpoints/credentials.
