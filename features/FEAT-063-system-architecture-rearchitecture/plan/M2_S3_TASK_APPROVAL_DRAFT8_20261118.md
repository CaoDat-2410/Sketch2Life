# M2 S3 — contract freeze, evidence reconciliation and M2 closure — Task Approval Draft 8

- **Status:** DRAFT / NOT APPROVED / NOT LAUNCHED. Until the owner approves it, this text authorizes nothing: no S3 work, test, validator run for evidence, OpenAPI generation, database or migration action, provider call, network access, stage, commit, push or merge. Drafts 1 to 7 remain unchanged.
- **Date:** 2026-11-18. **Author:** coordinating Claude session (Fable 5.2). **Owner:** Person 2. Not independently reviewed.
- **Worktree:** `.worktrees/m2-s2`, branch `feature/feat063-m2-s2`, HEAD `4cfd1412a4812cc862e3de00397c29c9c5b8c945` (five commits ahead of the remote; nothing pushed since `7cc5cf74`).
- **Predecessor:** `plan/M2_S3_TASK_APPROVAL_DRAFT7_20261117.md`, SHA-256 `3E55699F862F4650DD616C816458CCE784A892CF90340C3589EA8851D71036A9`; its cold review R1 (Sonnet 5.5, high): NOT READY, 0 P1 / 9 P2 / 12 P3, `evidence/M2_S3_DRAFT7_COLD_REVIEW_R1_20261117.md`, SHA-256 `FE0281A01B5DC1F10A47A22FCD94FA01C502C3DF991AA84633A80E2D18FC7164`. Section 10 disposes of its findings.
- `OWNER_MODAL_CALL_APPROVED=NO`.

## 0. What changed since Draft 7

| Topic | Draft 7 | Now |
|---|---|---|
| PostgreSQL evidence for M2-AT-08, 09, 10 | None; the review found M2 could not close by documentation alone | Gate G1 (reduced) ran for M2-AT-08 and M2-AT-10; the owner accepted the result as "gate G1 passed with deviations DV-1 to DV-19, on the second attempt" (`evidence/M2_S2_POSTGRES_GATE_G1_EVIDENCE_20261118.md`, SHA-256 `CEB5D6C092C422781A0F614A3B3806581AFADCF6B58467B0060DE8A5CA759640`). M2-AT-09 is DEFERRED by D-210 |
| Product state | S2 closed at `7cc5cf74` | Four PostgreSQL write defects in the Parent story-run repository were found by the gate work and repaired in commit `b430b67a`; three are verified on PostgreSQL, one (W3) is not |
| Owner decisions S3-D1 to S3-D4 | Recorded from a short reply; the review found that reading not defensible | Each asked separately and recorded as D-210 (section 1) |
| OpenAPI P3 gate of the baseline's S3 row | Omitted | Carried OPEN by D-210 |
| Controlling definition of the acceptance tests | Not named | Foundation plan Draft 10 (D-151) with later narrowings, D-210 item 3 |

## 1. Authority and decisions

- **Working SRS:** the copy adopted by D-209 (`artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md`, 701,157 bytes, SHA-256 `B9B1F42D0BB118C19C81607D3913B7E4F1D8B6F673F0C3FBB6402888FEB675F5`), unsigned and not final. The root checkout and the mobile worktree still point at an earlier copy; that pointer is reconciled before this lane's requirements are published across worktrees. Not S3 work.
- **Baseline:** `plan/M2_PARENT_TEACHER_FOUNDATION_PLAN_DRAFT10_20261106.md`, SHA-256 `7539D642FFD95A9A21C99A0C17C5095FF1443E19538017A92789F631D633E2B1`, accepted by D-151 as the M2 planning baseline with five carried conditions C1 to C5. Its S3 row (line 265) reads:

  > Điều kiện đề xuất, owner phải chấp nhận trong Task Approval S3: chỉ M2-AT-05/06/07 được phép ở trạng thái NOT RUN/DEFERRED khi S1b vẫn DEFERRED; mọi M2-AT khác phải chạy và pass. NFR-36 và NFR-38 có disposition; OpenAPI parity được kiểm; conditions được gán owner/phase; independent review ACCEPTED.

  and, for the work: "Đối chiếu evidence và freeze contract; đóng OpenAPI P3 hai POST submit/cancel trước frontend/client."
- **D-210 (2026-11-18)** fixes, each item selected by the owner with the governing sentence quoted:
  1. M2-AT-09: NOT RUN / DEFERRED. No frontend or client integration with the three assistance operations until a PostgreSQL gate for M2-AT-09 has passed or the owner decides otherwise.
  2. The OpenAPI P3 gate for the two assistance POST operations: carried OPEN; S3 does not close it.
  3. Controlling definition of M2-AT-01 to M2-AT-11: foundation plan Draft 10, each row read with the narrowings approved later (D-171, the S1a task approvals, S2 Draft 18 section 4, deviations DV-1 to DV-19 of gate G1). Differences in foundation plan Draft 11 (rows M2-AT-01 and M2-AT-10) are recorded, not applied.
  4. M2 may be closed "with recorded debt and deviations"; every item goes into the limitation ledger with an owner or phase.
  5. Freeze the composition captured by the mapper task's post export (both export flags on), stating which operations exist only because of those flags.
  6. Reuse that export: copy the two schema files byte-for-byte into the feature folder; manifests that contain local absolute paths are cited by hash only.

  **Departures from the baseline's S3 row, by D-210:** "mọi M2-AT khác phải chạy và pass" is relaxed for M2-AT-08 and M2-AT-10 (passed with deviations) and M2-AT-09 (deferred); "đóng OpenAPI P3" is not done in S3. S3 states both as departures in every output; it never reports them as met.
- **Other decisions carried, to be read at the pinned hash during S3 work before being relied on** (their texts were not re-read for this draft): D-171 (S1b deferred; M2-AT-05/06/07 NOT RUN / DEFERRED; NFR-36 and NFR-38 PARTIAL with stated contents), D-188 (S1a-P accepted with limitations; K3 an unresolved limitation), D-198 (S2 on the integrated Parent StoryRun implementation; K3 NOT VERIFIED), D-199 to D-202 and D-206 (cancel and job-status contract), D-203 (earlier SRS baseline, superseded as working source by D-209), D-207 (S2 allowlist), D-208 (FR-C-08 planning dispositions given against an earlier SRS copy; D-209 puts the deletion eligibility of FAILED and ABANDONED runs back under review: S3 records it OPEN-OWNER and neither resolves nor assumes it).
- **Decision-number caveat:** `DECISIONS.md` records that identifiers D-135 to D-149 occur twice (two branches numbered independently); references here mean the M2 line. D-127 has two rows; the cancel row is meant.
- **Draft 6 is not superseded on the rules it states that this draft does not change.** S3 work reads `plan/M2_S3_TASK_APPROVAL_DRAFT6_20261116.md` (SHA-256 `BF7792925F06ED66720850CEE916EFBF2F724100B84D3B2BF3545F11E19108C4`) in full first and treats as binding, in particular: the D-188 S1a-P limitations; the content of the D-171 NFR-36 and NFR-38 dispositions; no database, provider or network use to create evidence; credential and database isolation; recomputing every pin before review and before approval. Where Draft 6 names an SRS copy, an S2 state or a pin that has since changed, sections 0, 1 and 8 here govern. Draft 5 is stale and is not an input.

## 2. Purpose and scope

S3 is a documentation, contract-freeze and evidence-reconciliation phase. It adds no product feature, route, schema, table, migration, provider integration, client integration or M3 opening. It repairs no debt and runs no test.

Deliverables (exact paths in section 6):

1. The two frozen schema files, copied byte-for-byte.
2. An operation inventory: every method and path of the frozen runtime schema exactly once, classified, with authority and evidence level.
3. The M2-AT-01 to M2-AT-11 evidence ledger.
4. The limitation and inherited-condition ledger.
5. A closeout report with a recommendation; then, separately, the owner's decision on S3 acceptance and M2 closure.

Evidence levels stay distinct and are named in every row: source-declared; composed or mounted; present in the frozen runtime schema; present in the client-facing projection; exercised by an accepted offline test run; exercised on PostgreSQL by gate G1 (with its deviations); runtime-verified otherwise. Unavailable evidence is NOT RUN or NOT VERIFIED. A passed test selection is not by itself a passed acceptance test.

## 3. Contract freeze

**What is frozen.** The freeze is the pair of schema files themselves, pinned by hash:

| Source (git-ignored, on the owner's machine) | Bytes | SHA-256 | Copied to |
|---|---:|---|---|
| `backend/tmp/openapi-mapper-d10-post-367b579d97eb4f0a99cd6a6d329bb1f4/runtime-post.json` | 847,426 | `E9C2D7C8E95225F3D1F8B708C50C9ACC19CF822508ABEFD4F85298AD2E6B3A0C` | `artifacts/m2-s3/openapi-runtime-frozen.json` |
| `.../published-post.json` | 213,111 | `F23BF908A104667153F88D6438AE8E95BE9895A76DAB7099877EBE9EFC49589D` | `artifacts/m2-s3/openapi-client-projection-frozen.json` |

Counted for this draft by method and path with a JSON parser: runtime 151 operations on 134 paths; projection 34 operations on 24 paths.

Cited by hash only, **not copied** (they contain local absolute paths, or are not needed in the repository): `environment.json` `E974D4926BEEF15DA04A669F1F714DEF6C117E79484BF115F29FEB252E940AAE`; `run-manifest.json` `1286E0F36FA98C9CEE19CB09415CA0BDE05D5606A9289A878850B96F6965548F`; `source-state.json` `27DBD75A78DE3A3BB841558719F790D5E849F031469CA2E56DD8715C3A340E27`; `invocation.json` `305B1FBEE91D049778ACC042050D432147B771CB045D6AF9FC97B4DE7F446F0F`; and from the comparison folder `openapi-mapper-d10-compare-7e7f0b0d854e48099ea903ba920ba7f4`: `field-delta-report.json` `E8F265F51410FD968AC1A14F1113ACB07C555BEBA23DFBDE0093A7679FFE5C6D`, `run-manifest.json` `FCC401E0F46C64FA04DAD251ACC9139C7E39B59ADDAE2E173C4EBDC0094C3059`.

**Scope of the per-operation record.** Draft 6 listed, for every operation, request and response schemas, headers, status and error contract, idempotency and invariants. For 151 operations S3 does **not** re-type those: they are frozen as they stand in the runtime schema file, and the inventory row points at the operation in that file. The inventory row records: method; path with its parameter spelling; `operationId`; tag; present in the projection (yes or no); composition condition (always mounted, pilot flag, storage-example flag); classification; actor and authorization scope where an accepted record states it; authority (SRS section, decision, accepted phase record); evidence levels; open items. A fuller per-operation contract card is written only for the M2 target operations: the Parent profile operations accepted in S1a-P and S1a-P2, `POST /v1/story-runs`, the two owner-scoped Parent reads, and `POST /v1/story-runs/{run_id}/cancel`. Approving this draft approves that scope.

**Classification values:** M2 target contract; compatibility or legacy operation (mounted, not an M2 target); pilot-only (exists because of the pilot flag); local example (exists because of the storage-example flag); proposal or conditional operation; unclassifiable (a stop condition).

**Facts the freeze must state and may not soften:**

- The export ran with `SKETCH2LIFE_STORAGE_EXAMPLE_ENABLED` and `SKETCH2LIFE_SYNTHETIC_PILOT_ENABLED` on, in the lock-exact task environment with a cleared child environment, **without** an operating-system egress block; database, provider, runtime and network isolation are recorded as not proven for it. The owner accepted the egress deviation for the mapper task.
- The mapper comparison shows the projection equals the pinned projection of the runtime file, and that the **134 catalogued operations** carry the catalog description, tag and response status set. That evidence does not cover the 5 pilot-only and 12 uncatalogued operations. (Counts as given by review R1 of Draft 7; S3 work recounts them.)
- `POST /v1/story-runs/{run_id}/cancel` is uncatalogued: it has no description in the runtime schema and is absent from the client-facing projection. It is an M2 target operation with PostgreSQL evidence from gate G1 and no place in the published projection. S3 records that as an open item; it changes neither the catalog nor the projection.
- The three assistance operations of M2-AT-09 exist only with the pilot flag.
- No export has been made since. The schema inputs were verified equal to the commit `7cc5cf74` state by review R1 of Draft 7. Since `7cc5cf74` one file under `backend/src` changed, `infrastructure/persistence/parent_story_repository.py` (commit `b430b67a`: SQL NULL binding and a flush); it defines no route, schema or catalog entry. That it cannot change the schema is static reasoning, not a re-export.

**Precondition check before copying** (section 7, step 2): every path listed in the export's `source-state.json` as a pinned input is hashed and compared with the recorded value; any difference other than a test module is a stop condition.

## 4. Acceptance-test ledger

One row per acceptance test, definition from foundation plan Draft 10, with the narrowing that applies. Each status is copied from an accepted record; no test is run.

| Acceptance test | Status rule for S3 | Records to reconcile |
|---|---|---|
| M2-AT-01 to M2-AT-04B | The status the accepted S1a-T, S1a-P and S1a-P2 records give, with their scope limits. S1a-P2 is "accepted with known gap" and uses its own acceptance-test series: the mapping to the M2 rows is stated, not assumed. S1a-T covers M2-AT-04A and 04B only in part | `evidence/M2_S1A_T_CLOSURE_RECORD_20261109.md`, `M2_S1A_T_IMPLEMENTATION_REPORT_20261107.md`, `M2_S1A_T_K4_SOURCE_RECONCILIATION_20261107.md`, `M2_S1A_P_CLOSURE_RECORD_20261109.md`, `M2_S1A_P_IMPLEMENTATION_REPORT_20261109.md`, `M2_S1A_P2_CLOSURE_RECORD_20261112.md`, `M2_S1A_P2_IMPLEMENTATION_REPORT_20261112.md`, `M2_S1A_P2_REAL_POSTGRES_EVIDENCE_ADDENDUM_20261113.md` |
| M2-AT-05, 06, 07 | NOT RUN / DEFERRED under D-171. Never PASS | D-171 |
| M2-AT-08 | "Gate G1 passed with deviations DV-1 to DV-19, on the second attempt" (owner acceptance of 2026-11-18). Offline S2 evidence is listed separately at its own level. Not "ran and passed" | `evidence/M2_S2_POSTGRES_GATE_G1_EVIDENCE_20261118.md`; `plan/M2_S2_POSTGRES_GATE_G1_TASK_APPROVAL_DRAFT2_20261117.md` section 3.1; `plan/M2_S2_POSTGRES_GATE_G1_GATE_RUN_TASK_APPROVAL_DRAFT1_20261118.md`; `evidence/M2_S2_IMPLEMENTATION_REPORT_20261114.md`; `evidence/M2_S2_CLOSURE_VERIFICATION_EVIDENCE_20261117.md` |
| M2-AT-09 | NOT RUN / DEFERRED under D-210 item 1, with the client-integration block | D-210 |
| M2-AT-10 | Its PostgreSQL part: as M2-AT-08 (deviations DV-7, DV-8, DV-17 in particular). Its contract and unit part: what the accepted S1a and S2 records give. D-151 condition C2 (state the layer) applies | As M2-AT-08, plus the S1a records |
| M2-AT-11 | The status the accepted S1a records give | S1a records |

Each row carries: definition source and line; narrowing; runner or owner; date; the approved command or owner-run reference; result; evidence path and digest; accepted scope; limits. A failed, interrupted, missing, stale or owner-unverified result stays so. Where no accepted record gives a status, the row says NOT ESTABLISHED and that is a stop condition, not something S3 fills in.

D-151 conditions C1 to C5 are listed in the ledger with what became of each.

## 5. Limitation and inherited-condition ledger

Built from each phase's closure record, not from memory, and at least containing the following, each with an owner or phase:

- **Deferred or partial by decision:** S1b; M2-AT-05/06/07; NFR-36 PARTIAL and NFR-38 PARTIAL with the contents D-171 gives; M2-AT-09 and its client-integration block; the OpenAPI P3 gate (OPEN).
- **Gate G1:** deviations DV-1 to DV-19; S2 Draft 18 row 13 not covered; one run on one machine and one PostgreSQL minor version; no operating-system egress block; the API ran as the role that owns the schema; create with a lesson version not exercised; the first gate attempt was interrupted and the result comes from an owner-approved second attempt.
- **Product defects found after the S2 closure:** four PostgreSQL write defects in `parent_story_repository.py`, repaired in `b430b67a`; W3 (the pending receipt used by story-revision reservation) not verified on PostgreSQL; other modules not surveyed for the same patterns; M2-S2 was closed while these defects existed, and no addendum to the S2 closure record has been decided.
- **What S2 was closed with:** 19 added Mypy `arg-type` diagnostics accepted as typing debt and 336 existing; 17 existing Ruff diagnostics on the S2 source paths and one on a contract test; only the nine-file pytest selection ran, never the full backend suite; the production role adapter not exercised on PostgreSQL; the mapper task's recorded deviations (four commands needed a second run; post export without the egress block; two test files changed after export and comparison without re-runs; the request-identifier inventory OPEN beyond Amendment 1); the stale-version P3 on broader routes; the FEAT-047 description overlay kept; the unexplained hang of 2026-11-14; limits of the diagnostic comparison; open wording items recorded in the S2 report.
- **S1a:** the D-188 limitations; K3 NOT VERIFIED under D-188 and D-198; S1a-P2's known gap; partial coverage of M2-AT-04A and 04B.
- **Open owner questions:** deletion eligibility of FAILED and ABANDONED runs under the adopted SRS (FR-C-08); the decision-number citation convention; the SRS pointer in other worktrees; re-pinning of the roadmap addendum required by D-209; 28 repository documents that contain local absolute paths.
- **Records not independently reviewed**, listed by name.
- **Cancel operation** absent from the catalog and the projection (section 3).

The historical labels A2, B1, B2, N-1 and N-3 are evidence pointers needing reconciliation, never live database facts. "Gate A Story-chain target" is used as defined in the S1a records; the ledger quotes that definition or records that none was found.

S3 cannot repair, mask or broaden any of these.

## 6. Allowlist

New files, exactly these (dates are the date of writing):

| Path under the feature folder | Content |
|---|---|
| `artifacts/m2-s3/openapi-runtime-frozen.json` | byte copy (section 3) |
| `artifacts/m2-s3/openapi-client-projection-frozen.json` | byte copy (section 3) |
| `evidence/M2_S3_OPERATION_INVENTORY_AND_CONTRACT_FREEZE_20261118.md` | inventory table, contract cards for the M2 target operations, freeze statement |
| `evidence/M2_S3_ACCEPTANCE_TEST_LEDGER_20261118.md` | section 4 |
| `evidence/M2_S3_LIMITATION_LEDGER_20261118.md` | section 5 |
| `evidence/M2_S3_CLOSEOUT_REPORT_20261118.md` | reconciliation summary, pins, what was and was not read, recommendation |

Appended, never rewritten: `approvals/TASK_APPROVAL.md`, `status/STATUS.md`, `CONTEXT.md`. `.gitattributes` may gain an entry only if a copied file would otherwise be altered by line-ending normalisation; the copies must hash to the pins after `git add`.

Scratch only (repository-root `tmp/m2-s3/`, git-ignored): one read-only extractor script that parses the two schema files and prints method, path, `operationId`, tags and projection membership as a table; its output. The extractor imports no application code, opens no socket and reads no other file. It is linted before use; its hash and the hash of its output are recorded in the closeout report. Every inventory row is produced from that output; the count must be 151 and every row unique.

Not allowed: any change to a source, test, migration, catalog, schema or configuration file; any export or application start; any test run; any database, container, provider or network use; any change to an earlier record; any commit, push or merge without the owner's separate word.

Checks: SHA-256 of copies against pins; the extractor's count checks; `validate_harness`, `validate_repository_security`, `validate_architecture`, `validate_skeleton` (a new folder is added), `git diff --check`; a search of the new files for drive-letter paths.

## 7. Order of work

1. Recompute every pin of section 8; any difference is reported as CHANGED SINCE OBSERVATION and work stops.
2. Precondition check of section 3; copy the two files; verify hashes.
3. Read in full, at the pinned hashes: Draft 6; foundation plan Draft 10 rows M2-AT-01 to 11, its S3 row and D-151 with C1 to C5; the rows of Draft 11 that differ; D-171, D-188, D-198 to D-210; the eight S1a records; the S2 records; the gate G1 records; S2 Draft 18 section 4.
4. Inventory, then contract cards, then the acceptance-test ledger, then the limitation ledger, then the closeout report.
5. Validators; record entries.
6. Independent cold review of the pinned S3 package (section 9). Then the owner's separate decisions.

## 8. Pins at the time of this draft

Observed at HEAD `4cfd1412`, with `DECISIONS.md` carrying the uncommitted D-210 row. Not launch-time authorization: step 1 recomputes them.

| Input | Bytes | SHA-256 |
|---|---:|---|
| `docs/context/SRS_AUTHORITY.md` | 5,120 | `CACA7EC03CB570F3276AEA3EAF9214F93DDEC19F3030671A47DB590E19F74726` |
| `artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md` | 701,157 | `B9B1F42D0BB118C19C81607D3913B7E4F1D8B6F673F0C3FBB6402888FEB675F5` |
| `DECISIONS.md` (with D-210) | 223,438 | `6BC13701D64003671B0545041CD9191FC6D7FB3608BF077974818C641EAC32D5` |
| `approvals/TASK_APPROVAL.md` | 496,807 | `11E3DC400EFFAF166958A94C43AF159F6C7336F92F0F05BDDCED5C2E8CF302A2` |
| `status/STATUS.md` | 123,718 | `046E59EECA355848C8D78F98F24130C8FD322945F913C3F71B33B788098EA809` |
| `CONTEXT.md` | 123,910 | `220A4678FFA3D82FEB5C8FD9552395861C04A37ABAF02CBA4FF28AF871D69314` |
| `plan/M2_PARENT_TEACHER_FOUNDATION_PLAN_DRAFT10_20261106.md` | 111,790 | `7539D642FFD95A9A21C99A0C17C5095FF1443E19538017A92789F631D633E2B1` |
| `plan/M2_S2_TASK_APPROVAL_DRAFT18_20261114.md` | 101,153 | `5CA09CC6F9D936C1BA74772251F4D3A9C0480F3E6F82818FE11114205FD3E331` |
| `evidence/M2_S2_POSTGRES_GATE_G1_EVIDENCE_20261118.md` | 18,329 | `CEB5D6C092C422781A0F614A3B3806581AFADCF6B58467B0060DE8A5CA759640` |
| `evidence/M2_S2_IMPLEMENTATION_REPORT_20261114.md` | 25,879 | `F49D1FDB2B3C26387FFABC51C316F226C5D1FC5FC12B4856B0A6172A81941F55` |
| `evidence/M2_S2_SHARED_OPENAPI_MAPPER_IMPLEMENTATION_EVIDENCE_20261117.md` | 12,424 | `CCB014AFB23D7A156FC4E229C7B4A717B758982D425023E075AAED632F5C60C6` |
| `evidence/M2_S2_CLOSURE_VERIFICATION_EVIDENCE_20261117.md` | 10,487 | `CF644A09FF0802F7A2E4444CCBCC9E01B67528A3DC8B3F718686E441ED454525` |

The eight S1a records, the gate's other records, Draft 6 and Draft 11 are pinned in step 1 of the work and listed in the closeout report. `evidence/M2_REV67_CROSSWALK_FOR_S2_S3_20261113.md` was written against an earlier SRS copy and is stale; it is not an input.

**Not read for this draft:** Draft 6; the decision texts other than D-151, D-171 (first lines), D-209 and D-210; the eight S1a records; the Rev67 crosswalk; the adopted SRS beyond what earlier drafts state. The operation counts by method and path were recomputed; the 134 / 5 / 12 split was not.

## 9. Acceptance criteria for the S3 closeout

1. Every input is pinned at a named commit; nothing converts a failure, a waiver, a deviation, a deferral or an unavailable result into a pass.
2. The two frozen files are in the repository and hash to their pins; the composition and flags are stated; the precondition check is recorded.
3. Every one of the 151 runtime operations appears exactly once in the inventory with a classification and an authority, or the work stopped. Target contracts are sourced from accepted S1a-P, S1a-P2, S2 and gate G1 records. Compatibility, pilot-only, example and proposal operations stay distinct.
4. Every M2-AT row has: an accepted result; or its D-171 disposition (05, 06, 07); or its D-210 disposition (09); or the accepted G1 wording (08 and the PostgreSQL part of 10). Anything else blocks closure.
5. The departures from the baseline's S3 row (section 1) are stated in the closeout report and in the entry that closes M2. The OpenAPI P3 gate is reported OPEN. NFR-36, NFR-38 and S1b keep their partial or deferred status. K3 is reported NOT VERIFIED unless a newer accepted record changes it.
6. The limitation ledger contains at least section 5, each item with an owner or phase.
7. No new route, schema, product rule, migration or SRS change.
8. A fresh independent cold review of the exact pinned S3 package — reviewer model set explicitly to Sonnet 5.5 high or Opus 5.5 high, never Fable, model and effort recorded — returns READY or READY WITH NOTES with zero P1 and zero P2 findings. A review by another tool or model does not count for this criterion. A review is not an approval.
9. The owner separately records S3 acceptance and M2 closure. A push, and the merge of draft PR #29, each need the owner's own instruction.

Meeting these criteria authorizes nothing beyond S3: not FR-C-08, client integration, M3, a database action, a gate G2 or the integration of PR #26.

**Stop and return to the owner if:** a pin differs; the precondition check finds a changed schema input; an operation cannot be classified from current authority; a route, catalog or projection change would be needed; a required S1a, S2 or gate record is absent, failed or silent on a row; the adopted SRS and an earlier decision conflict on a point S3 must state; a new requirement or scope expansion appears; a check would need a database, network, provider or application start.

## 10. Disposition of review R1 of Draft 7

| ID | Disposition |
|---|---|
| F1 | D-210: every decision asked separately; the earlier reading is withdrawn |
| F2 | D-210 item 3; section 4 lists the narrowing sources and D-151 C1 to C5 |
| F3 | Gate G1 for M2-AT-08 and 10 (accepted with deviations); M2-AT-09 deferred by D-210 |
| F4 | Section 1 quotes the S3 row and states the two departures; criterion 4 is exact; the OpenAPI P3 gate is carried OPEN by decision |
| F5 | Section 1, last bullet (Draft 6 rules binding); criterion 8 (READY or READY WITH NOTES); sections 6 and 7 (pins recomputed, isolation) |
| F6 | Section 3: two files copied; manifests and the comparison report cited by hash only |
| F7 | Section 3: precondition check; isolation flags and profile stated; the one source change since stated |
| F8 | Section 6: a linted, read-only extractor in scratch; count and uniqueness checks |
| F9 | Section 5 |
| F10 | Section 3: 134 catalogued operations; the cancel operation; the flag dependency of the assistance operations |
| F11 | Section 1 (D-208 against an earlier copy; deletion eligibility OPEN-OWNER) |
| F12 | Section 5 (four commands; further deviations to be taken from the mapper evidence) |
| F13 | Draft 7's count is not carried; section 8 lists pins without that claim |
| F14 | STATUS and CONTEXT entries of 2026-11-18 record the commits; nothing is pushed since `7cc5cf74` |
| F15 | Section 3 names the S1a-P2 list and delete operations among the targets; parameter spelling is recorded per row |
| F16 | Section 8: the crosswalk is stale and not an input |
| F17 | Section 5, open owner questions |
| F18 | Section 5, last paragraph |
| F19 | Criterion 8 |
| F20 | Section 4, first row |
| F21, F22 | No change needed |

## 11. Approval block (for the owner)

- [ ] S3 approved as written (sections 2 to 9), including the per-operation scope of section 3 and the allowlist of section 6.
- [ ] Launch: the session may start S3 work.
- [ ] An independent review of this draft is wanted first (Opus 5.5 high recommended: long, cross-document).
