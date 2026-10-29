# B5-RT01: fix02 runtime review and one-test fix03 correction — 2026-10-16

- Result: **PASS_CODE_AND_PACKAGE_REVIEW** for the test-fixture correction.
- State: **Q01/B5_FIXED_PENDING_RUNTIME_REVIEW**; B5-RT01 **FIXED_PENDING_RUNTIME_REVIEW**.
  B5 is not closed; B6 **NOT_STARTED**. Same approved Phase B revision 3 scope, 14 cards,
  WIP 1, full-card DONE 0, parent BE2-01 IN_PROGRESS. No new business card or approval.
- Codex continues the user's authorized temporary B5 takeover and handover. Production
  source, approvals, approved plans, ADR, schema and frozen packages remain unchanged.

## Actual Studio result, not a successful whole-suite run

The supplied full output identifies exact fix02 manifest
`cf196e845d30179c2aa2b89e09970ccaf83777aa6d90fac7b29f68d091ad60d0`,
delta `3049e1bb`, base `993a26c`, 43 verified source files before the suites, and
`source_state=b5fix02_snapshot_verify_only`. Provenance is **USER_REPORTED_REMOTE**;
Codex has no direct Studio access. Run UTC 2026-10-15 17:12:17 corresponds to
2026-10-16 00:12:17 Asia/Saigon. Reported receipt directory, feature-relative:
`evidence/local/b5fix02-runtime-20261015/run-20261015T171217Z-7034/`.

| Actual reported result | Value |
|---|---|
| B2–B5 combined suite | **192 passed, 1 failed, 0 skipped**, 193 collected |
| Phase A | **224 passed, 0 skipped** |
| Fixture runner | 20 PASS, 215 checks, zero failed; optional HTTP NOT_RUN 1 |
| Fixture digest | `d17f58a3c9c535d45a2fe03ed0c1edad42a565422725aede21b22ba45af41f68` |
| B2–B5 suite / log exits | **1 / 0** |
| Phase A / log exits | 0 / 0 |
| Fixture / log exits | 0 / 0 |
| Outer / Studio command | **1 / 1**, RUNNER_RESULT=FAIL |

All 32 B5 PostgreSQL/Redis cases passed in that failed whole-suite run: 11 audit-durability,
6 capability, 8 completion-recovery and 7 notice-coverage. This includes the R01/R02
regressions. Retain those actual passes without treating B5 as closed or calling the whole
suite 193 PASS. There were 107 Alembic deprecation warnings; they are not the failing result.
The earlier missing-network/Docker-125 attempt is historical; services now ran these tests.

## B5-RT01 diagnosis and exact bounded correction

Only `test_enqueue_then_crash_before_mark_republishes_same_attempt_and_start_dedups`
failed, at the original child-published capability's `start_attempt` call. B5 updated shared
test wiring to an attempt-bound `FakeWorkerCapability` issuer/verifier with an in-memory
claims dictionary. The spawned dispatcher has its own dictionary. Its token is absent from
the parent rig's verifier; the parent's later republish registers only its own token.
`WORKER_CAPABILITY_INVALID` is therefore the correct verification response. This is a
cross-process test-fixture mismatch introduced by the B5 caller updates, not a demonstrated
production authentication defect, intermittent DB failure or missing dependency.

Exactly one file changes relative to fix02:
`backend/tests/integration/ai_jobs/test_dispatch_recovery.py`.
It uses the existing HMAC implementation only for this crash-window test: one random
32-byte `CapabilityKey` is generated in the parent, passed to the dispatcher through the
spawn pipe, and used by the child issuer and parent issuer/verifier. The key is not saved,
logged or sent in Redis/RQ payloads, SQL or environment variables. RQ carries the transient
capability as already approved. Production code and the general fake remain unchanged.

The test still starts with the **original child-published token** and asserts that the
parent's republished delivery returns `DUPLICATE_DELIVERY`. It preserves exit 17 after real
enqueue, no acknowledgement before crash, lease expiry/generation takeover, same message
and attempt, one attempt, and dispatch count 1. It does not substitute a parent-minted token
for the first delivery, weaken verification, skip the test or increase capability TTL.
The parent clock advances 10 seconds for the existing lease; existing HMAC TTL is 40 seconds.
Import grouping within this same file was adjusted for Ruff; no other test behavior changes.

Before SHA-256: `1f405ef1a587613919f7c9b7644c71c24b2e66e27cd135b3fb36cc0511c24232`.
After SHA-256: `0f775939eefeb5e58a831b223cc4e6280a34ec8befe7b3d0757468615281115d`.

## Direct local proof and its limits

Two independent probes execute real multiprocessing **spawn** and the actual application
service with an in-memory repository. Before: the original child fake token is unknown to
the parent and the service returns WORKER_CAPABILITY_INVALID. After: the original child HMAC
token verifies and starts after the lease wait; the parent's republished token returns
DUPLICATE_DELIVERY, and only one attempt remains. Tampering, a wrong key, a wrong attempt and
expiry remain denied. A probe also passes the `CapabilityKey` object through spawn just as
the corrected test does. Reports contain sanitized booleans, not keys or bearer strings.
These are actual process/service proofs, not PostgreSQL/Redis reproductions of the test.

| Direct local check on fix03 | Result |
|---|---|
| B2–B5 combined runner-selected suite | **97 passed / 96 skipped**, 193 collected, exit 0; skipped runtime NOT_RUN |
| Affected SQL/Redis test file | 11 collected, all NOT_RUN locally; not reported as 11 PASS |
| Ruff and mypy | PASS on the one changed test |
| Harness/security/architecture/diff | exit 0; final documentation check receipts also retained |
| Package | exact fix02 rebuilt and all 43 hashes verified; one-file delta, forward/reverse/repeat proofs PASS |
| Host runner simulation | **11/11 PASS**, Git apply/diff real in scratch, Docker stub only |

Phase A source is unchanged. Prior direct local 223 PASS / 1 missing-Pillow skip and actual
fix02 Studio 224 PASS / 0 skips are retained with their attribution; no redundant Phase A
suite was run for this single integration-test fixture change. Corrected fix03 PostgreSQL/
Redis runtime remains **NOT_RUN** until the user supplies the next Studio run.

## Reviewed fix03 transport

Folder: `evidence/local/b5fix03-studio-package-20261016/`.

| Artifact | SHA-256 |
|---|---|
| Exact input fix02 manifest | `cf196e845d30179c2aa2b89e09970ccaf83777aa6d90fac7b29f68d091ad60d0` |
| `b5fix03_delta.patch` | `d1f69a453a978c63ee2e077bb100c5900bf52ca81dd3eb8c01444bb779f22cd3` |
| `b5fix03_source.sha256` | `3930046b5f04a67b6ff2a52dc70a4f12d5d7a89c2675e149ab654f00da2ab670` |
| `run_b5fix03_on_studio.sh` | `e31676372e7d461387a660e80ed164728c8226590eb0b1a8c13ffbaf406a984f` |
| `be2-b5-fix03-studio-20261016.zip` | `ff4b2484691babf0a30fde656f4d75793b0174855f8cf7671210146b2b4bb4f1` |

The ZIP has four byte-identical operator files. It accepts exact fix02 source from the failed
run, applies a **one-file** delta and verifies all 43 output hashes. Exact fix03 can retry in
verify-only mode. Unknown edits, older B4/B5/fix01 snapshots and corrupted delta are refused
before Docker. Docker 125 propagates and the applied fix03 source can retry. No reset, clean,
force apply or deletion is used. All 54 older package files remain byte-identical, including
fix02. Scratch Git is independent, uses write-tree without commits, and remains ignored.
Of 547 protected source/test/fixture/approval/plan/package paths, only the declared test
changed; 546 and the real Git index remain unchanged.

## Next and handover

Use ignored operator `evidence/local/claude/prompts/B5_FIX03_STUDIO_RUN_20261016.md` to upload
the uniquely named ZIP into `$HOME/be2-b5-fix03-package/`, verify its checksum and run the
new runner on the same Studio. No environment rebuild or reinstall is needed for this test
correction. Keep the Studio running; report prerequisites rather than resetting resources.
Expected, not observed: **193 B2–B5 and 224 Phase A PASS, zero suite skips**, all suite/log/
outer/Studio exits zero, fixture digest unchanged. Then focused review can close B5.

Claude resumes read-only from full handover **§Z**, concise Codex handover, actual review,
source manifest and unchanged approval. Do not redo B5 or execute superseded prompts. B6
is not started and requires explicit continuation after B5 closure. OwnerFence remains
ASSUMED_CONTRACT; no real provider, production wiring, P1/P2/P4 integration or other card is
claimed. No installation, service recreation, staging, commit, push or deploy was performed.

Raw user output, before source, checks and builder/host proofs remain ignored in
`evidence/local/b5-fix03-20261016/`. Independent spawn proof is in
`evidence/local/b5-worker-fixture-20261016/security/`. Matching public metrics contain hashes,
attribution, preservation and final document validation; prompts and handovers stay local.
