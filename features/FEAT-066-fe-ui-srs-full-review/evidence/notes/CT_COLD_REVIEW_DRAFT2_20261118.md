# C-T package Draft 2 — cold review record (round 2, 2026-11-18)

- **Artifact:** `plan/PLAN_CT_TEACHER_SLICE_PACKAGE_DRAFT2_20261118.md`, 19,629 B, SHA-256 `709C229245CC8A0162689505B786328398B6747EA1BC6133F23DD0CC5ED4B117`.
- **Reviewer:** a separate subagent. Model Sonnet 5.5, reasoning effort high, both set explicitly. It worked read-only.
- **Pin check:** PASS (artifact, Draft 1, round-1 record, SRS, register, roadmap, CONV-1 Draft 5, C-M Draft 4, DECISIONS 68,171 B; BE `2dddc607`, web `297a28b1`).
- **Verdict:** **NOT READY**. P1 = 0, P2 = 9, P3 = 4. Round 1 was 0 / 6 / 6.
- **D-171 item 11:** both stop conditions are met: P1 + P2 rose from 6 to 9, and the round-1 classes CT-R1-05 (deferral disposal) and CT-R1-07 (FE control without its inputs) recur as CT-R2-07 and CT-R2-08. A round 3 needs the owner's word.

## Round-1 status

FIXED: CT-R1-02, 03, 04, 06, 08, 09, 10, 12, 13. PARTIAL: CT-R1-01 (CT-R2-01 to 04), 05 (CT-R2-07), 07 (CT-R2-08), 11 (CT-R2-06, 11).

## Findings

| ID | Sev | Finding (short) |
|---|---|---|
| CT-R2-01 | P2 | A part PUT does not lock the session row, so an in-flight PUT can insert a part after an abort commits; same-part concurrent PUTs hit `IntegrityError` → 409 instead of the idempotent SRS 1656 result. `put_upload_part` must lock and re-check |
| CT-R2-02 | P2 | EXPIRED is written lazily on read, so the derived revision can change without a client write; `FAILED` is missing from the terminal list; abort ignores expiry |
| CT-R2-03 | P2 | "Abort of a non-OPEN session → 409" contradicts the idempotent ABORTED path and SRS 1658; the order of the revision and state checks is unstated |
| CT-R2-04 | P2 | 410 `UPLOAD_SESSION_EXPIRED` covers only the OPEN→EXPIRED moment; an already EXPIRED or FAILED session goes to `INVALID_TRANSITION`; the three call sites must change |
| CT-R2-05 | P2 | `LESSON_FILE_TOO_LARGE` is nearly unreachable: the request schema caps `byte_length` at 25,000,000, so a larger file gets 400 before the service's 413 |
| CT-R2-06 | P2 | `test_http_error_conventions.py` asserts 413 `REQUEST_TOO_LARGE` and must be edited, not "kept green" |
| CT-R2-07 | P2 | The CONV-1 deferrals shared by "C-M and C-T" (BE1 domain 422 codes, `CLASS_SCOPE_MISMATCH`, route-specific scope checks, BE1 409 `IDEMPOTENCY_KEY_REUSED`) and `CANVAS_SOURCE_UNAVAILABLE` are not disposed in C-T or C-M |
| CT-R2-08 | P2 | The B07 "create version" control needs full lesson content and the lesson revision; the import page has neither, so a content editor is hidden scope |
| CT-R2-09 | P2 | The FE keeps the create-time session revision, so abort after any part always gets 409; it must GET the session right before abort |
| CT-R2-10 | P3 | The middleware path is `interfaces/http/middleware/bounded_image_upload.py`; only the part PUT reaches the branch |
| CT-R2-11 | P3 | A22 (GET session) and A21's response change missing from the row map; Bruno 079 missing |
| CT-R2-12 | P3 | Ordering mechanics: inner `_commit()` calls, early returns, the path for `current_version`, and a concurrent same-key retry getting 409 |
| CT-R2-13 | P3 | Pre-slice upload-create receipts have no `revision`; the resume record has no abort key |

## Checks passed

The derived revision is computable from stored data and monotonic in valid flows; replay → revision → execute is feasible; HTTPException headers pass through CONV-1; the OpenAPI constant grows from 11 to 16; the SRS 867–871 codes match CT-6; C-T3, C-T4 and G-T1 deferrals are SRS-faithful; queue and governance clean; FE caller facts confirmed.

## Not verified

Runtime and PostgreSQL concurrency (CT-R2-01 from code reading); other Rev37 constants; DTO field equality; ClamAV as the only scanner path.

## Next

The owner decides between Draft 3 with round 3 and pausing C-T (rounds used: 2 of 5).
