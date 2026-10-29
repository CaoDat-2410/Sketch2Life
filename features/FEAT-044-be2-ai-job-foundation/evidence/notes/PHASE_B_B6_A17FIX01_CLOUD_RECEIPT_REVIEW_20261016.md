# B6 A17-fix01: received cloud evidence and local source port — 2026-10-16

Disposition: **CLOUD_NATIVE_PASS_RECEIPTS_VERIFIED; STUDIO_A17FIX01_NOT_RUN**.
Active checkpoint: **Q01/B6_A17FIX01_CLOUD_RECEIPTS_VERIFIED_PENDING_STUDIO**.
This supersedes the earlier R2-only next-run instructions, not the historical results.

BE2-01 remains **IN_PROGRESS**, B6-CR01 **FIXED_PENDING_RUNTIME_REVIEW**, B-12 **HANDOFF**,
OwnerFence/audit/artifact integrations **ASSUMED_CONTRACT**. No owner closure or role-owner
sign-off is inferred. The Phase A and Phase B approvals and approved plan are unchanged.

## Scope and authority

The user provided the cloud archive after the agreed next step: inspect the raw receipts,
port the exact reviewed A17-fix01 correction if consistent, and prepare a separate Studio
package. This is the existing B6 runner correction scope, not another business card or a
new runtime/provider approval. Codex performed the local port and checks; remote runtime
was executed by Claude cloud. No local PostgreSQL/Redis execution is claimed.

## Received artifact and integrity

- Archive: `be2-a17fix01-cloud-evidence-20261016.zip`, **190782 bytes**.
- SHA256: `3bcaa05838b6fb59e0af67f3dd983b1412db300ff96afe047653d132f715ce24`.
- 71 members; safe member paths, no symlinks/duplicate case-folded paths, CRC valid.
- `FILES.sha256`: 70/70 match; the hash list correctly excludes itself.
- Exact archive, extracted files and independent audit details remain under ignored
  `evidence/local/cloud-a17fix01-received-20261016/`. Original downloaded archive is preserved.
- Current PASS, two prior FAIL receipts, targeted teardown run, source patch/copies,
  manifests/wrappers and sanitized environment/role-change evidence are retained separately.

## Source binding and correction

Published base HEAD is `8825e9ff0d99ff29f55f533447b22ba3fbda83d8` on
`feature/be2-01-ai-job-foundation`. A17-fix01 changes only:

- `src/run_durable_conformance.py` in this feature.
- `backend/tests/unit/test_ai_job_b6_conformance.py` in the repository.

The old A-17 scenario created its target and control jobs on the same fixed clock before
dispatch. SQL orders dispatch by available time then message ID, so the control job could
dispatch first. Its token was then valid for the selected message, invalidating the test's
"other job" premise. This was a scenario defect, not a reproduced product authorization bypass.

The correction dispatches the target before creating the control and explicitly proves
both job/attempt identities. It retains all four negative-capability checks and the real
RQ/token-redaction scenario. Four collected unit regressions cover the adverse ordering,
both message-ID orders, and identity premises; their fake scope is labelled explicitly.

| Artifact | SHA256 |
| --- | --- |
| Exact two-file patch | `e92344460b7ccf18c078140813991c1c1db7bf8877f29ff7f9c4f27a57e16703` |
| Corrected runner | `aea4172fd2565236b004b1befc7cec894a8ddc706337219187f9006ff0c4316b` |
| B6 unit tests | `12a06de8a080da94609f3a879ed1a8ffeca120a114925c463acaefab7a1270a9` |
| 46-file source manifest | `5b76868d8993284eed548a9db72d3a668b51ff0857aa875697cd2c450e9835d0` |
| Cloud wrapper | `11de42cb16b7b387e695571ec27ea74d57ee0fd2596c9dc6ada9833c218b53b7` |

The received bytes match the earlier independently reconstructed patch/wrapper/manifest.
Exactly two of 46 source hashes differ from HEAD; the other 44 are unchanged. After applying
the patch locally, all 46 actual worktree files match the cloud final manifest. Nothing was staged
during that receipt review. Later checkpoint commit/push authorization is recorded in DECISIONS125.

## Remote results verified from supplied raw artifacts

PASS receipt: `run-20261016T084310Z-pid635-TMiK3O`, under
`claude-cloud-r2-a17fix01-20261016/receipts/` in the archive. Window:
2026-10-16T08:43:09Z–08:45:35Z. This is inspection of received remote evidence, not direct
execution on or independent observation of the remote VM.

| Evidence | Result |
| --- | --- |
| B2–B6 JUnit | 221 cases; 0 failure/error/skip |
| Phase A JUnit | 224 cases; 0 failure/error/skip |
| Fixture | 20 PASS; 215 checks; 0 failed; digest d17f58a3 unchanged |
| A-17 / A-17-http | PASS, 9 / 4 checks |
| G-01–G-04 / W01–W12 / B-01–B-11 | PASS |
| Durable aggregate | 49 items, 43/43 required PASS, 141 checks, 0 failed |
| Recorded suite, log and outer exits | 0; summary RUNNER_RESULT=PASS |

A-18 remains DEFERRED, A-02/A-19/A-20 NOT_APPLICABLE and B-12 HANDOFF.
The fixture's optional HTTP NOT_RUN is distinct from the durable A-17-http PASS.
Both A17 receipts retain six matching provenance checks. The historical R2 A-17 failure
and later teardown failure remain FAIL; this review does not relabel them.

## Environment and evidence limits

Cloud profile: Python 3.12.3, PostgreSQL 17.11, Redis 8.10.2; package versions are recorded
in the received environment JSON. The dedicated synthetic cluster uses localhost ports
55432/56379. The test role retained NOSUPERUSER/CREATEDB and gained `pg_signal_backend`.
Autovacuum stayed on. This is a test-environment adjustment, not a production requirement
or permission change to apply automatically on Studio.

The targeted previously errored test subsequently passed once with a clean teardown.
The earlier backend identity remains unknown: the archive contains the pytest error but
not PostgreSQL server logs. No autovacuum root cause or permanent race elimination is claimed.
The archive omits the outer `/tmp` stdout/exit files; outer exit is supported by the
recorded summary/state and reviewed wrapper logic. These limits do not turn green raw
JUnit into a failed suite or require repeating it without a new concern.

## Local validation and next checkpoint

- B6 unit suite after the exact port: **25 passed**; JUnit retained locally.
- Ruff on the two changed source files: PASS.
- Focused mypy on those files with worktree imports: PASS.
- Harness, repository security and architecture validators: PASS.
- `git diff --check`: PASS after the source port.
- No full database/runtime suite is claimed on Windows.

New Studio package: `be2-a17fix01-studio-20261016.zip`, SHA256
`e6ce0192dc4299d08dda84ce3ec4c270334d98490246d226097ccc817b40307d`, six flat members.
Its separate Docker adapter is SHA256
`184584274f24b2e1754f8c521c1854a08a4132c69948a75fd53dc6568567fea6`; it preserves the
immutable cloud wrapper and old Studio packages. Source apply/reverse/double-apply and Bash
syntax checks PASS; independent static review PASS after fixing a missing host final Git
identity check. **22/22 offline host probes PASS**, including real isolated Git patch transitions,
wrong source/base/index/resource refusals, exit0/1/2 propagation, and source/HEAD/path changes
during a mocked Docker run preventing outer PASS. Docker/container execution was mocked;
package bytes stayed unchanged. Detailed host evidence remains package-local.

Instructions: `evidence/local/a17fix01-studio-package-20261016/README_STUDIO_RUN.md`.
The package accepts Studio HEAD993a26c plus exact source90724453, R2cb527d7f or final5b76868d;
it refuses other bases/dirty paths, uses existing Docker resources without pulling/installing,
and changes no database privileges. It retains stage producer/tee exits, full JUnit/required
inventory gates, source hashes before each stage and host Git/source checks at both boundaries.
Studio execution is NOT_RUN. When the named Studio is available, verify its actual source/environment,
run this package, then review source-bound results before any CR01/B6 closure decision.
No commit/push/merge/deploy occurred during the receipt-review turn. A subsequent user instruction
authorizes checkpoint commits/push for teammate planning (DECISIONS125); merge/deploy and closure
remain outside that publication. Machine summary:
`evidence/metrics/PHASE_B_B6_A17FIX01_CLOUD_RECEIPT_REVIEW_20261016.json`.
