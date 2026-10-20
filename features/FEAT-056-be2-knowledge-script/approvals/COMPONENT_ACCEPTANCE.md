# BE2-07 component acceptance

- Owner: user / Person 2, through a direct instruction in the Codex conversation on
  2026-10-20. The instruction is quoted verbatim below.
- Checkpoint: **KNOWLEDGE_SCRIPT_COMPONENT_OFFLINE — ACCEPTED**. No other scope is accepted.
- The acceptance is conditional on a PASS final review. That condition was met:
  - Review: `../evidence/cloud-review/final-review-20261020/REVIEW.md`, verdict **PASS**,
    SHA256 `de0321b4a0ece4e5a04bf5d5976228f6f6e02d0cf1ce4fe8665a908f142db5f5`.
  - Reviewed source: `feature/be2-07-knowledge-script` at
    `763a17cf39bf7343044d69d887597905d55644fd`, from base
    `23acf9e83e181305edfeb345be9a8e7eb9dbef88`.
  - Report commit: `0d07386eb7b6a17755eaa5ed03a127466194debf` (documentation only).
- Frozen plan: `../plan/PLAN_REV1_APPROVED.md`, SHA256
  `6de3ed6de3ef6008128d064ae28d3bf2b5fe78f91686afaa28eb63b4231aab36`. OD01–08 were chosen as
  recommended. `TASK_APPROVAL.md` is unchanged (`0010271d…2078`).
- Fresh checks on the reviewed snapshot:
  - 360 BE2-07 tests pass with 0 skips.
  - All 42 acceptance IDs map to fresh passing nodes: 506 references, 286 unique nodes.
  - 26 of 27 mutants are killed; the one survivor is equivalent.
  - Ruff, strict mypy and the harness, architecture, skeleton and repository-security
    validators pass.
  - `git diff --check` is clean except for the frozen approval EOF exception.
- Earlier findings:
  - P2-1..3 and P3-1/2/3/5/6, N1, N2 and R1 are fixed, each with a regression.
  - P3-4 follows the frozen R01 rule (recall requires a new bundle).
  - P3-6 keeps the frozen approval EOF line, as documented.
- Accepted limits:
  - The approved 56-module batch is NOT_RUN on cloud because dependencies are missing. Its
    latest execution is Codex's independent run on `f6db0d5`, whose backend, tests and
    config are byte-identical to the reviewed snapshot: 1,682 passed, 3 Pillow skips, 0
    failures.
  - The three Pillow live-app checks and the excluded Vision V2 server module are NOT_RUN.
  - External and foreign baselines are NOT_VERIFIABLE_ON_CLOUD.
  - Imagined-to-fact matching is a conservative literal heuristic, not semantic verification.
- The card remains **IN_PROGRESS / NOT_DONE**. Still open: Lightning and runtime, real
  provider/BE1/P4 adapters, HTTP/DB/durable storage, production policy, actual08
  adoption/lease/fence and cross-card integration. This acceptance does not claim runtime,
  production or actual08 adoption.
- Integration: the same instruction authorizes moving the reviewed BE2-07 snapshot onto
  `feature/be2-01-07` (normal fast-forward or merge, normal push) once the review passes. The
  integration result is recorded separately in status. It authorizes no other branch, no dev
  or main merge, no BE2-08–14 work and no deployment.

## Verbatim owner instruction

> Viết prompt cho claude review lần cuối đi nếu ok thì chấp nhận đẩy lên nhánh gộp
