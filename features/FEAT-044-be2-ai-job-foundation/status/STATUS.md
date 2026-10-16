# Feature status

## Publication instruction —2026-10-16

User authorized committing/pushing the reviewed A17 checkpoint on this feature branch for the
teammate to fetch. This supersedes earlier no-publication instructions only for this checkpoint;
BE2-01 remains IN_PROGRESS, Studio A17-fix01 NOT_RUN, CR01 open, B-12 HANDOFF. No dev merge.
DECISIONS125 and artifacts/BE2_08_14_TEAMMATE_HANDOFF.md record the7/7 allocation and candidate
BE2-12 planning-branch workflow. No additional implementation card is activated.

## Current checkpoint: A17-fix01 received cloud evidence —2026-10-16

**Q01/B6_A17FIX01_CLOUD_RECEIPTS_VERIFIED_PENDING_STUDIO**. Raw cloud archive3bcaa058 is
received/verified:221 B2–B6 +224 Phase A /0 failure/error/skip;43/43 required durable PASS.
Exact runner/test patch applied locally;46/46 files match manifest5b76868d;25 local B6 units,
focused ruff/mypy PASS. Cloud-native proof remains separate from Studio A17-fix01 NOT_RUN.
B6-CR01 FIXED_PENDING_RUNTIME_REVIEW; owner closure pending; BE2-01 IN_PROGRESS; B-12 HANDOFF;
OwnerFence ASSUMED_CONTRACT. Original approvals unchanged; no staging/commit/push/merge/deploy.
Evidence: notes/PHASE_B_B6_A17FIX01_CLOUD_RECEIPT_REVIEW_20261016.md. Older checkpoint routing
below is historical; the next Studio run uses the new A17-fix01 package, not the old R2-only ZIP.

## Local checkpoint decision —2026-10-16

**Q01/B6_CR01_R2_CODE_PACKAGE_REVIEW_PASS_PENDING_RUNTIME (unchanged).** Person 2 allowed local
checkpoint commits of the reviewed state before the r2 Studio run because the Lightning Studio is
not usable (DECISIONS 124). The commits save work; they are not acceptance. Runtime r2 NOT_RUN, B6-CR01
FIXED_PENDING_RUNTIME_REVIEW, owner B6 closure entry pending, BE2-01 IN_PROGRESS, B-12 HANDOFF.
Not every checkpoint commit is test-green: three source commits reproduce Studio snapshots that
failed and were corrected by the next commit. The Studio keeps base 993a26c and source 90724453;
run the existing b6cr01r2 package there, then review and add the results by a follow-up commit.
No push, merge or deploy.

## Codex R2 code/package pre-run review —2026-10-16

**Q01/B6_CR01_R2_CODE_PACKAGE_REVIEW_PASS_PENDING_RUNTIME** on 46-file manifest cb527d7f and ZIP 3a9d6ef2. The reviewed source is runner d42d697c / B6 unit b1d3bced. Independent local21 B6 tests PASS; heldout missing B2-B6/Phase A parameter variants are NOT_RUN; unmapped failure with a missing variant yields FAIL/exit1; collection errors fail closed. R2 package audit PASS: 46/46 current hashes, ZIP4 members, two-file delta from90724453, scratch apply/reverse, shell syntax, source-state pins and exit/skip guards. No actionable finding remains in this focused pre-run scope. Studio runtime is NOT_RUN; CR01 remains FIXED_PENDING_RUNTIME_REVIEW, not closed. See evidence/notes/PHASE_B_B6_CR01_CODEX_PRECOMMIT_REVIEW_20261016.md, latest R2 addendum. Next: run only b6cr01r2 on the approved synthetic Studio, review the source-bound results, then refresh publication documents and dry run. BE2-01 IN_PROGRESS, B-12 HANDOFF; approvals and source/packages unchanged by review. No staging/commit/push/merge/deploy.

Earlier checkpoints follow.


- Updated 2026-10-16, Asia/Saigon. Phase A ACCEPTED_CANDIDATE_FIXTURE.
- ACTIVE (2026-10-16, Claude): **Q01/B6_CR01_R2_PENDING_CODEX_REVIEW**. The Codex pre-commit review
  (notes/PHASE_B_B6_CR01_CODEX_PRECOMMIT_REVIEW_20261016.md) NEEDS_REVISION P2 (missing parameter variant still PASS) on runner 87f0961f is
  corrected: case identities are the full pytest ids (file path relative to backend/, class parts, parameter id) taken from `pytest --collect-only` of the running tree and normalised identically from JUnit; collection is all-or-nothing (exit code, pytest's own total, no case outside the suite files, every file collected). Scratch before/after on the same synthetic JUnit from real collection: the reviewed bytes 87f0961f still report G-01/G-02 PASS with `[120]` or a Phase A variant missing; the current runner reports NOT_RUN for both, PASS when complete and FAIL (exit 1) for a failure plus a missing case. Local: ruff/mypy 0; B6 unit 21 passed; B2-B6 118 passed / 99 PG-Redis skipped (NOT_RUN); Phase A 223 / 1 Pillow skip; fixture d17f58a3; collected identities equal the real JUnit identities (217/217 B2-B6, 224/224 Phase A); runner on real local evidence exit 2 with G-03/G-04 PASS and no FAIL; validators 0. package b6cr01r2 (delta 9d9146c6 from the Studio B6-fix01 snapshot 90724453 -> 46-file manifest cb527d7f, runner d027d05c, ZIP 3a9d6ef2); it supersedes the never-run b6cr01 package (ZIP d0b9f27b, kept unchanged); self-check and 10/10 host simulation PASS. B6-CR01 is
  not closed and r2 has no runtime result; next: Codex review, then Studio run, then a review of
  the fix. Evidence: evidence/notes/PHASE_B_B6_CONFORMANCE_EVIDENCE_20261016.md §12.6; DECISIONS 123. BE2-01 IN_PROGRESS.
- Before r2:
- ACTIVE (2026-10-16, Claude): **Q01/B6_CR01_FIXED_PENDING_RUNTIME_REVIEW**. Person 2 chose to
  harden B6-CR01 (not keep it as a limitation): the durable runner now gates itself: G-01/G-02 aggregate every JUnit case of the B2-B6 and Phase A suites against the test ids pytest collects from the running tree, parameter variants included (failure or a case outside the inventory = FAIL, missing or skipped case = NOT_RUN); W/B patterns must cover every inventory test they name; G-03 needs the complete fixture report (A-01..A-20 PASS, checks > 0, digest); G-04 needs a pinned, well-formed, non-empty manifest that matches the tree and lists every Phase B surface file. Only run_durable_conformance.py and
  test_ai_job_b6_conformance.py changed. Local: ruff/mypy 0; B6 unit 17 passed (11 new CR01 regressions for the review probes P1-P4/P7 and more); B2-B6 114 passed / 99 PG-Redis skipped (NOT_RUN); Phase A 223 / 1 Pillow skip; fixture d17f58a3 unchanged; hardened runner on real local evidence exit 2 (G-03/G-04 PASS, G-01/G-02 and scenarios NOT_RUN, no FAIL); validators 0. package b6cr01 (two-file delta 5e1f6012 from the Studio B6-fix01 snapshot 90724453 -> 46-file manifest a75841e0, runner 5f8858d7, ZIP d0b9f27b); self-check and 9/9 host simulation PASS.
  Next: Studio run (the Studio was stopped: run the reviewed rebuild_be2_env.sh first), then a
  review of the fix before CR01 is closed. The B6 component closure (CLOSE_WITH_NOTES) stands; the
  owner's B6 closure entry in DECISIONS is still pending. The B4-RT01 note/metrics stay in the
  repo (publication plan: 123 paths). Evidence: evidence/notes/PHASE_B_B6_CONFORMANCE_EVIDENCE_20261016.md §12; DECISIONS 122. BE2-01
  IN_PROGRESS.
- Before CR01:
- ACTIVE (2026-10-16, independent closure review — a separate Claude review session, not the
  B6 author; session-separate, not model-separate): **Q01/B6_CLOSED_WITH_NOTES** at component
  scope on manifest 90724453 (re-verified 46/46 OK); Phase B B1–B6 component-closed; B-12 HANDOFF
  (not PASS); OwnerFence ASSUMED_CONTRACT. Findings 0 H / 1 M / 4 L: B6-CR01 (M) the durable runner
  alone is not a self-sufficient gate (unmapped/missing tests, any Phase A JUnit, 0-check fixture
  report or empty manifest still pass) — compensated in the b6fix01 run by the package guards, so
  cite RUNNER_RESULT, never `durable_runner_exit` alone; owner to choose keep-as-limitation or
  harden (new package + Studio run). B6-RT01 CLOSED. Codex B6 review record INCONSISTENT (summary
  PASS/no findings postdates its own RT01 and runner-gap probes) — not counted as a Codex PASS;
  the author pre-run review stays AUTHOR_SELF_REVIEW. Local: B2–B6 103 passed / 99 PG-Redis
  NOT_RUN; Phase A 223/1 Pillow skip; durable runner without services exit 2; validators 0.
  Next: owner records the B6 closure decision, then BE2-01 card review and integration into dev
  per decision 116. **BE2-01 IN_PROGRESS, not DONE**; nothing staged/committed. Evidence:
  evidence/notes/PHASE_B_B6_CLOSURE_REVIEW_20261016.md.
- Before the closure review:
- ACTIVE (2026-10-16, Claude): **Q01/B6_RUNTIME_PASS — PENDING_INDEPENDENT_CLOSURE_REVIEW**.
  B6-fix01 Studio run (USER_REPORTED_REMOTE, 2026-10-15T18:49:30Z = 2026-10-16 01:49:30 Asia/Saigon) PASSED: source b6_snapshot 3940e529 -> 90724453 (46 files verified); B2–B6 202 passed / 0 failed / 0 skipped (all 3 restart tests and the 6 B6 unit tests included); Phase A 224 / 0 skipped; fixture 20 PASS / 215 (d17f58a3, optional HTTP NOT_RUN 1); durable runner exit 0 (required 39/39 PASS, 127 checks / 0 failed; W01..W12 and B-01..B-11 PASS; A-17-http PASS; A-18 DEFERRED; A-02/A-19/A-20 NOT_APPLICABLE; B-12 HANDOFF); every suite/log/outer/Studio exit 0, RUNNER_RESULT=PASS. Source 90724453 is identical locally and on the reported Studio run. The user stopped the Studio after the run (to avoid charges), so its Docker services, network and venv volume may be gone; any later runtime starts with an inventory and recreates nothing without the owner-approved procedure. Next: an
  independent B6/Phase B closure review (Codex when available, or a genuinely separate reviewer
  session) that also reconciles Codex's B6 review record. Evidence: evidence/notes/PHASE_B_B6_CONFORMANCE_EVIDENCE_20261016.md §11. B6 not
  closed; BE2-01 IN_PROGRESS.
- Current source manifest: 90724453b77b0cbf3a5843f1e78165a27155a8f76eb832ca0324e6a753a9dfec (46 files); base 993a26cae78c0a4fe983033f03881838c886b176.
- Before the run:
- ACTIVE (2026-10-16, Claude): **Q01/B6_FIX01_SELF_REVIEWED — READY_FOR_STUDIO_RUN**. B6-fix01
  pre-run review PASS as AUTHOR SELF-REVIEW (Claude; Codex out of tokens, user-directed), not an independent review; package audit and no-service restart-flow probe PASS. Run package b6fix01 (ZIP e813a48b) per the local prompt; lines 157–173 of the restart
  test have still never run on PostgreSQL. An independent review is still required at B6 closure.
  Evidence: evidence/notes/PHASE_B_B6_CONFORMANCE_EVIDENCE_20261016.md §10; DECISIONS 121. B6 not closed; BE2-01 IN_PROGRESS.
- Before the review:
- ACTIVE (2026-10-16, Claude): **Q01/B6_FIX01_CODE_COMPLETE — PENDING_CODEX_REVIEW**.
  B6 Studio run 1 (USER_REPORTED_REMOTE, 2026-10-15T18:19:36Z = 2026-10-16 01:19:36 Asia/Saigon) FAILED: B2–B6 201 passed / 1 failed / 0 skipped; Phase A 224 / 0 skipped; fixture 20 PASS / 215 (d17f58a3); durable runner exit 1 (A-01, A-03..A-17 and A-17-http PASS, 127 checks / 0 failed; FAIL only W02, W08, B-01, B-06); RUNNER_RESULT=FAIL. B6-RT01: the crash child in test_restart_recovery.py sent the Attempt object instead of attempt_id, so the restart lookup raised psycopg 'cannot adapt type Attempt'; all four FAIL rows map to that one test. Fix: one line (`"attempt": attempt.attempt_id`); no product, runner or other
  test change. Local after fix: ruff/mypy 0; B2–B6 103 passed / 99 PG-Redis skipped (NOT_RUN);
  validators 0. package b6fix01 (one-line delta 11e238c7 from the Studio B6 snapshot 3940e529 -> 46-file manifest 90724453, runner 55695aef, ZIP e813a48b); self-check and 9/9 host simulation PASS. Next: Codex review, then the
  user's Studio run, then closure. Evidence: evidence/notes/PHASE_B_B6_CONFORMANCE_EVIDENCE_20261016.md §9. B6 not closed; BE2-01 IN_PROGRESS.
- Before fix01:
- ACTIVE (2026-10-16, Claude): **Q01/B6_CODE_COMPLETE — PENDING_CODEX_REVIEW**. Added
  run_durable_conformance.py (A-01..A-20 mapped; durable scenarios on the real SQL adapter +
  Redis/RQ; §7.1 W01..W12 and B-01..B-12 resolved from the run's own JUnit; exit 0/1/2),
  test_restart_recovery.py (B-01 kill/restart; W01/W02/W06/W08) and B6 runner unit tests. No
  existing file changed. Local: B2–B6 103 passed / 99 PG-Redis skipped (NOT_RUN); B6 unit 6;
  Phase A 223/1 Pillow skip; fixture d17f58a3 unchanged; durable runner exit 2 (required NOT_RUN,
  no FAIL, no fake fallback). package b6 (additive 3-file delta f34d8b1a from fix03 3930046b -> 46-file manifest 3940e529, runner aa9cc843, ZIP 5c2e4641); awaiting Codex review, then user Studio run, then closure.
  Evidence: evidence/notes/PHASE_B_B6_CONFORMANCE_EVIDENCE_20261016.md; B-12 handoff: evidence/notes/PHASE_B_B6_HANDOFF_20261016.md. B6 not closed; BE2-01 IN_PROGRESS.
- Superseded routing:
- ACTIVE **Q01/B6_READY_FOR_HANDOFF**; **B5_CLOSED_REVIEW_PASS**.
  **B5-R01/B5-R02/B5-RT01 CLOSED_B5_SCOPE** after source-bound runtime and focused closure.
- USER_REPORTED_REMOTE fix03 run 2026-10-15T17:37:09Z (2026-10-16 00:37:09 Asia/Saigon): 193 B2-B5 passed / 0 failed / 0 skipped; 224 Phase A passed / 0 skipped; fixture 20 PASS / 215 checks / d17f58a3 unchanged (optional HTTP NOT_RUN 1). All suite/log/outer/Studio exits 0, RUNNER_RESULT=PASS. 43 source files verified as fix03 3930046b; local and reported Studio source match.
- Current source manifest: 3930046b5f04a67b6ff2a52dc70a4f12d5d7a89c2675e149ab654f00da2ab670; base 993a26cae78c0a4fe983033f03881838c886b176.
- Closure review: evidence/notes/PHASE_B_B5_CLOSURE_REVIEW_20261016.md; matching evidence/metrics/PHASE_B_B5_CLOSURE_REVIEW_20261016.json. Prior fix02 failure and local NOT_RUN records remain historical.
- B6 NOT_STARTED: conformance runner, crash-point matrix, Phase A scenarios on SQL, consolidated report and handoff under existing approved Phase B revision 3 B1-B6. Claude first rehydrates read-only from latest handover section AA, reports and stops; B6 implementation follows the agreed separate continuation message, without repeat approval.
- Parent BE2-01 IN_PROGRESS; exactly 14 business cards / WIP 1 / full-card DONE 0. B1-B5 closed at their recorded component scopes, not whole-product completion. OwnerFence ASSUMED_CONTRACT; real P1/P2/P4 integration/B-12, providers, live router and production adoption remain deferred. No other card, FEAT-018/Wan, install, service recreation, staging, commit, push or deploy. Original approvals/plans/ADR unchanged.

- Reset handover prepared at user request: evidence/local/claude/handover/CLAUDE_RESET_HANDOVER_B5_TO_B6_20261016.md; two separate prompts, no B6 execution.

- Workflow agreed (owner-branch-workflow-20261016): task review -> merge dev -> next task branch from dev; no Git operations performed.

## Historical ledger (entries retain their original checkpoint state)

- Housekeeping2026-10-15: user requests prompt Markdown remain local.15prompts+1sessionhandover
  moved to ignored evidence/local/claude/ (INDEX.md),7trackedoldpaths deleted in working tree,
  nothing staged. Active B3 correction uses its new local path. Approval-linked historical
  handoff/approvals/plans/reviews/source unchanged; Q01/B3_NEEDS_REVISION and B4_NOT_STARTED remain.

- Initial review/validation (historical): Claude's existing checks reproduced independently: combined new/targeted regression tests 172 passed + 1 skipped (Pillow absent), runner HTTP 171 checks/0 failures. Additional probes expose one P1, nine P2 and one P3 finding; review NEEDS_REVISION. Executor evidence preserved in PHASE_A_IMPLEMENTATION_EVIDENCE.md; review in evidence/notes/PHASE_A_CODEX_INDEPENDENT_REVIEW_20261014.md. A-20 consumer cross-review/adoption PENDING.
- Q00 (2026-10-14, Claude): R01–R11 fixed with before/after repro, 57 R-regression tests and 27 new negative fixtures; Phase A tests 204 passed + 1 skipped (Pillow), runner 20/20 criteria (217 checks with HTTP), ruff/mypy/harness/architecture/security/skeleton/diff PASS. FIXED_PENDING_REVIEW — evidence/notes/PHASE_A_Q00_FIX_EVIDENCE.md. Review report unchanged.
- Q00 follow-ups (2026-10-14, Claude): R03a/R04a/A18a reproduced and fixed; 19 follow-up regressions; Phase A tests 223 passed + 1 skipped (Pillow), targeted regressions 32 passed, runner 222 checks/0 failed, all repository gates PASS (q00a_run3). FIXED_PENDING_REVIEW — evidence/notes/PHASE_A_Q00_FOLLOWUP_FIX_EVIDENCE.md.
- Q00 acceptance prep (2026-10-14, Claude): handoff synced; gate record evidence/notes/PHASE_A_ACCEPTANCE_GATE_RECORD.md created — P1/P2/P4 and task-owner decisions PENDING_OWNER_DECISION, DATA-24/ProviderCopyLifecycle DEFERRED_TO_OWNING_CARD. Live-route test executed: exit 0, 1 skipped (Pillow) → NOT_RUN/REQUIRES_LIGHTNINGAI_TEST (raw/q00_accept_live_route_attempt.txt). Phase A acceptance PENDING.
- Phase B planning (2026-10-14, Claude, docs only): plan/PHASE_B_PLAN.md (rev 1), plan/PHASE_B_ADR_PROPOSAL.md, plan/PHASE_B_PORT_REVIEW.md prepared — PLANNED/AWAITING_APPROVAL, implementation NOT_STARTED; ADR D1–D6 PROPOSED; P2 Q1–Q5 / P4 Q6–Q7 PENDING_OWNER_DECISION.
- Next action: owner review/acceptance of the single candidate/component packet in plan/PHASE_B_DECISION_RECORD.md rev8 §13 and separate Phase B approval, then Claude B2-only implementation/review. O-08 environment baseline/connections/live-route passed by user report; no repeat setup. Plan rev3/ADR-0018 retained; code NOT_STARTED/UNAPPROVED.
- Phase B plan rev 2 (2026-10-15, Claude, docs only): PB-R01–R06 ADDRESSED_PENDING_REVIEW (evidence/notes/PHASE_B_PLAN_REVISION_EVIDENCE.md); PHASE_B_PLAN.md rev 2 PLANNED/AWAITING_APPROVAL, ADR D1–D7 PROPOSED, port review Q1–Q8 PENDING_OWNER_DECISION; implementation NOT_STARTED.
- Phase B plan rev 3 (2026-10-15, Claude, docs only): PB-C01/PB-C02 ADDRESSED_PENDING_REVIEW (evidence/notes/PHASE_B_PLAN_REV3_EVIDENCE.md); PHASE_B_PLAN.md rev 3 PLANNED/AWAITING_APPROVAL; implementation NOT_STARTED.
- Next gate: genuine candidate checkpoint/component contract directive and separate Phase B approval. Live-route test obligation is satisfied (1 passed,0 skipped, user report2026-10-15). Proposed consolidated answers in decision record rev8 §13; actual role-owner concurrence/production adoption remain deferred unless supplied.
- Execution routing: plan/BE2_ROADMAP.md revision 2 + plan/BE2_EXECUTION_TRACKER.md. ACTIVE Q00; one implementation card/checkpoint at a time, exactly 14 business cards. Old next-step suggestions resolve through this tracker; runtime scope/approval unchanged.
- Interim Q00 independent closure (historical, 2026-10-14, Codex): 236 tests passed + 1 Pillow skip, runner217 checks/0 failures, original11 repros resolved. R03a accepted-quarantined output, R04a nonstring code crash and A18a pre-existing cancel↔purge gap remain OPEN. Evidence: evidence/notes/PHASE_A_Q00_CODEX_CLOSURE_REVIEW_20261014.md. No backend code/approval changed by review.
- Final Q00 code review (2026-10-14, Codex): PASS; R01–R11 original cases and R03a/R04a/A18a CLOSED. Independent combined tests 255 passed + 1 Pillow skip; runner 222 checks/0 failures; original11 and follow-up3 repros clear. Evidence: evidence/notes/PHASE_A_Q00_FINAL_CODE_REVIEW_20261014.md. ACTIVE Q00 pending acceptance gates; approval/approved plan/backend code unchanged by review.
- Gate-delivery review (2026-10-14, Codex): unchanged 24-source snapshot and matching anchors confirmed; three handoff/gate wording clarifications applied. No code finding remains; candidate review/task-owner decision and live-route test still pending. Phase B planning-only prompt prepared at evidence/local/claude/prompts/CLAUDE_PHASE_B_PLANNING_PROMPT.md; ACTIVE Q00, Q01 implementation NOT_STARTED/UNAPPROVED. Review: evidence/notes/Q00_ACCEPTANCE_DELIVERY_REVIEW_20261014.md.
- Phase B independent plan review (2026-10-14, Codex): NEEDS_REVISION, six groups PB-R01–PB-R06 within B1–B6. Original rev1 docs retained; approved Phase A plan/approval and 24-source snapshot unchanged. Review: evidence/notes/PHASE_B_PLAN_CODEX_REVIEW_20261014.md. Q01 plan revision required, implementation NOT_STARTED/UNAPPROVED; ACTIVE Q00 remains.
- Phase B rev2 focused closure (2026-10-15, Codex): original PB-R01–PB-R06 CLOSED_ORIGINAL_PLAN_CASE; overall NEEDS_REVISION only PB-C01 queued dispatch-loss domain delta and PB-C02 explicit queue capability/quarantine event-id carriers. Three rev2 proposals preserved, 24-source/approval/approved-plan snapshot and rev1 archive verified unchanged. Review: evidence/notes/PHASE_B_REV2_CLOSURE_REVIEW_20261015.md. No runtime tests/code/approval.
- Phase B final focused plan review (2026-10-15, Codex): PASS at design-review scope; PB-C01/C02 CLOSED, original six closure retained. Rev3 proposals/archives and24 Phase A frozen source/test/runner/approved-plan/approval hashes verified unchanged; publication ignore/local originals preserved. Q01 PLAN_REVIEW_PASS_WAITING_GATES; ACTIVE Q00 still pending Phase A disposition. Evidence: evidence/notes/PHASE_B_PLAN_FINAL_REVIEW_20261015.md.

- Phase B B1 decision record (2026-10-15, Claude, docs only): plan/PHASE_B_DECISION_RECORD.md rev 1 PENDING_OWNER_DECISION — G1 (gate-record rows reused), G3 D1–D7 + ADR location, G4 Q1–Q8, G5 environment/inventory/secret mechanism/fixture profile, G2 preconditions + sample approval (not an approval). No actual owner input found; B1 diagrams NOT_STARTED. ACTIVE Q00; Phase B code NOT_STARTED/UNAPPROVED.

- B1 scoped Codex review (2026-10-15): decision record rev2 resolves D7/Q8 provenance wording and permits proposed diagrams before adoption. No owner input or new approval; actual P2 integration remains B-12. Plan rev3 unchanged/PASS; diagram draft NOT_STARTED, next prompt above. Review evidence/notes/PHASE_B_B1_DECISION_RECORD_REVIEW_20261015.md; source24 verified with existing EOF disposition only.

- Phase B B1 proposed sequences (2026-10-15, Claude, docs only): evidence/notes/PHASE_B_B1_PROPOSED_SEQUENCES.md — seven flows + crash-window table, PROPOSED/NOT_ADOPTED/NOT_RUNTIME_EVIDENCE, owner fence ASSUMED_CONTRACT. Docs checks: security/diff exit 0; harness exit 1 only for merged BE1 FEAT-045/046/047 missing evidence/screenshots+metrics (not FEAT-044). B1 exit PENDING actual decisions/adopted ADR; G1–G5 pending; ACTIVE Q00; Phase B code NOT_STARTED/UNAPPROVED.

- B1 sequence scoped re-review (2026-10-15, Codex): draft rev2 PASS after local diagram corrections; seven flows/twelve crash windows retained. Current harness/security/diff PASS; prior harness failure historical after separate placeholder fix. Decision record rev3 refreshes ADR number proposal0018 (BE1 uses0016/0017) and prepared status; no actual owner decision added. B1 exit pending, runtime/render NOT_RUN; source24 freeze retains EOF disposition only. Evidence diagram §12 and metrics/PHASE_B_B1_SEQUENCE_REVIEW_CHECKS_20261015.json.

- Owner selection/inventory (2026-10-15): architecture D1–D7 and current fixture profile selected; ADR-0018, decision record rev4 O-01/O-02. Local Windows inventory completed, target Linux/PostgreSQL17/Redis NOT_VERIFIED (service metadata PostgreSQL18 only; Docker engines unavailable; Pillow absent). Next handoff evidence/local/claude/prompts/CLAUDE_PHASE_B_ENVIRONMENT_INVENTORY_PROMPT.md. Phase A acceptance, remaining contract details and Phase B code approval stay pending.

- Environment O-03: new CPU Studio selected, working name sketch2life-backend-test; creation pending user dashboard access (no Lightning tools/session access here). Inventory, PostgreSQL17/Redis setup and remaining Phase B gates pending. Decision record rev5; implementation remains NOT_STARTED/UNAPPROVED.

- G5 remote inventory O-04: Studio created reported; Linux/Docker daemon available from user output. Host Python3.14.7 unsupported; Python3.12 runner, PostgreSQL17/Redis, dependency inventory and Phase A test pending. Decision record rev6; Phase B implementation still NOT_STARTED/UNAPPROVED.

- G5 O-05: user reports Python3.12.15 Docker runner success. Prepared PostgreSQL17/Redis8 first-run service bootstrap in evidence/notes/PHASE_B_ENVIRONMENT_RECORD.md, not yet executed/reported. Source branch/commit, service/authenticated connection, package inventory and G1 test remain pending; no implementation approval.

- O-06: user-reported PostgreSQL17.11/Redis healthy; runnerPython3.12.15 verified earlier. Source checkout/commit unresolved (Git invoked outside repo). Existing services retained; next source verification then package/authenticated-connection/G1 test proof. Decision record rev7; implementation remains unapproved.

- O-07 source verified by user: feature/be2-01-ai-job-foundation at993a26c (shallow). Preparing runner dependency install plus authenticated service checks/live-route test; outcomes pending. Remaining Phase A acceptance/contract/code gates unchanged.

- O-08 baseline: reported package versions within manifest bounds, authenticated PostgreSQL17.11/Redis8.10.2 connections PASS; live-route1 passed,0 skipped in2.72s. Evidence metrics/PHASE_B_LIGHTNING_ENVIRONMENT_20261015.json. Full Phase B fault/concurrency/migration proof and owner/code approvals remain pending; no parent-card DONE.

- O-09 actual approval2026-10-15: Phase A candidate/fixture ACCEPTED, rev8 §13 component packet
  accepted as PROJECT_OWNER_DIRECTIVE, Phase B planrev3 B1–B6 APPROVED. B1 component closure and
  B2 handoff complete. Current state is the summary above, superseding historical pending gates.

- Phase B B2 (2026-10-15, Claude): B2_CODE_COMPLETE — PostgreSQL checks NOT_RUN (REQUIRES_STUDIO_RUN). Schema `ai_jobs` + Alembic branch `ai_jobs` + B2 tests; local offline checks 6 passed, Phase A 223 passed/1 Pillow skip, ruff/mypy/harness/architecture/security/skeleton/diff exit 0 (pre-existing env.py I001). Studio run pending (evidence/notes/PHASE_B_B2_SCHEMA_MIGRATION_EVIDENCE.md). B3 NOT_STARTED.

- Independent B2 review2026-10-15: NEEDS_REVISION B2-R01/R02. Contract/service accepts120-character
  job_type/purpose_code; current SQL columns80. Mocked failed tests yield runnerexit0; current
  apply-once guard also blocks retry. Correct these within B2, then run Studio; no new scope/approval.

- Session handover (2026-10-15, Claude, docs only): `evidence/local/claude/handover/CLAUDE_SESSION_HANDOVER_20261015.md` + `evidence/local/claude/prompts/CLAUDE_NEW_SESSION_START_20261015.md`. No progress change: Q01/B2 NEEDS_REVISION, PostgreSQL NOT_RUN, B3 NOT_STARTED.

- User-requested handover wording correction (2026-10-15, Codex): both documents corrected per
  the four review points; no state/approval/source change. Q01/B2 NEEDS_REVISION and B3 NOT_STARTED.

- User-authorized Codex correction2026-10-15: B2-R01/R02 fixed with independent localcodePASS,
  new verified package and refreshed takeover docs;10PGchecks NOT_RUN. No B3/backend scope expansion
  or install/service mutation/provider/commit/push/deploy. Current top summary supersedes old pending entries.

- Studio B2 finalreview2026-10-15: PASS_B2_SCHEMA_MIGRATION, R01/R02CLOSED; correctsource
  18B2passed/0skip and224PhaseApassed/0skip USER_REPORTED_REMOTE. NextB3readycodeNOT_STARTED.
  FullB01restart/B11conformance/B12integration remainpending; no newapproval/card/code/deploy.

- User-requested two-step handover2026-10-15: waiting for Claude availability, no B3 code now.
  Step 1 bootstrap is read-only takeover/report then STOP; user sends step 2 in the same new
  session to implement approved B3 only, review before B4. No new gate/approval/card; existing
  B2 closure and ACTIVE Q01/B3_READY_FOR_IMPLEMENTATION/code NOT_STARTED are unchanged.

- Phase B B3 (2026-10-15, Claude): B3_CODE_COMPLETE — PostgreSQL NOT_RUN (REQUIRES_STUDIO_RUN).
  Repository/UoW + Δ1–Δ5 + ASSUMED_CONTRACT fixture; Phase A 223 passed/1 Pillow skip, runner
  digest unchanged, 22 B2/B3 offline passed, 47 PostgreSQL skipped = NOT_RUN, lint/type/
  harness/architecture/security/skeleton/diff exit0. Studio package prepared; no B4/commit/push/deploy.


- B5 fix02 Codex takeover 2026-10-15: bounded R01/R02 corrections reviewed locally; current
  Q01/B5_FIXED_PENDING_RUNTIME_REVIEW. Fix01 package superseded, preserved as history. User Studio fix02 run then focused
  closure, B6 explicit continuation only. Review evidence/notes/PHASE_B_B5_FIX02_CODEX_REVIEW_20261015.md.


## Codex CR01 pre-commit snapshot review —2026-10-16

Review of runner 87f0961f / B6 unit f07a1f4c: NEEDS_REVISION for the CR01 hardening snapshot. Missing parametrized testcase [120] while retaining [81] still yields G-01 PASS (211 of 212 collected B2-B6 cases). Compare full collected testcase identities, including parameter IDs; add focused regressions. Direct local B6 units16 PASS, ruff/mypy/harness/architecture/security/diff PASS; PostgreSQL/Redis NOT_RUN locally. The older 90724453 runtime and publication dry run do not cover these two changed files. This is a source-bound reviewer observation, not an owner decision or a new task/approval. See evidence/notes/PHASE_B_B6_CR01_CODEX_PRECOMMIT_REVIEW_20261016.md. Later source requires rechecking. Same approved Phase B scope; BE2-01 IN_PROGRESS, B-12 HANDOFF. No source/package/Git mutation by this review.


## Codex focused CR01 re-review —2026-10-16

PASS_LOCAL_PENDING_FINAL_PACKAGE_AND_RUNTIME on runner d42d697c and B6 unit b1d3bced. The earlier parameter-variant P2 is resolved: heldout B2-B6 and Phase A missing variants produce NOT_RUN; unmapped failure plus a missing variant produces FAIL/exit1; collection error fails closed. Direct local21 B6 units PASS, ruff/mypy PASS. Source hashes stayed stable through the probes. See evidence/notes/PHASE_B_B6_CR01_CODEX_PRECOMMIT_REVIEW_20261016.md (latest addendum) and ignored evidence/local/b6-cr01-codex-rereview-20261016/. Earlier ZIP d0b9f27b/a75841e0 package audit PASS applies to its immutable bytes; author edits advanced source beyond it. Final source-bound package/Studio result and refreshed publication dry run remain required. Runtime NOT_RUN locally; same approved B6 scope, BE2-01 IN_PROGRESS, B-12 HANDOFF. No code/approval/Git operation by this review.
