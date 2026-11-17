# BE2-07 Git publication and Claude cloud review plan

- Status: APPROVED for publication preparation, 12 commits, branch push and Claude cloud review handoff.
- Authority: `../approvals/GIT_PUBLICATION_APPROVAL_20261020.md`.
- Existing branch: `feature/be2-07-knowledge-script`; inherited base `23acf9e83e181305edfeb345be9a8e7eb9dbef88`.
- Product scope and frozen revision 1 remain unchanged. Component NOT_ACCEPTED; card IN_PROGRESS / NOT_DONE.

## Publication sequence

1. Approved feature plan, authorization and scaffold.
2. Knowledge bundle domain and domain tests.
3. Strict contracts and contract tests.
4. Application ports and service.
5. Coordinated transaction/publication boundary.
6. Atomic in-memory repository.
7. Source and consumer fixture adapters.
8. Executable harness and service tests.
9. Concurrent edit, fence and rollback tests.
10. Producer examples, canonical JSON fixture and adapter tests.
11. Fixture chain and isolation tests.
12. Review evidence, cloud handoff, final feature records and shared project routing.

Stage exact files per group and inspect each staged diff. Never recreate obsolete buggy source
to manufacture history. Keep original approval, approved plan, historical review and metric bytes.
These are publication groups of the already-reviewed final snapshot, not a reconstruction of
the original implementation chronology. Pre-commit repository checks run on the complete local
snapshot; no claim is made that historical intermediate groups reran the final offline batch.
Run harness, architecture, security and whitespace validators before every commit and push;
run skeleton validation when structure changes. Existing product verification remains pinned
because publication preparation does not change backend source or tests.

## Portable cloud review

Publish only explicitly selected, inspected evidence derivatives under this feature's evidence
directory. Record original hashes, derivative hashes and any path sanitization. Keep ignored
local originals, external documents, real child data, credentials and unrelated checkout
snapshots local. Export the reviewer findings and sufficient portable JUnit/selection/source
receipts to assess claims; explicitly label missing local checks NOT_VERIFIABLE_ON_CLOUD.
Give Claude a repository-relative prompt, commands and output directory. Reviewer must verify
the checked-out Git commit and evidence hashes, read actual source/tests, rerun offline checks
where dependencies are available, and report limits instead of fabricating results.

After all 12 commits, push this branch to origin without force and verify the remote commit.
Create a Claude cloud review session using an available authenticated capability; if the
environment cannot create it, deliver the exact repository, branch, commit and launch prompt
and state that session creation remains incomplete. No owner acceptance, PR/merge, deployment
or Lightning execution is part of this plan.

## Acceptance

- Exactly 12 focused commits above the inherited base; clean final index and working tree.
- Product source/test/example hashes agree with the reviewed post-Claude snapshot.
- Mandatory repository checks pass before each Git mutation.
- Portable evidence has provenance and passes the repository security validator.
- Origin branch points to the final local commit.
- Cloud session creation is verified by a returned session URL, or explicitly reported incomplete
  with a ready-to-use prompt and the concrete blocking condition.
