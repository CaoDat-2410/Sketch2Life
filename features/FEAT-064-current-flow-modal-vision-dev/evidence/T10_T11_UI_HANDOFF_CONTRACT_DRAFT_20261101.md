# T10/T11 — Hợp đồng bàn giao cho UI (bản đề xuất, chưa phải API live)

- Feature: FEAT-064 synthetic-only current-flow pilot; G5.
- Status: **XONG-CHƯA REVIEW cho tài liệu hợp đồng; UI DEFERRED-BY-OWNER; API/status wiring BLOCKED bởi T9 và các phụ thuộc G3/G4.**
- Phạm vi: đọc source và lập hợp đồng đề xuất; không sửa UI/backend, không chạy route test. Ví dụ dưới đây chỉ dùng ID giả.
- Nguồn chuẩn: `plan/PLAN.md` §5/AC20; `evidence/T0_CONTRACT_FREEZE_20261031.md` §§4–6; `evidence/T0_EXECUTION_MANIFEST_20261031.csv` O17/O18; `backend/src/sketch2life/contracts/schemas/assistance_requests.py`; `backend/src/sketch2life/interfaces/http/routers/assistance_requests.py`; T4/T5 reports and `CanvasRenderHandoffV1` source.

## Phân biệt bốn trạng thái hợp đồng

| Surface | Bằng chứng hiện có | Cách UI được phép coi là |
|---|---|---|
| BE1 accepted operations → T4/T5 internal export/render | Internal `CanvasSourceExportV1` / `CanvasRenderHandoffV1`; no public preview route | Backend artifact/handoff only; UI cannot call it yet |
| CMD-32 submit/CMD-33 cancel | Router under `/api/collaboration/v1`, `0.1-candidate`; module says fixture composition only, never production-mounted | Candidate reference only; not the FEAT-064 production API |
| Child-own status GET | T0 policy defined; candidate router has no GET status route | Required behavior documented, path/DTO not frozen |
| Teacher pending-analysis read | T0 policy defined; manifest O18 new panel/read route `NEW/TBD` | No route or wire DTO exists |

## T10 — Child flush, preview, request reference, actual status

### UI interaction contract

1. **Flush/ack:** wait until every locally queued stroke has a server acknowledgement and the accepted canvas revision is known. A timeout/reconnect does not mean accepted; keep pending operations visible and do not submit an AI request against an unknown revision.
2. **Preview source:** show only the server-rendered strokes-only export bound to accepted operations, source revision/hash, export spec and renderer. T4/T5 currently expose an internal handoff, not a public Child preview endpoint. No client PNG/checkpoint may stand in for this source.
3. **Submit:** only after a final request endpoint accepts the T4/T5 source binding and current synthetic eligibility. The current candidate CMD-32 schema takes `checkpoint_ref`, while T4 export rejects checkpoint/restore history and returns an operation-derived source. There is no lossless approved mapping between these shapes. **Do not submit CMD-32 as if it were the pilot request.**
4. **Lost reply:** persist the original idempotency key and any returned `assistance_id`; on timeout, reload/reconnect, or a denied poll, retain the request reference and show an indeterminate/waiting state. Never mint a new key or auto-resubmit.
5. **Paused/no turn:** T0 says a Child may read its own existing request while session is `active` or `paused`, if device key, admitted grant/membership, own Child/canvas scope and current eligibility still match. This status read does not require an active turn. A paused session admits no new request; `finished`, revoked grant, rotated key or lost eligibility returns a generic unavailable result. This is policy, not a currently implemented GET route.

### Existing candidate request shape — compatibility evidence only

Candidate route: `POST /api/collaboration/v1/assistance-requests` (fixture-only, not production-mounted). The candidate body fields are `canvas_id`, `checkpoint_ref` (`checkpoint_id`, `document_epoch`, `server_sequence`, SHA-256 `hash`), `target_scope` (`individual` + `participant_id` or `group` + `group_id`), optional `target_region_id`, `requested_level`, optional `child_intent` (up to 4,000 chars), `request_reason`, `context_revision`, and `client_request_id`. Unknown fields are forbidden. The router requires `Idempotency-Key`, JSON content type, and caps the entire body at 32 KiB.

Synthetic candidate example (schema example only; **not a valid T4/T5 pilot request**):

```http
POST /api/collaboration/v1/assistance-requests
Content-Type: application/json
Idempotency-Key: synthetic-key-0001
```

```json
{
  "canvas_id": "synthetic-canvas-001",
  "checkpoint_ref": {
    "checkpoint_id": "synthetic-checkpoint-001",
    "document_epoch": 1,
    "server_sequence": 3,
    "hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
  },
  "target_scope": {"kind": "individual", "participant_id": "synthetic-child-001"},
  "target_region_id": null,
  "requested_level": "visual_summary",
  "child_intent": "Please describe the shapes.",
  "request_reason": "child_request",
  "context_revision": 3,
  "client_request_id": "synthetic-request-001"
}
```

The candidate router returns HTTP 202 and a candidate `AssistanceReceipt` envelope. For a device principal, `data` is the minimal candidate `AssistanceRequestDeviceView` (`assistance_id`, `request_revision`, `status`=`pending|cancelled|unavailable`, nullable `job_id`, nullable `poll_after_ms`); `meta` carries `outcome`, `replayed`, `resource_revision`, and `projection`. `poll_after_ms` is only a polling hint, not a completion promise.

```json
{
  "contract_name": "AssistanceReceipt",
  "contract_version": "0.1-candidate",
  "correlation_id": "synthetic-correlation-001",
  "data": {
    "contract_name": "AssistanceRequestDeviceView",
    "contract_version": "0.1-candidate",
    "assistance_id": "synthetic-assistance-001",
    "request_revision": 1,
    "status": "pending",
    "job_id": null,
    "poll_after_ms": 1500
  },
  "meta": {
    "outcome": "created",
    "replayed": false,
    "resource_revision": 1,
    "projection": "device"
  }
}
```

Candidate cancel: `POST /api/collaboration/v1/assistance-requests/{assistance_id}/cancel`, JSON `{"reason":"child_cancelled"}`, with `Idempotency-Key` and `If-Match` carrying the expected request revision. It is not evidence that cancel prevents provider billing after possible-send; the future T6/T8 state machine must own that distinction.

### Known candidate errors and limits

| HTTP | Code | Evidence/meaning |
|---:|---|---|
| 400 | `MALFORMED_REQUEST` | malformed id/JSON or required idempotency key missing |
| 401 | `UNAUTHENTICATED` | candidate principal resolver has no principal |
| 413 | `PAYLOAD_TOO_LARGE` | body exceeds 32 KiB |
| 415 | `UNSUPPORTED_MEDIA_TYPE` | content type is not `application/json` |
| 422 | `FIELD_NOT_ALLOWED` | strict schema rejects an extra field |
| 422 | `FIELD_VALIDATION_FAILED` | candidate schema rejects a value/shape |
| service-defined | `AssistanceError.code` | exact inventory depends on service outcome; do not invent a closed list from the router |
| proposed status-own mapping | `REQUEST_UNAVAILABLE` | T0 generic denial for unknown/foreign/finished/revoked/rotated/ineligible scope; no route currently implements it |

**T10 blockers:** production submit/cancel path is not mounted; no status GET exists; source handoff and candidate `checkpoint_ref` are incompatible; T9/T6/T7 persistence/guard prerequisites remain blocked. The T4/T5 internal handoff fields include source/render/receipt references and hashes, but they are not a Child wire DTO.

## T11 — Teacher pending-analysis panel, read-only

### UI interaction contract

- Use a future, separate pending-analysis panel. Do not alter or reuse `apps/teacher-ui/src/pages/AiSuggestionReviewPage.tsx` approval/correction semantics.
- Require verified Teacher identity and current assignment to the organization/class/session plus exact request scope and current disclosure/eligibility. Display analysis as **pending/unconfirmed** only. No approve/correct/reject, no Sketch creation, and no result delivery to Child.
- Hide/unload data when authorization or current scope is lost; do not treat cached client rows as permission. T0 explicitly gives active/paused/no-turn policy for Child-own status. It does **not** settle Teacher pending-list visibility in paused/no-turn state; owner must decide. Until then do not infer that a Teacher read is allowed in those states.
- O18 says the new panel/read route is `NEW/TBD`. Do not call the existing candidate Teacher record the UI DTO: it includes age/consent references, child intent, target, budget, policy and provider-adjacent metadata that must not be exposed by default.

### Conceptual synthetic projection — not a wire schema

The following is only a display sketch to explain the intended meaning; route, fields, pagination and names are all unapproved:

```json
{
  "items": [
    {
      "request_ref": "synthetic-assistance-001",
      "display_state": "pending_unconfirmed"
    }
  ]
}
```

No URL, request parameters, response schema, cursor, or exact error mapping can be supplied truthfully while O18 remains `NEW/TBD`. T0's proposed privacy behavior is to return a generic unavailable response when authority/scope is lost, without disclosing whether a foreign request exists; exact status code and public error code require owner freeze.

**T11 blockers:** O18 new panel/read path and wire DTO are not frozen; T9’s request/status surface and T6/T7/T8 durable lifecycle are blocked. L6 remains DEFERRED-BY-OWNER. No Teacher route or UI was added or tested.

## UI handoff questions before implementation

1. What approved command binds `CanvasRenderHandoffV1` source/render/admission to assistance request creation without checkpoint fabrication?
2. What production routes and DTO version cover Child submit, cancel, own-status polling, and Teacher pending read?
3. Which error/status fields are safe and stable for Child/Teacher, including late/UNKNOWN, denied poll, and paused states?
4. Is Teacher pending-list read permitted while session is paused or has no active turn, and what current assignment/disclosure fence applies?
5. Which minimal source preview fields may Child/Teacher see, and what payload/preview fetch limit is approved?

## Verification

- UI/npm/visual AC20: DEFERRED-BY-OWNER / NOT RUN.
- L5 contract tests: NOT RUN because the production routes and source-binding DTO are not mounted/frozen. Candidate router contract tests do not satisfy this check.
- No backend, database, migration, provider, or network action was part of G5.
- `python tools/validate_harness.py`: `HARNESS_VALID`.
- `python tools/validate_repository_security.py`: `REPOSITORY_SECURITY_VALID` (`6,032` publishable files scanned).
- `python tools/validate_architecture.py`: `ARCHITECTURE_VALID`.
- `git diff --check`: clean. New G5 files: UTF-8, LF, no BOM, no trailing whitespace (`3/3`).
