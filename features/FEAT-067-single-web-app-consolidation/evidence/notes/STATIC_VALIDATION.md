# FEAT-067 static validation

Run date: 2026-11-16.

## Passed static checks

- Relative imports in `apps/web/src`: **0 missing**.
- Imported external npm packages: all declared in the web manifest.
- `apps/web/package-lock.json`: root dependency and devDependency specs match `apps/web/package.json`; all **21 direct packages** have lock entries.
- Non-bundled dependency targets in the merged npm lock: **0 missing**. The optional `@tailwindcss/oxide-wasm32-wasi` package contains bundled dependencies; the baseline `apps/admin-ui/package-lock.json` has the same representation.
- Unprefixed legacy role routes such as `/t01-*`, `/m01-*`, `/a01-*`: **0**.
- Runtime `BrowserRouter` files: **1**; Vite `index.html` files: **1**; `src/main.tsx` files: **1**.
- Superseded web directories: absent. `apps/api` and `apps/ui-mobile`: present and unchanged.
- Removed active `apps/mobile` lock importer; active CI and root web scripts target `apps/web` and have no references to the retired web app paths.
- Existing BE1 test file case count: **2 before / 2 after**; it was moved and its route URLs adjusted. No test case was added or executed.
- New `apps/web` source/docs had no trailing whitespace after correcting the migrated BE1 wrapper.

## Whitespace check and limits

A targeted `git diff --check` over active tracked configuration and FEAT-067 records reported no whitespace errors. The full worktree `git diff --check` still reports two existing end-of-file blank-line issues in dirty FEAT-066 records: `features/FEAT-066-fe-ui-srs-full-review/approvals/TASK_APPROVAL.md:329` and `features/FEAT-066-fe-ui-srs-full-review/plan/PLAN.md:514`. Those user-owned files were left untouched to preserve the active FEAT-066 work.

An offline `npm install --package-lock-only --ignore-scripts` could not regenerate the lock because the local npm cache lacks a Tailwind optional WASI package. No network install was attempted. The lockfile received only static JSON/direct-dependency checks; installability was not proven.

Per the approved scope, automated tests, typecheck, lint, build, browser walkthrough, and deployment deep-link fallback were not run. No commit or push was made.

## Repository validator results

- `python tools/validate_skeleton.py` could not run to completion because it reads `apps/mobile/package.json`, which is absent by the owner's earlier explicit request to remove the mobile app from this branch. The current consolidation leaves `apps/api`, `apps/ui-mobile`, and `apps/web`; the mobile app was not restored.
- `python tools/validate_harness.py` returns `HARNESS_INVALID` for that same `apps/mobile/package.json` expectation and missing evidence scaffolding in the unrelated existing FEAT-070 feature. FEAT-067's required `raw`, `screenshots`, and `metrics` evidence folders now contain notes explaining that those artifacts were not produced. No harness script was changed.

## 2026-11-16 closeout verification

The earlier section records the pre-UI-rebuild checkpoint. The owner later authorized the app build and browser review as part of FEAT-066 Rev28. `npm ci` completed and `npm run build` passed; nine role/entry screenshots and the API/SRS matrix are in FEAT-066 EV-034. No application tests were run.

Final repository checks: `validate_repository_security.py` passed after machine-specific paths were removed from the Rev23 provenance note; `validate_architecture.py` passed; `git diff --check` exited 0. Harness and skeleton still cannot pass because the user's earlier folder cleanup removed `apps/mobile/package.json`; harness also reports missing evidence directories in unrelated FEAT-070. No validator or unrelated feature scope was changed to hide those findings.
