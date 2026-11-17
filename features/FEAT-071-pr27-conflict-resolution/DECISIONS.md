# FEAT-071 decisions

## D1 — Integrate `dev` as a normal merge commit on the PR head

Keep the PR head as first parent and the exact `dev` SHA as second parent. Do not change the PR base or merge the PR into `dev`.

## D2 — Preserve all append-only approval history

The global approval file contains separate FEAT-063 and FEAT-066/067/070 records from the two histories. Retain every section and append the FEAT-071 approval without rewriting earlier approvals.

## D3 — Respect the web migration boundary

Keep the old Teacher/Admin portal directories removed after carrying applicable current `dev` behavior into the consolidated `apps/web` modules. Preserve Android/mobile source because FEAT-066/067 exclude it from this migration.

## D4 — Keep both backend route contract views

The test conflict represents two independent route assertions: the PR's unprojected OpenAPI route set and the `dev` compatibility app's full mounted-route view with its updated expected route catalog. Retain both views and assert that they agree before comparing the route set to the baseline-adjusted expected catalog.
