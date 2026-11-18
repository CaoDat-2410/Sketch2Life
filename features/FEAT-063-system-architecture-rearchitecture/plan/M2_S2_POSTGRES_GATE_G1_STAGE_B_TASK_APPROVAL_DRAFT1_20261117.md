# FEAT-063 M2 — PostgreSQL acceptance gate G1 (reduced) — Stage B Task Approval Draft 1

- **Status:** DRAFT / NOT APPROVED / NOT LAUNCHED. It authorizes nothing: no container, database, migration, connection, process start, test run, network access, commit or push.
- **Date:** 2026-11-17. **Author:** coordinating Claude session (Fable 5.2). **Owner:** Person 2. Not independently reviewed; a cold review (Sonnet 5.5 high or Opus 5.5 high, never Fable) of this draft, the two code files and the driver is recommended before approval.
- **Builds on:** Stage A approval (`approvals/TASK_APPROVAL.md`, entry of 2026-11-17, owner: "Duyệt chặng A") on `plan/M2_S2_POSTGRES_GATE_G1_TASK_APPROVAL_DRAFT2_20261117.md`, SHA-256 `5CCA1171534E8A4FD431E7FF0FAB4E645F3DE4CFA3AA942F1BDA8F996745FE4C` ("Draft 2" below); Stage A report `evidence/M2_S2_POSTGRES_GATE_G1_STAGE_A_REPORT_20261117.md`. Decisions, deviations DV-1 to DV-18 and the claim rule of Draft 2 apply unchanged.
- `OWNER_MODAL_CALL_APPROVED=NO`.

## 1. Pins

| Item | Pin |
|---|---|
| Test file `backend/tests/integration/test_m2_s2_g1_parent_story_postgres.py` | 47,233 bytes, SHA-256 `19D737A220AFC415D8EE46CBA1443C6F6C9DFBBE604BFD4181D9347D8318594E` |
| Launcher `backend/tests/integration/m2_s2_g1_launcher.py` | 5,075 bytes, SHA-256 `E251365CA0ABFA570BFB5CA0F02EFCC45B22FEEAAEDDC8091A7DCC10C8440E40` |
| Driver (scratch, repository-root `tmp/m2-s2-pg-gate/g1_gate_driver.py`) | 20,617 bytes, SHA-256 `5BD89F530B1557621E8EC19B79F13BB08342168920EB47B936E78141072E84E0` |
| Migration manifest (same folder, `migration_file_hashes_7cc5cf74.txt`, 31 files) | SHA-256 `8659E108D86135859A5F5EF8944A95CE9376DF818484B6744CCF474CFED9CAB6` |
| Image | `postgres@sha256:3540c0362c809df084ffac0ae69fe794515f9de92692f02178bcdce0ef0302ac` (read from the local Docker store by the session; **the owner confirms it by approving**) |
| Interpreter | the task interpreter (`tmp/m2-s2-mapper-env/.venv`), Python 3.12.10 |

The driver embeds the pins of both code files, the manifest, the image, the 13 heads and the 10 version rows, and stops when any differs. A change to a code file therefore needs a new driver pin and a new approval.

## 2. Preconditions the owner settles before the first card

1. **Commit.** The two code files are committed (one commit, on the owner's instruction, security validator rerun first). The resulting HEAD is the value passed as `--expect-head` to every card. The driver stops if HEAD differs or a tracked file is modified.
2. **Secret directory.** A folder the owner creates outside every Git checkout and outside the session's working folders (for example on drive D, not under the repository). The driver writes the generated passwords, the client password file and the run marker there. **The coordinating session never reads that folder.**
3. **Egress block (owner's choice per run).** With the flag `--require-egress-block` the `test` card stops unless outbound traffic is blocked (it attempts one connection to the documentation-only address `192.0.2.1` and requires the firewall refusal). Recommended for the gate run; the first rehearsal with the flag shows whether loopback still works under the block. If it does not, stop and ask.

## 3. Cards

Every card is one command, run by the owner in the worktree's `backend` directory. `PY` is the task interpreter; `DRV` is the driver path; `SEC` is the secret directory; `HEAD` is the commit of precondition 1.

```text
PY -I -B DRV <action> --mode <rehearsal|gate> --index <N> --secret-dir SEC --expect-head HEAD
```

| Card | Action | What it does | Ceiling |
|---|---|---|---|
| C0 | `preflight` | Read-only: HEAD and clean tracked state; 31 migration hashes; both code-file hashes; no `.env`; Docker reachable; image present by digest; container and volume names unused; database and API ports free | unlimited |
| C1 | `container-up` | Repeats C0; generates two random passwords and a run marker into `SEC`; starts the container (published only on `127.0.0.1`, own named volume, bootstrap password by mounted file); waits for readiness; creates role `s2l_m2_gate` (not superuser) and the empty database owned by it; stores the run marker as a database setting; saves inspection output after checking it and the container log for both passwords; probes identity and emptiness | 1 per run label |
| C2 | `migrate` | Probe (identity, marker, empty); `alembic heads` must print exactly the 13 pinned names; then **one** `alembic upgrade heads`; then `alembic_version` must hold exactly the 10 pinned rows | 1 per database (flag file) |
| C3 | `test` | Probe; API port free; optional egress requirement; runs the test file once with the fixed environment of Draft 2 section 4; writes `pytest-output.txt` and `result.json`; scans every output file for both passwords | 1 per database (flag file) |
| C4 | `container-stop` | Stops the container and keeps it and its volume | — |
| C5 | `container-remove` (rehearsal only; needs `--confirm-name <container>`) | Removes a rehearsal container and its volume (DV-11). Refuses the gate container | — |

Card outputs go to `tmp/m2-s2-pg-gate/runs/<mode>-<N>/` under the repository root (git-ignored). The driver prints one summary line per card; the owner pastes that line, and the session then reads the output folder.

**Rehearsal sequence** (`--mode rehearsal --index N`, N = 1, 2, 3, ...): C0, C1, C2, C3, C4, then C5 before the next rehearsal. Each rehearsal uses a new index, hence a new container, volume, passwords and marker. Database port 55441, API port 55451.

**Gate sequence** (`--mode gate --index 1`): C0, C1, C2, C3 with `--require-egress-block` if the rehearsals showed it works, C4. No C5. Database port 55440, API port 55450.

## 4. Exit and stop rules

- **Rehearsal exit:** at least three consecutive rehearsals in which C3 reports `all_passed_no_skips: true` (20 passed, none skipped), on unchanged pins. A failing or intermittent rehearsal is understood before continuing; a fix to a code file or the driver restarts the count and needs new pins.
- **Gate ceiling:** one. A failed gate keeps its container, volume and outputs and consumes the ceiling; another attempt needs a new approval.
- **Stop and return to the owner** on any `STOP:` line; on a product defect (in particular the G2 message from case 08-03p: `attach_artwork` failing under the product session factory); on a credential found in an output; on a mismatch of heads, version rows, identity or marker; when the launcher does not start without a source change; when a process survives termination; when the egress block and loopback cannot be combined.
- No source file is changed in Stage B. No row is deleted. The old database `sketch2life_m2_s1a` and ports 5432, 5433, 55432 are never used; the driver's database names and ports are fixed constants.

## 5. What a pass may be claimed to show

As Draft 2 section 3.1: "gate G1 passed with deviations DV-1 to DV-18", on one PostgreSQL 17 container, migrated to the 13 pinned heads, through the composed routes served by a real process, with a synthetic token verifier and seeded data. Not shown: everything in DV-1 to DV-18; anything about M2-AT-09; behaviour with a real provider. Whether that satisfies the M2-AT-08 and M2-AT-10 rows of the S3 ledger is the owner's decision at acceptance, after the evidence report and its independent review.

## 6. Known limits of these cards

- Nothing in the driver has been executed except `--help`. Its first real use is rehearsal 1; expect corrections there (lesson recorded in the handover: every one-shot without a rehearsal failed on first use).
- The readiness wait uses a TCP check inside the container; the role-creation step runs through the container's local socket as the bootstrap user. A failed role creation could write the statement to the server log; the driver checks the log for both passwords and stops if found.
- The run marker detects mistakes, not tampering.
- The emptiness check at the start of the test covers the fourteen tables the test touches, not every migrated table (Stage A report section 5).
- The driver's secret folder holds database passwords for throwaway containers bound to loopback. The owner deletes it when the containers are gone.

## 7. Approval block (for the owner)

- [ ] Commit of the two code files instructed (precondition 1).
- [ ] Image digest confirmed.
- [ ] Rehearsals approved (cards C0 to C5, rehearsal mode).
- [ ] Gate run approved (cards C0 to C4, gate mode) — may be given later, after the rehearsal results.
- [ ] A cold review is wanted first.
