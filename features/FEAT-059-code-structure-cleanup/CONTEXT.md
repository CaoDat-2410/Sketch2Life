# Feature context

- Status: DONE; FEAT-058 document authoring may proceed.
- Owner: Project owner
- Goal: Improve repository structure while preserving current product and demo behavior, before resuming the Review 2 document package.
- Scope: Structure and verification tooling for the current Child, Teacher, and Admin UI apps and the backend HTTP composition root. Keep the three UI apps separate.
- Non-goals: New UI, real API/auth wiring, behavior or contract changes, provider calls, deployments, migrations, deleting/merging legacy apps, and document authoring.
- Dependencies: Existing architecture and security governance. Owner selected the local `dev` baseline and directed that the unmerged P2-T5 branch stay separate.
- Risks: Current tests share a mixed FastAPI composition root; the root PNPM workspace excludes the three recently merged UI apps; there are other app directories and active remote branches whose ownership/status must not be guessed.

## Completed context snapshot

Confirmed cleanup baseline is local `dev@0a7ce768c153f2104cff930569c3eda6e484532c`. The owner selected “Giữ riêng, clean trên dev” for `origin/feature/feat018-p2t5-evaluation-harness`; that branch is excluded from this implementation baseline and will not be merged/cherry-picked under FEAT-059. The current Child, Teacher, and Admin interfaces are separate directories: `apps/child-ui`, `apps/teacher-ui`, and `apps/admin-ui`. Keep those boundaries. Other app directories (`apps/mobile`, `apps/ui-mobile`, `apps/child-app`, `apps/parent-web`, `apps/api`, and `apps/tmp`) require inventory/classification; do not delete or consolidate them in this scope.

Initial read-only findings:

- Root `pnpm-workspace.yaml` includes only `apps/mobile`, `apps/ui-mobile`, and `packages/art-renderer`; root recursive checks do not include the three current UI apps.
- Child API/session services, Teacher session/profile services, and Admin auth services return local fixtures/stub values. This plan preserves those results and does not claim live integration.
- `backend/src/sketch2life/interfaces/http/app.py` is an 869-line composition module. It creates durable BE1 runtime and local/demo services, stores both on `app.state`, and mounts BE1 plus demo routers. Many tests call `create_app()`, so its route and response compatibility is a hard constraint.
- `origin/feature/feat018-p2t5-evaluation-harness` is not merged into `dev`; it is 28 commits ahead of `dev` and its current remote tip adds a benchmark module, FEAT-018 tests, test changes, and substantial evidence. The local branch is four commits behind that remote tip. The owner directed that it remain separate from FEAT-059.
- `origin/feature/feat048-srs-diagram-pack` is not merged into `dev`; its 12-commit delta contributes two Mermaid diagrams only.

Relevant authority: `docs/context/PROJECT_CONTEXT.md`, `docs/context/SOURCE_REGISTER.md` (FEAT-058 current baseline entry), `docs/architecture/OVERVIEW.md`, `docs/architecture/DEPENDENCY_RULES.md`, `docs/architecture/CONTRACTS_AND_INTEGRATION.md`, `docs/governance/WORKFLOW.md`, `docs/governance/APPROVAL_POLICY.md`, ADR-0006, and ADR-0019. ADR-0019 records classroom runtime/demo separation as a target; runtime changes require their own scoped approval.

Implementation is complete on the approved `dev` baseline. The three current UIs have explicit per-app check scripts and core-flow tests while retaining separate dependency graphs. Backend local/demo stores and session construction are named in `interfaces/http/demo_composition.py`; classroom and demo router groups are named in `interfaces/http/router_composition.py`. The legacy `create_app()` still mounts the combined route surface.

Verification passed: Child 20/20 tests, Teacher 2/2, Admin 2/2, and the focused backend suite 9/9; all 76 baseline OpenAPI paths and 83 operations are unchanged. Architecture, harness, skeleton, security, and diff checks passed. The 72-file manifest is `evidence/metrics/implemented_file_manifest.json` (SHA-256 `87e84a4faedf0572ac0e88b21238b38eb7cd02c9ebc92aea5f4a7931528165ef`).

Known gaps remain explicit: Child service calls are stubs/fixtures, Teacher login is presentational, and Admin authentication/protected navigation remains prototype behavior. Child's dependency audit reports 47 findings and its linter reports one existing timer-effect warning; Teacher build emits a large-bundle advisory. These were not addressed because dependency upgrades and behavior changes were excluded. No commit or push was made. FEAT-058 will identify the source as commit `0a7ce768c153f2104cff930569c3eda6e484532c` plus the verified, uncommitted working-tree manifest.
