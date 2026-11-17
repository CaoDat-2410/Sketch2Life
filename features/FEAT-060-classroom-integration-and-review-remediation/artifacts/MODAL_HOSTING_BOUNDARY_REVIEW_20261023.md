# Modal and container placement review

**Status:** source/configuration review; no deployment, network call, GPU provision, or endpoint test.  
**Decision source:** ADR-0019 selects Modal as target AI hosting and places provider credentials behind the backend; implementation profile is TBD.

## Current repository facts

- `backend/Dockerfile` builds the FastAPI backend and starts `uvicorn sketch2life.main:app` on port 8000.
- The approved classroom entrypoint is `sketch2life.classroom_main:app`, whose factory mounts health and BE1 runtime routes only. The compatibility entrypoint remains for demos.
- BE1 runtime routes require Firebase-verified adult identity, device grants and PostgreSQL. Artifact storage is also provider-dependent; current artifact routes fail closed outside `local`/`test` until production storage is selected.
- Current settings allow `disabled`, `lightning_dev`, and `runpod`; there is no Modal AI provider adapter. Production validation currently expects Runpod settings if AI is enabled.
- FEAT-057 evidence is an offline Modal CPU test. It proves neither a live Function, GPU inference, app endpoint, production network path, nor latency/cost.

## Direct answer: must the whole backend container move to Modal?

**No.** The backend and AI worker have different responsibilities. The stable product boundary should remain:

```text
Child / Teacher / Admin
        │ Firebase adult auth or BE1 device grant
        ▼
Durable classroom API (FastAPI / BE1) ─── PostgreSQL + approved artifact storage
        │ typed, bounded AI job request/result
        ▼
Modal Function (model inference only; no client-held provider secret)
```

Modal can host a FastAPI ASGI application and can run GPU-backed functions, so the whole container is technically deployable there. It is a hosting option, not a requirement for invoking Modal AI. Moving BE1 to Modal would add a separate durable-app hosting decision: managed PostgreSQL connectivity, durable artifact object store, identity validation, regional/network path, scale/cold start, worker/queue recovery, endpoint auth, retention, and operational rollback all need to be designed and verified. Modal ephemeral local disk must not be used as BE1 relational/database persistence.

## Recommendation for this integration

1. Keep the classroom API as the durable system of record, with PostgreSQL and separately selected durable artifact storage.
2. Add a backend-owned Modal adapter only after the BE2 job/review contract is approved and an actual provider profile is supplied.
3. Send a bounded, consent-authorized, minimized payload; return a typed job/result reference. Persist request state, review outcome, and provider metadata in backend-controlled storage.
4. Do not send Firebase ID tokens, device keys, or Modal secrets to the Modal Function unless its approved contract requires a narrowly scoped service token; never send provider credentials to mobile or browser clients.
5. Until endpoint, model/license, GPU, region, scaling, timeout/retry, secrets, spend cap, and retention are configured, report `NOT_TESTED_CONFIGURATION_UNAVAILABLE`.

## Modal behavior to budget for

Modal web functions can start from zero and scale with demand. A cold request may incur container start/model load latency; keep latency targets separate for warm and cold requests and measure both only after a real profile is set. Modal functions support custom images, GPU configuration and injected secrets. Modal's documented Function input/output retention and logs are privacy/operations factors that must be reconciled with child-data purpose and retention before any product payload is sent. A persistent Modal Volume may preserve files, but it does not replace an approved PostgreSQL and object-storage design for BE1.

## Primary Modal documentation consulted on 2026-10-23

- [Web endpoints and ASGI apps](https://modal.com/docs/guide/webhooks)
- [Functions, images, GPU and scaling](https://modal.com/docs/guide/functions)
- [Secrets](https://modal.com/docs/guide/secrets)
- [Volumes](https://modal.com/docs/guide/volumes)
- [Security and data handling](https://modal.com/docs/guide/security)

## Gate to live test

No live test is possible from this checkout: there is no registered deployed product endpoint/profile or Modal provider adapter, and no endpoint details were supplied. Do not infer one from the offline CPU test. When the owner sets it up, record non-secret endpoint identity, model/version/license, GPU/region, warm/cold policy, timeout, spend limit, request correlation ID and synthetic payload. Then run one bounded synthetic call through the backend's provider adapter and capture the typed result and elapsed time without retaining child data or printing secrets.
