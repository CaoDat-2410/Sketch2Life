# BE2 planning evidence index

> Publication selection (2026-10-15): notes/PUBLICATION_SELECTION_20261015.md defines GitHub/local disposition. Phase A run1/run2 and Q00-follow-up initial/run2 receipts/metadata remain at their original local paths with names/hashes recorded there; clean run3/final, reviews and repros remain publishable. The copied installed-RQ extract is local-only. Historical intermediate references describe local evidence.

- Scope: source audit, implementation planning and static documentation/repository validation, 2026-10-14, Asia/Saigon.
- Baseline: branch `feature/be2-01-ai-job-foundation`, commit `b9204d8c9eb4f8a1ee6d4db4de5ee23672e0392c`.
- `notes/SOURCE_AUDIT.md`: read-only findings, source locations, legacy gaps and environment limits.
- `notes/VALIDATION.md`: actual check interpretation and independent review outcome.
- `metrics/PLANNING_CHECKS.json`: commands/results/timestamps and source hashes.
- `raw/planning_*.txt`: sanitized receipts from existing repository validators.
- `notes/INDEPENDENT_REVIEW.md`: independent comparison of plan with FEAT-040/SRS.
- `notes/CLAUDE_HANDOFF_REVIEW.md`: executor preference, six-step prompt review, clarified idempotency/fixture boundaries and handoff checks.

## Phase A implementation (2026-10-14, Claude)

- `notes/PHASE_A_IMPLEMENTATION_EVIDENCE.md`: commands, environment, A-01..A-20 results, fixed failures, NOT_RUN items.
- `notes/PHASE_A_HANDOFF.md`: file map, implemented transition table, P1/P2/P4 contract pack, adoption notes.
- `metrics/phase_a_run{1,2,3}_checks.json` + `raw/phase_a_run{1,2,3}_*.txt`: sanitized receipts (run 3 final, runs 1–2 preserved failures).
- `raw/phase_a_run3_runner_report*.json`: offline runner reports. Fixtures live in `../fixtures/` with `MANIFEST.json`.

- `notes/PHASE_A_Q00_FIX_EVIDENCE.md`: R01–R11 corrections (before/after repro `raw/q00_repro_{before,after}.json`, script `raw/q00_repro_source.txt`), receipts `raw/q00_*.txt`, `metrics/q00_checks.json`. Review report unchanged; closure pending.

- `notes/PHASE_A_Q00_FOLLOWUP_FIX_EVIDENCE.md`: R03a/R04a/A18a follow-ups (repro `raw/q00a_repro_{before,after}.json`, original rerun `raw/q00a_original_r01_r11_repro.json`, receipts `raw/q00a*_*.txt`, final `metrics/q00a_run3_checks.json`). Reviews unchanged; closure pending.

Phase A proves fake/contract semantics only. Durable recovery, live providers, actual purge and visual/device acceptance have no pass claim here.

## Independent implementation review (2026-10-14, Codex)

- `notes/PHASE_A_CODEX_INDEPENDENT_REVIEW_20261014.md`: NEEDS_REVISION, R01–R11 with source locations/scenarios/fix expectations; separate from earlier independent planning review.
- `raw/codex_review_pytest.txt`, `codex_review_runner.txt`, `codex_review_runner_report.json`: reproduced existing checks (172 pass/1 skip, 171 runner checks).
- `raw/codex_review_probes.json`, `codex_review_boundary_probes.json`: fresh synthetic reproductions not covered by current fixtures.
- `metrics/codex_review_*.json`, `metrics/CODEX_INDEPENDENT_REVIEW_20261014.json`: command/environment/outputs and reviewed source hashes.
- `../plan/CLAUDE_PHASE_A_FIX_PROMPT.md`: remediation handoff; code remains for Claude to fix within approved Phase A.

## Roadmap revision 2 (2026-10-14)

- `../plan/BE2_ROADMAP.md`: current complete task analysis/queue/exit/scope-change rules.
- `../plan/BE2_EXECUTION_TRACKER.md`: active Q00, current authorization, per-card readiness, exact waiting gates and substitution/later register.
- `notes/BE2_ROADMAP_REV1_ARCHIVE_20261014.md`: original roadmap preserved before replacement.
- `notes/BE2_ROADMAP_REV2_VALIDATION_20261014.md`: independent planning review and actual documentation/repository validation.
- `metrics/BE2_ROADMAP_REV2_CHECKS.json`, `raw/roadmap_rev2_*.txt`: commands/results, unchanged code/approval/plan/source checks and hashes.
## Latest Q00 independent closure review (2026-10-14)

- notes/PHASE_A_Q00_CODEX_CLOSURE_REVIEW_20261014.md: original11 repros resolved; overall NEEDS_REVISION for R03a/R04a/A18a, with source/observed behavior/exit.
- raw/codex_q00_closure_pytest.txt, runner/report, original_repro.json: actual independent reruns236 passed/1 skipped and runner217 checks.
- raw/codex_q00_closure_followup_probes.json and followup_probe_source.txt: fresh targeted observations; A18a explicitly pre-existing relative to Q00.
- metrics/codex_q00_closure_*.json and CODEX_Q00_CLOSURE_REVIEW_20261014.json: commands/environment/source snapshot/gates.
- ../plan/CLAUDE_Q00_FOLLOWUP_FIX_PROMPT.md: only three remaining corrections within Phase A approval; original review preserved.

## Final Q00 code review (2026-10-14, Codex)

This is the latest review; preceding pending/revision entries describe earlier checkpoints.

- `notes/PHASE_A_Q00_FINAL_CODE_REVIEW_20261014.md`: PASS at fake/contract scope; original11 and R03a/R04a/A18a CLOSED; adoption/Pillow/Phase B gates retained.
- `raw/codex_q00a_final_pytest.txt`: independently reproduced 255 passed/1 Pillow skip.
- `raw/codex_q00a_final_runner.txt`, `raw/codex_q00a_final_runner_report.json`: 222 checks/0 failures.
- `raw/codex_q00a_final_original_repro.{txt,json}`, `raw/codex_q00a_final_followup_repro.{txt,json}`: unchanged executor repros rerun independently, 11+3 defects absent.
- `metrics/codex_q00a_final_*.json`, `metrics/CODEX_Q00_FINAL_CODE_REVIEW_20261014.json`: actual commands/receipts, reviewed source hashes, unchanged approval/plan and remaining gates.
- `raw/codex_q00a_final_{harness,security,diff}.txt`: final documentation/repository gates. Backend implementation remains Claude's; no code/approval/runtime change by Codex review.

## Q00 acceptance prompt clarification (2026-10-14)

- `../plan/CLAUDE_Q00_ACCEPTANCE_PROMPT.md`: concrete next Claude work order; candidate cross-review/handoff and one remaining test, no backend/runtime scope.
- `metrics/Q00_ACCEPTANCE_PROMPT_CHECKS_20261014.json`, `raw/q00_acceptance_prompt_{harness,security,diff}.txt`: prompt/tracker documentation verification and unchanged reviewed-source/approval/plan check.
- `notes/PHASE_A_ACCEPTANCE_GATE_RECORD.md`: prepared 2026-10-14 by Claude for owner review — consumer/contract/evidence-hash table; all decisions PENDING_OWNER_DECISION (not an approval). Live-route attempt `raw/q00_accept_live_route_attempt.txt` + `metrics/q00_accept_live_route_attempt.json`: 1 skipped → NOT_RUN.

## Acceptance delivery review and Phase B planning preparation (2026-10-14)

- `notes/Q00_ACCEPTANCE_DELIVERY_REVIEW_20261014.md`: independent source/evidence verification, actual NOT_RUN and small handoff clarifications; candidate/owner decisions remain pending.
- `../plan/CLAUDE_PHASE_B_PLANNING_PROMPT.md`: next documentation-only Claude prompt for proposed plan/ADR/port questions, with no runtime authorization.
- `metrics/Q00_DELIVERY_REVIEW_CHECKS_20261014.json`, `raw/q00_delivery_review_{harness,security,diff}.txt`: documentation validation/frozen-source proof.
- Phase B planning (2026-10-14, Claude): `../plan/PHASE_B_PLAN.md` rev 1, `../plan/PHASE_B_ADR_PROPOSAL.md`, `../plan/PHASE_B_PORT_REVIEW.md` — PLANNED/PROPOSED/PENDING, not approved or adopted. Docs-check receipts `raw/phase_b_plan_docs_{harness,security,diff_check}.txt`, `metrics/phase_b_plan_docs_checks.json`.

## Independent Phase B plan review (revision 1, 2026-10-14)

- `notes/PHASE_B_PLAN_CODEX_REVIEW_20261014.md`: NEEDS_REVISION, PB-R01–PB-R06 with exact locations/counterexamples/minimal corrections/acceptance; does not reopen Phase A code review.
- `../plan/CLAUDE_PHASE_B_PLAN_REVISION_PROMPT.md`: bounded next Claude documentation turn to produce rev2, no code/runtime/approval.
- `raw/phase_b_review_rq_source.txt`: read-only installed RQ2.11.0 registry source supporting abandoned-worker recovery analysis, not a runtime reproduction.
- `metrics/PHASE_B_PLAN_REVIEW_CHECKS_20261014.json`, `raw/phase_b_codex_review_{harness,security,diff}.txt`: review-snapshot/source hashes and documentation validation.
- Official PostgreSQL17 constraints/isolation references are linked beside their claims in the review. Runtime tests NOT_RUN; no Phase B implementation exists.

- Phase B plan revision 2 (2026-10-15, Claude): `notes/PHASE_B_PLAN_REVISION_EVIDENCE.md` (PB-R01–R06 mapping, ADDRESSED_PENDING_REVIEW), rev 1 archive `notes/PHASE_B_PLAN_REV1_ARCHIVE_20261014.md`; docs-check receipts `raw/phase_b_plan_rev2_docs_*.txt`, `metrics/phase_b_plan_rev2_docs_checks.json`, frozen-hash check `metrics/phase_b_plan_rev2_frozen_hashes.json`.

## Focused Phase B revision2 closure (2026-10-15)

- `notes/PHASE_B_REV2_CLOSURE_REVIEW_20261015.md`: all original six plan cases closed, two grouped contract deltas PB-C01/C02 remain; no runtime/owner adoption claim.
- `../plan/CLAUDE_PHASE_B_REV2_COMPLETION_PROMPT.md`: only two documentation corrections to produce rev3; unchanged B1–B6/14-card scope.
- `metrics/PHASE_B_REV2_CLOSURE_REVIEW_CHECKS_20261015.json`, `raw/phase_b_rev2_codex_{harness,security,diff}.txt`: frozen rev2/source/archive snapshots and final documentation gates.
- Current model queued-failure guard and current queue/artifact port signatures provide the exact static counterexamples, referenced in the review. Phase B runtime tests NOT_RUN.

- Phase B plan revision 3 (2026-10-15, Claude): `notes/PHASE_B_PLAN_REV3_EVIDENCE.md` (PB-C01/PB-C02 mapping, ADDRESSED_PENDING_REVIEW), rev 2 archive `notes/PHASE_B_PLAN_REV2_ARCHIVE_20261015.md`; docs-check receipts `raw/phase_b_plan_rev3_docs_*.txt`, `metrics/phase_b_plan_rev3_docs_checks.json`, frozen-hash check `metrics/phase_b_plan_rev3_frozen_hashes.json`.

## Final Phase B revision3 focused plan review (2026-10-15)

- `notes/PHASE_B_PLAN_FINAL_REVIEW_20261015.md`: PASS at design-review scope, PB-C01/C02 CLOSED and original cases retained; exact implementation logging verification and remaining owner/runtime gates.
- `metrics/PHASE_B_PLAN_REV3_FINAL_REVIEW_CHECKS_20261015.json`: reviewed rev3/archives/Phase A source hashes and actual docs-check results.
- `local/phase-b-rev3-review-20261015/`: repeated individual validation receipts retained locally under the existing publication policy.
- `../plan/CLAUDE_PHASE_B_B1_GATE_PROMPT.md`: next documentation-only gate/decision work order; no code or approval.
- The final review and B1 prompt/summary are subsequent publication candidates added to the operator allowlist;61 intermediate diagnostics remain local.
