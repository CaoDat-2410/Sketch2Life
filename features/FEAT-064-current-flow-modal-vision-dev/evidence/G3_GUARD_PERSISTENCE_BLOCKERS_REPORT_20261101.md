# G3 closeout — Guard, persistence, fence, and invocation ledger

- **Status:** XONG-CHƯA REVIEW as a blocker closeout; implementation for T6/T7a/T7b/T7c is BLOCKED before code.
- **Scope:** G3 only. No tests, database operations, migrations, provider calls, Modal/GPU calls, or network calls were run for these four blocked task dispositions.
- **HEAD:** `1e93bc3f3ac645cf4baecbbc09c73afe48719c92`.

## Plans and append-only approvals

| Task | Plan | SHA-256 | Approval status |
|---|---|---|---|
| T6 | `plan/T6_INVOCATION_GUARD_IMPLEMENTATION_PLAN_20261101.md` | `C2186576249BA008D30ADEE47DCD132F8C8FCD3588F5E7FC1F87EE61AC7E2A71` | Blocker inventory/report only |
| T7a | `plan/T7A_DURABLE_PILOT_STATE_PLAN_20261101.md` | `6BB50353C244759CB054FF044A9298BC8252B630DA09C2D2A53C93DBFF3B6E6C` | Blocker inventory/report only |
| T7b | `plan/T7B_OWNER_FENCE_UOW_PLAN_20261101.md` | `D08D62A346D3397A0D7F0ED2FB0012E4C234B9D27505833B9A9410E1B4A020F1` | Blocker inventory/report only |
| T7c | `plan/T7C_RUN_LEDGER_WITNESS_PLAN_20261101.md` | `C3806A9DE0DB1502E8D971DB76A7CED1D551F503619FD1546313B9CBEF0C50BE` | Blocker inventory/report only |

## Task × layer

| Task | L1 | L2 | L3 | L4 | L5 | L6 | L7 |
|---|---|---|---|---|---|---|---|
| T6 | BLOCKED | BLOCKED | NOT RUN | BLOCKED | NOT RUN | DEFERRED-BY-OWNER | NOT RUN |
| T7a | NOT RUN | BLOCKED | BLOCKED | BLOCKED | NOT RUN | DEFERRED-BY-OWNER | BLOCKED |
| T7b | BLOCKED | BLOCKED | BLOCKED | BLOCKED | NOT RUN | DEFERRED-BY-OWNER | BLOCKED |
| T7c | BLOCKED | BLOCKED | BLOCKED | BLOCKED | NOT RUN | DEFERRED-BY-OWNER | BLOCKED |

## Blockers and owner questions

1. **T6:** T0 `§6` explicitly leaves total HTTP wall deadline, completion margin, and late-response handling unresolved and requires them frozen before T6/T13. The existing 12-second client bound and `urlopen` timeout do not prove an end-to-end transport deadline. The invocation handshake that carries a stable claim to the exact possible-send boundary is also not frozen. Questions: set the total deadline/completion margin/cold-start behavior; define late complete response disposition; freeze the invocation identity and guard handshake.
2. **T7a:** Manifest O16 leaves the single schema/migration owner, exact repository/schema/revision/parent, selected durable method subset, and writer unresolved. No migration or schema was invented. Questions: name owner, migration path/schema/revision, exact durable method subset and writer.
3. **T7b:** Owner instruction in the goal prompt §E.3 intentionally overrides waiting for signatures; missing signatures are not treated as the blocker and remain unsigned. Atomic acceptance still depends on T7a and a concrete BE1-owned source/eligibility fence transaction hook, which is absent from the approved B5.1 new-path boundary. Questions: identify BE1 atomic hook and exact approved UoW/fence contract.
4. **T7c:** Depends on T6/T7a/T7b. O16 paths/schema/writer remain open; selected witness directory/filesystem and actual Windows durability semantics have not been verified. Questions: freeze manifest issuer and IDs, paths/schema/writer, witness location/filesystem/primitive, and throwaway T12 fault-test identities.

## Tests and checks

- Task-level red/green tests: **NOT RUN** for all four tasks because each was blocked before implementation; no red count is fabricated.
- PostgreSQL, Alembic, witness/fault injection, Modal/GPU/provider/network: **NOT RUN**.
- The G2 snapshot `snapshots/G2_20261101T154756/` was revalidated before G3; all 14 content hashes matched.
- G3 validators: `HARNESS_VALID`; `REPOSITORY_SECURITY_VALID` (6,025 publishable files); `ARCHITECTURE_VALID`; `git diff --check` clean; new-file UTF-8/LF/no-BOM/trailing-whitespace scan clean. G3 snapshot: `.claude/handoff/snapshots/G3_20261101T160006/` (hash-verified after capture).

No co-owner signature, OwnerFenceV1 signature, or independent review is claimed.
