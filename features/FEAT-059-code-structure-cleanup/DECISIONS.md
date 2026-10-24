# FEAT-059 decisions

## D01 — Cleanup must preserve current behavior

- Date: 2026-10-23
- Authority: Direct owner reply in the current conversation.
- Decision: Scope code cleanup to structural organization while keeping current product and demo behavior. Keep Child, Teacher, and Admin as separate app surfaces. Do not implement real service integration or delete/consolidate legacy apps under this feature.
- Consequence: Capture behavior first and keep compatibility facades/defaults during refactoring.

## D02 — Verification bar

- Date: 2026-10-23
- Authority: Direct owner reply in the current conversation.
- Decision: Completion should include build/typecheck/lint plus tests for primary flows.
- Consequence: Current app packages without test scripts need a bounded test-runner plan before implementation; tests are not claimed or run during planning.

## D03 — Clean on dev; keep P2-T5 separate

- Date: 2026-10-23
- Authority: Direct owner reply in the current conversation: “Giữ riêng, clean trên dev”.
- Decision: Use local `dev@0a7ce768c153f2104cff930569c3eda6e484532c` as the FEAT-059 baseline. Keep `origin/feature/feat018-p2t5-evaluation-harness` separate; do not merge or cherry-pick it under this feature.
- Consequence: FEAT-059 cleans only the confirmed dev baseline. Recheck the branch later before document authoring if it has been independently integrated.

## D04 — Make checks executable without joining app dependency graphs

- Date: 2026-10-23
- Authority: Approved FEAT-059 plan and the owner's instruction to clean before documents.
- Decision: Add per-app build, typecheck, lint, and test scripts. Preserve current fixture values, route behavior, and independent Child, Teacher, and Admin packages.
- Consequence: Passing UI checks prove fixture and navigation behavior only. They do not establish live authentication or backend integration.

## D05 — Preserve the backend compatibility composition

- Date: 2026-10-23
- Authority: Approved FEAT-059 plan and the pre-cleanup route snapshot.
- Decision: Extract named in-memory demo store/session constructors and classroom/demo router groups while retaining `create_app()` as the existing combined entrypoint.
- Consequence: Separate runtime profiles remain a target design direction; this cleanup does not change which app entrypoint is used.
