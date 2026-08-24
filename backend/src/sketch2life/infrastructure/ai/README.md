# AI provider adapter boundary

Implementations in this folder translate the provider-neutral `AiGateway` port. Lightning is allowed only for fixture development; Runpod Serverless is the approved production target. Both require separately approved integration features.

Required adapter behavior:

- resolve input artifact IDs through an authorized object-storage port;
- load provider credentials only from runtime secret references;
- use a restricted, endpoint-scoped key for Runpod and rotate/revoke it;
- connect only to the configured provider endpoint over verified TLS;
- attach request/session versions and idempotency keys;
- enforce connect/request limits, retry budgets, and a circuit breaker;
- validate provider output before creating application artifacts;
- redact media, prompts, credentials, and model output from logs;
- return typed failures and never mutate session state directly.

Do not pass permanent S3 credentials to a provider job. Resolve artifacts through short-lived references or a backend-controlled transfer.

No live HTTP client, provider SDK, endpoint, or credential is included in this foundation.
