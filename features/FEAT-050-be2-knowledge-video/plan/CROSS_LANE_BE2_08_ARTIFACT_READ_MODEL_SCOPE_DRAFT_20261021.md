# BE2-08 read-only finalized-artifact model for BE2-09 — supplemental scope draft

- Status: DRAFT / AWAITING_INDEPENDENT_REVIEW_AND_OWNER_APPROVAL
- Prepared: 2026-10-21 (Asia/Saigon)
- Owner: FEAT-050 / BE2-08
- Consumer: FEAT-051 / BE2-09
- Supplements: CROSS_LANE_BE2_08_SCOPE_DRAFT_20261021.md, SHA256 6A195B6F3C9901621D268CF26B34AA217EECAFE66FA5922BD066149E6A9BC0B0
- Related FEAT-057 erratum: features/FEAT-057-be2-01-14-offline-integration/plan/CROSS_LANE_X01_X05_PLAN_ERRATUM_20261021.md, SHA256 7530294B18B30616EB9A968ABF0AD227C661294500CD0789A7EC514D54E5FE39
- Related foundation UoW scope: features/FEAT-044-be2-ai-job-foundation/plan/CROSS_LANE_FOUNDATION_UOW_SCOPE_REV2_DRAFT_20261021.md, SHA256 39B0FD5958D2C298460F7605A7F73E8BDC7BC9D269B6399822FD2A2EAAC4DDC4

This supplement records the owner's direction that BE2-08 publish a public, read-only finalized-artifact model for BE2-09. It does not choose final contract fields or grant implementation approval. The existing BE2-08 scope and official approval remain unchanged. No source, test, schema, migration, card status, acceptance or runtime gate changes are authorized.

## Proposed boundary

- BE2-08 owns the read model and its access checks over BE2-08-owned finalized output.
- BE2-09 consumes only the public read contract. It must not read or write BE2-08 tables directly.
- The read model returns an immutable identity for a committed terminal artifact; it does not grant current-use eligibility, playback access, worker authorization, or permission to bypass the X05d source fence.
- A missing or uncommitted artifact is unavailable. A read cannot make an incomplete finalization appear committed.
- Read-after-commit behavior must be specified against the same authoritative store used by finalization. No eventual projection may be described as immediately authoritative unless its version/consistency contract proves that claim.

## Candidate identity and response fields

The owner must approve a minimal field set. Candidate fields for review:

- organization ID and session ID;
- video ID and video/run revision;
- terminal run state and finalization receipt identity;
- artifact reference plus immutable media hash;
- exact producer pin: bundle ID/version/hash, audience revision, context/basis revision, and source reference/version/hash set;
- policy/profile identity and generation/activation revision needed for lineage, without exposing secrets or provider internals.

Do not infer that request_id, input_hash, pin_digest, and video ID are interchangeable. The field-level relationship to the foundation job/request and attempt belongs to CR08-01 and must be verified from persisted records. If the existing record cannot express the required relationship, stop for a versioned contract/schema proposal.

## Access, freshness, and visibility questions

Before implementation approval, BE2-08 and BE2-09 must agree:

1. Which authenticated principal and role may read the model, and how organization/session ownership is checked without revealing whether another tenant's artifact exists.
2. Whether lookup is by video ID, run ID, or both, and how the exact committed artifact version is selected.
3. Whether the endpoint returns historical finalized artifacts after a newer artifact or source change, and how a caller distinguishes historical lineage from currently eligible use.
4. What superseded, quarantined, revoked, missing, or incomplete records return. The response must not present them as current/playable.
5. Whether the model is a direct post-commit read or a projection; if projected, the read-after-commit guarantee and version cursor must be explicit.

No decision here closes X05d. The current-source resolver/fence for BE2-09 remains BLOCKED; CR09-02 session/access gateway remains OPEN. A successful read is not a playback session or current-use authorization.

## Candidate files and tests

Candidate BE2-08-owned paths, to be reduced to a minimal approved manifest:

- backend/src/sketch2life/application/ports/knowledge_video.py or a new read-only artifact port;
- a new application query service under backend/src/sketch2life/application/knowledge_video_artifact_read.py if required;
- backend/src/sketch2life/infrastructure/knowledge_video/sql.py or a new owned read adapter;
- backend/src/sketch2life/interfaces/http/routers/knowledge_video.py only if a public HTTP contract is selected;
- backend/tests/unit/test_knowledge_video_artifact_read.py;
- backend/tests/contract/test_knowledge_video_artifact_read.py;
- existing persistence/contract tests only if the final design requires them.

Do not add a BE2-09 table/query that reaches into BE2-08 storage. Do not add or modify a migration under this draft. Any schema or published contract change requires a versioned revision and separate approval.

## Acceptance criteria proposed

| ID | Required result |
|---|---|
| AR01 | Only a committed terminal artifact is returned; pre-finalization, rolled-back, or incomplete output is not exposed as finalized. |
| AR02 | The response binds one organization/session/video/run revision to one exact artifact reference and hash, with the adopted source lineage. |
| AR03 | Access checks are scoped to the authenticated principal and tenant/session; missing and inaccessible identities fail closed without cross-tenant disclosure. |
| AR04 | The read is immutable and read-only; no BE2-09 path mutates BE2-08 rows or migrations. |
| AR05 | Historical/superseded/stale/quarantined behavior is explicit and cannot be mistaken for current eligibility or playback permission. |
| AR06 | Read-after-commit and lookup/version behavior are tested at the chosen persistence boundary; fake evidence is labeled as fake. |
| AR07 | X05d remains BLOCKED and X05c/CR09-02 remains OPEN until their own contracts and evidence pass. |
| AR08 | No runtime, provider, playback, Modal, Lightning, database provisioning, card acceptance, or status change is inferred. |

## Approval state and next gate

This supplement is ready only for independent scope review and owner decisions on fields, access, and superseded-artifact semantics. After that, freeze the exact SHA and minimal file manifest in FEAT-050, record supplemental implementation approval in its official approval file, and obtain matching consumer agreement/approval in FEAT-051 before code. Until those records exist, implementation is not authorized.
