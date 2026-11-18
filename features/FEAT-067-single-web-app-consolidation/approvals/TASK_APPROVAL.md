# FEAT-067 task approval

- **Status:** APPROVED_FOR_IMPLEMENTATION.
- **Approver:** Project owner, direct instruction on 2026-11-16 (Asia/Bangkok): “Ok đc đó làm cho tôi đi”.
- **Approved plan:** `features/FEAT-067-single-web-app-consolidation/plan/PLAN.md`.
- **Plan SHA-256:** `0161673F9FD799B62E3CBA51D9AA2B9ACCDD4C3D8BFA574D7F4ACFEC483CF2ED`.
- **Scope:** the goal, boundaries, acceptance criteria, and sequence in the hash-identified plan: migrate Teacher, School Manager preview, BE1-backed school-admin, Platform Admin, and shared web source into one `apps/web` application; preserve dirty FEAT-066 work; namespace routes and scope portal styles; update active web scripts and CI; remove superseded web folders only after migration audit.
- **Exclusions:** mobile source, `apps/ui-mobile`, API/backend/contracts/database/authorization changes, new permissions, production data/services/secrets, automated test/build execution, SRS changes or sign-off, commit, push, PR, merge, or deployment.
- **Approval basis:** the owner's direct instruction authorizes this implementation scope. It does not approve the unsigned SRS or a project-wide final frontend stack.


## FEAT-067 Amendment 1 — one local commit

- Status: APPROVED for one local commit only, as a later owner instruction on 2026-11-16.
- Amended plan: features/FEAT-067-single-web-app-consolidation/plan/PLAN.md.
- Amended plan SHA-256: 9375A55AB5909D3D417F712832FC01B9720D9DD2714FC8108808D7B8D48561ED.
- Scope: commit the already-approved consolidation changes with the related FEAT-066 Rev28 web UI work and governance records after full staged-path and repository-security review.
- Supersedes only the earlier no-commit exclusion. No push, PR, merge, deployment, or expansion of FEAT-067 implementation scope is approved by this amendment.
- Approval basis: the user's current direct request to put the app cleanup and rebuilt web UI into one commit.
