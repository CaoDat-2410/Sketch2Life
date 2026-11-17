# CR-C4-01 — full CMD-48 owner delegate contracts

## Receiver-scope correction / C4b follow-up

User clarified BE2-13/14 also belong to this receiver (08–14); waiting for them as
another person's prerequisite was too broad. Fixed dispatcher and strict typed
binding/HTTP seam now exist with conformance fixtures and explicit unavailable
slots. See GOVERNANCE_BINDING_HANDOFF.md. Complete owner payload semantics and
real adapter adoption remain open, but do not block candidate dispatch work.
Original absence assessment below is historical, not current code inventory.

Status: OPEN / not cross-owner approved. Prepared by BE2-12 under approved plan;
not an instruction or approval for implementing BE2-13/14/BE1 policy business logic.

## Verified gap

Current source has a lightweight DATA-33 ShapeSpec only. It enumerates actions
and record kinds, not complete preset/policy payload schemas. No typed preset/
AI/core-policy owner command or delegate exists in the inspected backend contract
and application source at parent b7cb89f. SRS specifies preset field families but
does not supply complete stage/notification rule payload shapes or the allowlisted
AI/core-policy fields required for an actual closed union. Inventing them or
passing arbitrary dictionaries/JSON to owners would violate scope/security.

C4a content HTTP seam is implemented and deliberately not mounted by default.
It is not the full CMD-48 dispatcher and currently rejects non-content bodies.
Do not claim AC01/AC11 complete based on the content-only route inventory.

## Requested owner deliverables

| Owner | Contract required |
|---|---|
| BE2-13 | Versioned strict preset action models for create/edit/submit/review/changes/publish/recall/archive as applicable; exact stage_rules/notification_rules shapes; review/publication semantics for preset rather than fabricated learning_content review |
| BE2-14 | Versioned strict AI-policy action models, allowlisted write fields, pinned revision/hash/precondition semantics and independent command capability requirements |
| BE1-15 | Versioned strict non-AI policy branches (organization/purpose/retention as applicable), allowlisted fields, policy-kind discriminator, authority/CAS/error/receipt contract |
| BE1 identity/P4 | Verified principal/org resolver composition and adopted ContentBoundary guard with commit-time revocation/source/review fencing; no role-name-to-new-capability inference |

For each delegate supply a typed immutable command and typed DATA-33-compatible
response/error port. Preserve shared envelope action/record_kind/client key,
exact target/version/hash and record If-Match; no raw body dict, untyped
configuration or bearer token in application command. Define scope derivation,
independent capability verification, current authorization on duplicates,
transaction ownership and safe errors. BE2-12 must not write the owner's tables.
Missing bound implementation must yield an explicit typed unavailable outcome,
not mutate content or fabricate a successful result.

## Required integration acceptance

- One POST governance/records path with one closed discriminated union containing
  learning_content/preset/policy and closed AI/core policy subtypes.
- Invalid branch/action/field payload is rejected before any delegate invocation.
- Spy/contract tests prove exactly the correct typed owner receives the command,
  immutable verified scope, correlation and distinct record precondition.
- Missing delegates produce typed unavailable; they never fall through to content.
- Delegate implementation owns capability/current policy/receipt/commit checks;
  dispatcher does not borrow content permissions or write foreign schema tables.
- Real verified identity/adopted outer guard proves current revocation through
  commit, not an in-process fixture. No raw child access follows admin publication.
- Consumer tests cover published exact refs, recall denial, immutable provenance
  and at-least-once event deduplication without active-copy deletion/replacement.

This request and component code do not confer another owner's sign-off. Continue
scoped local HTTP/API/handoff checks; true full dispatcher/integration closure
requires the above contracts and authority, not a fabricated broad schema.
