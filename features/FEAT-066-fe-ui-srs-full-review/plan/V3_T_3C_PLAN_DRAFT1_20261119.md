# V3 T-3c plan, Draft 1: document revision edit as its own immutable revision (P-18b)

Status: DRAFT for fresh plan review. Date 2026-11-19. Goal v3, task T-3c (WP-3; AUD-T#15, SRS l.546, l.1437, l.1708). Facts verified read-only at HEAD `317b4da8`. Decisions are `T3C-Dn`. Nothing is implemented. **No migration**: `lesson.document_revisions` and its immutability trigger come from T-3a (`V3_T_3A_PLAN_DRAFT1_20261119.md` §4, item 3). Depends on T-3a and T-3b (revision 1 and the revision reads exist after T-3b).

## 1. HEAD facts

- **Today the edit rides the wrong route.** `POST /api/lesson-library/v1/organizations/{org}/lessons/{lesson_id}/versions` creates a lesson **version** (`routers/lesson_library.py`, `service.py:319-398`, C4 key at `:430-452` of the router per AUD-T#15); a library document revision is read-only (`get_document_revision`, `service.py:1045-1075`) and has `review_state` `NEEDS_REVIEW|CONFIRMED` only set when a version is created from it (`service.py:386`). There is no occurrence-level text edit (P-18b). The library routes stay unchanged.
- **Mutability today:** `lesson.library_document_revisions` has no trigger; immutability is by service convention only. DDL-A adds the DB-level guard for the new table (T-3a). Trigger tests exist for other modules (`tests/integration/learning_content/test_content_sql.py:176-185`).
- **Helpers:** `parse_idempotency_key` and `raise_stale_revision(current_version=, etag=)` (`api_conventions.py:59-80`; `error_envelope.py:240` carries `current_version` only for `STALE_REVISION`); receipts in `be1_command_receipts`; scope helper from T-3a (T3A-D3).
- **Text bound:** the parser caps extracted text at 2 MiB (`lesson_parser.py:19`), and DDL-A checks `octet_length(extracted_text) BETWEEN 1 AND 2097152`.

## 2. Decisions (SRS-cited)

- **T3C-D1 Route (l.798 "revision chỉnh sửa", l.546, TD-05).** `POST /v1/lesson-occurrences/{occurrence_id}/documents/{document_id}/revisions`. The SRS names the group but not the path; this is the plan's resource-style choice (TD-05 flag). A text edit never touches the source file or any earlier revision (FR-T-07 "giữ file giáo án gốc ... revision text bất biến mới").
- **T3C-D2 Request.** `{ "extracted_text": str, "expected_head_revision_no": int >= 1 }`, `extra=forbid`, and unlike the library schemas (`lesson_library.py:15` strips whitespace) **no `str_strip_whitespace`** on the text. `Idempotency-Key` required. The expected head is the body transport (C-D7, l.1699 "expected revision/hash"; the occurrence family uses body fields, T3A-D7). Text rules: UTF-8 byte length 1..2,097,152 (else 400 `INVALID_REQUEST`, `field_errors` `TOO_LONG` or `EMPTY`), not blank after trimming, no NUL character (400 `INVALID_FORMAT`). The text is stored exactly as sent (hash of the UTF-8 bytes); no normalisation, no HTML handling, never logged.
- **T3C-D3 Scope (l.864-865, T3A-D3).** Responsible `teacher` of the occurrence's class; unknown occurrence or document, other organization, unassigned, Manager, Parent: uniform 404; guide/observer 403 `ACTION_NOT_ALLOWED`; occurrence not writable or document `DELETED`: 409 `INVALID_STATE_TRANSITION`.
- **T3C-D4 Revision rule (l.546, l.1699).** In one transaction: lock the `source_documents` row `FOR UPDATE`; `head = max(revision_no)`; if `expected_head_revision_no != head`: **409 `STALE_REVISION`** with `current_version = head` and `ETag "<head>"` (the edit never overwrites or forks the head); else insert `revision_no = head + 1`, `origin=TEACHER_EDIT`, `base_revision_no = head`, `review_state=NEEDS_REVIEW`, `created_by` = the Teacher's account, parser columns NULL, `extraction_warnings []`, `page_coverage []`. A unique-violation on `(source_document_id, revision_no)` (a race the lock should prevent) is mapped to the same 409. **An edit whose text hash equals the head's hash writes nothing and returns 200 with the head revision** (no empty revisions; recorded as a technical choice, OQ-2).
- **T3C-D5 Immutability and review.** Revisions are never updated or deleted (DDL-A trigger: only the one-way `NEEDS_REVIEW -> CONFIRMED` stamp is allowed, applied by T-3d at plan confirm). An edit does **not** confirm itself: FR-T-07 "yêu cầu Teacher xem và duyệt trước khi dùng" is met when a plan that pins the revision is confirmed (l.1660, UC-04 postcondition). The SRS has no separate "approve revision" route; adding one is OQ-1.
- **T3C-D6 Pins are exact (l.546, l.1659).** Editing never moves an existing plan: a plan revision pins `document_revision_id`, so a newer text revision does not retarget a DRAFT or APPROVED plan (test).
- **T3C-D7 Keys and receipts (l.1697).** Scope `POST /v1/lesson-occurrences/{id}/documents/{doc}/revisions`; fingerprint over `{expected_head_revision_no, text_hash}`; same key and payload replays the stored result after re-authorising; another payload is 400 `INVALID_IDEMPOTENCY_KEY`. **The receipt stores references only** (`document_revision_id`, `revision_no`), not the text (the text can be 2 MiB); the replay reads the immutable row and returns it, and a replay after another edit still returns the original revision.
- **T3C-D8 Not planned here:** text screening (the SRS requires screened hints only for AI rewrites), concurrent live editing, per-document revision limits other than D9, AI help (X-10).
- **T3C-D9 Revision count guard (technical, OQ-3).** At most 50 revisions per source document (about 100 MiB worst case); the 51st edit is 409 `RESOURCE_CONFLICT`. The SRS sets no count; the bound protects storage and is easy to lift.

## 3. Route

| Route | Actor | Success | Errors |
|---|---|---|---|
| `POST /v1/lesson-occurrences/{occurrence_id}/documents/{document_id}/revisions` | responsible Teacher; key | **201** `LessonDocumentRevisionV2` (`revision_no`, `origin TEACHER_EDIT`, `base_revision_no`, `review_state`, `text_hash`, `extracted_text`, `created_at`), `Location` to the revision read (T-3b), `ETag "<text_hash>.<review_state>"`; **200** same body for a no-op | 400 `INVALID_REQUEST` (+`field_errors`), `INVALID_IDEMPOTENCY_KEY`; 404; 403; 409 `STALE_REVISION` (+`current_version`, `ETag`), `INVALID_STATE_TRANSITION`, `RESOURCE_CONFLICT` |

Reads come from T-3b (`GET .../revisions`, `GET .../revisions/{revision_no}`, document `ETag "<head>"` so a client knows the head). There is no `latest` alias; the head is `head_revision_no` on the document read.

## 4. Tests

- **Unit:** text validation (empty, blank, NUL, 2 MiB boundary in bytes with multi-byte characters), hash, head arithmetic, no-op detection, receipt holds no text, scope table reuse.
- **Contract:** one catalog operation; 201/200 bodies; 409 body has `current_version` and `ETag`; 400 field errors for each text rule; missing key; unknown field; the library `POST .../versions` operation unchanged (regression).
- **PostgreSQL (fresh `frc08_v3_t3c_*`; attach fixtures as in T-3b):** edit produces revision 2 with `base_revision_no 1` and revision 1 is byte-identical afterwards; edit of revision 2 gives 3; stale expected head 409 with the right current version (and the head unchanged); two concurrent edits on the same head: exactly one 201, one 409, no gap in numbering; same key replay equals the first and writes nothing, also after a later edit; same key another text 400; no-op edit returns 200 and the count is unchanged; 51st revision 409; another Teacher, Manager, unassigned, other organization: identical 404; guide 403; archived occurrence 409; deleted document 409; **trigger tests**: direct `UPDATE ... SET extracted_text`, `UPDATE ... SET extracted_text_hash`, `DELETE` and an update of any column other than the one-way review stamp each raise `DBAPIError`; the review stamp works once and cannot be reversed; a plan pinned to revision 1 still shows revision 1 after revision 2 exists.
- Base failures vs 83-id list; ruff/mypy on touched files; validators; `git diff --check`.

## 5. File allowlist

New: `tests/unit/test_lesson_document_revision_edit.py`, `tests/contract/test_lesson_document_revision_edit_route.py`, `tests/integration/lesson_occurrences/test_document_revision_edit_postgres.py`, evidence note `.../evidence/notes/V3_T_3C_EVIDENCE_20261119.md`.
Modified: `infrastructure/lesson_occurrences/documents.py` (T-3b file: edit command), `routers/lesson_occurrences.py`, `contracts/schemas/lesson_occurrences.py`; hot files `openapi_contract.py` (+ counts), `tests/contract/test_openapi_contract_catalog.py`, and, only if a new code needs a message, `error_envelope.py`. Not edited: alembic (no DDL), `lesson_library/*`, `app.py`, `router_composition.py`.

## 6. FE impact (not done), rollback, risks

- **FE:** Web Teacher "review and edit extracted text" screen: load head revision, send `expected_head_revision_no`, handle 409 by reloading, show history list; localized strings for any new message. Android: none.
- **Rollback:** revert the commit; rows written remain valid; no DDL.
- **Risks:** R1 large JSON bodies: add a request size guard if no global one exists (otherwise a 2 MiB text is parsed before the validator; check the app's body limit; if absent, declare the limit in the router and test it); R2 receipt replay depends on the immutable row, so the trigger and T-3a are prerequisites; R3 the no-op 200 may surprise a client that expects 201 (documented in OpenAPI).

## 7. Open questions (none blocks T-3c)

- **OQ-1** Does the owner want an explicit "approve extracted text" command before a plan may pin a revision (FR-T-07 says Teacher "duyệt" it; the SRS has no route)? Default: approval is the plan confirm. **OQ-2** No-op edit: 200 with the head (default) or 400. **OQ-3** Revision count cap (default 50). **BLOCKED_OPEN if** T-3a/T-3b are not landed.
