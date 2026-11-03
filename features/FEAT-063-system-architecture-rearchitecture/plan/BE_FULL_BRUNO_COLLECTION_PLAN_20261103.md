# FEAT-063 — Bruno collection for the full BE API surface

Status: **PLANNED — awaiting append-only task approval**. Owner requested this collection after Milestone 1 review. Milestone 1 review round 3 is ACCEPTED; this work is a separate FEAT-063 artifact task and does not reopen or change Milestone 1.

## Discovery baseline

- `artifacts/API_INVENTORY_FEAT063_REV31_20261028.md` is a static historical inventory: 135 declared operations, including 11 candidate/fixture/unmounted declarations; its combined-app baseline predates StoryRun-lite.
- A local, non-network app-factory inspection on `SKETCH2LIFE_ENV=test` with `STORYRUN_LITE_MAIN_DEMO_ENABLED=1` produced **133 runtime OpenAPI operations across 120 paths**, including 11 StoryRun-lite operations. This is the full internal runtime schema stored on the app state. The app's public `/openapi.json` is the FE-facing SRS projection and must not be mistaken for the full BE contract.
- Three local storage-example operations are optional and disabled in that inspection. The current source inventory also marks 11 declarations as unmounted/candidate/fixture. Reconcile both groups against current source before freezing the final counts; do not present unmounted candidates as active BE routes.

## Objective and scope

Create a separate, FEAT-063-owned Bruno collection and a matching full runtime OpenAPI snapshot/coverage matrix for every currently mounted BE contract operation across the combined, classroom and demo profiles. Use the combined profile as the union where possible; record profile exposure per operation. Include the opt-in StoryRun-lite routes and the optional local storage examples as clearly marked local-only operations. Preserve `artifacts/storyrun-lite/bruno/` unchanged.

Deliverables live under `features/FEAT-063-system-architecture-rearchitecture/artifacts/be-full/`:

- `openapi.runtime.json`: sanitized full runtime OpenAPI contract generated from the application factory, not the FE-facing projection.
- `bruno/`: a separate Bruno collection with one request per mounted operation, grouped by API domain.
- `API_COVERAGE.csv` and `README.md`: operation-to-request mapping, profile exposure, auth/data prerequisites, side-effect class, and safe setup/run instructions.
- A local validator that checks operation/request one-to-one coverage, duplicate/missing method-path pairs, request-name/path consistency and that all environment values are placeholders. No backend route, domain behavior or migration change is included.

Candidate, fixture-only and unmounted declarations are listed with their status in the coverage record, but are not counted as runnable mounted API operations. Request files may require a synthetic test record, bearer token or user-supplied IDs; mark those preconditions explicitly instead of making up successful responses. Destructive or state-changing requests must be clearly labeled and confined to a disposable local/test environment.

## Acceptance criteria

1. Recompute the operation inventory from the current runtime schema and source composition for combined/classroom/demo profiles; reconcile the historical 135 declaration inventory, StoryRun-lite and optional local routes. Record exact active/optional/unmounted counts and explain discrepancies.
2. Every active mounted `method + path` has exactly one Bruno request and one coverage row. Every request points back to an operation ID or source handler and an expected contract response. No active operation is silently omitted; duplicate mapping count is zero.
3. Request bodies, required headers, bearer auth placeholders, path/query variables and response expectations come from the current contract/source. If the contract lacks an example or requires seeded data, mark the request `manual-setup` and document the missing precondition; do not fabricate a contract.
4. The default environment contains only local base URLs and empty placeholders. No real credential, child data, local secret, provider URL or machine-specific path is written into the collection. External provider/Modal requests are disabled or explicitly marked; validation must not call them.
5. Bruno CLI can parse/list the collection and run a small, safe local smoke covering readiness/health, one documented read-only operation per representative domain, and the existing StoryRun-lite synthetic flow only if its local prerequisites are available. Do not claim all 100+ requests were executed successfully merely because coverage is complete.
6. The coverage validator, collection parser, repository security validator, harness validator, architecture validator and `git diff --check` pass. Any runtime request run uses only a disposable task-owned test DB and synthetic data; do not reset or migrate the user's `sketch2life` DB.
7. Update FEAT-063 context, source register, decisions, evidence and status. Create a supplemental snapshot with verified hashes. Leave Milestone 1 as ACCEPTED; do not begin another milestone in this task.

## Explicit boundaries

- No change to BE runtime routes/contracts, database schemas, migrations, authentication policy or SRS.
- No automatic test of the whole collection against production or the user's persistent database.
- No Modal/GPU/provider call, network-external request, seed account, real child data, stage, commit, push or merge.
- The existing StoryRun-lite collection remains a separate, unchanged demo collection.

## Owner request

The owner directly requested a complete Bruno collection for the full BE under FEAT-063 after Milestone 1 is complete. This plan defines the operation inventory and safe acceptance boundary for that requested implementation.
