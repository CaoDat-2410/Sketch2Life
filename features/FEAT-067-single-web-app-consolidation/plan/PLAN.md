# FEAT-067 — Consolidate web role portals into one application

- **Status:** APPROVED_FOR_IMPLEMENTATION for the exact scope below; the project-wide final frontend stack remains open.
- **Owner:** Project owner.
- **Worktree:** `F:/Github/Sketch2Life-worktrees/fe-ui-web-remediation` (`codex/fe-ui-web-remediation`).
- **Prepared:** 2026-11-16, Asia/Bangkok.

## Authority and source baseline

- Current user-supplied product SRS: `F:/Downloads/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md`, v2.7-draft Rev68, SHA-256 `69C83FE49CD4689D5D2540656D3319721838CF7343BAD00E24CDE558B8F5E944`, unsigned. Use §§1–31 as target requirements and §32 only as dated source evidence.
- The worktree's SRS authority pointers still name an older copy. They are stale for this task; do not use them to override the user-supplied Rev68 baseline. Do not rewrite historical FEAT-063 records as part of this feature.
- Relevant product boundaries: Rev68 §§3, 9.2–9.3, 10.1, 21.5. The web surfaces are Teacher, School Manager, and Platform Admin/content permission. Route/UI organization does not grant authorization; server-side role/resource checks stay authoritative. Parent remains Android.
- Current worktree contains user-owned uncommitted FEAT-066 UI revisions. This plan requires preserving their exact source/assets and does not supersede FEAT-066's feature-specific history or approvals.

## Goal

Make `apps/web` the sole web application and build entry point, with role-scoped Teacher, School Manager, and Platform Admin modules. Bring the existing BE1-backed `admin-ui` school-admin capability into the School Manager module without replacing it with mock UI. Keep the API, Android/mobile/reference UI, and backend authorization boundary outside this migration.

## Scope

- Migrate `apps/teacher-ui`, `apps/school-manager-ui`, `apps/platform-admin-ui`, `apps/admin-ui`, and `apps/shared` source, styles, public assets, UI-specific documentation, and existing admin-ui tests into `apps/web` modules/shared folders.
- Provide one Vite entry, one browser router, and route namespaces: `/teacher/*`, `/school/*`, and `/platform/*`, plus a central `/login` role entry. Preserve current role-specific preview/login behavior as clearly separated paths; preserve the Firebase/BE1 school-admin login, assignment check, class list/create API behavior, and unavailable states.
- Keep both existing School Manager surfaces under one School Manager module: the API-backed BE1 class-admin surface and the explicitly preview-only M01/M02 screens. Do not imply mock actions persist or silently promote preview screens to backend functionality.
- Use one web package manifest/lockfile, configure the active web scripts to point to `apps/web`, and remove only stale workspace/script references to the already-removed `apps/mobile` and `apps/child-ui` folders. Keep `apps/ui-mobile`, `apps/api`, and `packages/art-renderer` unchanged.
- Record the consolidation boundary in ADR-0023. Use a package pin suitable for this migration, but do not declare it the final project-wide technology-stack decision; keep any remaining stack questions open.
- Remove the superseded web app directories only after their contents and dirty user changes have been migrated and source references checked.

## Out of scope

- Parent Android, `apps/ui-mobile`, child UI, mobile source/dependencies, backend/API/contracts/database/authorization implementation, new role permissions, production data/services/secrets, deployment, generated visual assets, redesign beyond the central role entry needed by the single app, commit, push, PR, or merge.
- Automated test/build execution. Preserve existing tests and scripts; this task records source/static checks only, consistent with the active FEAT-066 review boundary. Do not add tests.
- Changing the product SRS or its sign-off state.

## Acceptance criteria

1. `apps/web` has one HTML/Vite entry and one browser router; each route namespace renders only its own role module, supports direct refresh/deep links, and preserves role-mismatch/unauthenticated behavior.
2. Teacher, School Manager preview, and Platform Admin screens/styles/assets include the current dirty FEAT-066 work exactly; no source is restored from Git HEAD over current user edits.
3. School Manager's BE1 integration retains Firebase login, BE1 current-assignment verification for organization-level `school_admin`, class list/create services, and its explicit unavailable state for unsupported capabilities. M01/M02 preview surfaces remain labelled/non-persistent and separate from BE1-backed classes.
4. Shared web login, role mismatch, API helpers, themes, and icons live under `apps/web/src/shared`; modules do not import from old app directories.
5. Existing admin-ui tests and their config move into the unified app without adding new test cases. Root active UI scripts target `apps/web`; the workspace no longer names removed `apps/mobile`; `apps/ui-mobile` remains registered.
6. Superseded `apps/teacher-ui`, `apps/school-manager-ui`, `apps/platform-admin-ui`, `apps/admin-ui`, and `apps/shared` directories are absent only after migration; `apps/api` and `apps/ui-mobile` remain unchanged.
7. ADR-0023, FEAT-067 context/decisions/status/evidence, and the root task-approval register record scope, route/security boundaries, source baseline, and the fact that no tests/builds or Git publication ran.
8. `git diff --check` and source/reference inventory pass; no automated tests/builds, commit, or push are performed.

## Implementation sequence

1. Inspect and inventory all active web entry points, imports, and dirty paths; write the ADR and verify the approval hash.
2. Create `apps/web`, migrate source by module while retaining current working-tree bytes, then add one router/login entry and prefix role routes.
3. Integrate the BE1 app under the School Manager module; keep the existing preview path explicitly separate.
4. Create one package manifest/config and consolidate assets/styles/tests; update active root scripts and remove stale references.
5. Remove source app directories after an import/reference audit. Record checks/evidence and update status.

## Risks and controls

- CSS is global in the source apps; scope or load role styles carefully so one portal does not silently restyle another.
- The worktree has substantial dirty and untracked FEAT-066 UI work plus earlier requested deletions. Migrate exact working-tree state; never reset, checkout, stash, or restore those paths from HEAD.
- School Manager preview uses fixture state while admin-ui uses Firebase/BE1. Keep them separately labelled and routed; do not merge their auth/state semantics or let client role routes stand in for backend authorization.
- Existing web apps have different React/router/tooling pins. Record an ADR for the migration pin and keep the project-wide final-stack choice open.
- Root manifests currently reference deleted app paths; limit cleanup to those stale active references and preserve `ui-mobile` workspace membership.

## Amendment 1 — one local commit authorized (2026-11-16)

The owner's later direct request to put the requested app cleanup and rebuilt web UI into one commit supersedes this plan's earlier exclusion of commit, for one local commit only. That commit may include the already approved FEAT-067 consolidation changes, the current user-requested FEAT-066 web work, their feature-local records/evidence, and the required root approval record, after a full path and security review. This amendment does not authorize push, PR, merge, deployment, or any expansion of FEAT-067's technical migration scope. Product UI redesign and SRS traceability are governed by FEAT-066 Revision 28.
