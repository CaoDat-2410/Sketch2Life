# T2C fake-owner keyword compatibility — GA2 scope addendum

- Status: **DRAFT / AWAITING_OWNER_APPROVAL**. This document grants no approval.
- Purpose: resolve one exact-path omission from the frozen T2C plan without editing that plan or its historical approval.
- Parent plan: `plan/T2C_BE1_CANVAS_OWNER_FACT_ADAPTER_PLAN_GA2_20261102.md`, SHA-256 `1B1EB635FEA67D6EFCD19B3506F83538454D5A75012742F54B2CA0EA15086774`.
- V4 SHA-256: `E11FFBCE0F655C010E679773D231D3E36930A0B960E705450499E2A2A69191F6`.
- GOAL A2 REV2 SHA-256: `47CEA408AA9A4984C2EFD9E71A2EF0CDB2DF02C46E56FD7281086EBAE574AE10`.

## Existing state requiring owner decision

`backend/src/sketch2life/infrastructure/assistance/fakes.py` already contains an A2 working-tree change: import `EligibilityScope`, add optional keyword-only `scope=None` to `FakeAssistanceOwner.members`, and return an empty tuple for a supplied mismatching organization/participant/purpose. The file's current SHA-256 is `E97A40AB5EEC4937BF1F9336162D731E4185F3A7B583DC16FAB11AAC636B71D5`.

The V4/goal assistance area and optional-keyword contract include this behavior in general. The frozen T2C exact source list omitted this concrete file, however, and the file is absent from the 35-row launch baseline. The final scope audit therefore withheld closeout. This addendum records the omission honestly; approval, if granted, accepts this specifically reviewed current diff and does not assert that an exact-path approval existed before it was first written.

## Sole proposed source scope

Only `backend/src/sketch2life/infrastructure/assistance/fakes.py`:

1. Import the existing domain `EligibilityScope` type.
2. Extend only the `FakeAssistanceOwner.members` signature with keyword-only `scope: EligibilityScope | None = None`.
3. When scope is supplied, refuse mismatching organization, participant membership or purpose with `()`.
4. Preserve the existing member-fact construction and the complete no-scope behavior.

No further source change is proposed. The already-existing diff has two hunks: the import and the method signature plus the scope check. This fake does not become a production authority adapter and does not grant legal consent or synthesize consent evidence.

## Acceptance after approval

| Check | Required evidence |
| --- | --- |
| Owner decision | Direct owner approval identifies this addendum or explicitly accepts the sole source path and changes above. Append a new approval entry; do not alter historical entries. |
| Diff boundary | Only the two described fake-owner hunks; no change elsewhere in the file. Current reviewed file hash remains the hash above unless owner requests a new revision. |
| Compatibility | Existing no-scope caller behavior stays unchanged; scoped pilot callers remain fail-closed. Use the existing named GA2 assistance/Sketch regression and digest test; no new test or runtime scope is introduced here. |
| Verification | Preserve actual 396-offline/68-PG results already recorded. Rerun tests only if source changes. Run Ruff, existing-source mypy delta, three validators and diff/byte checks for final records. |
| State | Seven protected files, frozen plans and historical approvals remain unchanged; index remains empty and HEAD remains `a88de875ff92e9b4d4fa5cc2f5f8d5fc1f626f58`. |
| Handoff | Append the scope resolution to the two GA2 reports and goal ledger, create a new GA2 snapshot, and stop at `GOAL A2 XONG-CHƯA REVIEW`. |

## Exclusions

No other source/test path, migration/schema, route/composition, AI Jobs contract/repository, policy changes, future goal, provider/Modal/GPU/external-network call, real-child data or stage/commit/push. Existing approval and snapshot bytes remain historical and are not rewritten.

Until owner approval arrives, keep the addendum DRAFT, leave the existing source untouched, and retain the scope hold recorded in the GA2 reports.
