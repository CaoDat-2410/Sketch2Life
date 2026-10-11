# Feature plan

- Status: APPROVED
- Plan revision: PUB-P1-EXEC-1
- Implementation status: IN_PROGRESS

## Goal

Publish the FEAT-018 Person 2 Task 2 offline WIP checkpoint to
`origin/feature/feat018-p2t2-live-lightning` as the five commits defined by the local draft
plan PUB-P1, without changing the selected original bytes, historical acceptance pins, the
protected FEAT-018 approval history or any live/D6 gate.

## Scope

Baseline `44af2e4f9a75064df327496f033c75f9fe0d0f5d`. The 18 selected originals from the
76-file PUB-P1 inventory are copied byte-for-byte. The other 58 inventory files stay local.

| # | Message | Files |
|---|---|---|
| 1 | `fix(security): guard repository text reads and declare exclusions` | `tools/validate_repository_security.py`, `backend/tests/unit/test_repository_security_validator.py` |
| 2 | `feat(feat018): add offline binding and execution contracts` | `backend/src/sketch2life/contracts/schemas/feat018_live_binding.py`, `backend/src/sketch2life/benchmark/feat018_live_lightning_execution.py`, `backend/src/sketch2life/benchmark/feat018_live_lightning_binding.py`, `backend/tests/unit/test_feat018_live_lightning_execution.py`, `backend/tests/unit/test_feat018_live_lightning_binding.py` |
| 3 | `feat(feat018): add preflight and runtime observations` | `backend/src/sketch2life/contracts/schemas/feat018_live_wiring.py`, `backend/src/sketch2life/benchmark/feat018_live_preflight.py`, `backend/src/sketch2life/benchmark/feat018_live_session_checks.py`, `backend/tests/unit/test_feat018_live_wiring_contracts.py`, `backend/tests/unit/test_feat018_live_preflight.py`, `backend/tests/unit/test_feat018_live_session_checks.py` |
| 4 | `feat(feat018): add guarded SSH development attempt` | `backend/src/sketch2life/infrastructure/ai/feat018_lightning_ssh.py`, `backend/src/sketch2life/interfaces/cli/feat018_lightning_dev_attempt.py`, `backend/tests/unit/test_feat018_lightning_ssh.py`, `backend/tests/unit/test_feat018_lightning_dev_attempt.py` |
| 5 | `docs(feat018): publish offline checkpoint and remaining gates` | `features/FEAT-018-live-image-canvas-flow/plan/P2_T2_LIGHTNING_DEV_ATTEMPT_PLAN_20261006.md`, the derived summary `features/FEAT-018-live-image-canvas-flow/evidence/notes/P2_T2_PUBLICATION_OFFLINE_STATUS_20261011.md`, an entry in `features/FEAT-018-live-image-canvas-flow/evidence/README.md`, and this FEAT-043 folder |

Non-goals: no live/Studio/SSH/provider/model/GPU action, no D6 rebind, no FEAT-018
`approvals/TASK_APPROVAL.md`, `CONTEXT.md`, `DECISIONS.md` or live-plan change, no scanner or
lint/type configuration change, no fix to FEAT-020 code, no dev merge, no force-push.

## Steps

1. Verify the 76 originals, the scanner and exclusion-list identities and the remote tip.
2. Prepare the FEAT-043 records in a separate local preparation area.
3. Create a local preparation branch in a separate publication worktree at the baseline.
4. For commits 1–4, copy the exact files, stage only the planned paths and confirm that the tree
   ID equals the freshly verified intermediate tree. Run the repository-security scanner, then
   commit.
5. For commit 5, add the plan, the summary, the index entry and the public FEAT-043 set. Run
   harness, security, architecture, skeleton and diff checks plus link/path review, then commit.
6. Re-check the remote tip, run the scanner, push `HEAD:refs/heads/feature/feat018-p2t2-live-lightning`
   without force, and verify the remote SHA.
7. Confirm that the originals, historical pins, root checkout and BE2 worktree are unchanged.

## Acceptance criteria

- AC-043-01: each of the five commits contains exactly its planned paths. The selected originals'
  bytes equal the inventory raw SHA-256 values.
- AC-043-02: each commit-1–4 tree equals the freshly verified intermediate tree (same Git tree
  ID). Each has a clean import closure, passing targeted suites and no stray files.
- AC-043-03: the scanner exits 0 on every commit tree and before the push. The owner semantics
  acceptance (decision A) covers exactly the 231 listed baseline exclusions plus the 8 FEAT-043
  `.gitkeep` files. The `mandatory_gate` output line is reported unchanged.
- AC-043-04: architecture, Ruff and mypy are reported as FAIL, matching the measured B1/C1
  findings. The 9 full-suite failures are attributed to the baseline only by exact test name and
  cause. No other failure is accepted.
- AC-043-05: the public documents contain no machine locators or held private content. They keep
  historical and fresh results separate, the Medium residual, POSIX UNVERIFIED and the
  live/security blockers.
- AC-043-06: the remote tip equals the baseline before the push. The push is a fast-forward to the
  fifth commit and the remote SHA is verified afterwards. The root checkout, originals,
  historical pins and BE2 worktree are unchanged.

## Risks and mitigations

- A dirty checkout could mask missing dependencies. Mitigation: exact intermediate trees in
  separate worktrees; imports pinned to the tree under test plus an origin guard; static import
  closure.
- Private paths could leak. Mitigation: derived summary only; quoted approval paths replaced by
  placeholders; scanner run plus a broader manual sweep.
- The approval-file hold: FEAT-018 `approvals/TASK_APPROVAL.md` is not touched; this feature holds
  the publication authority.

## Verification plan

See `evidence/notes/PUBLICATION_VERIFICATION_20261011.md` and
`evidence/notes/SCANNER_FRESH_REVIEW_20261011.md`.

## Evidence plan

Index: `evidence/README.md`. The exact exclusion list is `evidence/metrics/SCANNER_EXCLUSIONS_T1_T4.tsv`.
Post-push identities are reported to the owner and kept in a local record. They cannot be part
of commit 5 itself.
