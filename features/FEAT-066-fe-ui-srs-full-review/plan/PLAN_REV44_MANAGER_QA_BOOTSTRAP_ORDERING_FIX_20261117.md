# FEAT-066 Plan Rev44 — Manager QA bootstrap ordering repair

Status: APPROVED_FOR_IMPLEMENTATION.

Owner request: “Cho account test lun sau đó login đồ ổn thì qua tiếp nối các api nghiệp vụ”. The owner supplied the ignored worktree-root .env path for Firebase Web config during this task.

Worktree: F:/Github/Sketch2Life-worktrees/fe-ui-web-remediation, branch codex/fe-ui-web-remediation.
Product context: FEAT-063 SRS v2.7-draft Rev60 remains the repository working authority; this task changes only the development bootstrap utility and uses a reserved-domain QA account.

## Evidence and reason

Rev42 provisioning attempts successfully created temporary Firebase identities and signed into Firebase. The supported be1_bootstrap._provision flow failed with PostgreSQL IntegrityError on be1_organization_assignments_organization_id_fkey. The transaction rolled back and each temporary Firebase identity was deleted. Read-only counts after cleanup are one existing identity, zero organizations, and zero assignments.

The bootstrap utility adds OrganizationModel, AdultIdentityModel, and OrganizationAssignmentModel in one ORM flush without relationships that order those pending writes. Add an explicit flush of the two parent rows before adding the assignment.

## Scope

1. Add an explicit session.flush() after adding the organization and adult identity, then add the organization assignment.
2. Add a focused unit test that records the ORM operation order and verifies the assignment is added only after the parent flush.
3. Retry the already-authorized Rev42 flow once with a newly generated reserved-domain identity. Keep credential material in process memory only.
4. Verify Firebase password sign-in, GET /api/auth/v1/me role, GET /api/be1/v1/organizations/{id}/me scope, and the FE Manager login route when browser tooling permits.
5. If any step fails, remove only the just-created identity and any dedicated bootstrap rows. Record sanitized statuses.

## Acceptance criteria

- The focused backend test proves parent rows flush before the assignment is added.
- The supported bootstrap flow succeeds against the local sketch2life-dev Docker API/PostgreSQL.
- Authenticated role is school_manager and assignment is organization-wide school_admin for the generated organization.
- FE Manager sign-in reaches /school or records the specific environment limitation.
- No unrelated data, account, API contract, schema, authorization policy, business mutation, or production resource changes.
- No credential, Firebase ID token, API key, or personal data in repository files, logs, screenshots, or evidence.
- Existing worktree changes remain untouched. No commit or push.

## Work sequence

1. Record this plan and its approval before changing source.
2. Add and run the focused unit test.
3. Apply the explicit parent flush in the bootstrap utility.
4. Run the unit test and the requested live account/login verification.
5. Record results, cleanup status, and limitations in the feature evidence/status/context.
