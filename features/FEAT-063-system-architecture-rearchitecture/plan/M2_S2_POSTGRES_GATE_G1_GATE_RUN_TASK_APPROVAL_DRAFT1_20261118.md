# FEAT-063 M2 — PostgreSQL acceptance gate G1 (reduced) — gate run Task Approval Draft 1

- **Status:** DRAFT / NOT APPROVED / NOT LAUNCHED. It authorizes nothing: no container, database, migration, connection, process start, test run, commit or push.
- **Date:** 2026-11-18. **Author:** coordinating Claude session (Fable 5.2). **Owner:** Person 2. This draft is not independently reviewed.
- **Builds on:** G1 Draft 2 (`plan/M2_S2_POSTGRES_GATE_G1_TASK_APPROVAL_DRAFT2_20261117.md`, `5CCA1171534E8A4FD431E7FF0FAB4E645F3DE4CFA3AA942F1BDA8F996745FE4C`: decisions, deviations DV-1 to DV-18, claim rule) and Stage B Draft 2 (`plan/M2_S2_POSTGRES_GATE_G1_STAGE_B_TASK_APPROVAL_DRAFT2_20261117.md`, `07F93EC6B4D33C8928D7D4674E46EAAB19C0279B2A74DE6D20EE78EAF06AB192`: cards, environment, stop rules), both unchanged except as stated here.
- **Basis:** rehearsals 2, 3 and 4, each 20 passed with no skips at commit `b430b67a68e7934721f7ec9b44b96e9071cb989e` on unchanged pins (`evidence/M2_S2_POSTGRES_GATE_G1_REHEARSAL_2_RESULT_20261118.md`, `evidence/M2_S2_POSTGRES_GATE_G1_REHEARSALS_3_4_RESULT_20261118.md`): the rehearsal exit rule is met. Pre-gate delta review R2 (Sonnet 5.5, high): READY WITH NOTES for test, launcher and driver, READY for the product fix, 0 P1 / 2 P2 / 12 P3 (`evidence/M2_S2_POSTGRES_GATE_G1_PRE_GATE_DELTA_REVIEW_R2_20261118.md`).
- `OWNER_MODAL_CALL_APPROVED=NO`.

## 1. What is asked

One gate run: cards C0, C1, C2, C3, C4 of Stage B Draft 2 section 4 in **gate mode**, run by the owner, once.

```text
PY -I -B DRV <action> --mode gate --index 1 --secret-dir SEC --expect-head HEAD
```

Resources, fixed constants of the driver: container and volume `s2l-m2-s2-gate`; database `sketch2life_m2_s2_gate` on `127.0.0.1:55440`; API on `127.0.0.1:55450`; role `s2l_m2_gate`; image `postgres@sha256:3540c0362c809df084ffac0ae69fe794515f9de92692f02178bcdce0ef0302ac` (confirmed by the owner on 2026-11-17). Outputs in the repository-root `tmp/m2-s2-pg-gate/runs/gate-1/`. The gate container and volume are **kept** after the run; the driver refuses to remove them.

## 2. Pins (unchanged since the three passing rehearsals)

| Item | SHA-256 |
|---|---|
| `backend/tests/integration/test_m2_s2_g1_parent_story_postgres.py` | `BC3FBE628CEEA8E79CF6EDD96963F3EE45D6565FDDB65FD8C6888781476AF4A2` |
| `backend/tests/integration/m2_s2_g1_launcher.py` | `00FED31506F1510192471A81DA321CC5EBFD68140E0A089125FF3D4B14959749` |
| `backend/src/sketch2life/infrastructure/persistence/parent_story_repository.py` | `5E33C076A4A13439AB0D02A8D8088D543D277758E78076D709E23CB386CFBDA8` |
| Driver (scratch) `g1_gate_driver.py` | `E963B585BFB59FEF3F5ACA70C7D18FCF4E8D9E4FFB0FEAD3AF2062EB70A97CD6` |
| Migration manifest (31 files) | `8659E108D86135859A5F5EF8944A95CE9376DF818484B6744CCF474CFED9CAB6` |

The gate runs at a **later commit** than the rehearsals: the commit of section 3 adds records only. The driver checks the code-file and migration hashes on every card, so the code under test is the rehearsed code. The source file's hash is pinned here and is checked by the session before the first card and after the last (the driver does not pin it).

## 3. Preconditions

1. One commit, on the owner's instruction, of the approval record (with the entry recording this approval), this draft, the rehearsal records and the review record. Its hash is `--expect-head`. No tracked file is edited from then until card C4 has run.
2. The owner runs **C0 (`preflight`) first**. It is read-only, may be repeated, and consumes nothing. It shows whether ports 55440 and 55450 are free and that no gate container or volume exists.
3. The secret directory already in use, outside every checkout. The session never reads it.

## 4. Decisions carried from review R2

- **Egress block (J2): not required.** The flag was never exercised in rehearsal, and requiring it now could fail the one-shot for a reason unrelated to the product. Containment for the gate run is therefore: the database URL with the literal loopback address; the driver's probe of database identity and run marker; the cleared environment; the Python-level socket guard in the test process and the launcher (blocking connects and name lookups only); no provider configured. The evidence report states that no operating-system egress block was active. *The owner may instead ask for one more rehearsal with the flag before the gate; that is the alternative to this bullet.*
- **What consumes the one-shot (J1).** The ceiling of one is consumed when card C3 (`test`) has written its start flag. A failure of C1 or C2 — container start, role or database creation, probe, `alembic heads` check, or the upgrade itself — is an **infrastructure failure**: it is reported with its `STOP:` line and outputs; the gate result is NOT RUN, not FAILED. A new attempt after such a failure needs the owner's explicit word and a short recorded note, and the owner then removes the gate container, volume, the `gate-1` secret sub-folder and output folder by hand (the driver will not). A migration that fails on the gate database after passing three times in rehearsal is itself a finding and is reported as one.
- **Container log (J3).** After C4 the session reads the stopped gate container's log (read-only `docker logs`) and saves the error-level lines to the output folder with their hash, before anything else touches the container. Statements about overlap in case 08-01b cite that saved file or are not made.
- **Driver identity (J8).** The evidence report records the driver's hash, and a copy of the driver is kept in the output folder.
- **Extra assertion (J4).** Case 08-07 also asserts `current_version` in the 409 body, beyond S2 Draft 18. Recorded here as part of the gate: **DV-19**, accepted by approving this draft.

## 5. What a pass may be claimed to show (claim rule, extended per J10)

"Gate G1 passed with deviations DV-1 to DV-19", on one PostgreSQL 17 container migrated to the 13 pinned heads, through the composed routes served by a real process, with a synthetic token verifier and seeded data, without an operating-system egress block.

Not shown, in addition to DV-1 to DV-19: anything about M2-AT-09; behaviour with a real provider; create **with** a lesson version; the pending-receipt write used by story-revision reservation (product defect W3: fixed by reading, unit-tested offline, not exercised on PostgreSQL); privileges of a separate runtime database role (the API runs as the role that owns the schema).

Whether the result satisfies the M2-AT-08 and M2-AT-10 rows of the S3 ledger is the owner's decision at acceptance, after the evidence report and its independent review.

## 6. Result handling

- 20 passed, no skips, exit code 0, no credential in outputs: the gate result is PASSED WITH DEVIATIONS, pending the evidence report, review and owner acceptance.
- Anything else from C3: the gate result is FAILED; the container, volume and outputs stay; the ceiling is consumed; nothing is changed or rerun; another attempt needs a new approval.
- The session writes the evidence report from the outputs, with every hash, the table counts before and after, both pairs of process identifiers, the saved log lines, and the limits of section 5.

## 7. Approval block (for the owner)

- [ ] Gate run approved as written (egress block not required; consumption rule of section 4; DV-19).
- [ ] Commit instructed (precondition 1), after the entry recording this approval is appended.
