# FEAT-060 Plan revision 5 — CI readiness and Iteration 1 verification

- Date: 2026-10-24
- Status: APPROVED by the project owner's direct reply “Có, sau khi gate đạt” to the explicit CI, Iteration 1, BM02/tag gate question.
- Baseline: `dev` at the Rev10 publication commit plus the reviewed Rev11 documentation/CI changes.
- Parent: FEAT-060 classroom integration and Review 2 remediation.

## Objective

Establish a reproducible, credential-free continuous-integration workflow for the repository's current maintained baseline; inspect and run available Iteration 1 fixture/contract workstreams under ADR-0006 without turning that historical sprint plan into a new team allocation; record accurate pass/fail/blocked results for FEAT-058 Review 2 documentation.

## Approved scope

1. Inspect current repository CI definitions, package managers/lockfiles, existing check scripts, and Iteration 1/Sprint 1 runner/harness evidence. Do not replace authoritative project workstreams or invent allocations.
2. Add a GitHub Actions workflow for pull requests and pushes that runs only the reviewed, credential-free baseline checks: repository harness/security/architecture/team validators; active Child, Teacher, and Admin checks; and backend unit/contract tests. Use locked dependency installation and least-privilege workflow permissions. Do not pass repository secrets or invoke providers, Firebase, Modal, external databases, deployment, or real child data.
3. Add no end-to-end or database-backed test to CI unless the workflow can use an isolated synthetic test environment that is explicitly part of the approved plan. Database tests requiring a secret endpoint must remain reported as skipped/blocked and must not be described as passed.
4. Run the approved baseline checks locally where feasible and trigger the workflow on the authorized pushed `dev` change. Record the exact commit, run ID/URL, environment, counts, skips, and interpretation in FEAT-060 evidence.
5. Inspect the four ADR-0006 independent workstreams (domain fixtures/harness, AI-understanding fixtures/runner, standalone art-animation protocol/runner, and learning-media fixtures/runner). Run existing offline entrypoints that are present and reproducible. For missing, obsolete, or gated workstreams, record `PARTIAL`/`BLOCKED` with concrete evidence; do not create replacement product code or claim the Integration Sprint is complete.
6. Record a clear Iteration 1 status matrix and distinction between independent fixture/contract readiness and current integrated runtime behavior. The report is evidence for planning and Review 2 only.
7. Permit the owner-authorized `review-2` tag only after CI, selected Iteration 1 checks, document QA, clean-tree and repository-security gates all pass. This plan does not authorize a tag before those conditions.

## Exclusions

- Feature/runtime/schema/migration changes, provider/GPU work, Modal calls, deployment, secrets, real child data, production DB, and full E2E acceptance.
- Assigning owners or dates to Iteration 1 tasks; current replacement allocation remains governed by ADR-0015 and the approved project plan.
- Changing the repository security validator to suppress findings or include sensitive artifacts in public Git.

## Acceptance criteria

- AC1: A maintained CI workflow is present, syntactically valid, least-privilege, dependency-lock aware, and contains no credential or deployment step.
- AC2: The CI job set matches documented successful/intentional baseline checks and does not silently ignore a failure or relabel skipped database coverage as success.
- AC3: The local run and hosted CI run have reproducible command/environment evidence, exact source SHA, pass/fail/skip counts and any blocker interpretation.
- AC4: Each of the four ADR-0006 workstreams has a current evidence-based status with exact runnable entrypoint or specific missing/gated dependency; no live dependency is introduced.
- AC5: Iteration 1 evidence clearly separates the four independent fixture/contract streams from the integrated classroom runtime and from FE-to-BE/device acceptance.
- AC6: The `review-2` tag is not created until the evidence matrix, CI, document QA and repository security gates pass on one clean exact commit.

## Work sequence

1. Inspect current CI and the four workstream manifests/runners; preserve existing source ownership.
2. Write the smallest workflow that uses locked dependencies and existing check commands.
3. Run relevant checks on the local Windows environment; capture failures/skips without changing product behavior.
4. Add feature-local Iteration 1 matrix and reproducible CI evidence.
5. Run the repository security validator before commit and again before push; push the reviewed branch per owner authorization.
6. Wait for the hosted workflow to finish and record its result. Do not create the Review 2 tag if any required job fails or remains unverified.

## Risks and limits

- Some legacy packages or tests may not be maintained in the same way as the active UIs; include only checks demonstrated to be part of the current baseline.
- Hosted CI may expose pre-existing failures or environmental assumptions. Fix workflow defects within scope; do not hide product or architecture failures by removing test coverage.
- Passing offline checks cannot establish PostgreSQL persistence acceptance, physical-device behavior, provider readiness, or classroom release readiness.
