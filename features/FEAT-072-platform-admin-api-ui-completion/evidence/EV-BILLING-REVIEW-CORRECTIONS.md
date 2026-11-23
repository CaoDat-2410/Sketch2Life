# Billing review corrections evidence

- Teacher exit: runtime-session PostgreSQL regression passed; removing the flush caused the expected missing-return failure.
- Quota catalog: 236 runtime operations recorded; catalog and Parent recovery tests pass.
- Settlement and provider callbacks: local-fake tests cover mismatched amounts, duplicate events, paid-after-cancel, valid and invalid signatures, and non-ASCII MoMo signatures.
- Allocation/reclaim: PostgreSQL regression verifies balances and idempotent replay. Full admin PostgreSQL suite: 15 passed.
- Migrations: each requested revision upgraded on a fresh disposable PostgreSQL database; each attempted downgrade raised its intentional RuntimeError.
- Web check: build, lint and 665 tests passed (67 files), with lint/build warnings.
- Four billing files passed strict mypy and Ruff. Repository security and architecture validators passed.
- Full contract/unit run: 8,073 passed, 71 failed, 22 skipped, 18 collection errors. The catalog failures disappeared. The supplied failure list does not include 21 resulting IDs: 18 collection errors from missing tools/backend modules or imageio, plus three media/whiteboard failures involving missing tools imports. The focused schema-mapping failure is present in the head baseline. Security settings: 9 passed.
- P2-2 remains deferred by task scope; no live provider calls, commits, or pushes.
