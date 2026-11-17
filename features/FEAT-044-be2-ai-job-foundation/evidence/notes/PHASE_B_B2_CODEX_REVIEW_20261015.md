# B2 independent review —2026-10-15

- Result: **NEEDS_REVISION**, bounded to B2. Two correction groups below; no new card/plan or
  implementation approval required. B3 remains NOT_STARTED; cards14/WIP1/full-cardDONE0.
- Reviewers: Codex primary, b2_schema_migration_review, b2_studio_test_review.
- Inputs: actual Phase B approval, planrev3 §6/B2, ADR-0018/current component decisions and Claude's
  PHASE_B_B2_SCHEMA_MIGRATION_EVIDENCE.md. Reviewed snapshot = base993a26c + patch
  eb9d75bdca165ffb8ffbdb98db3fa79310930cf619d3c278640ec5a2fefa5bab; eight package files match
  the worktree. This review changes documentation/evidence only, not Claude's implementation.

## B2-R01 — P2: SQL columns reject contract-valid opaque IDs

Location: backend/src/sketch2life/infrastructure/ai_jobs/sql/tables.py:79 and84, repeated at
189/195/236; frozen migration20261015_ai_0001_ai_jobs_schema.py uses the same80-character helper.
Accepted Phase A contracts at contracts/schemas/ai_jobs.py:27,242–244 permit job_type and
purpose_code as OpaqueId up to120 characters. Both fields remain plain strings in domain/service.

An independent probe validated both120-character fields and successfully created a Phase A
fixture job with one attempt, semantic row, receipt and outbox. SQL metadata AND recorded
migration DDL instead use VARCHAR(80) for all five affected columns:

- job.job_type and job.purpose_code;
- semantic_request.job_type and semantic_request.purpose_code;
- cancellation_notice.job_type.

A valid81–120-character value therefore cannot be persisted by the planned SQL adapter. Widen
those five columns consistently in metadata and the initial, not-yet-published migration to
at least120; retain80 for genuine ErrorCode fields. Add a contract-boundary regression and real
PostgreSQL round-trip coverage; do not narrow the already accepted contract to fit this schema.

Proof: ignored evidence/local/b2-codex-review-20261015/peer-schema-contract-lengths.json.
This is actual local contract/fixture/DDL inspection, not a claim of PostgreSQL execution.

## B2-R02 — P2: Studio runner loses failure status and blocks safe retry

Location: evidence/local/b2-studio-package-20261015/run_b2_on_studio.sh:34,45–54 (exit status),
14/19–21 (retry precondition after patch application).

The inner runner uses set -uo pipefail, continues after failed commands, prints pytest statuses
through echo/tee and finally returns the last successful tee's status. An offline control-flow
probe extracted the exact heredoc, replaced venv activation and mocked python with exit1:

```text
b2_exit=1
phase_a_exit=1
runner_exit=0
```

The same flow can continue after required provenance/setup failures. Store pipeline/test statuses
immediately, retain receipt output and exit nonzero when either suite or required setup fails.
Verify both failure cases and the all-success case without Docker or a real server.

After the first patch apply, tracked files become dirty. Any later failure leaves that legitimate
snapshot in place; rerunning the script then stops at its clean-tree precondition. Accept either
a pristine993a26c source or the exact already-applied package verified by hashes/reverse check.
Reject other edits clearly. Never use reset/clean, delete user changes or recreate service volumes
to make rerun work. Source provenance must be revalidated before every test invocation.

Proof: ignored studio-failed-tests-exit-probe.json and studio-package-hash-audit.json in the same
review receipt directory. The failure-status case was reproduced locally with mocks; the retry
case is a direct current-control-flow/package-diff observation, not a remote rerun claim.

Handoff wording correction, part of this package delivery: upload all THREE files (patch,
manifest and run_b2_on_studio.sh) and invoke the script from the upload directory. The original
two-file upload sentence does not supply the script it subsequently invokes.

## Verification and unchanged scope

Independently reproduced on Windows, PYTHONPATH/MYPYPATH pinned to this worktree:

| Check | Actual result |
|---|---|
| B2 suite | 6 passed,8 skipped; PostgreSQL checks NOT_RUN |
| Six Phase A suites | 223 passed,1 Pillow skip in this local venv; prior user-reported live-route PASS remains valid for its original snapshot |
| Ruff on five B2 files, explicit --config backend/pyproject.toml | PASS; format check PASS |
| Mypy on five B2 files, explicit backend config | PASS |
| Architecture and git diff --check | PASS |
| Package fidelity | Eight file hashes match; reverse check and pristine-base forward check PASS |
| DDL/metadata comparison | Seven tables agree on column/type/nullability and32 CHECK expressions, including the same incorrect80-character widths |

Independent Alembic branches and branch-qualified upgrade commands are the approved D2/Q7
choice, not a new defect. No composite-FK requirement, new adapter or broad refactor is added.
The reported pre-existing env.py import-order finding is not a new B2 correction. No dependency
install, PostgreSQL/Docker/cloud operation, backend/test/script edit, stage, commit, push or deploy.

After Claude fixes the two groups, regenerate package/manifest/pinned script and update hashes/
evidence. Run the corrected package on the named Studio; real migration/constraint tests must
pass without PostgreSQL skips. Then record B2_READY_FOR_REVIEW for final closure before B3.
Use plan/CLAUDE_PHASE_B_B2_FIX_PROMPT.md; keep the existing approval and14-card roadmap.
