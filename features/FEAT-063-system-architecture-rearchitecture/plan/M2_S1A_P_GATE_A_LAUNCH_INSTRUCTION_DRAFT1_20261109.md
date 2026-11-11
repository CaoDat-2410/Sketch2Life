# M2 S1a-P Gate A Launch Instruction — Draft 1

**Status:** INSTRUCTION ONLY / NOT AN APPROVAL / NOT LAUNCHED.

> **DO NOT LAUNCH YET.** This instruction is inactive until the separate Gate A addendum is approved and independently reviewed.

This document is not an execution approval. The existing S1a-P approval authorizes implementation and offline checks only. Gate A requires a separate `APPROVED / NOT LAUNCHED` Task Approval addendum and a fresh cold independent review before this instruction may be used.

## Purpose and scope

Gate A applies the approved Parent-only revision to the task database and records a read-only inventory before and after migration. It does not authorize Gate B, cleanup, downgrade, changes to other schemas, or work in another M2 phase.

Target identity encoded in the reviewed runner:

- Database: `sketch2life_m2_s1a`.
- PostgreSQL instance: loopback host `127.0.0.1`, port `5433`, PostgreSQL major version `17`.
- Database user: `postgres`.
- Expected revision: `20261109_m2_parent_profiles`.
- Expected pre-migration inventory: the S1a-T `inventory.post.json`, SHA-256 `710F4A42FA817FA2EC27DC154BF6023F35FD51C012BBACA39782320357D8737E` (117 tables, 29 rows).

## Reviewed artifacts to pin in the separate Gate A addendum

| Artifact | Path | Current SHA-256 |
|---|---|---|
| S1a-P specification | `features/FEAT-063-system-architecture-rearchitecture/plan/M2_S1A_P_TASK_APPROVAL_DRAFT8_20261109.md` | `E9C7FC9D7843F7466B88B801BFF26278A0E1B9C726EF770F8229C419C62F8118` |
| Gate A runner | `features/FEAT-063-system-architecture-rearchitecture/evidence/scripts/m2_s1a_p_gate_a_20261109.py` | `7022F6532C8FB13E2F3147F6C4B2EBC46CAF2493E7CFC89DBB71CE8D11190105` |
| S1a-T baseline inventory | `.claude/handoff/logs/M2_S1A_T_20261107/f7fe88273c7f4dd89b3913efeac6f8fb/inventory.post.json` | `710F4A42FA817FA2EC27DC154BF6023F35FD51C012BBACA39782320357D8737E` |

The Gate A approval entry must contain the same exact backend source hash manifest. The runner compares this table with the approved manifest and the Draft 8 E/R/E/N backend allowlist before any owner prompt.

**Mode E/R/E/N backend source SHA-256:**

| Path | SHA-256 |
|---|---|
| `backend/alembic/env.py` | `21D68C1E4620F29E3A5ACD59359657EF365AF1121F1377DEE1A55D2671877F17` |
| `backend/alembic/versions/20261109_m2_parent_profiles.py` | `73B907E3782A324EF23F51C30A8F53F2145DDA0E90FE31B5CC686C18BC2922FB` |
| `backend/src/sketch2life/application/ports/parent_profiles.py` | `7DF4A2D583EDFC4908C067F777B681B7705C1C10043E27D580AA823472508AE6` |
| `backend/src/sketch2life/application/services/parent_profiles.py` | `D40E845A699835E1AFF566C540ECBBAE8F429525BEBEFA4DEDDB94FBD68BDF2B` |
| `backend/src/sketch2life/contracts/schemas/parent_profiles.py` | `9AFEB47C02505AC1A7EB1BC9FDEC9898C02E6D78FF87F06F0C32D7114086CFC4` |
| `backend/src/sketch2life/domain/parent_profiles.py` | `AFD924E3A2E72B8F3CD14582E6E8147525F5F6FFB465700AE934435490D478B3` |
| `backend/src/sketch2life/infrastructure/persistence/parent_models.py` | `B853878504D0A001C9B376DF4C08AC8554B25818D913D9AA42317DA26E0544E8` |
| `backend/src/sketch2life/infrastructure/persistence/parent_profile_repository.py` | `4D9C502FEA7E482607CF485CB11767C5280FFF3BA1F9E4055353978EB7424751` |
| `backend/src/sketch2life/interfaces/http/app.py` | `29C2776E268D38397DCDCDF7F0411E6E1BEC09FF9B27F91A84B62EAE2169AB67` |
| `backend/src/sketch2life/interfaces/http/openapi_contract.py` | `20FE4BB11C0C76FB4840AB9CF6BBCC30EBB3FB73EDEADDDC2381214BA51C7D44` |
| `backend/src/sketch2life/interfaces/http/openapi_contract_amendments.py` | `B0230E5E9820CEA221DBE00934FFC1C90B6BA04E5CD81B5A5DB9D2B0EF9D8AE1` |
| `backend/src/sketch2life/interfaces/http/openapi_srs_v22.py` | `11DCD2CE5D799A976265A5C14810340BBE8C858D2D37C87CB11BF3329358FE0B` |
| `backend/src/sketch2life/interfaces/http/parent_runtime.py` | `FCF6FDAA8A6BE8B6F14405CB5F0CFF25EB7D6ED9F1890A131342747C1BB74A22` |
| `backend/src/sketch2life/interfaces/http/router_composition.py` | `24FD0B2447D8E06762DCCFEA0CD94A23201D839EA4616B37E04F12E5E50B3217` |
| `backend/src/sketch2life/interfaces/http/routers/parent_profiles.py` | `DBEF892945862FA470DF514FF08A4578016C61C1E60F050D5F408F6660176066` |
| `backend/tests/contract/test_app_composition.py` | `8AB208492B97805FA996670180FB5718C43C03CD2BD250F5E6361EB57D92BE73` |
| `backend/tests/contract/test_openapi_contract_catalog.py` | `7FA90993191E7FD2533620878776FC90CD8BD9701FC0D4733E86BF8E8297D42B` |
| `backend/tests/contract/test_parent_profiles_routes.py` | `21FE0AC1FB1247620B18D5AAFA30CAD391CD9E9E7CAF15EFC174D658568F5FD3` |
| `backend/tests/integration/test_m2_s1a_parent_postgres.py` | `2B8E705DA1FA7017D153E59070FCB3214C2455D27EF639C6644BDB22729953A6` |
| `backend/tests/unit/test_parent_profiles.py` | `3BF726A8E0C934200DA1FE6F29C6254705D8A8EAABA174A3629CB0A0726C1853` |
| `backend/tests/unit/test_parent_profiles_migration.py` | `C28B2DE4AFE1946816DDD0D58DAC788895EC59D8E7973C64732442F7C9852BA1` |
| `backend/tests/unit/test_parent_profiles_service.py` | `B9B3346B766E821B2712FFED1B7CA858AD5C29284D107B8175480DECDD44F218` |
| `backend/tests/unit/test_synthetic_eligibility.py` | `1AED1F1D421EA52E20F8BA0B550B9E83FEF3EB953BF58867F212683AC6C4AD0A` |

The separate addendum must also pin the exact launch-instruction hash, the current `DECISIONS.md` hash, and the approved untracked-file manifest. At the one-time manifest snapshot, the only S2/S3 Markdown files remaining untracked in `plan/` and `evidence/` were S2 Draft 5, S3 Draft 5, and review Round 4. Their contents were not opened or edited; their SHA-256 values were recorded by path in the separate Gate A addendum. Eleven older S2/S3 drafts and review records were moved to `tmp/m2-s2-s3-archive/`. The Gate A addendum must pin the three remaining files and all other exact manifest entries from the snapshot; any changed or unexpected untracked path is a hard stop. Then a fresh cold reviewer must return READY or READY WITH NOTES with 0 P1 and 0 P2. The addendum must include the exact `M2 S1a-P Gate A Approval` heading and preserve `OWNER_MODAL_CALL_APPROVED=NO`.

## Owner-only command after the separate approval and review

From the repository root in PowerShell, run exactly once:

```powershell
& ".\backend\.venv\Scripts\python.exe" ".\features\FEAT-063-system-architecture-rearchitecture\evidence\scripts\m2_s1a_p_gate_a_20261109.py" --run-gate-a
```

Run this command only after the separate Gate A addendum is recorded as `APPROVED / NOT LAUNCHED` and receives a fresh cold independent review with READY or READY WITH NOTES and 0 P1 and 0 P2. The owner alone decides whether to execute it; this instruction is not itself authorization. The runner checks the branch, HEAD, empty Git index, clean database-related environment, pinned artifacts, approval entry, allowlist and baseline before proceeding.

The runner creates a new unique output directory under `.claude/handoff/logs/M2_S1A_P_20261109/`; it does not reuse or overwrite prior run folders. Do not rename, delete, or replace existing output folders. The generated directory name uses a UTC timestamp and a random suffix.

The runner first performs and records its offline SQL preview. At the explicit preview prompt, inspect the preview and type exactly `APPLY_PARENT_ONLY_PREVIEW` only if it matches the reviewed Parent-only scope. The runner then requests the PostgreSQL password using a hidden prompt. Enter it only there; do not put it in a command, environment variable, transcript, or log.

## Stop rules

Run no more than once. Do not retry after any stop, nonzero exit, timeout, missing official output, safety-scan finding, or inventory mismatch. Stop if the target identity, branch, HEAD, index, environment, approval, any pin, baseline, preview, or expected schema state differs. Do not manually repair the database or continue with Gate B.

The runner's success record intentionally states `PROCESS_TREE_CHILD_ENUMERATION=NOT_VERIFIED`; do not describe child-process enumeration as verified. `OWNER_MODAL_CALL_APPROVED=NO` remains unchanged. Modal, provider, Docker, network, database cleanup, and downgrade remain out of scope.

## Evidence to return

After the owner-run command finishes, return the generated relative log-directory path, the console summary and exit code, and the complete generated log contents, including `pre-inventory.json`, `post-inventory.json`, `runner-status.txt`, `runner-metadata.txt`, preview output and exit, Alembic stdout/stderr/exit, and safety scans. Include the reported post-inventory SHA-256. Do not send the password or any database URL. Stop after returning the evidence; Gate B requires separate reconciliation, owner acceptance of Gate A, and its own reviewed approval.
