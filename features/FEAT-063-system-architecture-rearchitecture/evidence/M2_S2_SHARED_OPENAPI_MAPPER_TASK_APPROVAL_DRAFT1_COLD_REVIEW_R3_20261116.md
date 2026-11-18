# M2-S2 Shared OpenAPI Mapper Task Approval Draft 1 — Cold Review R3

## Review identity

- Target: `features/FEAT-063-system-architecture-rearchitecture/plan/M2_S2_SHARED_OPENAPI_MAPPER_TASK_APPROVAL_DRAFT1_20261116.md`
- Reviewed pin: 230,361 bytes / SHA-256 `3A81C0FB8E039BB065A8A40129E61A33B3D223AD36945CCDABF5B90173D4FAFE`
- Owner-directed SRS comparison input: `D:\Zalo Received\SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS (2).md`, 701,157 bytes / SHA-256 `B9B1F42D0BB118C19C81607D3913B7E4F1D8B6F673F0C3FBB6402888FEB675F5`.
- M2 canonical working SRS Rev68: 639,948 bytes / SHA-256 `69C83FE49CD4689D5D2540656D3319721838CF7343BAD00E24CDE558B8F5E944`; `docs/context/SRS_AUTHORITY.md`: 4,313 bytes / SHA-256 `D6153D38000C95E43A4091C5DF2E856FAD872A33177E3A8542E30EF2BEDCAB60`.
- Prior Draft 1 R2 evidence: 4,318 bytes / SHA-256 `4E2C12BE141707B083E4632467BA4F3189076D2B8047A6345EE0D674E5A3DCB2`.
- Cold-review thread: `01a1e54e-fc9f-7600-9ec8-97b76963983d`.
- Completed review turn: `01a1e54f-028d-72a3-892a-f4439d79fdfb`.
- Worktree: `D:\GitHub\Sketch2Life\.worktrees\m2-s2`; branch `feature/feat063-m2-s2`; HEAD `5de30674bc826591ad4b3cc00fca53c7597ead51`.
- Review environment: fresh thread, no parent/fork; thread bridge verified `type=readOnly` and `networkAccess=false`.
- Verdict: **NOT READY** — P1: 0, P2: 1, P3: 1.

## Findings

### P2 — Exporter does not reject an absent runtime schema

The `openapi-export.py` payload reads `application.state.runtime_openapi_schema` and writes the value without first requiring a schema object (Draft 1 §7 payload, around line 1810). If the value is `None`, JSON serialization can write `null` and the exporter can still succeed. The §4 pre-export card checks that outputs exist and are hashed, but does not validate the JSON shape (around line 184). The new stop condition therefore does not yet guarantee that an absent runtime schema fails the export. Add an explicit schema-shape check before export success in a separately authorized planning correction. This is a guard gap in the proposal, not evidence that the current M2 worktree fails at runtime.

### P3 — Process-launch artifact gap remains disclosed

If `subprocess.run` raises before returning, expected-artifact states and the invocation log may be absent. Draft 1 §5 records this limitation and directs retaining available evidence and stopping without retry. This P3 remains open and is accurately disclosed.

## Coverage and disposition

- The target and supplied comparison pins matched. The reviewer verified the five embedded payload byte counts and SHA-256 values against the §7 roster and prior R2 evidence; no payload was executed.
- Owner-copy §§9.6 and 9.8 match the unsigned Rev68 text. The mapper remains a narrow mechanism and does not freeze the target API inventory or claim product conformance.
- The dated §§32.10 and 32.14 HTTP 500 observations are treated as an OpenAPI risk, not as proof of a current M2 runtime failure. The four-path E/E/N/R allowlist preserves components and does not authorize adding the missing component. The stop/report/no-retry language is present, subject to the P2 gap above.
- The owner-copy §21.2 DELETE wording conflict with Rev68/D-208 remains unresolved and outside mapper scope. No SRS, authority, decision, approval, or lifecycle changes are proposed.
- Option A exact `(method.lower(), path)` lookup, stable unique `operationId` invariant, Choice A E/E/N/R paths, OPEN fail-closed request-ID inventory, command ceilings, and other stop conditions are preserved.
- This is planning review only. It does not approve a baseline, implementation, or launch. S2 remains PARTIAL / NOT COMPLETE.

The reviewer used read-only inspection and hashing only. No files were changed by the reviewer, and no tests, validators, lint/typecheck, diff-check, OpenAPI generation, application/runtime, database, installation, network, provider, or Modal commands were run. The coordinator made no further Draft 1 correction after this review.
