# M2-S2 Shared OpenAPI Mapper Task Approval Draft 1 — Cold Review R4

## Review identity

- Review thread: `01a1e59d-10f4-7f32-86a7-20b2ab9e30a8`
- Review turn: `01a1e59d-168a-72f3-99b7-a8fe0686e4f6`
- Mutation request ID: `m2-s2-mapper-draft1-comparator-guard-review-20261117`
- Review mode: fresh-context, read-only, network disabled
- Result returned: 2026-11-17
- Reviewed Draft 1: 240,011 bytes / SHA-256 `20A3D12BCABF12003FCB5D46CB70064044DE991A38A18573E7D0357B0AC4E2B7`
- Verdict: **NOT READY — P1=0, P2=1, P3=2**

## Pin and scope observations

The reviewer confirmed the Draft 1 pin, all supplied context-file pins, the 13 present source/test/dependency entries in §1, and the five embedded payload hashes. The future mapping-test path remains absent as declared. The comparator payload is 50,890 bytes / SHA-256 `84F36CFD619708E0952B2EEB15A9C6EF24D798C820EEE0FA768B770064125687`.

The reviewer did not independently query Git metadata. The coordinating session separately rechecked branch `feature/feat063-m2-s2`, HEAD `5de30674bc826591ad4b3cc00fca53c7597ead51`, 88 status paths, and 0 staged paths while the pin remained unchanged.

## Findings

### P2 — Active comparator bypasses the schema-root guard

The payload defines `_load_openapi_schema` and an initial `main` that uses it, but a later second `main` shadows the first. The module entry point calls the later definition, whose direct `json.loads` calls bypass the required input-root/structure validation. A missing, blank, or wrongly typed `openapi` value can therefore evade the comparator guard. Section 2 acceptance is not met.

### P3 — Exporter pre-serialization check misses case-variant collisions

The exporter checks exact `openapi`, `info`, and `paths` values but does not enumerate key case variants. An object containing both `openapi` and `OpenAPI` could pass that guard. The PowerShell output gate rejects the collision and stops, so the reviewer assessed this as a pre-serialization/manifest-clarity gap.

### P3 — Child-launch exception can leave incomplete artifacts

If `subprocess.run` raises before returning, expected-artifact enumeration and invocation-log creation may not occur before the failure manifest is finalized. The Draft already discloses this retained limitation in §5; no retry rule is weakened.

## Other reviewed points

The §4 `ComparisonRoot` guard verifies terminating creation, directory type, canonical path, and reparse status before writing its hash manifest. Draft 10 remains historically **ACCEPT WITH CORRECTIONS**, with its P2 still present.

The review confirmed Option A exact `(method.lower(), path)` lookup; the E/E/N/R four-path allowlist; `operationId` as a unique unchanged invariant rather than a lookup key; and the OPEN, fail-closed request-ID inventory. Rev68 remains the canonical unsigned SRS; the external SRS remains comparison-only and the §21.2/D-208 conflict remains unresolved/out of scope. The S2 implementation report remains PARTIAL / NOT COMPLETE with historical test/type/lint results retained; mapper success alone does not close S2 or authorize S3.

## Gate outcome

The single authorized cold review is consumed. Because one P2 remains, stop at review: no additional Draft 1 correction, review, formal approval, baseline export, test, or implementation is authorized by this result. No reviewer file edits or execution occurred.