# FEAT-059: Code structure cleanup without behavior change

- Status: AWAITING_APPROVAL
- Plan revision: 1
- Implementation status: NOT_STARTED
- Confirmed baseline: local `dev@0a7ce768c153f2104cff930569c3eda6e484532c`; owner directed that P2-T5 remain a separate branch.

## Goal

Make the repository easier to navigate, build, and verify before returning to the Review 2 reports. Preserve the behavior and visible results of current apps, API routes, fixtures, and demos.

## Scope

- Keep `apps/child-ui`, `apps/teacher-ui`, and `apps/admin-ui` as three separate app boundaries.
- Inventory all app folders and active remote branches; classify current, legacy, research, and document-only sources. Do not delete, merge, or rename app folders.
- Make build/typecheck/lint/test commands cover the three current UI apps without collapsing their dependency graphs or changing the existing RN/Metro setup. Prefer explicit per-app commands if workspace consolidation risks dependency resolution.
- Extract backend composition responsibilities into named modules/factories for the durable classroom runtime and local/demo services, while preserving `create_app()` and the current default entrypoint's route surface and observable behavior. Retain a compatibility composition until all existing callers are verified.
- Make current fixture/mock service ownership explicit and injectable, preserving their current data, return shapes, timing semantics, and default selection. No live API/auth/provider wiring.
- Add or adapt regression coverage for the existing primary flows and app composition. Resolve missing test scripts/runners only as needed to execute the requested core-flow verification.
- Keep all changes feature-local in evidence and restrict product-code edits to files listed in the approved implementation manifest.

## Exclusions

- No UI redesign, new business behavior, API contract changes, real Child/Teacher/Admin backend integration, Modal/Lightning/provider call, credential/secret work, database schema/migration, cloud/runtime deployment, or Git push/tag.
- No application consolidation, legacy app deletion, dependency-version upgrade, product architecture finalization, or switch of `main:app` to another runtime profile.
- No Review 2 DOCX/PDF authoring during FEAT-059.
- Do not merge an unmerged branch until its source and overlap are reviewed and the owner chooses its inclusion. The P2-T5 branch is specifically pending this decision.

## Steps

1. **Pin the source baseline.** Use `dev@0a7ce768c153f2104cff930569c3eda6e484532c`. Keep `origin/feature/feat018-p2t5-evaluation-harness` separate; do not merge or cherry-pick it under FEAT-059. Record other recent unmerged branches as separate candidates without importing them. Preserve all existing dirty/untracked workspace files.
2. **Capture behavior before restructuring.** Inventory UI entrypoints, local mock outputs, backend routes/OpenAPI, app-state dependencies, default configuration, and current primary flows. Create focused characterization checks so behavior comparisons are reproducible.
3. **Repair verification reach.** Add aggregate commands for Child, Teacher, Admin, and backend that call their existing package-level commands. Preserve isolated package graphs unless a tested workspace experiment demonstrates no Metro/dependency regression. Add test scripts/runners only where needed for the agreed core-flow checks.
4. **Separate backend composition.** Extract service construction and router groups into small named composition modules. Keep `create_app()` and `sketch2life.main:app` compatible, preserve default middleware/exception handling, route order/surface, dependencies, lifespan/state, and current demo/BE1 responses. Add explicit classroom/demo factories only as additive entrypoints; do not change which entrypoint existing commands use.
5. **Clarify mock adapters.** Move or wrap existing fixture implementations behind named local/mock providers with explicit injection points, preserving fixture content and default behavior. Do not silently turn mocks into network clients or report a stub as live integration.
6. **Verify and record.** Run the agreed per-app build/typecheck/lint and focused primary-flow/backend composition tests; run applicable architecture/harness/security validators. Compare route/OpenAPI and representative fixture results against the captured baseline. Record commands, versions, outputs, changed-file hashes, and any known gap in this feature's `evidence/`.
7. **Review before documents.** Summarize what was structurally changed, what was preserved, test results, unresolved gaps, and the final source SHA. Only then resume FEAT-058 document work against the verified baseline.

## Acceptance criteria

- AC01: `apps/child-ui`, `apps/teacher-ui`, and `apps/admin-ui` remain separate applications; no existing app directory is deleted or silently promoted/demoted.
- AC02: Root or documented aggregate commands reach build/typecheck/lint checks for each of the three current UI apps and the backend, without breaking the existing app-local commands or React Native/Metro dependency graph.
- AC03: Existing `create_app()` import/callers and `sketch2life.main:app` remain compatible; current route paths/methods, route availability, auth/error boundaries, and OpenAPI surface do not unintentionally change.
- AC04: Characterization/regression checks demonstrate that representative existing Child, Teacher, Admin fixture flows and BE1/demo route behavior return the same contract/data outcomes as the captured baseline.
- AC05: Current fixture behavior stays local and deterministic; no UI calls Modal, Lightning, provider credentials, or newly-live backend endpoints.
- AC06: Backend composition code is split along explicit responsibilities and dependency direction without changing domain rules, persistence semantics, migration heads, or router contracts.
- AC07: The implementation includes the approved core-flow checks: Child PIN join, drawing/offline persistence, and feeling submission; Teacher fixture sign-in/profile and session create/read/advance; Admin fixture sign-in/current-user and main guarded navigation; backend health, durable route availability, and representative demo route compatibility. Final test targets may be narrowed only if a flow cannot be executed in the current harness, with the reason recorded for owner review.
- AC08: Build/typecheck/lint and the agreed tests pass, or any failure is isolated, evidenced, and explicitly accepted before calling cleanup complete. No tests/builds/lint are claimed before execution.
- AC09: Applicable architecture/harness/security checks and `git diff --check` results are recorded; repository security validation runs before any later commit/push.
- AC10: No implementation begins until this exact plan revision is recorded `APPROVED` in `approvals/TASK_APPROVAL.md`; no document authoring begins until cleanup completion evidence is reviewed.

## Risks and mitigations

- **Compatibility surface is wider than one factory.** Many backend tests invoke `create_app()`. Capture route/state/error behavior first; keep the existing factory as a compatibility wrapper and use characterization tests before moving components.
- **Workspace changes can perturb React Native tooling.** The existing workspace documents a Metro conflict between different RN versions. Prefer explicit aggregate commands over workspace hoisting; do not unify lockfiles by default.
- **Mocks can look like live services.** Preserve data behavior but label and inject them as mock/fixture adapters; never add live calls as part of structural cleanup.
- **App folder names do not establish ownership.** Inventory and classify only; require separate direction before deleting, moving, or consolidating legacy/research apps.
- **Unmerged P2-T5 work can affect a later document baseline.** Keep it outside FEAT-059 as directed. Before document authoring, re-check whether it has since been independently integrated; do not use the stale local branch tip.
- **The worktree has pre-existing modifications and untracked artifacts.** Record the starting status, avoid broad formatting/rewrite operations, and edit only approved paths.

## Verification plan

- Before changes: route/OpenAPI and representative fixture behavior snapshot; app-specific command inventory; repository status.
- After changes: per-app build/typecheck/lint; the agreed primary-flow tests; backend composition regression/contract tests; applicable architecture/harness/security validators; `git diff --check`.
- Compare before/after route+method sets, OpenAPI paths/schemas where stable, fixture return shapes, and UI flow outcomes. Any intentional difference blocks acceptance and requires a separate owner decision.
- Do not run providers, databases, or live external services. Do not claim full integration.

## Evidence plan

Store baseline inventory, branch delta review, verification command receipts, route/contract comparisons, before/after file manifests, and a final review note only under `features/FEAT-059-code-structure-cleanup/evidence/`. Keep secrets, actual child data, and provider tokens out of evidence.

Implementation is blocked until `approvals/TASK_APPROVAL.md` records `APPROVED` for this plan revision and its exact SHA-256.
