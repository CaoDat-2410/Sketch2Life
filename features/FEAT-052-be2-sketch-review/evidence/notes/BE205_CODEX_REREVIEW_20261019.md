# BE2-05 independent re-review — 2026-10-19

**Verdict: CODEX_REREVIEW_PASS_WITH_NOTES — 0 P1 / 0 P2 remaining.**
Verification is complete for RV-CR01–05 and the approved offline component snapshot. The
component remains **NOT_ACCEPTED** pending owner acceptance; BE2-05 remains IN_PROGRESS /
NOT_DONE. This review does not accept runtime, production or cross-feature integration.

## Identity and review inputs

- Worktree: .worktrees/be2-05-sketch-review; branch feature/be2-05-sketch-review.
- HEAD: 58293f1a29ec630e2603c2860b6a2337fadfa713; staged paths: 0.
- Approved plan plan/PLAN_R2_APPROVED.md: SHA256
  ab29530545b94346102bd037822572e483828fa697582e74a74be334cecf0c00.
- Approval approvals/TASK_APPROVAL.md: SHA256
  6ba9f310d0735e6bdfaf80dc8696308989d0ed51012d813c0b991788f2aeeb24.
- Earlier Codex review evidence/notes/BE205_CODEX_REVIEW_20261019.md: SHA256
  0091e8e7fcdab235beee98f28fefc6919decd2b94e43d2c2f721416e4a91194a.
- All 25 files pinned in the review-fix metrics match their recorded SHA256 and byte count.
  Approval, frozen plan, previous review and its probes remain unchanged.

## Findings

All five original findings are closed in the current implementation.

| Finding | Re-review result | Evidence |
|---|---|---|
| RV-CR01 (P1), old PASSED moderation overrode a new BLOCKED policy | **CLOSED.** Moderation identity includes proposal/version/content, pinned artifact hashes and policy version. Commit, moderation and reads select the current-policy assessment; old records remain append-only. | domain/sketch_review.py:300–337; coordination.py; application/services/sketch_review.py:275–286, 362–391, 729–738. Three regressions cover new BLOCKED policy, direct approval and closing an existing approval. |
| RV-CR02 (P2), pre-token authority/policy reads could authorize stale work | **CLOSED.** Early reads are preliminary. Decisive grant, policy and generation reads occur after token capture; final coordinated hold checks their epochs for both review and moderation. | application/services/sketch_review.py:172–224, 253–286, 366–391. Four regressions cover policy disable/grant revoke during the preliminary read on both paths. Independent probes also published changes during the decisive read and observed typed denials with no stored decision. |
| RV-CR03 (P2), a warm cache could return quarantined content | **CLOSED.** Every hit rechecks current eligibility and device binding; stale entries are evicted and recomputed. | infrastructure/sketch_review/fakes.py:169–201, wired by harness.py. Five regressions cover quarantine, consent, policy, context and device changes. The original cache probe now returns no text or asset and records a miss. |
| RV-CR04 (P2), restoring old policy/context values revived an old review | **CLOSED.** Entries pin monotonic policy/context generations. Once a generation moves, restoring field values cannot make the old entry applicable; a fresh review can reopen a nonterminal target. | coordination.py:91–100; application/services/sketch_review.py:290–295, 719–722. Policy and audience restoration probes remain closed without an explicit refresh; a new approval uses a new review identity. |
| RV-CR05 (P2), raw-input fingerprinting rejected equivalent retries | **CLOSED.** Receipt fingerprinting uses the normalized semantic command (NFC/trim and sorted set-valued fields); live binding still runs after a receipt miss. | contracts/schemas/sketch_reviews.py:93–113; application/services/sketch_review.py:166–168. Typed and JSON retries for normalized reason/audience replay the original receipt; genuinely different semantics still return 409. |

The updated contract check compares literal bytes for the shared pack. The chain regression now
checks the complete lifecycle-only mutation allowlist, exactly one consent event and an eligibility
epoch bump. The original 18 new regression tests have meaningful state/output assertions. They were
written after the source fixes and were not run against the overwritten pre-fix bytes; therefore
this review does not claim those new tests were observed failing before the fix. The preserved,
unmodified diagnostic probes did reproduce the original counterexamples on the pre-fix snapshot.

## Independent checks run for this re-review

Environment: Windows 11, existing backend/.venv, CPython 3.12.10; no package installs or network.
PYTHONPATH and MYPYPATH point to this worktree's backend/src. Pytest used separate temporary
directories per suite.

| Check | Result |
|---|---|
| BE2-05 focused suite (7 files) | **117 passed**, 0 skipped |
| Accepted SK1 regression suite | **175 passed**, 0 skipped |
| Contract suite excluding seven Pillow-importing modules | **400 passed**, 3 skipped; seven modules NOT_RUN |
| BE2-02/03 selected unit suite (14 files) | **405 passed**, 0 skipped |
| Ruff from backend/ on 16 source/test files | PASS |
| mypy project configuration and --strict on 9 source files | PASS / PASS |
| validate_harness, validate_repository_security, validate_architecture, validate_skeleton | PASS |
| git diff --check | PASS |
| Pinned snapshot | **25/25 hashes and byte counts match** |

The all-unit run was not repeated during this re-review. Codex parsed the preserved baseline and
executor JUnit files as multisets: baseline **2,429 cases** (2,340 passed / 18 failed / 34 errors /
37 skipped), fixed snapshot **2,533 cases** (2,444 passed / the same 18 failed / 34 errors /
37 skipped). No baseline case is missing or changed; 104 added cases all pass. These existing
collection/runtime failures are unchanged from the baseline and are not a green full-suite claim.

Unmodified Codex probes and fresh real-harness probes independently confirmed closure of all five
counterexamples. Their raw logs and JUnit files are under ignored
evidence/local/codex-rereview-20261019/; focused review artifacts are retained under
evidence/local/codex-rereview-20261019/{access,fence,contracts}/.

## Notes and remaining gates

- The policy/context invalidation generation is organization/session-wide and fails closed:
  unrelated publications may require a fresh review.
- After a moderation-policy change, content remains unavailable until a current-policy assessment
  and current approval exist.
- Cache, coordinator and fencing guarantees are fixture/single-process evidence. Durable database
  fencing and production transaction behavior remain unverified.
- BE1 authority, consent and ticket integration; BE2-14 adopted policy; runtime 01/04; SQL,
  event delivery, HTTP and UI remain outside this checkpoint.
- Seven Pillow-importing contract modules, Studio/runtime, providers, SQL, HTTP routes and UI were
  not run.

No source, tests, approval, frozen plan or Git index were changed during this review. No commit,
push or merge was made. Owner acceptance is the next decision for the offline component checkpoint.
