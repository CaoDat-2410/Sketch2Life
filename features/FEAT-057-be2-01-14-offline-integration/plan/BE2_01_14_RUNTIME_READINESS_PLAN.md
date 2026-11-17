# BE2-01–14 runtime-readiness and command-preparation plan

- Status: APPROVED
- Plan revision: 1
- Work type: cross-card analysis and documentation only
- Updated: 2026-10-20 (Asia/Saigon)

## Goal

Analyze the current BE2-01–14 candidate and each owning card's authoritative
plan, approval, status, runtime handoff, and existing command. Prepare a truthful
readiness matrix and staged command runbook for a later Lightning recovery, so
operators can run only the checks whose implementation, source pin, environment,
and approval gates are satisfied.

## Scope

- Review task cards 01 through 14, the current integrated candidate, source
  register, project context, Lightning setup/start scripts, and feature-local
  runtime handoffs.
- Map dependencies, current offline/owned-SQL evidence, missing implementation
  versus unexecuted checks, exact runnable commands, and stop conditions.
- Record the current source identity and provide a future staged execution order
  with feature-local evidence destinations.

## Out of scope

- Starting or contacting Lightning, a model/provider, HTTP service, PostgreSQL,
  Redis, Docker, or any external endpoint during this planning task.
- Installing dependencies, provisioning or migrating a database, creating
  credentials, changing environment resources, editing product code, or claiming
  runtime/adoption/card acceptance.
- Inventing a one-shot BE2-01–14 runner where the required adapters and owner
  contracts do not exist.

## Acceptance criteria

1. A row for every task 01–14 identifies its feature record, current offline and
   owned-SQL evidence, actual-runtime state, blocker and responsible owner
   boundary, and next executable command or `NOT_IMPLEMENTED` gate.
2. The runbook separates the frozen BE2-01 A17 Studio checkpoint from a future
   shared-source campaign, and distinguishes BE2 tests from generic Lightning
   environment tests.
3. Every command is traced to an existing approved script/handoff; any install,
   database, provider, or service side effect has an explicit gate and is not
   run as part of this plan.
4. Source identity, evidence destinations, stop/rollback rules, and the meaning
   of PASS / FAIL / NOT_RUN / NOT_IMPLEMENTED are explicit.
5. Existing per-card statuses and acceptance records remain unchanged.

## Verification

- Review each mapped command against its current tracked entrypoint and approval.
- Run only repository documentation/security/harness validators and
  `git diff --check`; no Lightning, service, database, or provider execution.
- Store analysis and machine-readable task matrix under FEAT-057 evidence.
