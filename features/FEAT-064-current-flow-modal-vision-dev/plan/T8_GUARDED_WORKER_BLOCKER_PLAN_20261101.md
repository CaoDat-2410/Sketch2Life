# T8 — guarded worker blocker disposition

- Status: **BLOCKED before implementation**; this plan covers only the blocker record.
- Feature: FEAT-064 synthetic-only current-flow pilot; G4.
- Owner authorization: direct instruction to execute G2–G6 in TREO KHÔNG COMMIT mode, under `.claude/handoff/CODEX_GOAL_PILOT_T2C_TO_T12_20261101.md` §E.

## Intended behavior

Worker flow: guarded observation → atomic acceptance → analysis-only reconciliation; one attempt maximum; UNKNOWN/HOLD creates no new attempt; `NOT_SENT_*` is not displayed as a provider failure and does not expose retry; zero Sketch side effects. Provider remains fake/mock in tests.

## Blocking dependencies

- **T6 BLOCKED:** plan `plan/T6_INVOCATION_GUARD_IMPLEMENTATION_PLAN_20261101.md`, SHA-256 `C2186576249BA008D30ADEE47DCD132F8C8FCD3588F5E7FC1F87EE61AC7E2A71`. Total HTTP wall deadline, completion margin, cold-start policy, late complete-response disposition, and transport-bound invocation handshake are unresolved.
- **T7a BLOCKED:** plan `plan/T7A_DURABLE_PILOT_STATE_PLAN_20261101.md`, SHA-256 `6BB50353C244759CB054FF044A9298BC8252B630DA09C2D2A53C93DBFF3B6E6C`. O16 has no single schema/migration owner, selected parent/revision/schema, durable method subset, or writer.
- **T7b BLOCKED:** plan `plan/T7B_OWNER_FENCE_UOW_PLAN_20261101.md`, SHA-256 `D08D62A346D3397A0D7F0ED2FB0012E4C234B9D27505833B9A9410E1B4A020F1`. No established BE1-owned atomic source/eligibility fence boundary. Missing signatures remain unsigned, but are not treated as a blocker per owner instruction §E.3.
- The T2C BE1→BE2 scoped owner-fact adapter is also BLOCKED under `plan/T2C_BE1_CANVAS_OWNER_FACT_ADAPTER_PLAN_20261101.md`; a worker cannot be wired to a source/roster/turn adapter that is not yet contractually scoped.

## Layer disposition

| Layer | Status |
|---|---|
| L1 contracts/domain | BLOCKED at the T6 invocation handshake and the approved digest-bearing acceptance boundary. |
| L2 application | BLOCKED by T6/T7b; no worker orchestration implementation. |
| L3 persistence | BLOCKED by T7a. |
| L4 adapter | BLOCKED by T2C/T6; no provider transport or bypass. |
| L5 HTTP | NOT RUN; no route scope. |
| L6 UI | DEFERRED-BY-OWNER. |
| L7 integration | BLOCKED by T6/T7a/T7b and T2C. |

## Test, allowlist, and owner questions

No implementation test was added or run; no safe worker boundary exists to test without inventing the guard contract. Status is `NOT RUN`, not zero failures. This disposition permits only this plan, the G4 blocker report, a separate append-only T8 blocker approval entry, and the T8 ledger entry. It permits no source/test/schema/route/DB/provider changes.

Owner must resolve T6 deadline/late-response/transport identity; T7a O16 schema/migration/writer; T7b the BE1-owned fence publication and UoW boundary; and the T2C scoped source. T8 needs a new implementation plan/approval after those decisions.

