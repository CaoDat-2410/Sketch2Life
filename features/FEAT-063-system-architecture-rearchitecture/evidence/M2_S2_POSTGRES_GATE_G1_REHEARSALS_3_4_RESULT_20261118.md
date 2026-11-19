# FEAT-063 M2 PostgreSQL gate G1 — rehearsals 3 and 4 result; rehearsal exit rule met — 2026-11-18

- **Status:** rehearsal record, not gate evidence. Owner-run under the rehearsal approval of 2026-11-17. Written by the coordinating Claude session (Fable 5.2) from the card summary lines the owner pasted and from the output folders. Not independently reviewed.
- **Commit under test:** `b430b67a68e7934721f7ec9b44b96e9071cb989e` on `feature/feat063-m2-s2`, unchanged since rehearsal 2. Pins unchanged: test file `BC3FBE628CEEA8E79CF6EDD96963F3EE45D6565FDDB65FD8C6888781476AF4A2`, launcher `00FED31506F1510192471A81DA321CC5EBFD68140E0A089125FF3D4B14959749`, driver `E963B585BFB59FEF3F5ACA70C7D18FCF4E8D9E4FFB0FEAD3AF2062EB70A97CD6`. No tracked file was modified during the runs.
- **Resources:** each rehearsal on its own container and volume (`s2l-m2-s2-rehearsal-3`, `s2l-m2-s2-rehearsal-4`), database `sketch2life_m2_s2_rehearsal` on `127.0.0.1:55441`, API on `127.0.0.1:55451`, new passwords and run marker each time (`729d4009386f4f279e09556cdd82f48a`, `3a483131f5cc4b6294b7760b5f277644`). Egress flag not used. Containers 2 and 3 were removed with card C5 before the next rehearsal; container 4 is stopped and kept.

## Results

| | Rehearsal 3 | Rehearsal 4 |
|---|---|---|
| C1 `container-up` | OK, empty database confirmed | OK, empty database confirmed |
| C2 `migrate` | 13 heads, 10 version rows, 123 tables | 13 heads, 10 version rows, 123 tables |
| C3 `test` | exit 0, **20 passed**, none skipped, 20.15 s | exit 0, **20 passed**, none skipped, 19.90 s |
| Credential found in outputs | none | none |
| Restart identifiers (old spawned / old reported → new spawned / new reported) | 48472 / 59424 → 21216 / 61664 | 35896 / 9052 → 7052 / 34744 |
| `result.json` SHA-256 | `8B5DC56CD57A1900F9BC0C016142353487AFA8F6FB3D15DEB33641FC4F282E29` | `3316CE9CB9CE48A57447BFA0E038F8601BF9740D19F305CF4119318180831584` |
| `pytest-output.txt` SHA-256 | `AF57AAB626A50471B9B0C506484EC981F05506D0EA4FC68916687D14FD1C0E51` | `E5442AB25D930AB9816896695DF15DA1887362D99B29D61567C1C523BB091910` |

In both runs every table was empty before the test except `alembic_version` (10 rows), and the table counts after the test are identical to rehearsal 2: identities 40, child profiles 40, profile revisions 40, runs 41, run inputs 32, command receipts 42, understanding revisions 1, review decisions 1, asset metadata 2, asset lineage 1; `ai_jobs.job`, `ai_jobs.outbox` and `core_outbox_events` 0. The server log of rehearsal 4 shows the same error set as rehearsal 2 (19 violations of `uq_story_run_active_parent`, the four expected age-check violations, one readiness-check line) and nothing else. The log of rehearsal 3 was not read before its container was removed.

## Rehearsal exit rule

Rehearsals 2, 3 and 4 are **three consecutive full passes (20 of 20, no skips) on unchanged pins and one commit**. The exit rule of the gate's Task Approval (G1 Draft 2 section 6; Stage B Draft 2 section 2) is met.

Summary of all rehearsals:

| Rehearsal | Commit | Result |
|---|---|---|
| 1 | `2bfa1ac0` | 3 passed, 17 failed: product defect W1 (create refused by PostgreSQL) |
| 2 | `b430b67a` | 20 passed |
| 3 | `b430b67a` | 20 passed |
| 4 | `b430b67a` | 20 passed |

## Still open before the gate run

- The gate run is not approved. It needs its own owner approval, including the choice whether to require the egress block.
- The revisions made after cold review R1 of Stage B (test file, launcher, driver, Stage B Draft 2) and the product fix have not been independently reviewed. A delta review before the one-shot gate run was advised to the owner and is not yet done.
- Product defect W3 (pending receipt) is fixed by reading and unit-tested offline, but no rehearsal exercises it.
- Deviations DV-1 to DV-18 apply. This record claims nothing about M2-AT-08 or M2-AT-10.
