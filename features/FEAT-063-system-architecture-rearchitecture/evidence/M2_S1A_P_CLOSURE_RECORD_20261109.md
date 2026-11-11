# M2 S1a-P Closure Record — 2026-11-11

**Status:** OWNER-ACCEPTED S1a-P closure evidence. The owner accepted the original record at SHA-256 `BC843711A391DA6E2FF3696AD9D414232C7234D4C3F2C4CA877100D83F39F73C`; this copy includes the authorized operator-attribution correction. Acceptance is recorded separately in `TASK_APPROVAL.md`. This record does not open S1b, S2, S3, or M3–M6.

**Scope:** Parent profile foundation in the approved S1a-P Draft 8 scope, including the separate owner-run Gate A migration and Gate B PostgreSQL acceptance. `OWNER_MODAL_CALL_APPROVED=NO` remains unchanged. S1b remains DEFERRED; S2, S3, and M3–M6 are not opened by this record.

## 1. Repository and approval snapshot

| Item | Observed value |
|---|---|
| Branch | `feature/feat063-m2-parent-teacher-foundation` |
| HEAD | `4b7f07cc283721f01f64e41ff2d81f135f63ad29` |
| Index | Empty |
| S1a-P Draft 8 | `M2_S1A_P_TASK_APPROVAL_DRAFT8_20261109.md`, SHA-256 `E9C7FC9D7843F7466B88B801BFF26278A0E1B9C726EF770F8229C419C62F8118` |
| Gate B launch instruction | `M2_S1A_P_GATE_B_LAUNCH_INSTRUCTION_DRAFT1_20261109.md`, SHA-256 `FEEEFF1F95736172B9E73BBCE5BBEA10F5A11E8724C69A5D321A95F695569C59` |
| Gate B runner | `m2_s1a_p_gate_b_20261109.py`, SHA-256 `F858C38B439BB3D2F61A8CF71B0D71129390F4D7034130B4A5C4AA79C9C0156E` |
| DECISIONS.md | 165,498 bytes, SHA-256 `CBE15D74569AF03B8A53EF5EDF58C4B09F3058FE77A1D0F81023FE3FBE8DF979`; D-188 was not present at this evidence snapshot |
| TASK_APPROVAL.md | 318,152 bytes, SHA-256 `F2624D17197BA10F761D1214C6980D85BB2C0B0F336C8F01818A0467F4F7C5F6` |
| Gate B approval prefix | Stored and recomputed SHA-256 `7D9694CB2499F4343363E23CADDA412C444A51D71EEED7A5D227EF256122BADC` |

The current Gate B approval section is the exact R11 text and has status `APPROVED / NOT LAUNCHED`. Its append was authorized by the owner's direct instruction after D-187. D-188 was recorded after Gate B so the `DECISIONS.md` hash pinned by the Gate B approval remained unchanged for that run. This evidence record does not authorize another execution.

## 2. Delivered implementation

S1a-P adds the Parent profile operations `POST /v1/parent/profiles`, `GET /v1/parent/profiles/{profile_id}`, and `PATCH /v1/parent/profiles/{profile_id}` with the Parent-owned tables `parent.child_profiles`, `parent.profile_revisions`, and `parent.command_receipts`. The implementation and its offline evidence are described in `M2_S1A_P_IMPLEMENTATION_REPORT_20261109.md` (SHA-256 `1CE028736700824DC8D52806AAFF4D35B0995540FE6FA4A3E73E75429E1A4E65`). This closure record supersedes that report's earlier statement that no owner-run gate had occurred; the report itself is left unchanged.

The implementation is evaluated against the approved Draft 8 contract and D-171–D-187, including verified issuer-plus-subject ownership, the shared 404 `PROFILE_NOT_FOUND` behavior, synthetic-only creation, immutable revisions, normalized PATCH snapshots, and Parent-scoped idempotency receipts. This record does not claim that upstream age-band limitations or inherited K3 debt are resolved.

## 3. Verification evidence

| Check | Result | Evidence / limits |
|---|---|---|
| Independent implementation review | READY WITH NOTES; 0 P1, 0 P2, 0 P3 | Cold review session `01a1c419-9e2b-7a00-99cf-db88516dfc68`; the review covered the D-184 remediation and complete `ParentProfileView` assertions. |
| Gate B approval package review | READY WITH NOTES; 0 P1, 0 P2, 2 P3 | Cold review session `01a1cb00-dc29-7ad3-ad02-40f18cd8ee87`; the owner accepted R11 with both notes. |
| Pinned post-implementation pytest | 280 passed in 56.68s; exit 0 | Coordinator (Claude)-run log `.claude/handoff/logs/M2_S1A_P_20261109/20261111T085228Z_post-pytest_049b7fe8a334/`; official summary and zero safety matches. |
| Ruff | Exit 1; NO PASS; exactly one accepted pre-existing D-176 `I001` at `backend/tests/contract/test_openapi_contract_catalog.py:3:1`; no other diagnostics | run via the pinned wrapper; operator not recorded. Log `.claude/handoff/logs/M2_S1A_P_20261109/20261111T123559Z_ruff_a81d529c4e5c/`; wrapper exit 0, inner Ruff exit 1, zero safety matches. |
| Repository security validator | `REPOSITORY_SECURITY_VALID`; exit 0; 7,108 publishable files scanned | run via the pinned wrapper; operator not recorded. Log `.claude/handoff/logs/M2_S1A_P_20261109/20261111T123611Z_validate-security_d886839d88d2/`; zero safety matches. |
| `git diff --check` | Exit 0; stdout and stderr empty | run via the pinned wrapper; operator not recorded. Log `.claude/handoff/logs/M2_S1A_P_20261109/20261111T123636Z_diff-check_f2e2161a7b96/`; zero safety matches. |
| Strict mypy | Exit 1; 6,723 errors in 308 files; not a PASS | The approved post-install/post-implementation comparison recorded no new diagnostics versus its prior baseline. This was not rerun after subsequent Gate B runner preparation. |
| Temporary approval-parser pytest | NOT VERIFIED; a prior report said 17 passed but lacked official exit-code and safety receipts | Not used as verified evidence. |

Earlier offline-check logs listed in the pinned Gate B launch instruction (operator provenance only; these are not the final verification results above):

| Check | Log folder | Operator |
|---|---|---|
| Ruff | `20261111T085505Z_ruff_89fcbc2672cd` | run via the pinned wrapper; operator not recorded |
| `validate_repository_security.py` | `20261111T085531Z_validate-security_d134b35883f7` | run via the pinned wrapper; operator not recorded |
| `git diff --check` | `20261111T085627Z_diff-check_fe20c7653a66` | run via the pinned wrapper; operator not recorded |

## 4. Owner-run Gate A

Gate A was explicitly accepted by the owner in `M2 S1a-P Gate A Closure Acceptance — 2026-11-11` and its artifact-pin correction. The accepted run is `.claude/handoff/logs/M2_S1A_P_20261109/20261111T063503Z_gate_a_486a6b6388d7/`; its accepted post-inventory SHA-256 is `A198BF505273FFB81F75A819E9A12400B918B17B189D4DB33F494B3B1B2F2E28`.

- The owner reports seven invocations: six stopped and one PASS. The six stops were one `PINNED_APPEND_ONLY_INPUT_MISMATCH` (owner-reported, with no reserved run folder) and five `OFFLINE_PREVIEW_NOT_ACCEPTED` stops. The five preview-stop folders have zero-byte pre/post inventories and upgrade artifacts; the accepted run is the seventh invocation.
- Accepted transition: 117 tables / 29 rows to 120 tables / 30 rows. The three Parent tables were created empty. The only existing-table row change was `public.alembic_version`, from zero to one row at `20261109_m2_parent_profiles`. The 29 S1a-T marker rows remained unchanged; inventory status was `MARKER_COUNTS_MATCH`, with no unmatched tables.
- The safety-scan provenance correction is `preview-safety-scan.json`, not `final-safety-scan.json` as stated in Gate A Correction 4.
- The owner accepted the Gate A `_run_upgrade` residual risk that `PYTHONPATH` and `PYTHONHOME` may be inherited. The owner reports checking the specified `PYTHON*`, `PYTEST*`, `DATABASE*`, `PG*`, `POSTGRES*`, `SQLALCHEMY*`, and `ALEMBIC*` environment-variable families were empty immediately before the accepted run. This compensating check is owner-reported and is not present in the sanitized logs or enforced by the runner.
- Gate A status records `PROCESS_TREE_CHILD_ENUMERATION=NOT_VERIFIED`.

## 5. Owner-run Gate B

The Gate B log folder `.claude/handoff/logs/M2_S1A_P_GATE_B_20261109/20261111T151904Z_8b6474437245/` was read without opening credentials or connecting to the database. Its `runner-status.txt` reports `GATE_B=PASS`, `PRE_INVENTORY=MATCHED_ACCEPTED_GATE_A_POST_INVENTORY`, `POST_INVENTORY=PASS`, `PYTEST=EXIT_0; OFFICIAL_SUMMARY=1_PASSED`, and `SAFETY_MATCHES=0`. The runner metadata does not identify a human operator; the owner accepted the run from the owner-run handoff context.

| Evidence | Bytes | SHA-256 |
|---|---:|---|
| `runner-status.txt` | 236 | `606767262577E60232CC74B60D828AA730F655182ACCB78B43E5B65278AFFC15` |
| `pre-inventory.json` | 5,243 | `17233BFDBEB6F2415CFF00F591C02F52E6A0A40F5D7A7862B269A9D6C709E84B` |
| `post-inventory.json` | 5,344 | `5A5DBC464ED1FD57C88860BD9E0313920B328A9EF39BB37EA4C91B631B8C1D98` |
| `pytest.exit.txt` | 2 | `9A271F2A916B0B6EE6CECB2426F0B3206EF074578BE55D9BC94F6F3FE3AB86AA` |
| `pytest.stdout.txt` | 101 | `62AC631BBB79FEB2346A3AA86C280AA872ADB40E0A737B0E6A5E42BD8E085181` |
| `pytest.stderr.txt` | 0 | `E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855` |
| `safety-scan.json` | 171 | `D4020540FD71D94CDFFC63005DE017ED7AF8775137F74AEEE0519DAFBE781538` |

The read-only inventory comparison passed all checked invariants: both inventories identify `sketch2life_m2_s1a` on `127.0.0.1:5433` as PostgreSQL 17; both contain 120 tables; total rows are 30 → 36; marker rows are 29 → 35; existing marker counts and known control rows are unchanged; `parent.child_profiles` has 1 row, `parent.profile_revisions` has 2, and `parent.command_receipts` has 3; the Alembic version remains `20261109_m2_parent_profiles`; and `unmatched_tables` is empty. The pytest log has the official summary `1 passed in 21.97s`, exit 0. Every reported safety-scan count is zero.

`PROCESS_TREE_CHILD_ENUMERATION=NOT_VERIFIED` remains a declared limitation. The run log reports PASS; owner acceptance is recorded separately in `TASK_APPROVAL.md`.

## 6. Carried review notes and open conditions

1. **R11 P3 — historical approval snapshot hash.** The older R9 launch-instruction snapshot hash did not represent the current full `TASK_APPROVAL.md` hash. R11 recalculated the current approval bytes and prefix; the historical launch instruction was left unchanged. Carried as a provenance note.
2. **R11 P3 — temporary parser test.** The reported 17-pass temporary parser result has no official exit-code or safety receipt. It remains NOT VERIFIED and is not evidence of a pass.
3. **Gate A residual P2 — inherited `PYTHONPATH` / `PYTHONHOME`.** Accepted by the owner for the successful Gate A run with the owner-reported empty-environment check described above; not enforced by the runner.
4. **Gate A provenance P3.** Correction 4 names the wrong self-matching scan file. The correct file is `preview-safety-scan.json`; the correction is recorded in the Gate A acceptance entry without changing Correction 4.
5. **Inherited implementation limits.** K3 remains unresolved and outside S1a-P. The SRS age-band reference/version remains an upstream limitation; this record does not claim NFR-38 or AC-65 is fully satisfied. System-role negative cases not representable by the current identity model remain NOT RUN. External consumers of the Teacher-profile POST remain NOT VERIFIED; Bruno request 013 and `validate_be_full_collection.py` remain documentation debt under D-164.
6. **Acceptance record.** Gate A and Gate B are ACCEPTED by the owner. S1a-P is ACCEPTED at the Parent profile foundation scope and with the limits listed in this section. D-188 records the owner decision after Gate B. S1b remains DEFERRED; S2, S3, and M3–M6 are not opened.

## 7. Boundaries and NOT RUN

- No cleanup, downgrade, or further database operation is authorized by this record. The coordinator did not connect to PostgreSQL or run Alembic, a launcher, Gate A, or Gate B; the Gate A and Gate B results above are recorded from their respective log folders.
- No Modal/provider/network action occurred; `OWNER_MODAL_CALL_APPROVED=NO` remains unchanged.
- No stage, commit, or push was performed.
- S1a-P is owner-accepted at the documented scope and limitations. S1b remains DEFERRED; S2, S3, and M3–M6 remain closed pending their own approval workflows.
