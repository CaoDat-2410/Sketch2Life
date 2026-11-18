# FEAT-063 M2 — PostgreSQL acceptance gate G1 (reduced) — Stage B Task Approval Draft 2

- **Status:** DRAFT / NOT APPROVED / NOT LAUNCHED. It authorizes nothing: no container, database, migration, connection, process start, test run, network access, commit or push.
- **Date:** 2026-11-17. **Author:** coordinating Claude session (Fable 5.2). **Owner:** Person 2. This draft and the revised files are not independently reviewed.
- **Predecessor, unchanged:** Stage B Draft 1 (`07575D88CD275FF3A5108F4F04E6AAD8D2D09849BCD8E39F0C5DA89922A0D522`); cold review R1 (Opus 5.5, high): code, driver and draft NOT READY, 0 P1 / 4 P2 / 15 P3, `evidence/M2_S2_POSTGRES_GATE_G1_STAGE_B_COLD_REVIEW_R1_20261117.md`, SHA-256 `38480930B4A2999F45328C03A962BD98F99D5D5323F301D90E3734DC2A6EC003`. Section 7 disposes of H1 to H19.
- **Builds on:** Stage A approval (`approvals/TASK_APPROVAL.md`, owner: "Duyệt chặng A") on `plan/M2_S2_POSTGRES_GATE_G1_TASK_APPROVAL_DRAFT2_20261117.md`, SHA-256 `5CCA1171534E8A4FD431E7FF0FAB4E645F3DE4CFA3AA942F1BDA8F996745FE4C` ("G1 Draft 2"). Its decisions, deviations DV-1 to DV-18 and claim rule apply unchanged.
- **Scope of this draft (owner: "Sửa rồi chạy thử"):** rehearsals only. The gate run is **not** requested here; it cannot be requested until finding H1 is decided (section 2).
- `OWNER_MODAL_CALL_APPROVED=NO`.

## 1. Pins

| Item | Pin |
|---|---|
| Test file `backend/tests/integration/test_m2_s2_g1_parent_story_postgres.py` | 47,847 bytes, SHA-256 `BC3FBE628CEEA8E79CF6EDD96963F3EE45D6565FDDB65FD8C6888781476AF4A2` |
| Launcher `backend/tests/integration/m2_s2_g1_launcher.py` | 5,218 bytes, SHA-256 `00FED31506F1510192471A81DA321CC5EBFD68140E0A089125FF3D4B14959749` |
| Driver (scratch, repository-root `tmp/m2-s2-pg-gate/g1_gate_driver.py`) | 23,270 bytes, SHA-256 `E963B585BFB59FEF3F5ACA70C7D18FCF4E8D9E4FFB0FEAD3AF2062EB70A97CD6` |
| Migration manifest (same folder, `migration_file_hashes_7cc5cf74.txt`, 31 files) | SHA-256 `8659E108D86135859A5F5EF8944A95CE9376DF818484B6744CCF474CFED9CAB6` |
| Image | `postgres@sha256:3540c0362c809df084ffac0ae69fe794515f9de92692f02178bcdce0ef0302ac` (read from the local Docker store by the session; **the owner confirms it by approving**) |
| Interpreter | the task interpreter (`tmp/m2-s2-mapper-env/.venv`), Python 3.12.10 |

These supersede the code-file pins in the Stage A report and in Stage B Draft 1. After the changes the static checks were repeated: Ruff 0 and Mypy 0 on the two code files, LF only, 20 tests collected offline; driver Ruff and Mypy clean, only `--help` executed. The driver embeds the pins of both code files, the manifest, the image, the 13 heads and the 10 version rows, and stops when any differs.

## 2. Finding H1: a product defect, and what the first rehearsal is for

By reading (review R1 of Stage B, and the earlier review of G1 Draft 1), `attach_artwork` in `backend/src/sketch2life/infrastructure/persistence/parent_story_repository.py` fails on PostgreSQL under the product's own session factory: it queues two asset-metadata rows, then inserts into `core_asset_lineage` without a flush, the factory has `autoflush=False`, and the lineage foreign keys are checked immediately. Expected effect: 409 `PARENT_STORY_ARTWORK_CONFLICT` on every call, in the test and on the production artwork route alike. No existing test calls this method. Nothing has been run.

Consequences for this approval:

- Case 08-03p is expected to **fail with its STOP message in rehearsal 1**. Expected rehearsal-1 result: 19 passed, 1 failed (`test_08_03p_...`). That outcome confirms the defect by execution; any other outcome is reported as it is.
- The exit rule of G1 Draft 2 (three consecutive full passes) cannot be met while the defect stands. After rehearsal 1 the owner decides, in a separate decision: fix the product in its own approved task and re-pin, or record 08-03p as NOT RUN with an amended count and claim. **No product source is changed under this approval, and the test is not rewritten to avoid the defect.**
- Rehearsal 1 is still worth running first: it exercises every card, the launcher, the migration and the other 19 items for real.

## 3. Preconditions the owner settles before the first card

1. **Commit.** One commit, on the owner's instruction, security validator rerun first, containing: the two code files, `approvals/TASK_APPROVAL.md` (with the Stage A entry and the entry recording this approval), and the gate's record files written so far. Its hash is the `--expect-head` value of every card. This is an explicit exception to "one finished task is one commit": the gate pins a commit, so the files must be committed before the task ends; a second commit will carry the results.
2. **No tracked file is edited between that commit and the last card of a run.** The driver stops if HEAD differs or a tracked file is modified. Results and notes go to new untracked files or stay in scratch until the owner asks for the next commit.
3. **Secret directory.** A folder the owner creates outside every Git checkout and outside the session's working folders (the repositories folder and the downloads folder; the driver refuses both). The driver writes the generated passwords, the client password file and the run marker there. **The coordinating session never reads that folder.**
4. **Ports.** Windows can reserve port ranges that make a free port look busy. If C0 reports a port in use, the owner checks `netsh int ipv4 show excludedportrange protocol=tcp` and reports it; ports are not changed without a new decision.
5. **Egress block: not used in rehearsal 1.** With `--require-egress-block` the `test` card makes one outbound attempt to the documentation-only address `192.0.2.1` and stops unless the firewall refuses it (measured in the driver process only; a per-program rule may not cover the child processes). Without the flag no outbound attempt is made. Whether to require the block for later rehearsals and the gate is decided after rehearsal 1.

## 4. Cards

One command per card, run by the owner in the worktree's `backend` directory. `PY` is the task interpreter, `DRV` the driver path, `SEC` the secret directory, `HEAD` the commit of precondition 1.

```text
PY -I -B DRV <action> --mode rehearsal --index <N> --secret-dir SEC --expect-head HEAD
```

| Card | Action | What it does | Ceiling |
|---|---|---|---|
| C0 | `preflight` | Read-only: HEAD and unmodified tracked files; 31 migration hashes; both code-file hashes; no `.env`; Docker reachable; image present by digest; container and volume names unused; database and API ports free; secret directory acceptable | unlimited |
| C1 | `container-up` | Repeats C0; generates two random passwords and a run marker into `SEC`; starts the container with `--pull never`, published only on `127.0.0.1`, own named volume, bootstrap password by a read-only mounted file; waits for readiness over TCP inside the container; creates role `s2l_m2_gate` (not superuser) and the empty database owned by it; stores the run marker as a database setting; checks inspection output and the container log for both passwords **whether or not role creation succeeded** and reports the result; saves the inspection output; probes identity and emptiness | 1 per run label |
| C2 | `migrate` | Checks the imported package path; probe (identity, marker, empty); `alembic heads` must print exactly the 13 pinned names; then **one** `alembic upgrade heads`; then `alembic_version` must hold exactly the 10 pinned rows | 1 per database (flag file) |
| C3 | `test` | Probe; API port free; checks the imported package path; runs the test file once with the fixed environment of G1 Draft 2 section 4 and the repository's default pytest options cleared; writes `pytest-output.txt` and `result.json`; scans every output file for both passwords | 1 per database (flag file) |
| C4 | `container-stop` | Stops the container and keeps it and its volume | — |
| C5 | `container-remove` with `--confirm-name <container>` | Removes a rehearsal container and its volume (DV-11). Refuses anything that is not a rehearsal container | — |

The environment given to Alembic and pytest is built from the owner's environment with every variable removed whose name starts with `PG`, `AWS_`, `SKETCH2LIFE_`, `M2_S2_G1_`, `S1A_P_`, `BE1_`, `STORYRUN_`, `PYTEST`, `PYTHON`, `ALEMBIC` or `SQLALCHEMY`, plus `DATABASE_URL`; the gate variables are then set. The driver's own probe runs with the `PG` variables removed.

`result.json` records: exit code, timeout flag, the list of test identifiers per outcome, `all_passed_no_skips` (exit code 0, exactly 20 passed, no other outcome), the command, the imported package path, tool versions, hashes of `pyproject.toml` and `uv.lock`, the code pins, the image, and hashes of every output file.

Outputs go to `tmp/m2-s2-pg-gate/runs/rehearsal-<N>/` under the repository root (git-ignored). The driver prints one summary line per card; the owner pastes it, and the session then reads the output folder.

**Sequence for rehearsal N** (N = 1, 2, ...): C0, C1, C2, C3, C4; C5 before the next rehearsal. Each rehearsal uses a new index, hence a new container, volume, passwords and marker. Database port 55441, API port 55451. A card that stops after C1 leaves that run label used: the next attempt takes the next index after C5.

## 5. Stop rules

- Stop and return to the owner on any `STOP:` line; on any failing test other than the expected 08-03p failure of section 2; on a credential found in an output or log; on a mismatch of heads, version rows, identity or marker; when the launcher does not start without a source change; when a process survives termination; on a timeout (the driver then says to check for a leftover launcher on the API port).
- No source file is changed. No row is deleted. The old database `sketch2life_m2_s1a` and ports 5432, 5433, 55432 are never used; the driver's names and ports are fixed constants.
- This approval covers rehearsal mode only. The driver also contains a gate mode; **running it is not authorized by this text.**

## 6. Known limits

- Nothing in the driver has been executed except `--help`. Expect corrections in rehearsal 1.
- The role-creation step runs through the container's local socket as the bootstrap user; the `psql` output is withheld because it can echo the statement.
- The run marker detects mistakes, not tampering.
- The socket guard covers blocking-socket connects and name lookups only (see the launcher's docstring).
- The start-of-run emptiness check covers the fourteen tables the test touches. Review R1 found no INSERT in any migration by text search, so a check of every table would also hold; the narrower check is kept and all table counts are recorded.
- Process liveness is checked through the task list and the port; identifier reuse could give a false "alive".
- G1 Draft 2 section 4 says `role_revision` has only an application-side default; migration `20261110_ar_0001` gives it a server default. The seeding sets it explicitly either way.

## 7. Disposition of review R1 of Stage B (H1 to H19)

| ID | Disposition |
|---|---|
| H1 (P2) | Section 2. Owner's choice: "Sửa rồi chạy thử" — confirm by rehearsal 1 before deciding on the product |
| H2 (P2) | Driver: default options cleared (`-o addopts=`), no extra `-q`; the result is decided from the exit code and the per-test outcome lines |
| H3 (P2) | Preconditions 1 and 2 |
| H4 (P2) | Test: the second tree-kill is removed |
| H5 | Driver: the egress probe runs only with the flag; limits stated in precondition 5 |
| H6 | Driver: logs and inspection are checked on the failure path too; card C1 text corrected |
| H7 | Driver: `result.json` extended; package-path check added to C2 and C3 |
| H8 | Driver: `PYTEST`, `PYTHON`, `ALEMBIC`, `SQLALCHEMY` prefixes cleared; the driver's own `PG` variables removed |
| H9 | Driver: refuses secret folders under the session's working folders |
| H10 | Driver: `--pull never` |
| H11 | Precondition 4 |
| H12 | Launcher docstring corrected |
| H13 | Test: the holder is rolled back before the pool waits when the lock wait fails |
| H14 | Test: 08-03p also checks the cancel receipt's purge state in the database |
| H15 | Partly: the fixture no longer reads a private attribute. The import of the product's private scope-hash helper is kept on purpose, so the test cannot drift from the product's hashing |
| H16 | Driver: timeout recorded in `result.json` with a note; Docker output decoded as UTF-8 with replacement. Gate-label consumption is outside this approval |
| H17 | Section 6 |
| H18 | Precondition 1 |
| H19 | Section 6 |

## 8. Approval block (for the owner)

- [ ] Image digest confirmed.
- [ ] Rehearsals approved (cards C0 to C5, rehearsal mode only), with the expected rehearsal-1 outcome of section 2.
- [ ] Commit instructed (precondition 1), after the entry recording this approval is appended.
- [ ] A delta review is wanted first (Sonnet 5.5 high or Opus 5.5 high; never Fable).
