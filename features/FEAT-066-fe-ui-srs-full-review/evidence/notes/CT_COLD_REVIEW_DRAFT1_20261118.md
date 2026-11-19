# C-T package Draft 1 — cold review record (round 1, 2026-11-18)

- **Artifact:** `plan/PLAN_CT_TEACHER_SLICE_PACKAGE_DRAFT1_20261118.md`, 14,777 B, SHA-256 `2E994E20F3DDF7886D19AFD9E8CD80EC096BB9A3A762589F41C51402C823E57B`.
- **Reviewer:** a separate subagent. Model Sonnet 5.5, reasoning effort high, both set explicitly. It worked read-only.
- **Pin check:** PASS (artifact, SRS, register, roadmap, CONV-1 Draft 5, C-M Draft 4, DECISIONS 65,589 B; BE `2dddc607`, web `297a28b1`; SRS lines and Bruno numbers verified).
- **Verdict:** **NOT READY**. P1 = 0, P2 = 6, P3 = 6. No safety or privacy break.

## Findings

| ID | Sev | Finding (short) |
|---|---|---|
| CT-R1-01 | P2 | Upload sessions have no stored revision (`tables.py` 58–83), and the router's `_ETAG` accepts only a positive integer; decide now between a derived revision (no migration) and a migration in the allowlist; say what the revision covers |
| CT-R1-02 | P2 | The FE cannot read the session `ETag` (`backendRequest` returns only the body; `UploadSessionV1` has no `revision`); create (201) is not listed though the import page aborts right after create; the complete response is a source-document status |
| CT-R1-03 | P2 | The receipt mechanism (`_idempotent`, `_replay`) is in `service.py`, but the allowlist limits `service.py` to the upload ETag; the four methods take no key; the order must be replay, revision check, execute (the `decide_access_grant` pattern) with a fingerprint over target ID, `If-Match` and body |
| CT-R1-04 | P2 | C-D7 stale 409s must carry the current `ETag` and `current_version`; CONV-1 deferred that for Lesson Library; C-T1 covers only abort, not A18, A19, B07, B08 |
| CT-R1-05 | P2 | CONV-1 assigned to C-T the upload and file code and status alignment (`REQUEST_TOO_LARGE`, `PART_CONFLICT`, `UPLOAD_EXPIRED` 409→410, `UPLOAD_INCOMPLETE` 409→422), the Lesson Library and Teacher AI domain 422 codes, Teacher AI items, `assistance_requests.py` envelope and ClamAV; the package does not dispose of them |
| CT-R1-06 | P2 | 202 on complete is a status relabel only (complete is synchronous; success is terminal `READY_FOR_REVIEW`); the SRS 1653 extraction job is not assigned to C-T4 |
| CT-R1-07 | P2 | B07 needs a ready source-document revision, so its control belongs on the import page; B08 needs a grant ID, but a Teacher has no route listing a lesson's grants |
| CT-R1-08 | P3 | PATCH already creates an immutable version (`service.py` 209–244); settle it |
| CT-R1-09 | P3 | C01 is always mounted; the gate is a request-time 409 |
| CT-R1-10 | P3 | Cite D-066-76; C-T1 position relative to the runner and B-2 to B-5 |
| CT-R1-11 | P3 | Bruno 087; `IDEMPOTENCY_MISMATCH_OPERATION_KEYS` constant and its catalog test; `test_http_error_conventions.py` |
| CT-R1-12 | P3 | Lesson paging already done in the FE; NEW markers incomplete |
| CT-R1-13 | P3 | A19 and B08 use `_staff`, so the key requirement also applies to School Manager calls (no web manager caller today) |

## Checks passed

Current route facts (defaults, headers, status codes, complete already keyed, abort unkeyed), MGR-7 behaviour, FE helper headers, queue and branch policy, only the web is affected, C-T3 and C-T4 deferrals SRS-faithful, no omitted register row, governance clean.

## Not verified

Rev37 catalog constants beyond those read; runtime behaviour; DTO field equality; ClamAV as the only scanner path.

## Next

Draft 2 (rounds used: 1 of 5).
