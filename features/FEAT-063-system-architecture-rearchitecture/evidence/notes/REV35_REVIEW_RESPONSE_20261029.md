# Rev35 response to Rev34 independent review

- Input: owner supplied review of Rev34, NEEDS_REVISION, 0 P1, 5 P2 and 5 P3. Reviewed Rev34 SHA-256 `F2EBA2C2570DC98663120A724565038E18DE434B622A48D76B5FE668889FE780`.
- Rev35 SHA-256: `D181BF43BDDABE3262AEFF990EC54F4CF69EAD92E5FEB774C634C80FD952F4BC`.
- Rev35 S1 candidate inventory SHA-256: `0C64EECCB7B0720223CD60939DDD73B7D3A09BB6C2DC0023309B8AACFB72051C`; candidate entries still need individual disposition and pinning at approval.
- Status: documentation draft; no implementation approval. Rev33/Rev34 and previous approvals are preserved.

| Finding | Response |
| --- | --- |
| P2-1 | Replaced single-head assumption with source graph: nine Alembic heads plus BE1 effective head. S2/S3 branch parents are provisional and graph/migration manifest must be rechecked. |
| P2-2 | Kept newly created legacy-family jobs compatible. Target kinds are not job types; require a reviewed server-controlled persisted family/version mapping, full typed tuple and anti-downgrade tests. |
| P2-3 | Existing NULL or assigned identities fail closed; classification cannot override active conflicts. New identity onboarding, historical assignments and transaction race require policy/tests. |
| P2-4 | Require actual CI collection and explicit skip reporting. Disposable PostgreSQL rehearsal is an S2/S3 acceptance gate, subject to distinct OD-7 approval; without it acceptance is blocked. |
| P2-5 | Document FEAT-064 current-flow pilot, shared files and schema/migration ownership. Person 2 coordinates FEAT-064; owner cosigns and file allocations are not inferred. Neither plan approves the other. |
| P3-1 | Explicit server-controlled origin, legacy fallback, guard inventory and eligibility requirements; no client self-assertion. |
| P3-2 | Explicitly defer voice/transcript, context review, quota/billing/notification, lifecycle, organization/roster and sketch capabilities; Parent deletion awaits a lifecycle contract. |
| P3-3 | Explicit proposed Parent mounting and `/v1` boundary; exact Parent composition remains a decision; update route/method and error tests. |
| P3-4 | S1 approval requires final inventory/disposition hash and plan hash. |
| P3-5 | Clarified 55 BE1 declarations including its health plus root health = 56 classroom-profile declarations; avoid counting health twice. |

Read-only checks corroborated CI's explicit five backend files and PostgreSQL integration skip without its test DB environment, and Alembic's nine heads plus one effective head. Independent follow-up reviewers checked migration/job and identity corrections; their final cautions on discriminator persistence, race safety, backfill scope and six-hour deadline separation were incorporated. This is not a complete independent re-review verdict for final Rev35.

`python tools/validate_harness.py` returned `HARNESS_VALID`; `git diff --check` returned exit 0. No product tests, service/DB/provider execution, approval edits, commit or push occurred.
