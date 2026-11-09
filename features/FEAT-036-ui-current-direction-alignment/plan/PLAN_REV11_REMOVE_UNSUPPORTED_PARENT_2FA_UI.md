# FEAT-036 plan revision 11 — Remove unsupported Parent 2FA UI

- Revision: 11
- Status: `APPROVED`
- Prepared: 2026-11-10
- Type: Parent account-security UI correction and release consolidation
- Product baseline: FEAT-063 SRS v2.7-draft Rev57 (unsigned), routed by
  `docs/context/SRS_AUTHORITY.md`

## Objective

Remove misleading two-factor authentication controls and placeholder recovery codes from the Parent
Settings UI because the current Parent requirements and auth integration do not establish a usable
2FA flow. Consolidate the owner-approved FEAT-036 UI work in this worktree into one commit and push
the current branch for use on another machine.

## Scope

1. Remove the Parent Settings 2FA row, detail subview, local enable/disable toggle, method selector,
   and hard-coded/re-generatable backup codes.
2. Preserve the password-change row and other security/account settings.
3. Do not change the SRS or infer whether 2FA should later be offered to Parent accounts. The SRS
   requirement for organization and billing administrators remains separate.
4. Update FEAT-036 context, decision, status, and evidence.
5. Stage the owner-approved current FEAT-036 worktree changes explicitly, run required governance
   checks, create exactly one conventional commit, and push it to the current feature branch.

## Acceptance criteria

1. Parent Settings no longer exposes a false “enabled” 2FA state, factor choices, or backup codes.
2. Existing account/password/settings navigation continues to work.
3. All accumulated owner-approved FEAT-036 UI work in the current worktree is included in exactly
   one commit; no unrelated files or secrets are staged.
4. `python tools/validate_harness.py`, `python tools/validate_repository_security.py`,
   `python tools/validate_architecture.py`, and `git diff --check` pass before the commit.
5. The commit is pushed to the current branch and the resulting commit/remote state is reported.

## Out of scope

- Implementing Parent MFA, changing the SRS, admin MFA, authentication/backend changes, other
  portals, tests/builds, deployment, or publishing.

## Authorization

The owner confirmed that the current Parent 2FA UI should be removed and explicitly requested that
all current approved UI work be consolidated into one commit and pushed for another-machine work.
