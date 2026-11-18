# FEAT-066 — owner decision proposals checked against the adopted SRS (working note, 2026-11-18)

- **Status:** proposals only. Nothing here is decided until the owner answers each item. Answered items are then recorded as decision rows, append only, in FEAT-066 `DECISIONS.md`, on the owner's instruction.
- **SRS:** the owner-supplied copy, 701,157 bytes, SHA-256 `B9B1F42D0BB118C19C81607D3913B7E4F1D8B6F673F0C3FBB6402888FEB675F5` (D-209, unsigned). It is byte-identical to the canonical repository SRS. Line numbers refer to it.
- **Sources of the questions:**
  - `PLAN_API_CONVENTIONS_CONTRACT_DRAFT1_20261118.md` (C-D1 to C-D10);
  - `tmp/feat066-phase-a/mobile-brief/PARENT_MOBILE_RECONCILIATION_BRIEF_20261118.md` (D-A to D-E);
  - the register: O-PRIV and O-ACCREV, which the SRS answers directly.
- **Basis labels:**
  - **SRS** — the SRS states the answer.
  - **SRS-compatible** — the SRS sets the rule but not the detail; the proposal stays inside the rule.
  - **SRS-silent** — a process or engineering choice the SRS does not cover.

| ID | Question | SRS text (line) | Proposal | Basis |
|---|---|---|---|---|
| C-D1 | Error envelope | §9.8 (853–858): fields `code`, `message`, `correlation_id`, `retryable`, `retry_after_seconds`, `field_errors`. §21.1 (1635): "có thể phát hành trường tùy chọn bổ sung trong version hiện hành". §21.4 (1699): `STALE_REVISION` "cùng version hiện tại" | **A**: use the M2 Parent shape for every route (top-level §9.8 fields). `current_version` is returned with `STALE_REVISION` (§21.4). `request_id` is kept as an optional extra equal to `correlation_id` (§21.1 allows optional extras). This also answers M2 ledger O4 for the two extra fields | SRS-compatible |
| C-D2 | Correlation header | §21.1 (1636): "Backend trả correlation ID cho request trong mọi response" — no header name | **A**: `X-Request-ID`, already the global middleware; body `correlation_id` equals it | SRS-silent on the name |
| C-D3 | Validation status | §9.8 table (862): 400 `INVALID_REQUEST`; 422 lists only semantic codes (871) | **A**: schema and validation errors return 400 `INVALID_REQUEST` with `field_errors`; 422 only for the §9.8 semantic codes | SRS |
| C-D4 | 404/403 | §9.8 (864–865) and §21.6 (1720–1721): 404 `RESOURCE_NOT_FOUND` "cùng một shape cho ID không tồn tại và resource ngoài scope"; 403 only in scope | Apply the rule. **Timing:** CONV-1 changes the shared scope guards (BE1 common assignment check, Lesson Library scope check) once. Any route-specific check is fixed in its capability slice | SRS (rule); timing is the owner's |
| C-D5 | Idempotency key format | §21.1 (1636), §21.4 (1697): a key is required; no format given | **A**: header `Idempotency-Key`, exactly one value of 1–128 visible ASCII characters (33–126). This is the rule the M2 Parent routes already enforce (`routers/parent_profiles.py`, function `_idempotency_key`) | SRS-compatible |
| C-D6 | Key retention | §21.4 (1697): "Gửi lại cùng key/payload trả kết quả ban đầu" — no expiry | **A**: durable receipts with no expiry, as the existing BE1, Lesson Library and Parent receipt tables. Only successful results are stored | SRS-compatible |
| C-D7 | Revision transport | §21.4 (1699): send "expected revision/hash"; stale → 409 `STALE_REVISION` with the current version; no transport given | **A**: keep the body `expected_revision` (M2 Parent) and strong `If-Match`/`ETag` (Lesson Library). Every stale case returns **409 `STALE_REVISION`** with `current_version` or the current ETag. A precondition failure must not return 412, because the SRS names 409 | SRS-compatible |
| C-D8 | `limit` above 100 | §21.1 (1640): "page size mặc định 25 và tối đa 100" | **A**: 400 `INVALID_REQUEST` with a field error (explicit, no silent change) | SRS-compatible |
| C-D9 | Path prefix | §21.1 (1635): "Base path có version, bắt đầu từ /v1". §9.6 (790): "chưa phải OpenAPI cuối". §9.6 (818): exact path "phải được đối chiếu … với OpenAPI hiện hành". 1685: "Hình dạng route là contract sẽ chốt trong OpenAPI" | **A as an interim reconciliation**: keep `/api/<namespace>/v1/...`, record it as the §9.6 OpenAPI reconciliation of the §21.1 base path, and add an SRS reconciliation note. The M2 Parent and StoryRun `/v1/...` routes stay. Option C (move every route) is not proposed now because of its cost. **Not a literal match of §21.1**, so the owner approves it knowingly | SRS-compatible through §9.6, not literal |
| C-D10 = D-E | Wire the 8 Parent operations before CONV-1 | SRS-silent. Evidence: the M2 Parent routes already use the §9.8 superset, `Idempotency-Key`, cursor pages and `/v1` | **Yes**, provided C-D1 = A and C-D2 = A (then the Parent parser does not change again) | SRS-silent |
| O-PRIV | What the School Manager may read of class profiles (register row A09) | §31.3 permission table (2586), School Manager column: "Không đọc profile contents mặc định" | The School Manager gets **no profile contents** (no name, no age) by default. Roster views show counts and opaque refs only, until the owner approves a separate process. The Teacher keeps its granted fields. BE change in C-M; FE `RosterConsentPage` follows | SRS |
| O-ACCREV | Is an account revision precondition (If-Match) required for Platform Admin account updates (A05)? | §21.4 (1699) names only "hồ sơ, lesson plan, story và script" | **Not required.** Accounts keep returning their revision; there is no mandatory precondition. The idempotency key is still required (C-D5) | SRS (by its explicit list) |
| D-A | Staged FEAT-081 Plan 19 work in the mobile worktree | SRS-silent (Git process). Note: the staged routes `/api/parent/v1/child-profiles…` contradict SRS §21.2, which names `/v1/parent/profiles` (lines 795, 1648) | **(c)** Preserve it non-destructively (patch plus both conflict sides under `tmp/`, or a backup branch); start C-P clean from the M2 projection; a FEAT-081 record marks Plan 19 as superseded | SRS-silent |
| D-B | Who resolves `parentSrsBehavior.test.ts` (unmerged) | SRS-silent | Its author, inside the D-A preserve step; nobody auto-resolves | SRS-silent |
| D-C | How the mobile branch catches up with `dev` | SRS-silent | Merge `origin/dev` into the branch (no force-push). HieuNewBie joins for `backend/alembic`. Needs O-0 (M2 on the base) first | SRS-silent |
| D-D | Which feature carries C-P | SRS-silent | A new FEAT-081 addendum, referencing the FEAT-066 register rows | SRS-silent |

## Owner answers (2026-11-18, in chat, one question per item)

| ID | Answer (owner's words) | Status |
|---|---|---|
| C-D1 | "Duyệt A" | approved: M2 Parent superset envelope everywhere; also settles M2 ledger O4 |
| C-D2 | "Duyệt A" | approved: `X-Request-ID` |
| C-D3 | "Duyệt A" | approved: 400 `INVALID_REQUEST` for validation |
| C-D4 | "Duyệt" | approved: SRS 404/403 rule; shared guards in CONV-1, the rest per slice |
| C-D5 | "Duyệt A" | approved: `Idempotency-Key`, 1–128 visible ASCII |
| C-D6 | "Duyệt A" | approved: durable receipts, no expiry |
| C-D7 | "Duyệt A" | approved: transport per family, 409 `STALE_REVISION` everywhere |
| C-D8 | "Duyệt A" | approved: `limit` > 100 → 400 |
| C-D9 | "A: giữ tạm" | approved: keep `/api/<namespace>/v1` as the interim §9.6 reconciliation; SRS reconciliation note needed |
| C-D10 = D-E | "Cho Parent đi trước" | approved: C-P may precede CONV-1 |
| O-PRIV | "Duyệt theo SRS" | approved: no profile contents for the School Manager by default |
| O-ACCREV | "Duyệt" | approved: no mandatory account revision precondition |
| D-A | "(c) Lưu rồi làm sạch" | approved: preserve, then start C-P clean |
| D-B | "Tác giả tự xử lý" | approved |
| D-C | after asking "là merge dev vào nhánh ui mobile hiện tại hay sao ?" and the clarification: "Đúng, merge vào đó" | approved: merge `origin/dev` into `feature/fe-mobile-remediation` (no force-push), after D-A/D-B and with M2 on `dev` (O-0); HieuNewBie joins for `backend/alembic` |
| D-D | "FEAT-081 addendum" | approved |

These answers are not yet decision rows. They are recorded in FEAT-066 `DECISIONS.md` (append only) when the owner says so.

**Not proposed here, because the SRS does not decide them and they need the owner's or a teammate's input:**
- O-0 (merge order);
- O-SEQ;
- O-PAY;
- O-PCONSENT: the SRS makes the Parent the consent actor (§31.3), but no route or contract exists;
- O-ASSIST;
- O-CONTENTADMIN;
- O-UPLOAD path mapping (folded into C-D9);
- O-PROJ;
- O-L3SCOPE;
- O-BRU;
- O-TOKEN;
- the Billing residuals and names;
- O-SEED-PAY, O-SEED-CLOCK.
