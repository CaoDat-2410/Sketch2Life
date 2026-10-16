# BE2-02 C1 — final R04 code review, 2026-10-16

**CODE_REVIEW_PASS_WITH_NOTES.** R04 is CLOSED_C1_COMPONENT_SCOPE; all six findings
C1-R01–R06 are now closed for the approved offline component scope. No new blocking
defect was found in this narrow follow-up. This is a code-review disposition, not
owner acceptance, all-acceptance PASS, full-card DONE or authorization to publish.

## Identity and scope

- Branch/worktree: `feature/be2-02-vision-correction` /
  `.worktrees/be2-02-vision-correction`.
- HEAD/base: `6dcc57ee0b3d053f071c8c92e72aaaee2e98d899`; staged paths 0.
- Only `domain/vision_analysis.py` and `test_vision_analysis_review_fixes.py` differ
  from the previous Codex re-review's 19-file source/test manifest. Other 17 match.
- Domain SHA256: `6b488d6a0f1942c10400c6731531a18c61c0aea5d818a4bf108b66e9fef28b9c`.
- Regression SHA256: `cc3f777f2c7d48733b9c2444fc0dc3d496fc8d914a0df4469dae2eabb54ebd3d`.
- Approval and approved plan unchanged; plan SHA256 remains
  `f4733c88797edbcce225ecd63700634f929ca75789362c7f3a58a2b57f19df30`.
- Existing Python 3.12.10 with source imports pinned to this worktree; no installs,
  network/model/service/Studio runs. Review changed documentation/evidence only.

## Why R04 closes

`observation_bounds_violation` now uses `if ref is not None` for optional action
references and `_OBSERVATION_REF.fullmatch` in the shared reference loop. The empty
string is validated and rejected; a final newline no longer passes. `None`, valid
refs and the accepted length/count boundaries retain their prior behavior. No
reference is stripped/dropped, no output schema is loosened and no post-commit
serialization exception is used to conceal partial success.

Root inspected the guard and new regression, then independently ran the entire
focused suite and the six original promoted service probes. A delegated domain
reviewer additionally ran 24 independent assertions: ten newline positions and
both empty optional references fail OUTPUT_MALFORMED before storage; positive
None/valid/120/256 cases project and support CMD-34 200 plus replay 200; 121/257
cases reject safely. Invalid cases leave no head, observation, provider result,
correction, receipt or invalidation. These facts close the two remaining R04
bypasses; the prior five finding closures remain applicable to the unchanged code.

## Actual verification

| Check | Result |
|---|---|
| Root eight-file focused suite | 233 collected: **232 passed, 1 skipped**, 0 failures/errors |
| Included new R04 follow-up regression | **19 passed** (subset of the 232, not additive) |
| Root original promoted service probes | **6 passed**, 3 deselected |
| Delegated independent R04 assertions | **24/24 passed**; separate proof, not added to suite totals |
| Root ruff / strict mypy, two changed paths | PASS / PASS |
| Post-documentation harness / security / architecture / diff check | All exit 0; security scanned 3,099 publishable files |

Raw proof is ignored under `evidence/local/codex-r04-final-20261016/`. Root JUnit,
reviewed source and raw receipt hashes plus final validators are recorded in
`evidence/metrics/C1_CODEX_R04_CLOSURE_20261016.json`.

Claude's 19-case before/after evidence is preserved in its original report/receipts;
the follow-up report records 12 failures/7 passes before and 19 passes after. Root
did not rerun the broader legacy/foundation suites this turn: these two small guard
changes are covered by focused bridge/API tests and their earlier evidence remains
explicitly historical, not silently refreshed.

## Notes and remaining gates

- The focused skip is the production-app route walk: importing the live app needs
  Pillow, absent in this environment. That check and the Pillow-dependent V2 server
  tests remain NOT_RUN. This review does not convert missing evidence into PASS.
- N01 body buffering remains a non-blocking P3 limitation; legacy F-01 is contained
  and unchanged. The qualified overlapping invalidation/read note remains unchanged.
- The executor's `_require_sha` observation is outside this reference-guard fix;
  no new blocking finding or extra implementation batch was established here.
- Real typed provider context, owner/admission/request adapters, persistence/delivery,
  model/profile/quality/runtime and live composition remain outside C1 and open for
  full BE2-02. Owner integration remains ASSUMED_CONTRACT/NOT_RUN.
- BE2-01 stays WAITING_STUDIO, CR01 open. BE2-02 remains IN_PROGRESS/NOT_DONE.
- Before C1 acceptance, preserve the explicit NOT_RUN disposition and obtain the
  missing checks in an authorized suitable environment or an explicit owner decision
  on those limitations. No owner acceptance is manufactured by this review.
- No stage/commit/push/merge/deploy by review; publication remains a separate action.
