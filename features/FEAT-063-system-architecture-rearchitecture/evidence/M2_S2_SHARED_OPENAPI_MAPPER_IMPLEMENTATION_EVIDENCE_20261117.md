# FEAT-063 M2-S2 Shared OpenAPI Mapper — implementation evidence — 2026-11-17

- **Status:** EVIDENCE REPORT / NOT OWNER-ACCEPTED. The implementation is done and every one-shot command has run. Acceptance of the task is the owner's decision and has not been given. M2-S2 remains PARTIAL / NOT COMPLETE.
- **Author:** coordinating Claude sessions (Fable 5.2); owner Person 2. This report was not independently reviewed.
- **Authority:** Task Approval Draft 1, `plan/M2_S2_SHARED_OPENAPI_MAPPER_TASK_APPROVAL_DRAFT1_20261116.md`, 321,800 bytes, SHA-256 `4EAEA5340B1369E2A484FE86DE04AD6A1D949C2E838295C17988B3BCEC9666C3`, with Amendments 1 to 3 (section 3). Approvals, launch instructions and results are in `approvals/TASK_APPROVAL.md`; after the last result entry that record was 463,049 bytes, SHA-256 `D2F0241FB4C3B61729C1CF133E8EB63D8431302A10FC0C06EDC178ED7BE75851`.
- **Where:** worktree `.worktrees/m2-s2`, branch `feature/feat063-m2-s2`, HEAD `5de30674bc826591ad4b3cc00fca53c7597ead51`. Nothing was staged or committed. Run outputs are under the git-ignored `backend/tmp/`; payloads, cards, the lock-resolution evidence and the source inventory are under the git-ignored repo-root `tmp/m2-s2-mapper-evidence/`. Hashes below identify them; the files themselves are local only.

## 1. Result in one table

| Command | Run 1 | Run 2 | Authority for run 2 |
|---|---|---|---|
| Pre-fix OpenAPI export | FAILED CLOSED (package `av` missing from the environment) | Success | Environment amendment in the approval record |
| Mypy baseline | Captured, 353 diagnostics, NOT CLEAN | — | — |
| Ruff baseline | Captured, 1 diagnostic, NOT CLEAN | — | — |
| Post-fix OpenAPI export | Success, but without the egress block (accepted deviation) | — | — |
| Schema comparison | FAILED (113 invariant errors, 1 source-state error) | PASSED (0 errors) | Amendment 1 |
| Pytest, three selections | FAILED (22 of 23 passed) | PASSED (23 of 23) | Amendment 2 |
| Mypy post | No new diagnostics; NOT CLEAN (353 existing) | — | — |
| Ruff post | FAILED (1 new diagnostic on the new test file) | No new diagnostics; NOT CLEAN (1 existing) | Amendment 3 |

Four commands needed a second run. Each first run stays on record as failed. Neither static check is a clean pass.

## 2. Implementation

| Mode | Path | State after the task |
|---|---|---|
| E | `backend/src/sketch2life/interfaces/http/app.py` | 74,198 bytes, SHA-256 `AF5DB1BE7FCB1B844A53A1BBFC109EC59F5761759D88C9734A114BA07C57738A` |
| E | `backend/tests/contract/test_openapi_contract_catalog.py` | 21,274 bytes, SHA-256 `8E728A68E4BF35D001FC608DE9C86560EEB71349CCCE0A11AA14F998C9015A67` |
| N | `backend/tests/contract/test_openapi_schema_catalog_mapping.py` | 10,597 bytes, SHA-256 `102B7D26C7E5E791592A953A8EEB0BF3DDA0AAE765BDEB05AE5D12094497BF50` |
| R | `backend/tests/contract/test_app_composition.py` | unchanged, SHA-256 `1ED234FD8B75847F2668A2B23C9325C1D229CA679943B65166E96144A4463B52` |

- `app.py`: the handler-name guard was removed; the catalog mapping was moved, otherwise unchanged, into the module-level function `_apply_catalog_metadata(schema, catalog)`; the lookup key is exactly `(method.lower(), path)` taken from the OpenAPI document.
- E test file: two tests appended (exact description and tag; operationId non-empty and unique). Under Amendment 2 one existing assertion changed from `len(spec["tags"]) == 19` to `== 20`.
- N test file: nine test functions, one of them parametrized (pure mapper tests and a source-level declaration audit of the catalog). The per-file split of the 23 collected test cases was not tabulated for this report. Under Amendment 3 one blank line was inserted after `import pytest`.
- No other source or test path was edited for this task.

## 3. Amendments

| No. | Text (copied byte-for-byte into `plan/`) | SHA-256 | Content | Review |
|---|---|---|---|---|
| 1 | `M2_S2_MAPPER_COMPARATOR_AMENDMENT1_DRAFT_20261117.md`, 14,680 bytes | `A21C3C9F3947E8BB84E9B4EE71E3F28FF473D690FAFA883D2122C3376AC4D66E` | Criteria 7, 9 and 11 amended; comparator payload replaced; one more comparison on the existing exports | Cold review R18, Sonnet 5.5, effort high: ACCEPT WITH NOTES, 0 P1 / 3 P2 / 9 P3, on an earlier revision; later text changes not re-reviewed. `evidence/M2_S2_SHARED_OPENAPI_MAPPER_AMENDMENT1_COLD_REVIEW_R18_20261117.md` |
| 2 | `M2_S2_MAPPER_PYTEST_AMENDMENT2_DRAFT_20261117.md`, 5,056 bytes | `AB31404D1DE4350449ED43C615F1035AB0DA511AE6B1E9A210A724CEFAA0072C` | One-line change in the E test file; one more pytest invocation | None; owner approved without review |
| 3 | `M2_S2_MAPPER_RUFF_AMENDMENT3_DRAFT_20261117.md`, 4,732 bytes | `90421225E768E56A03BA75B546B206E9A579F92DBDE8746AC1D21E47BEAF049E` | One blank line in the N test file; one more Ruff post check | None; owner approved without review |

The file names keep the word DRAFT because the approval record pins these exact bytes; their status is APPROVED as recorded there.

Amendment 1 comparator: `schema-comparator.py`, 55,917 bytes, SHA-256 `573DE1BF0E877994134E80693105D5FA8672C920ED88510070BC9E8A53EDE396`, replacing `4CB27EA71D419BEBCF99ABB0142D2B789D226A84F2665B2F76C96A5B21402A14`. Before approval it was rehearsed once directly on the eight inputs (passed) and run on seventeen direct negative controls (one unmodified control passed, sixteen single mutations each failed with the expected error). Those runs bypassed the task runner and are not acceptance evidence.

## 4. Environment pins

- Interpreter `D:\GitHub\Sketch2Life\tmp\m2-s2-mapper-env\.venv\Scripts\python.exe`, SHA-256 `0B471133E110CFB53A061CAD528CE8E517D7B9AC41A0A396C39AD795A487FC14`; extras `dev` and `image-admission`; 108 installed distributions equal to 108 lock-resolved; FastAPI 0.162.0.
- `lock-resolution.json` SHA-256 `96B578F185D9497985C72F8D9CE5224B42236941E4857DF4C026EB855E971AC9`; `source-inventory.json` SHA-256 `DBFEFED25F636D296058092200E3A8C323F49BE6AF2E9CFA49359F960C7C078B`; Git executable SHA-256 `9BF8EE81D79F38A11EAF7799499A634C46A718E009A4A9B2B20B115804643302`.
- Payloads: task runner `A5E339B1374F23542FD83E2CF42658B307346F380656BE2B2DD7C0A24415351B`; child bootstrap `2633055A83C5ABEE45AC9A45E6F679DC4168BC1C099B0FD691065C04252120E7`; exporter `AAF3F04E1F402871FC4DA948BF0538480E7BE39E2AABDCF129390E66F2F8589F`; pytest bootstrap `8EC5337FA7D97EC59FE6B5291C4EA6F3C874CC2B06EE008CE2D55813EE44AAC4`.
- Egress: an operating-system block (two Windows Firewall outbound rules, effective while the third-party firewall product was paused) was probed from the task interpreter immediately before each of the comparison, pytest, Mypy post and Ruff post runs, and every probe was refused (Windows error 10013). The post export is the exception (section 6). The run manifests themselves do not prove network, database or provider isolation.

## 5. Run evidence

All roots are under `backend/tmp/`. Hashes are of `run-manifest.json` unless stated.

| Run | Root | Manifest SHA-256 | Outcome |
|---|---|---|---|
| Pre export, run 1 | `openapi-mapper-d10-pre-ca31ba1d94df4860b411d6850957abfa` | not re-hashed for this report | Failed closed before schema output |
| Pre export, run 2 | `openapi-mapper-d10-pre-4bfb106bb3f94f1db7cc79c4af6c0385` | `82B49531E11FF62CE989E3FF52C6DC9ABC34A558C5FB0D5B675A4974114D142B` | Success; runtime 151 operations, published 34 |
| Mypy baseline | `mypy-openapi-d10-baseline-374e1950e4f442f2bf9ca00e59e3432a` | `C2015BA040C569796CD3A37E05731177BDDF41D4D2F2B23D382F91FE3F42BB1B` | 353 signatures, tool exit 1 |
| Ruff baseline | `ruff-openapi-d10-baseline-dd33464e603f43abbe21b1207de4d16a` | `7C8B06FF1001E64C27DB163265DC98AD83A1B33385B4981A88CA130951CEADEC` | 1 signature, tool exit 1 |
| Post export | `openapi-mapper-d10-post-367b579d97eb4f0a99cd6a6d329bb1f4` | `1286E0F36FA98C9CEE19CB09415CA0BDE05D5606A9289A878850B96F6965548F` | Success |
| Comparison, run 1 | `openapi-mapper-d10-compare-7bcb994593bc42b6bfb2249500cc2a9f` | `675870BA6D1035A59CDEB87FF63EB46293C8531634BFC3D2D1010CF5B44AD0B2` | Failed; report `1EE2B3E9F21A88EA436F48A64D020923ED138CFFB744BA5E7CDACBF52F4699F8` |
| Comparison, run 2 | `openapi-mapper-d10-compare-7e7f0b0d854e48099ea903ba920ba7f4` | `FCC401E0F46C64FA04DAD251ACC9139C7E39B59ADDAE2E173C4EBDC0094C3059` | Passed; report 861,869 bytes, `E8F265F51410FD968AC1A14F1113ACB07C555BEBA23DFBDE0093A7679FFE5C6D`; 0 errors; 55 catalog-declared additions (53 `default`, 2 `422`) |
| Pytest, run 1 | `pytest-openapi-d10-04e6f233980749808b0b99316d7640d4` | `D9465305EDB83D5323D6629BF27F954769D6C2EE4700410A1CAAE39B0D7E1BC7` | 22 passed, 1 failed |
| Pytest, run 2 | `pytest-openapi-d10-82edd05b07d34123a8eae702254a7c89` | `8AC9FB3CE48600667781001789A51907D3D9D1C2507AF74310E26D004DDF6970` | 23 passed; JUnit `E645D458640F78CAF0FAA4A6E5BA497CB1C85C3D4DBD992780BA0A11FE61B50A` |
| Mypy post | `mypy-openapi-d10-post-3852b620f3bb454b875bc46e0fc7d93b` | `56D6B692596DE1239E4B70FF3F1A880B05254A0A104ACDE7EF612C522C730256` | 0 added, 353 signatures, tool exit 1 |
| Ruff post, run 1 | `ruff-openapi-d10-post-6c55a97c01b8453ea7947ffb67035133` | `20F01E9047C8B277F199B1FF81CA17CB4B91B5802A87039DB4C6184B063FC747` | 1 added (`I001` on the N path) |
| Ruff post, run 2 | `ruff-openapi-d10-post-7d6c6aca059a4de594137d227e34ae22` | `61BBC8999542EFBFED52D0C21BBEC5B75391C0C381648B12F9B6B2C9A937E158` | 0 added, 0 on the N path, 1 signature (baseline), tool exit 1 |

What the failures showed:

- **Comparison, run 1.** Criterion 7 as written rejected every response-status addition while also requiring the post status set to equal the catalog projection; the catalog declares `default` (53 operations under `/api/be1/v1/`) and `422` (2 operations under `/v1/parent/profiles`) that the generated schema did not have. The request-ID inventory check failed as a consequence. The approval record itself differed between the two exports because entries were appended in between. Amendment 1 narrows the three rules; the mapper code was not changed.
- **Pytest, run 1.** An assertion committed at HEAD expected 19 top-level tags; the schema has 20 in both exports. The test used to stop earlier, on the missing description that this task fixes, so the assertion had not been reached before.
- **Ruff post, run 1.** The new test file's import block lacked one blank line. It had not been lint-checked before the one-shot run; that omission is the coordinating sessions'.

## 6. Deviations accepted by the owner (all recorded in the approval record)

1. The post export ran without the operating-system egress block; the probe just before it had connected and the coordinating session did not stop. No evidence exists about whether the exporter made any network connection. The passed comparison reuses that export.
2. The approval record changed between the two exports. Amendment 1 accepts this only with an in-comparator proof that both export-time snapshots are byte prefixes of the record.
3. After the post export and the comparison, the E test file changed by one literal (Amendment 2) and the N test file by one blank line (Amendment 3). The export's source-state manifest and the comparison pin their earlier hashes (`6D7967B6D321FFE4762F9DAEAF0A331D3E543A765FAACB84ECACEB69988909F9` and `A6E5C7918B2460B9F8CFE1682168B3A41F83662F936480653F3635BEF438CC70`). No export or comparison was repeated. The basis is static reasoning: test modules are not inputs of the schema export.
4. Both pytest invocations ran on the N file before its blank-line change. The syntax trees before and after that change were computed to be identical; pytest was not repeated.
5. Criterion 10 asked for exactly one pytest invocation; two were run.

## 7. Not done, not proven

- The task is not owner-accepted. Amendments 2 and 3 and this report were not independently reviewed.
- Mypy and Ruff are not clean: 353 existing Mypy diagnostics and 1 existing Ruff diagnostic (`I001` on `tests/contract/test_openapi_contract_catalog.py`) remain. They are debt outside this task and need their own approval.
- Only the three approved pytest selections ran. The full test suite was not run for this task.
- The request-ID inventory remains OPEN except for the scope decided in Amendment 1.
- The other M2-S2 debts in `evidence/M2_S2_IMPLEMENTATION_REPORT_20261114.md` are untouched. M2-S3, FR-C-08 and later gates are not started.
- Nothing was committed or pushed. No Modal or provider call was made; `OWNER_MODAL_CALL_APPROVED=NO`.
