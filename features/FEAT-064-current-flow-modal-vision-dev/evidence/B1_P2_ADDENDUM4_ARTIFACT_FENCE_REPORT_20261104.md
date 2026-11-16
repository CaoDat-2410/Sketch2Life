# B1 P2 Addendum 4 — artifact fence implementation report

**Disposition:** `XONG-CHƯA REVIEW`
**Review boundary:** this report does not mark B1 or Finding 2 accepted.
**Scope:** bounded artifact-owner-fence fix and test evidence only; no approval record was edited.

## Inputs and checkout

| Item | Observed value |
| --- | --- |
| Addendum 3 diagnostic report | `28BCB6AC384A6769F1B6AD71CCBE41F530005C06097C5630A190547A00B3DE14` |
| Addendum 4 plan | `2BC43A289D2415B2EC0C3A9B8134AC376B76CF94D21042182852AC68C979E6E9` |
| Branch | `feature/feat063-be-foundation` |
| HEAD | `b6dbfa68e66718f3f40902c093e9ebd634b1ebb9` |
| Staged paths | `0` |
| Worktree entries | `106` at final capture, including this untracked report |

The Addendum 3 report already exists and its input Addendum 2 report hash matches the pasted diagnostic addendum. It records the root cause as a missing artifact fence. The diagnostic was not rerun in this Addendum 4 continuation. Existing unrelated working-tree changes were preserved.

## Implementation

- `pilot_composition.py` now issues versioned `be1-pilot-artifact-v1:` fences bound to artifact reference, organization and SHA-256. The process-local store checks existence, quarantine state, metadata binding, and an exact integer epoch under its lock; first quarantine increments the epoch. Unknown or malformed scopes fail closed.
- `_CombinedBe1OwnerFence` routes authorization, BE1 facts, and artifact fences to their respective checks. The auth/facts paths retain their transaction requirement. The local/test composition now shares the same `PilotFakeArtifacts` instance between both owner-fence factory sites. `LocalArtifactStore` remains the source for local image-byte reads.
- The fake artifact fence is process-local and non-durable. It is not a production or cross-process locking guarantee.
- The PostgreSQL stale-artifact case quarantines the output after its descriptor is read and before completion is decided. It proves one loopback stub call, a durable `SUCCEEDED` invocation, no successful job state, no accepted result reference, and a quarantined artifact.
- The stale-facts test changes the BE1 revision after provider success and before the completion fence. The hold-before-send test now asserts rejection before worker/provider invocation when eligibility is revoked.
- Addendum 3 diagnostic wrappers were removed from the PostgreSQL test; the existing ordering wrapper remains.

## Changed implementation files and hashes

| File | SHA-256 |
| --- | --- |
| `backend/src/sketch2life/infrastructure/vision_analysis/pilot_composition.py` | `D79726EAEB949DA5EDBC7C95F5AF5C101A3BFC29A9114A165B35F7EB71C6AE9F` |
| `backend/tests/integration/test_be1_synthetic_pilot_postgres.py` | `25278C81DC842265B2CC73F7E62C8D9CBA4275B87983A3E8AF61DC9918244C7C` |
| `backend/tests/unit/test_be1_pilot_artifact_fence.py` | `364C430A317F569082F2578CA1EB190DB871F9E39D0ACEF6FE5459A309763756` |
| `backend/tests/unit/test_pilot_queue_composition_b1.py` | `5917CAAD6E318765CBA2026CA513D6FAED9C22BD0D739052F5D64E96EBC711F4` (unchanged from Addendum 4 baseline) |

## Test and static-check results

All commands used the repository backend virtual environment. Full stdout/stderr and exit codes are in `.claude/handoff/snapshots/GB1_P2_A4_20261104T142953/logs/`.

| Check | Result |
| --- | --- |
| Artifact-fence + queue-composition unit tests | `27 passed in 0.85s`, exit `0` |
| PostgreSQL success durable before acceptance | `1 passed`, exit `0` |
| PostgreSQL UNKNOWN / replay-after-SENT | `1 passed`, exit `0` |
| PostgreSQL HOLD before send | `1 passed`, exit `0` |
| PostgreSQL stale BE1-facts fence | `1 passed`, exit `0` |
| PostgreSQL stale artifact fence | `1 passed`, exit `0` |
| PostgreSQL concurrent duplicate delivery | `1 passed`, exit `0` |
| Pinned offline regression runner with the three GA1 add-ons | `460 passed in 19.95s`, exit `0` |
| Ruff check on four scoped source/test files | `All checks passed!`, exit `0` |
| Ruff format check on the same files | exit `1`; two files would be reformatted. No whole-file formatting was applied. |
| Strict mypy on the four scoped files | exit `1`; `69 errors in 2 files` (`pilot_composition.py` and the existing PostgreSQL test file); the new artifact-fence unit test has no remaining mypy errors. The production-factory type mismatch found in the first run was fixed by sharing the correctly typed pilot artifact store. |
| Configured strict mypy package run (`packages = ["sketch2life"]`) | exit `1`; `259 errors in 49 files` (`576 source files checked`). |
| `tools/validate_harness.py` | `HARNESS_VALID`, exit `0` |
| `tools/validate_repository_security.py` | `REPOSITORY_SECURITY_VALID`; `6411` publishable files scanned, exit `0` |
| `tools/validate_architecture.py` | `ARCHITECTURE_VALID`, exit `0` |
| `git diff --check` | exit `0`; Git emitted CRLF-to-LF working-copy warnings for pre-existing dirty documentation/approval/status files |

The strict mypy and format-check failures remain visible for independent review; no broad annotation or formatting sweep was made. Earlier failing attempts and their outputs are retained alongside the final runs.

## PostgreSQL boundary and unrun work

The six PostgreSQL nodes ran sequentially against only task-owned DB `s2l_b1_review_20261104_6a1af65b` on local PostgreSQL 17, loopback port `5433`, user `postgres`. Only fixture-owned exact-row cleanup ran. No database was created, reset, migrated, dropped, truncated, or manually cleaned. The connection URL and password are absent from the logs and this report.

No full PostgreSQL suite, Alembic command, Modal/GPU/provider call, external network call, route-surface comparison, historical URL-guard replay, stage, commit, push, merge, reset, stash, or clean was performed. Route-surface comparison remains `NOT DETERMINED`; historical URL-guard replay remains `NOT RUN`.

## Snapshot

Snapshot: `.claude/handoff/snapshots/GB1_P2_A4_20261104T142953/`. Its manifest records the final file hashes, baseline hashes, log hashes, checkout state, and test outcomes. The disposition remains `XONG-CHƯA REVIEW`; independent review is still required.
