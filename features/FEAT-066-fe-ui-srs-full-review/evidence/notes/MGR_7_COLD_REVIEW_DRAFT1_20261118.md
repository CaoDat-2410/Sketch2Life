# FEAT-066 MGR-7 Cold Review — Draft 1

**Verdict: CHANGES REQUIRED**

Review type: independent, read-only planning review. This report is not implementation approval, FE integration approval, or launch authorization.

## Identity and input completeness

- Reviewed plan: `features/FEAT-066-fe-ui-srs-full-review/plan/PLAN_MGR7_BE_IMPLEMENTATION_APPROVAL_PACKAGE_DRAFT1_20261118.md`
- Live plan size and SHA-256: **31,831 bytes**, `4141C9D5AC2E7D685A0BF4985D037498A0303FAF307CABC8AD1D0CC7C408B8DF` — both match the supplied pin.
- I read all **31,654 decoded characters** in consecutive ranges from character 0 through 31,653. The plan input was complete and not truncated.
- BE worktree: `D:\GitHub\Sketch2Life\.worktrees\manager-api`; branch `feature/feat066-manager-api-contracts`; HEAD `1c9148e88600a101887e477541c4c4893ba1c7df` — both match the expected identity. Current status showed 28 dirty FEAT-066 documentation/evidence/plan paths (3 modified, 25 untracked), with **0 staged**.
- FE worktree identity matched the plan: branch `codex/fe-ui-web-remediation`, HEAD `297a28b1f406ab80e25d6e0aa5577e4b6f505ee2`. The current FE audit plan pin matched: 63,453 bytes, SHA-256 `8B1EB54A05A4B4A6FF502D45B278DBFE3B885EC278229A7ADEA98D3DA7ECA50`.

`docs/context/SRS_AUTHORITY.md` matched 4,054 bytes / SHA-256 `032223EDDD46D251DE052C54BFF16AB1D4D794F865A457272507D893E3C1521F`. The canonical FEAT-063 Rev60 SRS matched 553,948 bytes / SHA-256 `70DA43A35106E8C02B4BB8FCCB9628C0376C9E7EA6CFC51909ACB569703B218B` and remains an unsigned draft. Rev60 §§9.8, 21.1, and 21.4 specify HTTP 400 `INVALID_IDEMPOTENCY_KEY` for reuse of a key with a different payload.

The live hashes for the MGR-2–MGR-6 plans, source evidence, latest listed reviews, and MGR-5 owner decision brief matched the pins in MGR-7 §1. The MGR-2 R4 review identifies the external Rev69-header/Rev68-history SRS as historical provenance, OPEN / NOT VERIFIED, and says it was not used as current authority. MGR-7 §1 names Rev60 as its only current product SRS; the MGR-7 matrix claims reviewed before the stop cite Rev60. No MGR-7 requirement was found to rely on the external copy. An additional cross-reference could make that provenance easier to follow, but it is not a blocking issue.

## Findings

### P2 — Exact allowlist omits a unit test that asserts the old shared-helper error

**Plan locations:** §4.1, lines 74–77; §4.3, line 95.

MGR-7 proposes changing the shared Lesson Library `_replay` conflict from HTTP 409 `IDEMPOTENCY_KEY_REUSED` to HTTP 400 `INVALID_IDEMPOTENCY_KEY` (§4.1, line 74). Its acceptance criterion requires regression coverage for all consumers of the shared receipt helper (§4.3, line 95). The exact test allowlist names only `backend/tests/integration/lesson_library/test_lesson_library_api.py` and `backend/tests/contract/test_openapi_contract_catalog.py` (§4.1, lines 76–77).

The pinned source also has `backend/tests/unit/test_lesson_library_receipt_compatibility.py`, whose direct `_replay` test asserts status 409 and code `IDEMPOTENCY_KEY_REUSED` at lines 217–228, specifically lines 226–227. The helper currently emits those values at `backend/src/sketch2life/infrastructure/lesson_library/service.py:491–507`. If the planned shared-helper change is implemented within the exact allowlist, this existing unit assertion remains inconsistent with the new contract. The allowlist must include that unit test and its expected 400/code update, or otherwise define a compatible test scope before an implementation approval package is ready.

This finding is based on static source inspection. No test was run, and no test result is inferred.

## Review stop boundary

The review stops at the first P2, as instructed. I verified the authority pins, plan and FE-audit pins, listed MGR-2–MGR-6 artifact hashes, the affected BE helper, and the directly conflicting unit-test assertion. I did not complete the remaining line-by-line validation of the MGR-2–MGR-6 closure matrix or the FE UI source claims, and I did not independently compare working-tree D-066-62/D-066-63 against the pinned `DECISIONS.md` blob. Those checks remain incomplete in this review. No tests, build, typecheck, lint, validator, diff-check, OpenAPI generation, backend/runtime, database, Docker, network/provider, or Modal command was run.

The MGR-7 package remains DRAFT / NOT APPROVED / NOT LAUNCHED. No plan or other file was edited; this report is the only file created for this review.
