# T6 bounded DNS resolver plan review — OWNER APPROVAL PENDING

**Plan review:** TECHNICALLY ACCEPTABLE
**Implementation approval:** NOT GRANTED
**Date:** 2026-11-01

## Pins and evidence checked

- V4 SHA-256 `E11FFBCE0F655C010E679773D231D3E36930A0B960E705450499E2A2A69191F6` and Goal A1 SHA-256 `90B546430E1E1E2E8B40078EBD7FF2CA108D0F785C054C06620F2EBBF6902949` match.
- Draft plan `T6_BOUNDED_DNS_RESOLVER_PLAN_GA1_20261101.md` SHA-256 `2D1E5D4B46613FA7AEBCC8A96E6288F87423DF725174FF88DBAA46DA7A66B10F` matches the plan pin.
- Regression correction report SHA-256 `0E6870260AB74BB3C2CC64B0C81C3086DAEC6AD17E0399FB0F7B6BF74681D1DE` matches. The new copied runner has SHA-256 `766225385A00C5E6537C000F5BA71E559E5BABCF58243E0DB199FE342D3C8E76`; the saved command includes the M1, T7a, and T6 add-ons. Its captured output is **646 passed, 4 skipped**, with `TEST_EXIT 0` and outer exit code `0`. This clears the previous aggregate-evidence finding. The reviewer inspected saved evidence and did not rerun tests.
- Current `transport.py` and focused test hashes still match the plan's baseline pins. Branch/HEAD are `feature/feat063-be-foundation` / `1e93bc3f3ac645cf4baecbbc09c73afe48719c92`; the Git index is empty.

## Plan assessment

The proposed fix addresses the identified resource risk and preserves the approved T6 boundaries. It limits resolver concurrency across all `HttpJsonTransport` instances in one Python process to a fixed cap of two, uses no unbounded submission queue, retains capacity until the underlying resolver actually exits, and fails saturated attempts closed before `SENT` or HTTP bytes. The planned tests cover saturation, deadline expiry without prematurely releasing a resolver slot, capacity recovery, and loopback-only HTTP. The implementation scope is limited to `transport.py`, the focused T6 test, and append-only task records.

**Owner decision required:** cap 2 is per process, not global across containers/processes. A deployment with N BE processes can have up to 2N resolver workers. The plan documents that boundary and the tradeoff that two permanently blocked resolvers disable later DNS-dependent calls in that process. Confirm the cap and process-wide scope explicitly before implementation.

No approval entry for plan SHA `2D1E5D4B46613FA7AEBCC8A96E6288F87423DF725174FF88DBAA46DA7A66B10F` was found in the FEAT-064 approval record at review time. The plan is still `DRAFT`; this review does not grant implementation authorization.

## Gate result

The regression correction is accepted as evidence. The bounded-resolver plan is technically acceptable **pending explicit owner approval of cap 2 per process**. Do not modify source/tests or start A2 until that approval is recorded. No tests or validators were run by the reviewer; no source, test, plan, approval, or snapshot was changed. No PostgreSQL/Alembic, Modal/GPU/provider, or external network operation occurred.
