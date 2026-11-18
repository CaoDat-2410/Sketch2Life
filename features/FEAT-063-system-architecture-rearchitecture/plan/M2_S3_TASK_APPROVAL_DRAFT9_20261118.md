# M2 S3 — contract freeze, evidence reconciliation and M2 closure — Task Approval Draft 9

- **Status:** DRAFT / NOT APPROVED / NOT LAUNCHED. Until the owner approves it, this text authorizes nothing: no S3 work, test, validator run for evidence, OpenAPI generation, database or migration action, provider call, network access, stage, commit, push or merge. Drafts 1 to 8 remain unchanged.
- **Date:** 2026-11-18. **Author:** coordinating Claude session (Fable 5.2). **Owner:** Person 2. This draft is not independently reviewed.
- **Worktree:** `.worktrees/m2-s2`, branch `feature/feat063-m2-s2`, HEAD `4cfd1412a4812cc862e3de00397c29c9c5b8c945` (five commits ahead of the remote; nothing pushed since `7cc5cf74`).
- **Predecessors, unchanged:** Draft 8 (`plan/M2_S3_TASK_APPROVAL_DRAFT8_20261118.md`, SHA-256 `358B9E03834BD25CD0EC7531E34867B150F07798E5ABB827FC08D13484EACEF2`) and its cold review R1 (Opus 5.5, high): NOT READY, 0 P1 / 7 P2 / 12 P3 (`evidence/M2_S3_DRAFT8_COLD_REVIEW_R1_20261118.md`, SHA-256 `DC0F8B4FD85981F9833E7A6ECAB3A3608FF683C7917142D57337AACFD84A80F5`). Before that, Draft 7 (`3E55699F862F4650DD616C816458CCE784A892CF90340C3589EA8851D71036A9`) and its review (`FE0281A01B5DC1F10A47A22FCD94FA01C502C3DF991AA84633A80E2D18FC7164`; ten P2 rows, F1 to F10, although its header says nine). Section 10 disposes of both reviews.
- **This draft is self-contained.** No rule of an earlier S3 draft applies unless it is written here. Draft 6 (`BF7792925F06ED66720850CEE916EFBF2F724100B84D3B2BF3545F11E19108C4`) was read for this draft; its rules that still apply are restated in sections 2 to 9.
- `OWNER_MODAL_CALL_APPROVED=NO`. No real-child data, provider or Modal call, external service or production inference.

## 1. Authority and decisions

- **Working SRS:** the copy adopted by D-209 (`artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md`, 701,157 bytes, SHA-256 `B9B1F42D0BB118C19C81607D3913B7E4F1D8B6F673F0C3FBB6402888FEB675F5`), unsigned and not final.
- **Baseline:** `plan/M2_PARENT_TEACHER_FOUNDATION_PLAN_DRAFT10_20261106.md` (SHA-256 `7539D642FFD95A9A21C99A0C17C5095FF1443E19538017A92789F631D633E2B1`), accepted by D-151 with five carried conditions C1 to C5. Its S3 row (line 265) reads, in the three columns that matter here:

  > Đối chiếu evidence và freeze contract; đóng OpenAPI P3 hai POST submit/cancel trước frontend/client.

  > Điều kiện đề xuất, owner phải chấp nhận trong Task Approval S3: chỉ M2-AT-05/06/07 được phép ở trạng thái NOT RUN/DEFERRED khi S1b vẫn DEFERRED; mọi M2-AT khác phải chạy và pass. NFR-36 và NFR-38 có disposition; OpenAPI parity được kiểm; conditions được gán owner/phase; independent review ACCEPTED.

  > Không tích hợp frontend/client khi OpenAPI P3 còn mở; không tự mở M3 hoặc bật workload.

- **D-210 and D-211 (2026-11-18)** fix the following; each item was selected by the owner with the governing text quoted:

  | # | Decision | Source |
  |---|---|---|
  | 1 | M2-AT-09: NOT RUN / DEFERRED | D-210 item 1 |
  | 2 | OpenAPI P3 gate for the two assistance POST operations: carried OPEN; S3 does not close it | D-210 item 2 |
  | 3 | Client-integration block after M2 closure: the three assistance operations only, until the OpenAPI P3 gate is closed and a PostgreSQL gate for M2-AT-09 has passed. Parent profile and Parent story-run operations are not blocked by this gate | D-211 item 1 |
  | 4 | Controlling definition of M2-AT-01 to M2-AT-11: foundation plan Draft 10, each row read with the narrowings approved later (D-171, the S1a task approvals, S2 Draft 18 section 4, deviations DV-1 to DV-19 of gate G1). Differences in foundation plan Draft 11 (rows M2-AT-01 and M2-AT-10) are recorded, not applied | D-210 item 3 |
  | 5 | M2 may be closed "with recorded debt and deviations"; every item goes into the limitation ledger with an owner or phase | D-210 item 4 |
  | 6 | Freeze the composition captured by the mapper task's post export (both export flags on) | D-210 item 5 |
  | 7 | Reuse that export: copy the two schema files byte-for-byte; manifests with local absolute paths are cited by hash only | D-210 item 6 |
  | 8 | Parity: checked by reading, for the M2 target operations only, against SRS section 21.2 and D-199 to D-206; mismatches recorded OPEN, not repaired; the mapper comparison cited for the 134 catalogued operations; the rest recorded as not checked | D-211 item 2 |
  | 9 | Story-chain target: the migration of an empty PostgreSQL 17 database to the 13 pinned heads in gate G1 (they include `20261112_parent_story_context`) is the accepted evidence that establishes it on a new database. K3 stays NOT VERIFIED. Nothing is concluded about the earlier task database | D-211 item 3 |
  | 10 | S1a-T class operations under `/api/be1/v1/`: frozen compatibility surface (D-171 item 7), noted as carrying the evidence for M2-AT-02, 04A and 04B. The absence of the three SRS section 21.2 foundation routes from the runtime schema goes into the limitation ledger | D-211 item 4 |
  | 11 | Mounted operations outside the catalog with no current authority: listed as "mounted, no current authority — OPEN-OWNER"; not guessed; not a stop | D-211 item 5 |

- **Departures from the baseline's S3 row. S3 states all four in every output and never reports any of them as met:**
  1. "mọi M2-AT khác phải chạy và pass": relaxed for M2-AT-08 and M2-AT-10 (accepted as "gate G1 passed with deviations DV-1 to DV-19, on the second attempt") and for M2-AT-09 (deferred).
  2. "đóng OpenAPI P3": not done; the gate stays OPEN.
  3. "OpenAPI parity được kiểm": checked in part only (decision 8).
  4. "Không tích hợp frontend/client khi OpenAPI P3 còn mở": narrowed to the three assistance operations (decision 3). The baseline's other mentions of this block (lines 317, 396 to 398, 407 to 408, including "trước D9") are covered by the same narrowing; what "D9" denotes was not established for this draft and is recorded as such.
- **Decisions to be read in full at the pinned hash during S3 work before they are relied on:** D-151, D-170, D-171, D-188, D-196 to D-211. D-208's planning dispositions were given against an earlier SRS copy; D-209 puts the deletion eligibility of FAILED and ABANDONED runs back under review: S3 records it OPEN-OWNER.
- **Citation caveats:** `DECISIONS.md` records that identifiers D-135 to D-149 occur twice; references here mean the M2 line. D-127 has two rows; the cancel row (line 263) is meant.

## 2. Purpose and scope

S3 is a documentation, contract-freeze and evidence-reconciliation phase. It adds no product feature, route, schema, table, migration, provider integration, client integration or M3 opening. It repairs no debt and runs no test. No database, provider or network is used to create evidence.

Deliverables (paths in section 6): the two frozen schema files; the operation inventory with contract cards and the parity check; the acceptance-test ledger; the limitation ledger; the closeout report with a recommendation. The owner's decisions on S3 acceptance and M2 closure are separate.

Evidence levels stay distinct and are named in every row: source-declared; composed or mounted; present in the frozen runtime schema; present in the client-facing projection; exercised by an accepted offline test run; exercised on PostgreSQL by gate G1 (with its deviations); runtime-verified otherwise. Unavailable evidence is NOT RUN or NOT VERIFIED. A passed test selection is not by itself a passed acceptance test. Historical labels (A2, B1, B2, N-1, N-3) are evidence pointers, never live database facts; no live database state is claimed from files.

## 3. Contract freeze

### 3.1 What is frozen

| Source (git-ignored, on the owner's machine) | Bytes | SHA-256 | Copied to |
|---|---:|---|---|
| `backend/tmp/openapi-mapper-d10-post-367b579d97eb4f0a99cd6a6d329bb1f4/runtime-post.json` | 847,426 | `E9C2D7C8E95225F3D1F8B708C50C9ACC19CF822508ABEFD4F85298AD2E6B3A0C` | `artifacts/m2-s3/openapi-runtime-frozen.json` |
| `.../published-post.json` | 213,111 | `F23BF908A104667153F88D6438AE8E95BE9895A76DAB7099877EBE9EFC49589D` | `artifacts/m2-s3/openapi-client-projection-frozen.json` |

Counted by method and path with a JSON parser, by this session and by review R1 of Draft 8: runtime 151 operations on 134 paths; projection 34 operations on 24 paths, all inside the runtime set. The catalog has 134 entries; test constants name 5 pilot-only and 12 uncatalogued operations (134 + 5 + 12 = 151).

Cited by hash only, not copied: `environment.json` `E974D4926BEEF15DA04A669F1F714DEF6C117E79484BF115F29FEB252E940AAE`; `run-manifest.json` `1286E0F36FA98C9CEE19CB09415CA0BDE05D5606A9289A878850B96F6965548F`; `source-state.json` `27DBD75A78DE3A3BB841558719F790D5E849F031469CA2E56DD8715C3A340E27`; `invocation.json` `305B1FBEE91D049778ACC042050D432147B771CB045D6AF9FC97B4DE7F446F0F`; from `backend/tmp/openapi-mapper-d10-compare-7e7f0b0d854e48099ea903ba920ba7f4/`: `field-delta-report.json` `E8F265F51410FD968AC1A14F1113ACB07C555BEBA23DFBDE0093A7679FFE5C6D`, `run-manifest.json` `FCC401E0F46C64FA04DAD251ACC9139C7E39B59ADDAE2E173C4EBDC0094C3059`. D-210 item 6 decided this for manifests with absolute paths; extending it to `invocation.json` and the comparison report is decided by approving this draft.

**Both source files have CRLF line endings.** The copies must keep them. A `.gitattributes` entry `features/FEAT-063-system-architecture-rearchitecture/artifacts/m2-s3/*.json -text whitespace=cr-at-eol` is therefore part of the allowlist (the repository already uses this form for other pinned files). Hash checks: the working copies immediately after copying; `git check-attr text` on both paths must report `unset`; after the owner-instructed commit, `git show HEAD:<path>` piped to SHA-256 must equal the pins.

### 3.2 Facts the freeze states and may not soften

- The export ran with `SKETCH2LIFE_STORAGE_EXAMPLE_ENABLED` and `SKETCH2LIFE_SYNTHETIC_PILOT_ENABLED` on, in the lock-exact task environment with a cleared child environment, without an operating-system egress block; database, provider, runtime and network isolation are recorded as not proven for it. The owner accepted the egress deviation for the mapper task.
- The freeze is **not reproduced** in S3: no export is run. Reproducibility rests on the pinned sources and the precondition check below. (Draft 6 asked for reproducibility in an authorized offline environment; reusing the export instead is D-210 item 6.)
- The mapper comparison shows that the projection equals the pinned projection of the runtime file and that the 134 catalogued operations carry the catalog description, tag and response status set. It does not cover the 5 pilot-only and 12 uncatalogued operations.
- `POST /v1/story-runs/{run_id}/cancel` is uncatalogued: no description in the runtime schema (a summary only), absent from the client-facing projection. It is an M2 target operation with PostgreSQL evidence from gate G1. S3 records this as an OPEN item and changes neither catalog nor projection.
- The three assistance operations of M2-AT-09 exist only with the pilot flag.

### 3.3 Precondition check before copying

The export's `source-state.json` holds two different hash sets. The reference is **`pinnedInputStates`** (the state at export time), not `pinnedInputManifest` (the earlier pins of the mapper task, which differ for `app.py` by design). The check hashes: every entry of `pinnedInputStates`; and every entry of `changedPaths` under `backend/src` (the S2 source files that define routes and schemas, which the export recorded there). Expected result, as review R1 of Draft 8 observed by reading: all non-test entries equal; two test modules differ; exactly one `backend/src` entry of `changedPaths` differs, `infrastructure/persistence/parent_story_repository.py` (repaired in commit `b430b67a`: SQL NULL binding and a flush; it defines no route, schema or catalog entry — static reasoning, not a re-export). Any other difference is a stop condition.

### 3.4 Inventory rows, classification and contract cards

Every one of the 151 runtime operations appears exactly once. A row records: method; path with the runtime's parameter spelling; `operationId`; tags; present in the projection (yes or no); composition condition (always mounted, pilot flag, storage-example flag) with its evidence level; classification; authority; evidence levels; open items. Request and response schemas, headers and status sets are **not re-typed** for the 151 rows: they are frozen as they stand in the runtime schema file and the row points at the operation there. Approving this draft approves that scope.

Classification values and their authority:

| Value | Applies to | Authority |
|---|---|---|
| M2 target contract | The Parent profile operations accepted in S1a-P and S1a-P2 (create, read, update, list, deletion request); `POST /v1/story-runs`; the two owner-scoped Parent reads; `POST /v1/story-runs/{run_id}/cancel` | SRS section 21; the accepted S1a-P, S1a-P2 and S2 records; D-199 to D-206; gate G1 |
| Frozen compatibility surface | Every mounted BE1, classroom or demo operation, including the S1a-T class operations (noted as carrying M2-AT-02, 04A, 04B evidence) and the three assistance operations (noted as pilot-flag dependent, M2-AT-09 deferred, client integration blocked) | D-171 item 7; D-211 item 4 |
| Pilot-only | Operations that exist because of the pilot flag | source and test constants; evidence level source-declared |
| Local example | Operations that exist because of the storage-example flag | source; evidence level source-declared |
| Proposal or conditional | Operations the schema or an accepted record marks as proposed (for example the Parent confirmation operations) | the schema's own summary text; accepted S2 records |
| Mounted, no current authority — OPEN-OWNER | Mounted operations outside the catalog for which no current SRS section or decision gives an authority | D-211 item 5 |

An operation may carry a second value where two apply (for example compatibility surface and pilot-only); the row says so. An operation that fits none of these values is a stop condition.

A contract card is written for each M2 target operation only: contract key and version; method and path; actor and authorization scope; request and response schema names as in the frozen file; required headers; status and error contract; idempotency and revision rules; composition; SRS, decision and record citations; evidence levels; open items.

### 3.5 Parity check (decision 8)

For each M2 target operation, by reading: its entry in the frozen runtime schema against SRS section 21.2 and against D-199 to D-206 — method, path, status codes, error envelope. Each comparison is tabulated as EQUAL, DIFFERENT (with both texts) or NOT STATED IN THE SRS. Nothing is repaired. Known in advance and to be confirmed: the SRS spells the path parameter `{id}` where the runtime and D-199/D-206 use `{run_id}` (D-151 condition C3; the baseline says the spelling is fixed at the S3 freeze). **Rule:** the freeze records the runtime spelling as the frozen one and the SRS spelling as a DIFFERENT item, OPEN for the SRS; this is not a stop. The three SRS section 21.2 foundation routes absent from the runtime schema are tabulated as ABSENT FROM RUNTIME. For the 134 catalogued operations the mapper comparison is cited; all other operations are recorded as parity NOT CHECKED.

## 4. Acceptance-test ledger

One row per acceptance test. Definition: foundation plan Draft 10, with the narrowing that applies. Each status is copied from an accepted record; no test is run.

**The eight S1a evidence records do not state a status per M2 row.** The row mappings are in the approved S1a specifications, and the acceptances are in the approval record. All are sources and are pinned in section 8:

| Acceptance test | Status rule for S3 | Sources |
|---|---|---|
| M2-AT-01, 02, 03, 11 | The status the approved S1a specification assigns to the row together with the owner's acceptance of that phase, at the approved scope, with every NOT RUN part named (for example the system-role negatives of M2-AT-01 under D-188) | `plan/M2_S1A_T_APPROVAL_SPEC_FINAL_20261107_R7.md` (row table); `plan/M2_S1A_P_TASK_APPROVAL_DRAFT8_20261109.md` (M2-AT-01, 03, 10 persistence part, 11); the S1a-T and S1a-P acceptance entries in `approvals/TASK_APPROVAL.md`; D-188; the S1a-T and S1a-P closure records and implementation reports |
| M2-AT-04A, 04B | PARTIAL as the S1a-T specification and closure record state (capacity not covered; expected class revision not covered) | as above |
| M2-AT-05, 06, 07 | NOT RUN / DEFERRED under D-171. Never PASS | D-171 |
| M2-AT-08 | "Gate G1 passed with deviations DV-1 to DV-19, on the second attempt". Offline S2 evidence listed separately at its own level. Not "ran and passed" | `evidence/M2_S2_POSTGRES_GATE_G1_EVIDENCE_20261118.md`; G1 Draft 2 section 3.1; the gate-run draft; the acceptance entry; the S2 report and closure evidence |
| M2-AT-09 | NOT RUN / DEFERRED under D-210 item 1, with the client-integration block of D-211 item 1 | D-210, D-211 |
| M2-AT-10 | No single record states its status. The row lists three parts separately: service and contract part (S1a-T specification: PARTIAL); persistence part (S1a-P specification with its accepted gate); StoryRun part on PostgreSQL (as M2-AT-08, deviations DV-7, DV-8, DV-17) with the offline service-level refusal at 121 and 155 months from the accepted S2 selection. D-151 condition C2 (state the layer) is met by listing the parts. The row's overall status is the weakest part's | the S1a specifications; the S2 records; the gate G1 records |

**S1a-P2** uses its own series P2-AT-01 to P2-AT-08 and no record maps it to M2 rows. The ledger lists the S1a-P2 series as a separate block with its own statuses ("accepted with known gap"; P2-AT-03 NOT RUN; the consumed first gate attempt; the PostgreSQL addendum, which says it is not a closure) and does not assign it to M2 rows.

Each row carries: definition source and line; narrowing; runner or owner; date; the approved command or owner-run reference; result; evidence path and digest; accepted scope; limits. A failed, interrupted, missing, stale or owner-unverified result stays so. If, after reading the sources named above, a row still has no accepted status, the row says NOT ESTABLISHED and that is a stop condition.

D-151 conditions C1 to C5 are listed with what became of each. Expected, to be confirmed by reading: C1 kept by gate G1's pinned heads; C2 met as above; C3 an OPEN spelling item (section 3.5); C4 applies (must-run-and-pass limited to cases approved in the relevant task approval); C5 answered by D-171 item 10 with no explicit closing record, to be recorded as such.

## 5. Limitation and inherited-condition ledger

Built by reading each phase's closure and acceptance record, each item with an owner or phase. It contains at least:

- **Deferred or partial by decision:** S1b; M2-AT-05/06/07; NFR-36 PARTIAL (child-media access deferred to M5, cross-organisation feedback to M6, Platform Admin child-media access deny by default) and NFR-38 PARTIAL (M2 claims age and language metadata only; AC-65 story work to M4, video to M5), as D-171 gives them — M2 dispositions, not completed SRS acceptance; M2-AT-09 with its client-integration block; the OpenAPI P3 gate (OPEN); the four departures of section 1.
- **Baseline items not covered:** BR-58; FR-C-10 and BR-35 (the baseline says no profile deletion route in M2, while S1a-P2 added a deletion request: recorded as it is); the B1 stale-owner orphan gate (baseline lines 392 and 407), with what later records say of it or NOT ESTABLISHED; the three SRS section 21.2 foundation routes absent from the runtime schema.
- **Gate G1:** deviations DV-1 to DV-19; S2 Draft 18 row 13 not covered; one run on one machine and one PostgreSQL minor version; no operating-system egress block; containment by a Python-level socket guard and literal loopback addresses; trust authentication on the container's local socket; the API ran as the role that owns the schema; create with a lesson version not exercised; no real-provider behaviour; the first gate attempt, read literally under the approved rule, is a failed attempt, and the result comes from an owner-approved second attempt (review finding K1).
- **Product defects found after the S2 closure:** four PostgreSQL write defects in `parent_story_repository.py`, repaired in `b430b67a`; W3 not verified on PostgreSQL; other modules not surveyed for the same patterns; M2-S2 was closed while these defects existed, and no addendum to the S2 closure record has been decided.
- **What S2 was closed with:** 19 added Mypy `arg-type` diagnostics accepted as typing debt and 336 existing; 17 existing Ruff diagnostics on the S2 source paths and one on a contract test; only the nine-file pytest selection ran; the production role adapter not exercised on PostgreSQL; the stale-version P3 on broader routes; the FEAT-047 description overlay kept; the unexplained hang of 2026-11-14; the deviations S2 Draft 18 section 6 records against the SRS, kept as DEVIATION and not as conformance (D-203); the S2 report's open items (cancel receipt envelope fields; current-run reference in the conflict body; dispatch after context confirmation; OQ-S2-4 and OQ-S2-5 deferred).
- **Mapper task and closure verification:** four commands needed a second run; the post export ran without the egress block; two test files changed after export and comparison without re-runs; the approval record changed between the exports (Amendment 1); two pytest invocations where one was specified; the request-identifier inventory OPEN beyond Amendment 1; the closure comparison ignores line numbers; the driver's timeout path was never exercised.
- **S1a:** the D-188 limitations; K3 NOT VERIFIED under D-188 and D-198; S1a-T debt recorded under D-170 (including the items in `openapi_contract.py` and six Ruff `I001`); partial coverage of M2-AT-04A and 04B; the S1a-P2 block of section 4; synthetic rows left in the earlier task database `sketch2life_m2_s1a`.
- **Story-chain target:** established for a new database by gate G1's migration to the 13 pinned heads (D-211 item 3); nothing concluded about the earlier task database. The term comes from D-196, D-198 and the S2 drafts (the explicit Alembic target on the Story chain), not from the S1a records.
- **Mounted operations with no current authority** (section 3.4), listed by name; and the cancel operation's absence from catalog and projection.
- **Kept on the owner's machine, not in the repository:** the export folder; the gate containers, volumes, run outputs and the secret directory; the gate driver.
- **Open owner questions:** deletion eligibility of FAILED and ABANDONED runs (FR-C-08); the decision-number citation convention; the SRS pointer in other worktrees; re-pinning of the roadmap addendum required by D-209; what "D9" denotes; whether the S2 closure record needs an addendum; that commit `7cc5cf74` and its push have no repository record of their own (the status and context entries of 2026-11-17 still say "uncommitted"); repository documents that contain local absolute paths (S3 counts them by search and records the count and the search used).
- **Records not independently reviewed**, listed by name.

S3 cannot repair, mask or broaden any of these.

## 6. Allowlist, tools and ceilings

**New files, exactly these** (dates are the date of writing):

| Path under the feature folder | Content |
|---|---|
| `artifacts/m2-s3/openapi-runtime-frozen.json` | byte copy (section 3.1) |
| `artifacts/m2-s3/openapi-client-projection-frozen.json` | byte copy (section 3.1) |
| `evidence/M2_S3_OPERATION_INVENTORY_AND_CONTRACT_FREEZE_20261118.md` | freeze statement; 151-row inventory; contract cards; parity table |
| `evidence/M2_S3_ACCEPTANCE_TEST_LEDGER_20261118.md` | section 4 |
| `evidence/M2_S3_LIMITATION_LEDGER_20261118.md` | section 5 |
| `evidence/M2_S3_CLOSEOUT_REPORT_20261118.md` | reconciliation summary; every pin; what was and was not read; the four departures; recommendation |

**Edited:** `.gitattributes` at the repository root — one added line, exactly the entry of section 3.1. **Appended, never rewritten:** `approvals/TASK_APPROVAL.md`, `status/STATUS.md`, `CONTEXT.md`.

**Read-only inputs:** the files pinned in section 8, the two export folders, and `backend/src` and `backend/tests/contract` for the composition conditions and the test constants. Nothing else is needed; a further input is named in the closeout report with its hash.

**Scratch (repository-root `tmp/m2-s3/`, git-ignored):** one extractor script `extract_operations.py` and its output. It parses the two schema files with the standard library only, imports no application code, opens no socket, reads no other file, and prints one line per operation (method, path, `operationId`, tags, in projection). Before use: syntax check and `ruff check` with the cache under `tmp/m2-s3/cache/`. Its hash and its output's hash go into the closeout report. Checks built into it: 151 runtime operations, 134 paths, 34 projection operations, every row unique, every projection operation present in the runtime set.

**Interpreter and commands** (task interpreter in the repository-root `tmp/m2-s2-mapper-env/.venv`, run with `-I -B`; no credential or database variable is set or read; at most 10 runs each):

| Command | Purpose |
|---|---|
| SHA-256 hashing of the pinned inputs and the copies | pins |
| `python -I -B tmp/m2-s3/extract_operations.py` | inventory rows |
| `python -B -m ruff check --cache-dir tmp/m2-s3/cache/ruff tmp/m2-s3/extract_operations.py` | lint of the extractor |
| `python -B tools/validate_harness.py`, `validate_repository_security.py`, `validate_architecture.py` | repository checks (they place no rule on the new folder; they are run as required by the harness) |
| `git check-attr text -- <the two copies>`; `git diff --check`; a search of the four new record files and the changed lines for drive-letter paths | line-ending and path checks. The drive-letter search is the operative check for local absolute paths: the security validator's patterns do not cover that form |

**Not allowed:** any change to a source, test, migration, catalog, schema or configuration file other than the one `.gitattributes` line; any export or application start; any test run; any database, container, provider or network use; any change to an earlier record; any stage, commit, push or merge without the owner's separate word.

## 7. Order of work

1. Recompute every pin of section 8. Any difference is reported as CHANGED SINCE OBSERVATION and work stops.
2. Precondition check (section 3.3); add the `.gitattributes` line; copy the two files; verify hashes and attributes.
3. Read in full, at the pinned hashes: foundation plan Draft 10 rows M2-AT-01 to 11, its S3 row, sections 5.3, 6.3 and 7, and D-151 with C1 to C5; the two differing rows of Draft 11; D-170, D-171, D-188, D-196 to D-211; the S1a specifications and acceptance entries; the eight S1a records; the S2 records; S2 Draft 18 sections 4 and 6; the gate G1 records; SRS sections 9.6, 9.8 and 21.
4. Extractor; inventory; contract cards; parity table; acceptance-test ledger; limitation ledger; closeout report.
5. Validators and checks; record entries.
6. Independent cold review of the pinned S3 package (criterion 8). Then the owner's separate decisions.

## 8. Pins at the time of this draft

Observed at HEAD `4cfd1412`, with `DECISIONS.md` carrying the uncommitted D-210 and D-211 rows. Step 1 recomputes them; they are not launch-time authorization.

| Input | Bytes | SHA-256 |
|---|---:|---|
| `docs/context/SRS_AUTHORITY.md` | 5,120 | `CACA7EC03CB570F3276AEA3EAF9214F93DDEC19F3030671A47DB590E19F74726` |
| `artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md` | 701,157 | `B9B1F42D0BB118C19C81607D3913B7E4F1D8B6F673F0C3FBB6402888FEB675F5` |
| `DECISIONS.md` (through D-211) | 227,109 | `570744ADD09BA11EDF09177396B2817CE38A2C549358D83CC12D9658748111BC` |
| `approvals/TASK_APPROVAL.md` | 496,807 | `11E3DC400EFFAF166958A94C43AF159F6C7336F92F0F05BDDCED5C2E8CF302A2` |
| `status/STATUS.md` | 123,718 | `046E59EECA355848C8D78F98F24130C8FD322945F913C3F71B33B788098EA809` |
| `CONTEXT.md` | 123,910 | `220A4678FFA3D82FEB5C8FD9552395861C04A37ABAF02CBA4FF28AF871D69314` |
| `plan/M2_PARENT_TEACHER_FOUNDATION_PLAN_DRAFT10_20261106.md` | 111,790 | `7539D642FFD95A9A21C99A0C17C5095FF1443E19538017A92789F631D633E2B1` |
| `plan/M2_PARENT_TEACHER_FOUNDATION_PLAN_DRAFT11_20261107.md` | 133,204 | `6F3EFD72D3A70209B06771AC437998AE241842ABD4F20D11019E6B1166B48A68` |
| `plan/M2_S1A_T_APPROVAL_SPEC_FINAL_20261107_R7.md` | 41,998 | `D79EB097CBFC775F0FD411F94A743B8E2074EAE289BC60316E10CF263DC16E59` |
| `plan/M2_S1A_P_TASK_APPROVAL_DRAFT8_20261109.md` | 76,176 | `E9C7FC9D7843F7466B88B801BFF26278A0E1B9C726EF770F8229C419C62F8118` |
| `plan/M2_S2_TASK_APPROVAL_DRAFT18_20261114.md` | 101,153 | `5CA09CC6F9D936C1BA74772251F4D3A9C0480F3E6F82818FE11114205FD3E331` |
| `plan/M2_S2_POSTGRES_GATE_G1_TASK_APPROVAL_DRAFT2_20261117.md` | 26,937 | `5CCA1171534E8A4FD431E7FF0FAB4E645F3DE4CFA3AA942F1BDA8F996745FE4C` |
| `plan/M2_S2_POSTGRES_GATE_G1_GATE_RUN_TASK_APPROVAL_DRAFT1_20261118.md` | 7,467 | `10FDF73F2F155F3C83C784FDFB26401C0BCC9567B81FA564D1D6EE17A8766F08` |
| `evidence/M2_S1A_T_CLOSURE_RECORD_20261109.md` | 7,527 | `D2ACD33F03E28C961F30270F310F27913257D39A28CEC8281D29ADAE5D285FDE` |
| `evidence/M2_S1A_T_IMPLEMENTATION_REPORT_20261107.md` | 22,796 | `AF3CFFABA7B1C5D199DB4EC5CD123BA92C5D338647EB0A794C78E431DB3B028E` |
| `evidence/M2_S1A_T_K4_SOURCE_RECONCILIATION_20261107.md` | 9,011 | `7CC1D51D4091FF95CEF0A5863C559DDB8C73B8C9A9DB197A2AD796035F523998` |
| `evidence/M2_S1A_P_CLOSURE_RECORD_20261109.md` | 11,614 | `61B3F4A2A8E817DA514D42580EE2F040360FEB1E0786E5180676077FAF60B275` |
| `evidence/M2_S1A_P_IMPLEMENTATION_REPORT_20261109.md` | 17,166 | `1CE028736700824DC8D52806AAFF4D35B0995540FE6FA4A3E73E75429E1A4E65` |
| `evidence/M2_S1A_P2_CLOSURE_RECORD_20261112.md` | 3,503 | `0C1801119F17D98FBD4ADA2C7D884530DFAB4A068AF88DE7C74525ADA61F40E4` |
| `evidence/M2_S1A_P2_IMPLEMENTATION_REPORT_20261112.md` | 18,186 | `60DC1BF030D08D27C902FA64F874FF3ED70F0DC3CD5F1907B7AE892374F72D13` |
| `evidence/M2_S1A_P2_REAL_POSTGRES_EVIDENCE_ADDENDUM_20261113.md` | 5,547 | `6BB4A6EA6F477B44486A4E518766099CC2DA9A97246DE7ADAD08E4C00C891485` |
| `evidence/M2_S2_IMPLEMENTATION_REPORT_20261114.md` | 25,879 | `F49D1FDB2B3C26387FFABC51C316F226C5D1FC5FC12B4856B0A6172A81941F55` |
| `evidence/M2_S2_SHARED_OPENAPI_MAPPER_IMPLEMENTATION_EVIDENCE_20261117.md` | 12,424 | `CCB014AFB23D7A156FC4E229C7B4A717B758982D425023E075AAED632F5C60C6` |
| `evidence/M2_S2_CLOSURE_VERIFICATION_EVIDENCE_20261117.md` | 10,487 | `CF644A09FF0802F7A2E4444CCBCC9E01B67528A3DC8B3F718686E441ED454525` |
| `evidence/M2_S2_POSTGRES_GATE_G1_EVIDENCE_20261118.md` | 18,329 | `CEB5D6C092C422781A0F614A3B3806581AFADCF6B58467B0060DE8A5CA759640` |
| `evidence/M2_S2_POSTGRES_GATE_G1_EVIDENCE_REVIEW_R3_20261118.md` | 7,705 | `D2DA5567654447CB5F0352B3315BE8D0253D4486066DD43A037EB3091C67E85E` |
| `evidence/M2_S2_PARENT_STORY_POSTGRES_WRITE_DEFECTS_FIX_EVIDENCE_20261118.md` | 4,985 | `D2C93693CC4E6302A8299B01E72F7BEF040E7B260B2F3C66DD1F8C3C206F95C9` |

The S1a-P2 task approval is `plan/M2_S1A_P2_TASK_APPROVAL_DRAFT6_20261112.md` or a later draft; S3 work identifies the approved one from the approval record and pins it in the closeout report. `evidence/M2_REV67_CROSSWALK_FOR_S2_S3_20261113.md` was written against an earlier SRS copy and is not an input.

**Not read for this draft:** the decision texts other than the parts of D-151, D-171, D-198, D-209, D-210 and D-211 quoted or summarised here; the S1a specifications and records (their content is taken from review R1 of Draft 8); the adopted SRS; the comparison report's contents.

## 9. Acceptance criteria for the S3 closeout

1. Every input is pinned at a named commit; nothing converts a failure, a waiver, a deviation, a deferral or an unavailable result into a pass.
2. The two frozen files are in the repository and hash to their pins after commit; the composition, flags and isolation limits are stated; the precondition check is recorded with its result.
3. Every one of the 151 runtime operations appears exactly once in the inventory with a classification of section 3.4 and its authority. Target contracts are sourced from accepted S1a-P, S1a-P2, S2 and gate G1 records; the S1a-T class operations are recorded as compatibility surface carrying acceptance evidence. Compatibility, pilot-only, example, proposal and OPEN-OWNER operations stay distinct.
4. Every M2-AT row has: an accepted status from the sources of section 4; or its D-171 disposition (05, 06, 07); or its D-210 disposition (09); or the accepted G1 wording (08 and the StoryRun part of 10). Anything else blocks closure.
5. The parity table of section 3.5 is complete for the M2 target operations; every DIFFERENT or ABSENT item is listed as OPEN; the partial extent of the check is stated.
6. The four departures of section 1 are stated in the closeout report and in the entry that closes M2. The OpenAPI P3 gate is reported OPEN. NFR-36, NFR-38 and S1b keep their partial or deferred status. K3 is reported NOT VERIFIED; the Story-chain target is reported as established for a new database by gate G1 under D-211 item 3, and not otherwise.
7. The limitation ledger contains at least section 5, each item with an owner or phase ("conditions được gán owner/phase"). No new route, schema, product rule, migration or SRS change.
8. Independent review ("independent review ACCEPTED"): a fresh cold review of the exact pinned S3 package — reviewer model set explicitly to Sonnet 5.5 high or Opus 5.5 high, never Fable, model and effort recorded — returns READY or READY WITH NOTES with zero P1 and zero P2 findings. A review by another tool or model does not count. At most five review rounds (D-171 item 11); the work returns to the owner when a finding repeats in two consecutive rounds, when the P1 and P2 count does not fall after a round, or when a change of scope or allowlist is proposed. A review is not an approval.
9. The owner separately records S3 acceptance and M2 closure. A push, and the merge of draft PR #29, each need the owner's own instruction.

Meeting these criteria authorizes nothing beyond S3: not FR-C-08, client integration, M3, a database action, a gate G2 or the integration of PR #26.

**Stop and return to the owner if:** a pin differs; the precondition check finds a difference other than the three expected; an operation fits no classification value; a route, catalog or projection change would be needed; an acceptance row has no accepted status after the named sources are read; a required record is absent or failed; the adopted SRS and a decision conflict on a point other than the parameter spelling of section 3.5; a new requirement or scope expansion appears; a check would need a database, network, provider or application start.

## 10. Disposition of the reviews

**Review R1 of Draft 8 (L1 to L16):**

| ID | Disposition |
|---|---|
| L1 | Section 3.3: reference set named; `changedPaths` under `backend/src` added; expected result stated |
| L2 | Section 4: S1a specifications and acceptance entries are sources; S1a-P2 listed as a separate block; section 8 pins them |
| L3 | D-211 items 4 and 5; section 3.4 (authority table; OPEN-OWNER value; the foundation-route gap in section 5) |
| L4 | D-211 item 2; section 3.5; departure 3; criterion 5 |
| L5 | D-211 item 1; departure 4 with the stop column quoted; "D9" recorded as not established |
| L6 | This draft is self-contained; Draft 6's rules restated in sections 2, 5, 6 and 9; reproducibility conflict stated in section 3.2; tools, cache, ceilings and pins in sections 6 and 8; the approval block covers sections 1 to 9 |
| L7 | D-211 item 3; criterion 6; source of the term corrected in section 5 |
| L8 | Section 3.1 and section 6: explicit `.gitattributes` line; hash checks defined |
| L9 | Section 6: the drive-letter search named as the operative check; `validate_skeleton` dropped |
| L10 | Section 5, open owner questions: the commit and push of `7cc5cf74` have no repository record of their own |
| L11 | Section 5 |
| L12 | Criterion 8 |
| L13 | Section 3.5 rule |
| L14 | Section 5: counted by search during S3; no figure asserted here |
| L15 | Section 3.1 (extension decided by approving this draft); D-210's preamble is left as recorded: its items 5 and 6 concern the export and quote no baseline sentence |
| L16 | Header |

**Review R1 of Draft 7 (F1 to F22):** F1, F3, F6, F10, F11, F13, F16, F17, F19, F21, F22 were found resolved by Draft 8. F2: section 4 and decision 4. F4: section 1 (row quoted in three columns; four departures). F5: this draft is self-contained (L6). F7: section 3.3. F8: section 6. F9: section 5. F12: section 5. F14: see L10. F15: section 3.4 (list and deletion request among the targets) and section 3.5 (spelling). F18: see L7. F20: section 4, S1a-P2 block.

## 11. Approval block (for the owner)

- [ ] S3 approved as written (sections 1 to 9), including the per-operation scope of section 3.4, the hash-only citations of section 3.1 and the allowlist of section 6.
- [ ] Launch: the session may start S3 work.
- [ ] A further independent review of this draft is wanted first.
