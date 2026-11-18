# FEAT-063 M2 PostgreSQL gate G1 — Task Approval Draft 1 — cold review R1 — 2026-11-17

- **Reviewer:** Claude subagent, fresh context, model Sonnet 5.5, effort high, read-only by instruction (no sandbox enforcement; network not sandbox-disabled). Started by the coordinating session (Fable 5.2) at the owner's instruction ("Review Sonnet").
- **Pin reviewed:** `plan/M2_S2_POSTGRES_GATE_G1_TASK_APPROVAL_DRAFT1_20261117.md`, 18,348 bytes, SHA-256 `196A60F374FA41AB5501FD8B3915988133795EA898433F1E8644640DC618FA6C`, at HEAD `7cc5cf74d03c249d17b6c98c877ed3fb1a36b09a`. The reviewer states the pin and HEAD matched at the start and at the end, that it made no writes and connected to nothing, and that it ran only read-only shell commands. It also read Alembic's source in the existing task interpreter.
- **Verdict:** READY WITH NOTES — P1=0, P2=3, P3=9, as a basis for the owner to approve Stage A after the three P2 items are fixed. Not an approval.
- **This file** is the coordinator's condensed transcription of the reviewer's report, not the verbatim report.

## P2 findings

| ID | Finding | Reviewer's smallest fix |
|---|---|---|
| G1 | The allowlist ("exactly these two" files plus scratch) contradicts the Stage A deliverables: the case map, the seeding-statement list and the Stage B approval draft have no authorized location. | Name the exact extra record paths, or say they are delivered only in chat and scratch. |
| G2 | DV-6 depends on `attach_artwork`. It adds two asset-metadata objects with `add_all` and then runs a Core insert into `core_asset_lineage` with no flush between them; the two foreign keys are immediate; the runtime session factory has `autoflush=False`. Under a runtime-factory session the lineage insert would raise a foreign-key error, mapped to 409 `PARENT_STORY_ARTWORK_CONFLICT`; a default session would not. A reading, not a run. No PostgreSQL test of `attach_artwork` exists, and the production artwork route uses the same factory, so a failure there would be a product defect. Evidence: `parent_story_repository.py:565-609`; `20261102_story_run_lite.py:294-305`; `database.py:43`. | State which session the test uses for the repository calls; state that a failure under the runtime-factory session is a product defect and a stop condition, not something to work around with SQL seeding. |
| G3 | "13 heads pinned by name" is not mapped to baseline section 5.3 item 4 ("tối đa một upgrade tới target revision đã pin"). The Alembic command line takes one revision string, so 13 explicit targets mean 13 invocations or a private call. Item 2 of the same section also asks for script and snapshot hashes. | Add a deviation, or fix the mechanism: how many invocations, in what order, how they count against the ceiling; state the snapshot expectation for a throwaway database. |

## P3 findings (summary)

G4 the list of fixed gate variables omits the artifact-root setting (the local artifact store creates its folder at construction; under `backend/` the default path is not git-ignored), the S3 and AWS names of F1, and the API port value. G5 install the socket guard before `create_app()`. G6 `git diff --check` skips untracked files; add a byte-level LF and trailing-whitespace check for the two new files. G7 name cache and base-temp paths under scratch; scope the exit condition to diagnostics located in the two files; consider ceilings. G8 the "Accepted" column cannot be verified from the repository; quote the owner per row or tie acceptance to approval of the draft. G9 Draft 4 pins "commit and clean status" for the gate; say when the two files are committed. G10 "application cannot be built" cannot be established in Stage A, which starts no process; say it is by reading in Stage A and by running in Stage B rehearsal. G11 list the superseded parts of Draft 4 (its DV-6, DV-8, section 7 table, guard 5 "ten heads", sections 9 to 11); review R3 says "11 P3" but lists 12; the DV-10 baseline clause is a paraphrase. G12 seeding in section 4 is complete only for the 08-01a holder; a seeded run the owner must read (08-16, 08-14) also needs `current_input_revision`, a `story.run_inputs` row with context fields, UUID-formatted references and an allowed `job_state`, or should be built with a product method such as `fail_drawing_analysis`; the 08-01a leftover account must never be read. Wording: `age_months` appears only inside `context_snapshot` in the create response.

## Claims the reviewer verified as correct (reading)

- 31 revision files; the 13 heads as listed; the three `depends_on`-covered heads; 10 `alembic_version` rows after the upgrade, by Alembic 1.20.1 logic (`runtime/migration.py:1143-1199`), in every ordering it traced; revision names fit the version column.
- `20261110_ar_0001` adds `account_role`; the story-context migration fails closed on existing runs and has no downgrade; no migration needs a superuser; `alembic/env.py:98-106` URL order.
- `create_app()` under the test environment needs no source edit and makes no network call at construction; provider factories return nothing; identity classes are lazy; the scanner only stores host and port; the engine is lazy; the runtime object accepts assignment of the verifier. A single S3 key raises a settings error, so the dummy keys must be set as a pair; with explicit keys the storage library does not walk its credential chain.
- `ai_jobs.job`, `ai_jobs.outbox`, `core_outbox_events` exist; create and cancel write none of them.
- DV-6 chain moves the run through INPUT_PROCESSING and SUBJECT_REVIEW to PREPARATION_REVIEW with no context-confirmation step (subject to G2). F4 retention sets are right. DV-15 code is what the repository returns (receipt check, then revision check, then state check). DV-16 is correct. All four late-result methods refuse `DELETE_PENDING` before writing and leave a row lock open.
- Seeding columns for identities, profiles, revisions and the 08-01a holder are complete (`account_id` and `role_revision` have only Python-side defaults, so SQL must set them).
- The launcher name is not collected; CI runs an explicit file list; the validators place no rule on test files beyond the content scan; module-level imports of the application do not connect.
- Baseline quotes in the DV rows match Draft 10 (DV-10 excepted); all of F1 to F17 and the seven missing deviations have a disposition.

## Not read or not verifiable (reviewer)

Nothing was run. Docker state, image digest and PostgreSQL minor version unchecked. `parent_ai.py`, the 31 migrations line by line, and the remaining story-revision methods not read. The owner's acceptance of DV-1 to DV-18 has no repository record.

## Notes by the coordinating session

- Spot-checked after the review: `database.py:43` is `sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)`; the repository file contains no `flush()` call; baseline section 5.3 items 2 and 4 read as the reviewer quotes. G2 was not otherwise re-verified and remains a reading.
- On G8: the acceptances were given in this session, one question per deviation with the baseline sentence quoted; they are recorded in the scratch note of the read-only preparation, not yet in a repository record.

## Disposition

Not yet addressed. Draft 1 is not revised.
