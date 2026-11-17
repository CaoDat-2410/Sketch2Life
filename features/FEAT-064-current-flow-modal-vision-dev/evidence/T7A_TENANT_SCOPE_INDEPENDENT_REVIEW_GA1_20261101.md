# Independent review — T7a tenant-scope finding (GOAL A1)

**Disposition: ACCEPTED.** The P2 finding is closed. This record captures the independent review report supplied by the owner after Claude reviewed the source and diff read-only.

## Authority pins verified by reviewer

- V4: SHA-256 `E11FFBCE0F655C010E679773D231D3E36930A0B960E705450499E2A2A69191F6`.
- Goal A1: SHA-256 `90B546430E1E1E2E8B40078EBD7FF2CA108D0F785C054C06620F2EBBF6902949`.
- T7a plan: SHA-256 `8A277676DC3DE4DDD19A7B69FFFC14ABF12EA729E9B87254980D71D422C201C7`.
- The tenant-scope fix report hash verified by the reviewer: `5677467DC4D0B29DB4F4EE53D15D7995F70CDD20FEBF3E035D87C9D85FE0B9E2`.

## Finding and review result

The earlier review found that `SqlAssistanceUnitOfWork.put_receipt()` validated the receipt key's organization but not `receipt.snapshot.facts.organization_id`, which could allow an org-A receipt row to carry an org-B snapshot payload.

The reviewer confirmed that `put_receipt()` now calls `_check_org(receipt.snapshot.facts.organization_id)` immediately after validating the key and before constructing SQL values, calling `connection.execute()`, or entering the conflict-read path. The existing `_require_org` rejects empty or mismatched organization IDs.

The regression test uses a receipt key scoped to `org`, a `foreign-org` snapshot, and a connection mock configured to fail if storage is accessed. It expects the organization-scope `ValueError` and asserts `connection.execute` was not called. Removing the new guard would make the test fail at the storage mock. The reviewer found the P2 resolved and no blocker in the reviewed scope.

## Non-blocking notes and evidence limits

- The reviewer suggested `connection.mock_calls == []` as optional strengthening; the current `execute.assert_not_called()` already verifies no SQL execution for this method. No change was required by the accepted review.
- Nested organization validation elsewhere in `vision_analysis/repository.py` was not reviewed as part of this specific finding; no new blocker was identified or inferred from that note.
- The reviewer did not rerun tests or validators. Counts below are from the implementation report: focused T7a unit **18 passed**; offline GA1 **649 passed, 4 skipped, 0 failed**. Ruff, mypy, three validators, and scoped diff-check were reported passing.
- At review time, branch `feature/feat063-be-foundation` was at `fcfadad298c874c7f66236c424e370159771857b`, ahead of origin by one. The existing amended commit did not yet contain the one-line source fix and regression test; they were still local changes. No stage, commit, push, test, database, provider, or Modal operation was performed by the reviewer.

## GOAL A1 disposition

M1 and T6 were previously independently accepted; this review accepts T7a after the P2 correction. GOAL A1 is accepted and may be closed as **COMPLETE**. A2 was not started. Its checked-in execution goal still pins the old HEAD `1e93bc3f…`; before A2, the owner must choose and approve an updated post-A1 HEAD pin and refreshed goal hash.
