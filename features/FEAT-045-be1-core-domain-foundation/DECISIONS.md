# Feature decisions

## D-01 — Bound the request to BE1-01

- Date: 2026-10-14 (Asia/Saigon).
- Status: adopted for this feature scope.
- Basis: the current allocation in ADR-0015 identifies P2 as BE1 and lists BE1-01 as the independent core foundation starting task. The user asked for BE1 core work.
- Decision: implement BE1-01 only; do not treat the request as approval for every BE1 card or the separate integration workstream.

## D-02 — Preserve requirement authority labels

- Date: 2026-10-14 (Asia/Saigon).
- Status: adopted.
- Decision: owner-confirmed requirements and explicit BE1-01 acceptance cases may be validated. Other SRS `PROPOSED` and `TBD` details remain candidate metadata and are not silently adopted as product policy.

## D-03 — No persistence or live-service binding

- Date: 2026-10-14 (Asia/Saigon).
- Status: adopted for BE1-01.
- Decision: use pure domain/application boundaries and synthetic in-memory fixture adapters. Durable adapters, migrations, HTTP wiring, and cross-workstream integration remain later tasks with their own feature approval.

## D-04 — Preserve source status on fixture contracts

- Date: 2026-10-14 (Asia/Saigon).
- Status: adopted for this feature.
- Decision: mark the handoff schemas/manifest `PROPOSED_UNADOPTED` and retain source labels such as `CONFIRMED`, `OWNER_CONFIRMED`, and `TBD` on each fixture. A passing fixture does not adopt a proposed schema or resolve TBD policy.

## D-05 — Bind requested resource scope to loaded state

- Date: 2026-10-14 (Asia/Saigon).
- Status: adopted for this feature.
- Decision: canvas commands must match the loaded active turn and membership scope; admission must match the target class. Mismatches return `SCOPE_DENIED` before state mutation.
