# FEAT-072 decisions

Append-only. The teammate's commit a77bb2a8 carried no decision record; this file starts at integration.

## D-072-INT-01 Backend taken without the web UI (2026-11-21)

**Decision:** the backend of a77bb2a8 (`backend/**`, this feature folder, `compose.yaml`, `.env.example`) is brought onto the integration line as one commit. `apps/web/**` stays on `codex/fe-ui-web-remediation`, where the Admin UI is being redesigned.

## D-072-INT-02 Accounts routes follow the goal v3 C5 contract (2026-11-21)

**Decision:** `GET/POST/PATCH /api/platform-admin/v1/accounts` keep the FEAT-066 C5 behavior: opaque keyset cursor with `next_cursor`, `Idempotency-Key` read by `parse_idempotency_key` (required, 1-128 printable characters, 400 `INVALID_REQUEST` on a bad key), receipts in `be1_command_receipts`, no `If-Match` on PATCH (no SRS rule names an expected revision for account role or state; C5 CA-4). The teammate's additive account behavior is kept: `pending_verification` state, password-setup email outbox row, `pending_activation` on School Manager assignments, `content_admin` grant revocation on role or state loss, `SELF_DISABLE_DENIED`, and the `AdminRoute` no-store and ETag headers.

**Consequence:** the teammate's own account tests that assumed `If-Match` (428) or the 422 key error were adjusted to this contract; see `evidence/notes/INTEGRATION_BACKEND_20261121.md`.
