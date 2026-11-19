# FEAT-063 M2-S3 — closeout report — 2026-11-18

- **Status:** S3 WORK DONE; PACKAGE AWAITING INDEPENDENT REVIEW. This report does not accept S3 and does not close M2: both are the owner's separate decisions (Draft 11 criterion 9). The S3 outputs are not committed; the commit, any push and the merge of draft PR #29 each need the owner's own instruction.
- **Author:** coordinating Claude session (Opus 5.5); owner Person 2. Not independently reviewed at the time of writing.
- **Authority:** `plan/M2_S3_TASK_APPROVAL_DRAFT11_20261118.md`, 55,114 bytes, SHA-256 `C45B9D89BAB0960780BAD45A1350280ED22D8CBDCD166F073F83868F732C9C6E`, approved as written and launched under D-213 item 7 after review round 4 (`evidence/M2_S3_DRAFT11_COLD_REVIEW_R4_20261118.md`, Sonnet 5.5 high, READY WITH NOTES, 0 P1 / 0 P2 / 8 P3). Approval entry: "M2-S3 — task approval: S3 Draft 11 approved as written and launched under D-213 item 7 — 2026-11-18" in `approvals/TASK_APPROVAL.md`.
- **S3 base:** the step-0 commit `7950d303239455ba492e33ffe3bae3828be9a469` on `feature/feat063-m2-s2` (planning records: D-210 to D-213, S3 Drafts 8 to 11, review records R1 to R4, the approval entry). Six commits ahead of the remote; nothing pushed.
- `OWNER_MODAL_CALL_APPROVED=NO`. No export, application start, test, database, container, provider, Modal or network use took place in S3.

## 1. The five departures from the baseline

The baseline S3 row (foundation plan Draft 10, line 265) is not met in full. These are stated departures; none is reported as met:

1. "mọi M2-AT khác phải chạy và pass": relaxed for M2-AT-08 and the StoryRun part of M2-AT-10 (accepted as "gate G1 passed with deviations DV-1 to DV-19, on the second attempt"), for M2-AT-09 (deferred), and for the rows accepted at a narrowed scope — M2-AT-01 (system-role negatives NOT RUN), M2-AT-04A and M2-AT-04B (PARTIAL), the service and contract part of M2-AT-10 (PARTIAL) — on the basis of D-210 items 3 and 4.
2. "đóng OpenAPI P3": not done; the gate stays OPEN.
3. "OpenAPI parity được kiểm": checked in part only (D-211 item 2).
4. "Không tích hợp frontend/client khi OpenAPI P3 còn mở" (S3 row, stop column) and line 398: narrowed to the three assistance operations (D-211 item 1). The N-1 route test sentences — "trước D9 hoặc frontend/client integration" (lines 317 and 396) and "trước D9/client integration" (lines 76, 264 and 407) — are departed from to the same extent; the same sentences require that test "trước khi thoát S2", and M2-S2 was closed on 2026-11-17 without it. What "D9" denotes is not established (D-213 item 6).
5. "OpenAPI request/response/error parity được freeze trước client integration; P3 đóng trong S3" (line 409): narrowed to a per-operation rule for the Parent target operations (D-212 item 2); "P3 đóng trong S3" is departure 2.

## 2. Outputs

| Path under the feature folder | Bytes | SHA-256 |
|---|---:|---|
| `artifacts/m2-s3/openapi-runtime-frozen.json` | 847,426 | `E9C2D7C8E95225F3D1F8B708C50C9ACC19CF822508ABEFD4F85298AD2E6B3A0C` |
| `artifacts/m2-s3/openapi-client-projection-frozen.json` | 213,111 | `F23BF908A104667153F88D6438AE8E95BE9895A76DAB7099877EBE9EFC49589D` |
| `evidence/M2_S3_OPERATION_INVENTORY_AND_CONTRACT_FREEZE_20261118.md` | 56,475 | `B72228CE918DE75A6531ED6A01C9E2A1C9643D26BC69442505D87591414AE351` |
| `evidence/M2_S3_ACCEPTANCE_TEST_LEDGER_20261118.md` | 15,031 | `25DF0A6232722FD206F96FFD22A9EFC5BEF41A9B4933D290474DA34F5BEEE351` |
| `evidence/M2_S3_LIMITATION_LEDGER_20261118.md` | 17,463 | `A82335ECBB3AE1BD600956FEFD75D0885CFE7EF095BA9BBD64303DBD91B5CF4A` |
| `evidence/M2_S3_CLOSEOUT_REPORT_20261118.md` | this file (its hash is in the approval entry that records the S3 work) | |

Edited: `.gitattributes` at the repository root, one added line `features/FEAT-063-system-architecture-rearchitecture/artifacts/m2-s3/*.json -text whitespace=cr-at-eol` (11,853 bytes, SHA-256 `4DA0D0318B63EA4EA315D9A811A8D63E512221F123C09084355BB86D00030EE7` before; 11,956 bytes, SHA-256 `C4C8C7C2598C97FC8BF0DB331977ECB5B195225C4B89378C1C883357C67F9F7E` after). Appended: `approvals/TASK_APPROVAL.md`, `status/STATUS.md`, `CONTEXT.md` (one entry each, after this report).

## 3. Reconciliation summary

- **Contract freeze:** both schema files copied byte for byte and verified in the working tree; `text` unset for both. The staged-blob check follows the owner's commit instruction and is recorded in that commit's entries.
- **Precondition check:** exactly the three expected differences (two test modules in `pinnedInputStates`; `parent_story_repository.py` in `changedPaths`); no stop.
- **Inventory:** 151 runtime operations on 134 paths, 34 in the projection on 24 paths, all inside the runtime set; each operation has one primary classification value. Tally: M2 target 9; proposal 3 (+1 second value); pilot-only 5; local example 3; OPEN-OWNER 11; BE1 compatibility 54; demo-group compatibility 35; outside the M2 scope 31. No stop condition.
- **Contract cards:** nine, one per M2 target operation.
- **Parity:** the nine target operations checked by reading on method, path, status codes and error envelope. One DIFFERENT (parameter name only) pair (`GET /v1/story-runs/{run_id}`, cancel); three SRS foundation routes ABSENT FROM RUNTIME; the cancel operation ABSENT FROM THE CLIENT-FACING PROJECTION. Under D-212 item 2 and D-213 item 3: client integration allowed for eight Parent target operations on the compared dimensions, not for the cancel operation until its OPEN item is closed. Every other operation is parity NOT CHECKED except the 134 catalogued ones, for which the mapper comparison is cited.
- **Acceptance-test ledger:** every row has an accepted status, a recorded disposition or the accepted gate G1 wording; none is NOT ESTABLISHED. M2-AT-01 accepted at a narrowed scope; 02, 03, 11 accepted at the approved scope; 04A, 04B PARTIAL; 05, 06, 07, 09 NOT RUN / DEFERRED; 08 "gate G1 passed with deviations DV-1 to DV-19, on the second attempt"; 10 "PARTIAL — see parts". The per-requirement table for the twelve requirements of baseline section 4 and the D-151 conditions C1 to C5 are in the same file. S1a-P2 is a separate block (ACCEPTED WITH KNOWN GAP).
- **Limitation ledger:** every item has an owner or a phase; items with no decided owner say "Person 2 to assign". It includes the baseline section 7 item 5 mapping (target migration covered for a new database only; schema inventory, data disposition and rollback limits NOT COVERED; live graph reconciliation NOT RUN; no approved M2 Mypy baseline).
- **NFR-36, NFR-38 and S1b** keep their partial or deferred status. **K3** is NOT VERIFIED. The **Story-chain target** is established for a new database by gate G1 under D-211 item 3, and not otherwise. The **OpenAPI P3 gate** is OPEN.

## 4. Pins verified in step 1

- All 29 rows of Draft 11 section 8 by `sha256sum -c` against a check file (`tmp/m2-s3/step1_whole_pins.sha256`, scratch): 36 of 36 lines OK, which also covered the two section 3.1 source files and the six hash-only citations. The prefix pin of `approvals/TASK_APPROVAL.md` (first 496,807 bytes) was checked with `head -c` piped to `sha256sum`: `11E3DC40...` as pinned; `git diff --numstat` of the step-0 commit shows 11 added lines and none removed for that file (the approval entry), 4 added lines and none removed for `DECISIONS.md` (D-210 to D-213, relative to the parent commit). `DECISIONS.md`, `status/STATUS.md` and `CONTEXT.md` equalled their whole pins.
- **S3 base sizes of the appended files at the step-0 commit:** `DECISIONS.md` 233,645 bytes, `7EA82DB5D94D0B0457091E6F9D1E568E50BABB77CAC2533E18F1467791EF4C2D`; `approvals/TASK_APPROVAL.md` 501,103 bytes, `76D7278FA126627158D553D3C8AA0854B74A175B1377D78154D6D6908A9931EC`; `status/STATUS.md` 123,718 bytes, `046E59EECA355848C8D78F98F24130C8FD322945F913C3F71B33B788098EA809`; `CONTEXT.md` 123,910 bytes, `220A4678FFA3D82FEB5C8FD9552395861C04A37ABAF02CBA4FF28AF871D69314`.
- The seven read-only source files: hashes in the inventory record, section 6.
- The round-3 review record was redacted before the step-0 commit (owner selection "Sửa R3, ghi lại hash"); its Draft 11 header pin is historical and was not recomputed, as the approval entry states.

## 5. Commands run (all from the worktree root unless stated)

| Command | Runs | Result |
|---|---:|---|
| `sha256sum -c ../../tmp/m2-s3/step1_whole_pins.sha256` | 1 (output read twice with `grep -c`) | 36 OK, 0 not OK |
| `head -c 496807 <approval record> \| sha256sum` | 1 | prefix pin equal |
| `sha256sum` and `wc -c` of the read-only sources, the copies, `.gitattributes`, the scratch scripts and outputs, the S3 records | several invocations, each under 10 | values as recorded |
| `git diff --numstat 7950d303^ 7950d303 -- <four appended files>` | 1 | as section 4 |
| `PY -I -B -m ruff check --cache-dir ../../tmp/m2-s3/cache/ruff <scripts>` | 3 (precondition script alone; both scripts; both after the encoding change) | all checks passed each time |
| `PY -I -B ../../tmp/m2-s3/check_preconditions.py` | 1 | three expected differences |
| `printf ... >> .gitattributes` (the one line), `mkdir -p`, two `cp` | 1 each | copies equal to the pins |
| `git check-attr text eol whitespace -- <two copies>` | 1 | `text: unset` |
| `PY -I -B ../../tmp/m2-s3/extract_operations.py` | 2 | run 1: checks passed, tag text written in the console's legacy encoding (output superseded); run 2 (after adding a UTF-8 stdout setting only): checks passed, cited output `CB9CF581...` |
| `git grep -l -E '(^\|[^A-Za-z0-9])[A-Za-z]:[\\]' 7950d303 -- '*.md'` and the same for the FEAT-063 folder | 2 attempts each | first attempt failed on the pattern (`Trailing backslash`, no output); second: 40 and 22 files |
| Read-only inspection with the Read tool and `grep`, `sed`, `tr`, `head`, `tail`, `cat`, `ls` in Git Bash | — | reading of pinned inputs, the frozen schema file, the comparison folder and the read-only sources |

Validators, `git diff --check`, the byte-level check and the drive-letter search of the new records are run after this report and recorded in the approval entry (Draft 11 step 5). The scratch scripts are `tmp/m2-s3/check_preconditions.py` (1,790 bytes, `D17E05FC4F7EFDAB2DADC31CD376BF4559FA70E235BC21107C381538281DE740`; output 4,492 bytes, `9F9A992CCD0068EB5AAC0C21D9879765665167944059D1DC206A7FAAA7B35EBA`) and `tmp/m2-s3/extract_operations.py` (2,843 bytes, `D95848501A2AAAF00EF3D6A48B50A1F9F61FE58B3921743DDF237D842D339CE9`; output 26,460 bytes, `CB9CF58105261C0815D6DCA7F219F2080C68FA3A790B28B31E620B63DFC38D99`). Other files in `tmp/m2-s3/` (the scripts used before launch to append D-213 and the approval entry, to build Draft 11, and a byte checker used for the step-0 commit; the reviewers' folders) are not S3 scripts.

## 6. What was read for S3, and what was not

**Read in full:** the adopted SRS sections 9.6, 9.8 and 21.1 to 21.6 (and searched for "D9", no match); foundation plan Draft 10 lines 255 to 410 (phase table with the S3 row, section 4 with the requirement table and rows M2-AT-01 to 11, sections 5 and 6, section 7 items 1 to 7); foundation plan Draft 11 rows M2-AT-01 and M2-AT-10; decisions D-110, D-151, D-170, D-171, D-188, D-196 to D-213; the S1a-T closure record; the S1a-P closure record; the S1a-P2 closure record and its real-PostgreSQL addendum; the S2 implementation report; the shared OpenAPI mapper implementation evidence; the S2 closure-verification evidence; the gate G1 evidence report, its review R3 and the gate-run Task Approval Draft 1; the write-defect fix evidence; S2 Draft 18 sections 4, 5 and 6; the acceptance entries for S1a-T, S1a-P, S1a-P2, the S2 closure and gate G1; `router_composition.py`; the relevant parts of `app.py` (composition and storage-example mount) and of the contract test's constants.

**Read in part:** the S1a-T specification (its M2-AT row table and the paragraph after it, lines 100 to 114); the S1a-P specification (its contract and acceptance crosswalk, lines 50 to 66); the S1a-P2 implementation report and Draft 7 (their P2-AT rows); gate G1 Draft 2 (its deviation table DV-1 to DV-18); the frozen runtime schema (the nine target operations and the error and cancel schemas); the comparison report `field-delta-report.json` (its inputs, which include the two post-export files at the frozen pins and the pre-export files; `invariants` with an empty error list and `passed: true`; top-level `passed: true`; the counts of its delta kinds — 67 added-status, 281 addition, 598 removal, 511 removed-status, 336 value-change entries between the pre and post exports; the cancel operation does not occur in it), and its folder's `child-result.json` (`comparison.passed: true`); the individual field deltas were not read.

**Not read:** the S1a-T implementation report and K4 source reconciliation; the S1a-P implementation report; D-172 to D-187 and D-189 to D-195 beyond their citations. Nothing found in the parts not read was relied on; where a ledger cell depends on them, the cell cites the record that was read.

## 7. Notes Q1 to Q8 of review round 4 (carried as notes, as the approval entry states)

Q1: all five departures are stated (section 1). Q2: the S3 base is the step-0 commit itself; no STATUS or CONTEXT entry was added at step 0. Q3: the approval entry pins Draft 11 and the round-4 record. Q4: the drive-letter search of the S3 records uses an anchored pattern and treats URL schemes as not local paths; it is also recorded for the step-0 files in the approval entry. Q5: copies made with Git Bash `cp`; prefix pin checked with `head -c`; the comparison report was read in part as a read-only export input (section 6: inputs, invariants, pass flags, delta-kind counts); its parity coverage of the 134 catalogued operations is cited from the mapper evidence and acceptance, not re-derived from the field deltas. Q6: the second sentence of baseline section 7 item 5 is dispositioned in the limitation ledger. Q7: drafting notes on Draft 11, no effect on the outputs. Q8: "D9" stays an open owner question; the reviewer's candidate reading is noted in the limitation ledger, not adopted.

## 8. Points for the owner (not decided by S3)

1. **Error-envelope reading** in the parity table: the extra fields `request_id` and `current_version` are tabulated NOT STATED IN THE SRS rather than DIFFERENT. If the owner reads them as DIFFERENT, client integration with the five Parent profile operations (and the cancel operation, already blocked) would wait under D-212 item 2.
2. **`GET /v1/story-runs/active/current`** is an M2 target read by D-199 while its summary text says "[PROPOSAL]"; recorded OPEN, not repaired.
3. **The cancel operation** is uncatalogued and absent from the client-facing projection: client integration not allowed until closed.
4. The open owner questions and the "Person 2 to assign" items of the limitation ledger.

## 9. Recommendation

The S3 package is complete against Draft 11 criteria 1 to 7, with the limits stated above, and is ready for its independent cold review (criterion 8: Sonnet 5.5 at high effort only; READY or READY WITH NOTES with zero P1 and zero P2). If that review passes, the coordinating session recommends that the owner accept S3 and close M2 "with recorded debt and deviations" (D-210 item 4), stating the five departures of section 1 in the closing entry, the OpenAPI P3 gate OPEN, M2-AT-09 DEFERRED with its client-integration block, NFR-36, NFR-38 and S1b at their partial or deferred status, and K3 NOT VERIFIED. That recommendation authorizes nothing: not FR-C-08, client integration, M3, a database action, a gate G2 or the integration of PR #26.
