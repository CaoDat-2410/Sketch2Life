# M2 S1a-P Gate B Launch Instruction — Draft R6
**Review-copy path:** `tmp/m2-s1a-p-gate-b-review/GATE_B_LAUNCH_INSTRUCTION_DRAFT_R6_20261111.md`.

**Intended repository path:** `features/FEAT-063-system-architecture-rearchitecture/plan/M2_S1A_P_GATE_B_LAUNCH_INSTRUCTION_DRAFT1_20261109.md`.

**Status:** DRAFT / NOT APPROVED / NOT LAUNCHED.

> **DO NOT LAUNCH.** Gate B is unavailable until Gate A's logs have been reviewed, the owner has explicitly accepted the Gate A closure, and a separate Gate B approval addendum has been pinned and independently reviewed.

## Scope and preconditions
### Gate A result and required closure record

The owner reports that Gate A was accepted on 2026-11-11. The successful runner log is `.claude/handoff/logs/M2_S1A_P_20261109/20261111T063503Z_gate_a_486a6b6388d7/`. Its pre-inventory is SHA-256 `765271C257868A4CFC4AB5F9E2CF6BB9912306A94F35E4A785692E45D325D3E7` (117 tables, 29 rows, 29 marker rows). Its post-inventory is SHA-256 `A198BF505273FFB81F75A819E9A12400B918B17B189D4DB33F494B3B1B2F2E28` (120 tables, 30 rows, 29 marker rows); the three new `parent.*` tables are empty, and `public.alembic_version` advances from zero rows to one row for `20261109_m2_parent_profiles`.

At this snapshot, the owner has reported accepting Gate A, but `approvals/TASK_APPROVAL.md` has no `M2 S1a-P Gate A Closure Acceptance —` section, and the intended Gate B launch-instruction destination is not present. This review copy substitutes for neither record. Do not launch until the Gate A closure acceptance is recorded append-only, the canonical launch instruction is materialized byte-for-byte from an approved copy, and final pins are refreshed and independently reviewed.

The current Gate B runner was corrected to select the latest of the five `M2 S1a-P Gate A Approval —` entries. `_latest_gate_a_approval()` validates the selected entry status, branch, HEAD, Modal flag, required fields, and the approval-prefix hash against the first Gate A heading. The current `_verify_approval()` still safely stops with `APPROVAL_SECTION_INVALID` because no `M2 S1a-P Gate B Approval —` entry exists. Separately, it requires an accepted `M2 S1a-P Gate A Closure Acceptance —` entry; that closure entry is also absent. This candidate is therefore not runnable and does not grant permission to append either record.


Gate B runs the single owner-only PostgreSQL acceptance in `backend/tests/integration/test_m2_s1a_parent_postgres.py` against only `sketch2life_m2_s1a` on the local PostgreSQL 17 instance at loopback port 5433, user `postgres`. It does not run Alembic, connect to `sketch2life`, clean rows, downgrade, launch Modal/provider work, or open another phase.

Before the owner types the command, the Gate B runner requires all of the following:

- The Gate B record is expected to use the standard list and inline-code formatting, but the current `_status_value()` parser validates the expected status value without requiring the `- ` marker or inline-code formatting; it also accepts a matching plain-text value. This is owner-accepted parser residual risk R6 item 4. Do not describe formatting alone as a runner-enforced authorization check. The Gate B record must still contain exactly one matching status value, and its approval-prefix SHA-256 and artifact pins must match the approved inputs.
- The approval's `OWNER_MODAL_CALL_APPROVED` field is exactly `NO` in the required Markdown field format; the runner checks that record value and separately requires the process environment value to remain `NO`.
- The Gate A approval, Gate B approval and this pinned instruction contain identical Mode E/R/E/N backend source hash tables whose path set exactly equals Draft 8's E/R/E/N backend paths. The runner recomputes each current file hash before proceeding.
- Separately, Gate B rechecks every Draft 8 §5 R/H hash. It requires exact bytes except for the three append-only records `DECISIONS.md`, `TASK_APPROVAL.md`, and `M2_PROGRESS_REPORT_FOR_CODEX_20261109.md`, where the Draft 8 hash must match a current byte prefix. The current full `DECISIONS.md` hash and the approved `TASK_APPROVAL.md` prefix are checked separately. This includes `backend/pyproject.toml`.
- The Gate A closure section must contain the accepted status value and an artifact table containing the same post-inventory path and hash. The Gate A approval section must contain the approved/not-launched status value. The current parser's permissive Markdown handling remains as described above and in R6; do not infer stricter syntax validation than the code performs.
- Branch, HEAD and empty index match the Gate B approval; tracked edits remain in the Draft 8 editable set.
- Every path from `git ls-files --others --exclude-standard` is either an exact Draft 8 mode-N path or appears in the separately pinned exact untracked Markdown manifest with matching bytes. No path-prefix filtering is used for untracked files. Every manifest path must be canonical and repository-relative, contain no empty, `.` or `..` component, and resolve under an approved evidence or plan root before it is hashed; unsafe paths stop before hashing.
- All inherited database environment variables are absent. The script does not read `.env`. It reserves a unique ignored log directory and all files, including pytest basetemp, before asking for the password.
- The read-only pre-inventory matches the accepted Gate A post-inventory projection: identity, all tables and row counts, S1a-T markers, total rows, unmatched rows, Parent schema, and exact Alembic version. Only capture run ID and derived status are excluded from the comparison.


## Candidate pins at this review snapshot

| Input | SHA-256 |
|---|---|
| Draft 8 S1a-P specification | `E9C7FC9D7843F7466B88B801BFF26278A0E1B9C726EF770F8229C419C62F8118` |
| DECISIONS.md | `0928BDFEBBBB30AF887F80E656940CF6759EC7637A8703477A54CBE28F7CF8F2` |
| TASK_APPROVAL.md current bytes | `FC39AC2CFD38437647DE6598436C5299C0730D78D9F7BD3C4A56C10968945BA1` |
| Gate B runner | `F858C38B439BB3D2F61A8CF71B0D71129390F4D7034130B4A5C4AA79C9C0156E` |
| Temporary Gate B parser regression test | `CCFA464395A997F0D5B14ACC6F2A5627525063AF68BBACFA56AF56B411FA3818` |
| Gate A post-inventory | `A198BF505273FFB81F75A819E9A12400B918B17B189D4DB33F494B3B1B2F2E28` |

## Gate A invocation reconciliation

The latest owner report states seven Gate A invocations: six stops followed by one PASS. The six reported stops were one `PINNED_APPEND_ONLY_INPUT_MISMATCH` before output reservation and five `OFFLINE_PREVIEW_NOT_ACCEPTED` stops caused by rejected preview input. The inspected Gate A log root contains six reserved runner directories: five preview-stop records and one PASS record. The pin-mismatch stop has no corresponding reserved directory in that log root. Each of the five reserved preview-stop directories has zero-byte pre- and post-inventory files. These counts distinguish owner-reported invocations from log-backed reserved directories; no missing log is inferred to exist.

## Offline checks completed before this draft

| Check | Result and evidence |
|---|---|
| Temporary parser regression pytest | The latest saved stdout file `tmp/m2-s1a-p-gate-b-review/checks_20261111/parser-pytest-owner-fix-01.stdout.txt` records `15 passed in 0.66s`; the paired stderr file is empty. No standalone `exit-code.txt` or `safety-scan.json` exists for this command, so its exit and safety status are NOT VERIFIED. Stdout SHA-256: `ecfb95851f6f1b222142751526f97131b30821a270ce26f807338177f0ab8485`; parser test source SHA-256: `CCFA464395A997F0D5B14ACC6F2A5627525063AF68BBACFA56AF56B411FA3818`. |
| Pinned post-pytest attempt 1 | NOT RUN: log `20261111T082803Z_post-pytest_9c5f144f22b2` had no official exit/summary/safety result. |
| Pinned post-pytest attempt 2 | NOT RUN: log `20261111T084528Z_post-pytest_5a841d3618c5` had no official exit/summary/safety result. |
| Replacement pinned post-pytest | Coordinator-run via the approved wrapper; log `20261111T085228Z_post-pytest_049b7fe8a334`; exit 0; `280 passed in 56.68s`; safety counts all zero. |
| Ruff | Log directory `20261111T085505Z_ruff_89fcbc2672cd`; saved `exit-code.txt` records inner Ruff exit 1, with only the accepted pre-existing I001 at `backend/tests/contract/test_openapi_contract_catalog.py:3:1`; no other diagnostic; safety counts zero. The coordinator-reported outer wrapper exit was 0, but no separate outer-wrapper receipt is persisted in this directory, so that outer exit is NOT independently verified from the saved files. |
| `validate_repository_security.py` | Wrapper log directory `20261111T085531Z_validate-security_d134b35883f7`; exit 0; `REPOSITORY_SECURITY_VALID`, 7107 files scanned; safety counts zero. |
| `git diff --check` | Wrapper log directory `20261111T085627Z_diff-check_fe20c7653a66`; exit 0 with empty stdout/stderr; safety counts zero. |

These offline checks are evidence only. They do not create a Gate B approval, do not create Gate A closure acceptance, and do not authorize a database action.

## Mode E/R/E/N backend source hashes

The final Gate B Approval must copy this full table unchanged from the latest Gate A Approval and this reviewed launch instruction. The runner rejects missing, extra, duplicate, different or stale hashes across those sections.

**Mode E/R/E/N backend source SHA-256:**

| Path | SHA-256 |
|---|---|
| `backend/alembic/env.py` | `21D68C1E4620F29E3A5ACD59359657EF365AF1121F1377DEE1A55D2671877F17` |
| `backend/src/sketch2life/interfaces/http/app.py` | `29C2776E268D38397DCDCDF7F0411E6E1BEC09FF9B27F91A84B62EAE2169AB67` |
| `backend/src/sketch2life/interfaces/http/openapi_contract.py` | `20FE4BB11C0C76FB4840AB9CF6BBCC30EBB3FB73EDEADDDC2381214BA51C7D44` |
| `backend/src/sketch2life/interfaces/http/openapi_contract_amendments.py` | `B0230E5E9820CEA221DBE00934FFC1C90B6BA04E5CD81B5A5DB9D2B0EF9D8AE1` |
| `backend/src/sketch2life/interfaces/http/openapi_srs_v22.py` | `11DCD2CE5D799A976265A5C14810340BBE8C858D2D37C87CB11BF3329358FE0B` |
| `backend/src/sketch2life/interfaces/http/router_composition.py` | `24FD0B2447D8E06762DCCFEA0CD94A23201D839EA4616B37E04F12E5E50B3217` |
| `backend/tests/contract/test_app_composition.py` | `8AB208492B97805FA996670180FB5718C43C03CD2BD250F5E6361EB57D92BE73` |
| `backend/tests/contract/test_openapi_contract_catalog.py` | `7FA90993191E7FD2533620878776FC90CD8BD9701FC0D4733E86BF8E8297D42B` |
| `backend/tests/unit/test_synthetic_eligibility.py` | `1AED1F1D421EA52E20F8BA0B550B9E83FEF3EB953BF58867F212683AC6C4AD0A` |
| `backend/src/sketch2life/domain/parent_profiles.py` | `AFD924E3A2E72B8F3CD14582E6E8147525F5F6FFB465700AE934435490D478B3` |
| `backend/src/sketch2life/application/ports/parent_profiles.py` | `7DF4A2D583EDFC4908C067F777B681B7705C1C10043E27D580AA823472508AE6` |
| `backend/src/sketch2life/application/services/parent_profiles.py` | `D40E845A699835E1AFF566C540ECBBAE8F429525BEBEFA4DEDDB94FBD68BDF2B` |
| `backend/src/sketch2life/contracts/schemas/parent_profiles.py` | `9AFEB47C02505AC1A7EB1BC9FDEC9898C02E6D78FF87F06F0C32D7114086CFC4` |
| `backend/src/sketch2life/infrastructure/persistence/parent_models.py` | `B853878504D0A001C9B376DF4C08AC8554B25818D913D9AA42317DA26E0544E8` |
| `backend/src/sketch2life/infrastructure/persistence/parent_profile_repository.py` | `4D9C502FEA7E482607CF485CB11767C5280FFF3BA1F9E4055353978EB7424751` |
| `backend/src/sketch2life/interfaces/http/parent_runtime.py` | `FCF6FDAA8A6BE8B6F14405CB5F0CFF25EB7D6ED9F1890A131342747C1BB74A22` |
| `backend/src/sketch2life/interfaces/http/routers/parent_profiles.py` | `DBEF892945862FA470DF514FF08A4578016C61C1E60F050D5F408F6660176066` |
| `backend/alembic/versions/20261109_m2_parent_profiles.py` | `73B907E3782A324EF23F51C30A8F53F2145DDA0E90FE31B5CC686C18BC2922FB` |
| `backend/tests/unit/test_parent_profiles.py` | `3BF726A8E0C934200DA1FE6F29C6254705D8A8EAABA174A3629CB0A0726C1853` |
| `backend/tests/unit/test_parent_profiles_service.py` | `B9B3346B766E821B2712FFED1B7CA858AD5C29284D107B8175480DECDD44F218` |
| `backend/tests/unit/test_parent_profiles_migration.py` | `C28B2DE4AFE1946816DDD0D58DAC788895EC59D8E7973C64732442F7C9852BA1` |
| `backend/tests/contract/test_parent_profiles_routes.py` | `21FE0AC1FB1247620B18D5AAFA30CAD391CD9E9E7CAF15EFC174D658568F5FD3` |
| `backend/tests/integration/test_m2_s1a_parent_postgres.py` | `2B8E705DA1FA7017D153E59070FCB3214C2455D27EF639C6644BDB22729953A6` |

## Owner-only command

From the repository root in PowerShell, only after the approval and review gates above:

```powershell
& ".\backend\.venv\Scripts\python.exe" ".\features\FEAT-063-system-architecture-rearchitecture\evidence\scripts\m2_s1a_p_gate_b_20261109.py" --run-gate-b
```

The runner creates a unique directory under `.claude/handoff/logs/M2_S1A_P_GATE_B_20261109/`. Gate B has no offline preview confirmation prompt. After local preflight and output reservation, it prompts directly for the PostgreSQL password through hidden `getpass` input. The runner builds the DSN in memory and passes it only to the test child through `S1A_P_TEST_DATABASE_URL`. It also supplies a unique 32-character `S1A_P_GATE_B_RUN_ID`; test rows use that ID in the Parent principal marker. The command must not be retried.

Before pytest starts, the runner constructs a fixed minimal child environment that does not inherit `PYTEST_ADDOPTS` or other pytest/Python control variables, and uses only its fixed pytest arguments plus the pinned `backend/pyproject.toml` configuration. Child stdout and stderr remain in memory until scanned for URI and credential patterns. If a match occurs, both streams are withheld from the logs; only fixed redaction notices and match counts are persisted.

## Expected evidence and stop rules

The runner captures pre-inventory, exact command text, stdout, stderr, exit code, post-inventory, metadata, status and a safety scan. Before writing `post-inventory.json`, it resets the safety-scan state to `NOT_RUN`; write failure or interruption therefore cannot preserve an earlier `PASS`. The pytest official summary must report exactly one passed test and no failure/error. Post-inventory must show exactly one marked Parent profile, two marked revisions and three marked receipts; all pre-existing table counts and the Alembic version remain unchanged; total row count increases by six; there are no unmatched rows. No cleanup occurs.

If the process times out or termination is unconfirmed, do not perform another database query and do not retry. A stop after output reservation, including Ctrl+C at a prompt, records a stopped status. If termination is confirmed, the runner scans the reserved logs and records the safety-scan state. For `PROCESS_TERMINATION_UNCONFIRMED` or `PYTEST_ROOT_EXIT_UNCONFIRMED`, it records `SAFETY_SCAN=NOT_COMPLETE_PROCESS_TERMINATION_UNCONFIRMED`; do not claim the logs were scanned. Always record `PROCESS_TREE_CHILD_ENUMERATION=NOT_VERIFIED`. For any nonzero exit, missing pytest summary, inventory mismatch, safety match, missing output or changed pin, stop and return the complete relative log directory and actual exit code. Never send a password, DSN or raw secret-bearing line.

This instruction does not itself approve Gate B or accept S1a-P. Gate B remains owner-only and `OWNER_MODAL_CALL_APPROVED=NO`.
