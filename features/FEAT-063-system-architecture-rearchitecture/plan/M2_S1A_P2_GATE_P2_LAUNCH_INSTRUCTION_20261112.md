# M2 S1a-P2 Gate P2 Owner Launch Instruction

**Status: APPROVED (Gate P2 only) / NOT LAUNCHED.** This reviewed instruction accompanies the Gate P2-only approval entry and contains the single owner-run command. Gate P2 remains NOT LAUNCHED until the owner runs that command.

## Scope and effect

This is one owner-run PostgreSQL Gate P2 invocation for Parent-owned list, deletion-request, and command-receipt behavior only. It uses an application-layer Parent-role stub. It does not query the production BE1 role adapter or seed/change BE1 identity data. Production BE1 role-adapter behavior against PostgreSQL remains NOT COVERED. The owner-reported absence of account_id, account_role, and role_revision in public.be1_adult_identities is unverified by Codex. No Alembic command, migration or DDL is included; the runner and test perform a read-only check of `public.alembic_version`. No Docker, Modal, provider, or external network action is included. The target is the local PostgreSQL instance only: database sketch2life_m2_s1a, loopback 127.0.0.1:5433, PostgreSQL 17, user postgres.

The pre-run inventory must equal the accepted S1a-P Gate B post-inventory: 120 tables, 36 total rows, and SHA-256 5A5DBC464ED1FD57C88860BD9E0313920B328A9EF39BB37EA4C91B631B8C1D98. The run is expected to add exactly one parent.child_profiles row, two parent.profile_revisions rows, and three parent.command_receipts rows, for six rows total. The `public.alembic_version` value must remain unchanged. Rows are retained; no cleanup or retry is allowed.

## Pins

Before launch, match the final values below against the installed bytes and the separately reviewed Gate P2 approval entry:

| Artifact | Repository-relative path | SHA-256 |
|---|---|---|
| Gate P2 runner | features/FEAT-063-system-architecture-rearchitecture/evidence/scripts/m2_s1a_p2_gate_p2_20261112.py | 314978BB27BCB2B24C1F24F2F041F482550A33FB6A2782F9D0766124C52AF1F9 |
| Gate P2 PostgreSQL test | backend/tests/integration/test_m2_s1a_p2_parent_postgres.py | E60EA792B715837685A1AF3C73CF497F12FBF24C0130BFAE5B3E36319ACBE665 |
| Draft 7 specification | features/FEAT-063-system-architecture-rearchitecture/plan/M2_S1A_P2_TASK_APPROVAL_DRAFT7_20261112.md | 49B5352CA552DEC9C53C4B155C196C64FD0CE9115E844FC0CBFB8BF3613B66A1 |
| R5 implementation allowlist | tmp/m2-s1a-p2/ALLOWLIST_DRAFT_20261112_R5.md | 4C891112CB894ADF265927F392A437D66BE9DFDF5B1B06DF162ABD1264188DFA |
| Accepted Gate B post-inventory | .claude/handoff/logs/M2_S1A_P_GATE_B_20261109/20261111T151904Z_8b6474437245/post-inventory.json | 5A5DBC464ED1FD57C88860BD9E0313920B328A9EF39BB37EA4C91B631B8C1D98 |

Canonical destination: `features/FEAT-063-system-architecture-rearchitecture/plan/M2_S1A_P2_GATE_P2_LAUNCH_INSTRUCTION_20261112.md`. A separately reviewed Gate P2 approval entry and a separate current owner launch authorization are required before execution.

## Preconditions

Before launch, confirm that the feature TASK_APPROVAL.md has a separately cold-reviewed Gate P2 approval entry with Status APPROVED / NOT LAUNCHED; runner, test, instruction, decision, implementation-file and exact untracked-manifest pins all match; and the Gate B post-inventory file matches the hash and inventory above. Stop on any mismatch. Confirm the expected branch, HEAD, and empty index.

Immediately before launch, the owner must confirm that the parent PowerShell shell and its process environment have no variable whose name begins with PYTHON, PYTEST, DATABASE, PG, POSTGRES, SQLALCHEMY, or ALEMBIC. Do not read .env.

### Credential boundary

**Credential boundary (Owner decision, 2026-11-13, Option A):** The prohibition on a database URL or password applies to the parent PowerShell shell and its process environment, command text, shell history, logs, and files. After the hidden `getpass` prompt, the runner may construct the database URL in memory and pass it in the pytest child-process environment as `SKETCH2LIFE_DATABASE_URL` and `S1A_P_TEST_DATABASE_URL` for the duration of the run, matching the accepted S1a-P Gate B runner. Residual risk: another process running as the same account may read that child-process environment while pytest runs. The owner may rotate the database password after the run. The runner remains unchanged.

## Owner command

After all approvals, pins and environment checks pass, run this one command from the repository root in PowerShell:

    & .\backend\.venv\Scripts\python.exe .\features\FEAT-063-system-architecture-rearchitecture\evidence\scripts\m2_s1a_p2_gate_p2_20261112.py --run-gate-p2

The runner reserves its unique output directory and completes local guards before prompting once for the PostgreSQL password with hidden getpass input. Enter the password only at that prompt. Gate P2 has no APPLY_PARENT_ONLY_PREVIEW prompt. Do not retry this one-shot run.

## Expected result and evidence to return

Expected successful evidence: RUN_ID; LOG_DIR; POST_INVENTORY_SHA256; process exit code 0; official pytest summary exactly 1 passed; and the full log folder, including runner-status.json, safety-scan.json, pre-inventory.json, post-inventory.json, pytest.exit.txt, pytest.summary.txt, and pytest stdout/stderr. Confirm the total row increase is six with the exact 1/2/3 table delta above and the expected inventory hash. Never send the password or database URL. If the runner stops, the summary is absent or ambiguous, the safety scan finds anything, the inventory differs, or output writing fails, stop and do not retry.

OWNER_MODAL_CALL_APPROVED=NO. This instruction does not grant Modal approval or accept S1a-P2, and it does not open S1b, S2, S3, or M3-M6. Gate P2 remains NOT LAUNCHED until the owner runs the single command.


## Proposed changes from the current live draft

- Adds the accepted Gate B inventory hash, 120-table / 36-row baseline, unchanged Alembic revision, and exact six-row expected delta.
- Adds a pin table for the Gate P2 runner, PostgreSQL test, Draft 7, R5 allowlist, and accepted Gate B post-inventory.
- Makes branch, HEAD, empty-index, implementation-pin, exact-untracked-manifest, database-identity, and environment-prefix checks explicit preconditions.
- Gives the single PowerShell command, hidden `getpass` prompt, no-preview-prompt note, no-retry rule, and exact evidence to return.
- Records Owner Decision Option A: the no-URL/no-password environment rule applies to the parent PowerShell process; the runner-created pytest child environment may hold the URL during the run, with same-account process-read risk and optional post-run password rotation. The runner and pin remain unchanged.
- Records the status `APPROVED (Gate P2 only) / NOT LAUNCHED`; the owner has not yet run the single command.
