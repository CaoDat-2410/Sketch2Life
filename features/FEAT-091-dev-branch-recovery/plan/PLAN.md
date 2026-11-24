# Plan Rev 1 — Restore root checkout to dev and integrate Parent/Modal work

See [`../CONTEXT.md`](../CONTEXT.md) for the exact as-found refs, scope, sequence, acceptance criteria, and risks.

## Commit grouping

Existing commits on the published source branch will retain their original ancestry; the fetched source ref contributes four commits not already in `origin/dev`. Newly integrated dirty work will be staged and committed in focused groups, expected to cover:

1. Parent mobile navigation, screens, and client contract tests.
2. Backend Parent APIs, domain/application changes, schemas, and migrations with their focused tests.
3. Modal workloads and video pipeline changes with worker contracts.
4. Teacher presentation/UI integration.
5. FEAT-063 SRS, authority, source register, and status reconciliation.
6. Feature plans/evidence and legacy documentation packages, split further where a group is too large or unrelated.

The final grouping will follow the actual staged diff; this list does not authorize omitting non-protected root changes.

## Verification

- Confirm branch ancestry and file presence after each integration step. The refs have multiple merge bases, so inspect and review the merge result.
- Review staged file lists and diffs before each commit.
- Run `python tools/validate_repository_security.py` before every commit.
- Confirm no push occurred and both recovery snapshots remain available.
