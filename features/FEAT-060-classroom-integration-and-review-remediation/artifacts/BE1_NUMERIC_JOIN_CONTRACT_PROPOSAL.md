# BE1 six-digit room code proposal

**Status: IMPLEMENTED LOCALLY under FEAT-060 Plan Rev4; not yet BE1-owner reviewed or PostgreSQL-verified.** This proposal is retained as design history. The current routes and client connections are documented in `evidence/notes/API_INTEGRATION_CATALOGUE_20261024.md`; migration is `backend/alembic/versions/20261024_0005_classroom_srs_contracts.py`. The owner clarified that the six-digit value is a shared room-entry code like Quizizz/Kahoot, not a one-time password. Multiple children use the same code to request entry into the same live class. QR/deep-link is the second way into that room. Owner also confirmed that both entry methods close to new join requests after class start.

## Current gap

At initial drafting, Child numeric-code submit was local-only and BE1 had no shared room-code route. Rev4 now calls `POST /api/be1/v1/room-code/join`; Teacher issues/rotates a code through `POST /api/be1/v1/organizations/{organization_id}/sessions/{session_id}/room-code/rotate`. UI and database verification limits remain as recorded in the current API catalogue.

## Proposed shared room flow

1. Teacher creates the session and opens the lobby.
2. Backend generates one random six-digit room code for that session. Teacher displays it alongside the QR. It is **not one-use**: every child entering that class uses the same code.
3. Each Child scans the QR or types the room code. Either method creates a pending device request for the same session.
4. Teacher selects the matching managed child profile and admits the device. Existing purpose-consent checks remain in force.
5. **Owner-confirmed:** the six-digit shared room code stays active throughout the Lobby, and Teacher may rotate it before start. Rotation invalidates the old code. On successful start, the code stops accepting new requests. Already admitted devices keep their grants unless revoked.
6. QR/deep-link late admission follows the same owner-confirmed close-on-start rule: after start, neither link nor code creates a new join request. Requests that are still pending at the successful start boundary are atomically revoked; Child refresh returns `revoked`. Already admitted devices retain grants. BE1 must review the transactional start/admit race and exact response receipt.
7. After admission, existing device-key refresh, group assignment, class start, turn, and canvas APIs apply.

The room code identifies a room, not a child. It does not authenticate a child profile or reveal the roster, artwork, canvas, or session detail. The code can be shared with the whole class and multiple children can use it. A Teacher admission step is retained because the SRS requires profile mapping and consent validation.

## Proposed child request

```http
POST /api/be1/v1/classroom-join-requests
Content-Type: application/json
```

```json
{
  "classroom_code": "481205",
  "device_key": "<random device key>"
}
```

Successful result reveals no profile, class, or session detail:

```json
{
  "contract": "Be1DeviceJoinV2",
  "grant_id": "...",
  "state": "pending"
}
```

The Child then uses existing `POST .../device-grants/{grant}/refresh` polling. Teacher uses existing pending-request list, managed-profile selection, `/admit`, consent validation, group assignment and explicit `/start`. QR and room-code entry converge at the same pending-grant/Teacher-admission step.

## Room-code behavior and protections

- Generate six digits using a cryptographically secure RNG; do not derive from a session ID or timestamp.
- Code is unique among concurrently joinable sessions and active for the open Lobby, not an OTP-style countdown. Teacher can rotate it before start. Backend closes numeric-code and QR/deep-link admission immediately after successful start.
- Store only a keyed hash/HMAC of the room code. The HMAC key stays in server-side secret management; use constant-time verification. Never put raw room codes in general logs.
- Invalid, closed, rotated, and unknown codes return the same generic failure, e.g. `404 JOIN_UNAVAILABLE`; do not reveal whether a room/session exists.
- **Owner-approved initial limit:** persistently throttle 10 invalid attempts per source IP per 15 minutes across backend replicas/restarts. Khoa/BE1 must approve trusted-proxy/source-IP attribution and storage/enforcement details; do not use process-local counters. Any proposed change to the approved threshold returns to the project owner.
- Repeated valid entry from the same active device key should not create duplicate pending grants. Room code never bypasses Teacher profile selection, admission, or consent checks.

## BE1 changes needed

The current high-entropy `join_code_sha256` field is not a six-digit room-code contract. BE1 must define storage for the room-code hash, active/rotated state, room lifecycle, rate-limit/audit references, and uniqueness. A dedicated room-code row is one possible design; no migration is proposed here because SR-03 still has unresolved migration heads/order.

Teacher also needs an authenticated way to display and rotate the code. Options to review: return it when the lobby first opens, or add `POST .../sessions/{session}/room-code/rotate` that returns the active digits to the authorized Teacher. Do not include raw room code in a general session-read response. QR should open the same room and lead to the same pending-request/admission flow.

## Verification needed before enabling six-digit entry

1. Multiple devices using one code create separate pending requests for the same session.
2. Duplicate retries by one device do not create duplicate pending grants.
3. Wrong, closed, rotated and unknown codes look the same to Child UI.
4. At successful `start`, both the same six-digit code and QR/deep-link are rejected for new requests; all still-pending requests are atomically revoked and refresh as `revoked`; already admitted device grants continue to refresh/reconnect.
5. Automated guesses and floods are rate-limited across backend instances.
6. Collision test proves only one joinable room owns a code.
7. Pending requests reveal no class, child, roster, session ID, or title.
8. Teacher must select a valid managed profile; effective consent is checked before admission/start.
9. Revocation prevents refresh/reconnect/write; logs/evidence contain no plaintext room code or device key.
10. Synthetic end-to-end request reaches PostgreSQL-backed grant state and then follows the same pending/admission flow as QR.

## Review gate

Khoa/BE1 must review endpoint/version, storage/migration path, confirmed close-on-start and pending-revocation rules, room-code rotation, uniqueness, the owner-approved persistent 10/source-IP/15-minute threshold, proxy/IP trust, cross-replica limiter, key lifecycle, and generic error semantics. Keep six-digit entry marked “not connected” until the reviewed route and tests pass.
