# FEAT-003 P2-T4 implementation-approval package draft - reissued

- Status: **DRAFT - READY FOR OWNER FREEZE DECISION**
- Revision: 12
- Reissued: 2026-09-14
- Owner: Person 2
- Package purpose: docs-only remediation and reissue of the future offline core direction
- Final task status: **DRAFT - READY FOR OWNER FREEZE DECISION**

This package is a review handoff. It is **not an implementation approval**, **not a
contract freeze**, **not a runtime authorization**, **not a migration/adoption decision**,
and **not an Integration Sprint allocation**. No implementation is performed by this
revision.

The filename retains the 2026-09-13 draft lineage. Revision 5 supersedes the former
conditional nine-file proposal and its mapping/preservation-envelope implementation
content. The prior B0 report, manifest, technical review, governance review, and
follow-up impact record remain committed historical evidence and are not modified here.

## 1. Authority, selected semantics, and approval meaning

This reissue follows the current task, `AGENTS.md`, ADR-0006, the source register, the
P2-T2/P2-T3 schemas, the dated P2-T4 decisions, and the feature-local B0 evidence. The
current task authorizes edits only to the seven documentation files named in the task;
this package is one of those files.

The owner selected these values for synchronization in this documentation reissue:

- active proposed output identity: exactly `P2T4.P2T4FusedResultV1@1.0`, serialized as
  `P2T4FusedResultV1 / 1.0`;
- previous `RawUnderstandingResultV1` wording: historical baseline only, not the active
  P2-T4 output and not FEAT-018 adoption;
- rejected live identities: `FEAT018.LiveAsrResultV1@1.0` and
  `FEAT018.LiveVisionUnderstandingResultV1@1.0`;
- matching: independently for each validated `AsrSegmentV1.text`; reset normalized token
  coordinates and the three-token negation window for every segment; never cross segments;
- coordinates: canonical `(segment_index, claim_start, claim_end)` over normalized segment
  tokens; `transcript_raw` is not authoritative;
- policy arithmetic: `corroboration_increment` is the exact canonical contract/hash string
  `"0.10"`; conversion to `Decimal("0.10")` is approved only for arithmetic;
- ambiguous Vision regions: no fused observations and no ambiguous text/preservation
  envelope; source provenance remains only through the canonical source-result ref/digest;
- mixed positive/refuting spans: retain support and canonical positive/refuting references,
  emit the contradiction, and suppress adjustment plus primary eligibility.
- upstream fact and T4 admissibility: the current `AsrSuccessV1` contract permits duplicate
  `AsrSegmentV1.index` values, so the T4 invariant is exactly: `For AsrSuccessV1, all
  AsrSegmentV1.index values MUST be unique.` The current Vision V1 validator enforces global
  `observation_id` uniqueness across entities, actions, relations, themes, and ambiguous
  regions through `_validate_observation_references`; T4 adds no redundant Vision uniqueness
  rule or new owner decision.
- terminal pipeline: exactly `identity/version -> strict upstream-contract validation ->
  P2-T4 admissibility invariants -> correlation equality -> typed upstream status -> fusion`;
  the first failing stage is terminal and ASR is checked before Vision where slot ordering
  applies.
- canonical narration references: exact order `(segment_index ASC, claim_start ASC,
  claim_end ASC)`; identical coordinate tuples are deduplicated before independently selecting
  the canonical earliest positive and earliest refuting reference, with selection independent
  of source tuple traversal order.

These selected values are recorded for the owner-freeze decision. They do not approve the
contract, implementation, mapping, migration, or runtime behavior.

The owner approval recorded in `approvals/TASK_APPROVAL.md` on 2026-09-14 authorizes only:

1. documentation-only remediation of the prior package;
2. reissue of the future seven-file offline core direction;
3. preparation of a reviewable, versioned contract-freeze draft; and
4. recording the resulting review checklist and non-actions.

It does not approve the contract-freeze draft, the seven-file implementation, any schema
or service code, any test or fixture file, mapping adoption, migration, runtime wiring,
registry work, provider/GPU/network work, or a cross-feature allocation.

The B0 mapping family `P2T4_FEAT018_CONTRACT_FAMILY_MAPPING_V1@1.0` remains
`PROPOSED_NOT_ADOPTED`. Existing B0 artifacts remain immutable. No mapping module,
mapping test, preservation envelope, mapping case, or FEAT-018 consumer behavior is
introduced by this reissue.

## 1.1 Post-sync FEAT-018 implementation fact and incompatibility boundary

The review base is `d706d88a70c6a9136e397bea10d29f96bafd190b`. The merged tree contains the
current FEAT-018 P2-T2 implementation: the FEAT-018-owned, frozen/implemented
live-development handoff is `RawUnderstandingResultV1 / 1.0`, with its schema, port, mapper,
and focused contract/unit tests. Its bounded offline closure was approved at
`11468d3a5a327697a491f09251a3210987337da0`. This is current implementation state, not the
historical proposal described by the immutable B0 snapshot.

The current FEAT-018 handoff is neither an alias of nor a replacement for the proposed P2-T4
output. The actual incompatibilities are:

| Concern | Proposed P2-T4 direction | Current FEAT-018 implementation |
|---|---|---|
| Vision input | P2 `VisionUnderstandingResultV1@1.0` | Raw mapper consumes FEAT-003 `VisionUnderstandingResultV2@2.0`; optional input is P2 `AsrResultV1` |
| Output identity/status | `P2T4FusedResultV1@1.0`; `FUSED | UPSTREAM_FAILURE` | `RawUnderstandingResultV1@1.0`; discriminated `SUCCEEDED | FAILED` |
| Required envelope/provenance | P2 source-result refs/digests, correlation, and fusion-policy hash | Required `session_id`, `source_image_ref`, `gate_a_required=true`, and V2 profile/catalog/model provenance |
| Ambiguity/fused claims | Ambiguous regions omitted from fused observations; no `fused_claims` array | Ambiguous observations preserved; `fused_claims` carries source refs and confidence |
| Conflicts/confidence/uncertainty | P2-T4 conflict reason/observation/claim-reference rows and per-observation certainty statuses | `RawConflictV1` claim-reference/code rows, required Vision candidate confidence, nullable ASR claim confidence, and scalar uncertainty/status invariant |
| Failure shape | Typed ASR/Vision/BOTH upstream references or separate input rejection | Typed `RawFailureV1` in a `FAILED` branch, with different codes and optional failure provenance |

These are semantic and structural incompatibilities, not documentation-only naming differences.
No alias, replacement, or silent projection is valid. The immutable B0 report, manifest, and review
records predate the implemented FEAT-018 Raw module; they remain an old snapshot and are not
edited or silently upgraded. The B0 mapping remains `PROPOSED_NOT_ADOPTED`; separately approved
integration reconciliation is required before adoption, registry change, consumer update, or
edge-3 handoff.

Two independent post-sync final audits passed, so this package is `DRAFT - READY FOR OWNER FREEZE
DECISION`. This restores owner review only; it is not a contract freeze or implementation
approval. The future T4 freeze/implementation source commit is
`UNKNOWN_UNTIL_REVIEW_APPROVED_COMMITTED`, distinct from the review base and the existing
FEAT-018 closure commit; no future or self-referential digest is asserted.

## 2. Stage model

| Stage | Artifact/action | Status in this task |
|---|---|---|
| A0 | Existing B0 reconciliation evidence and reviews | Historical, committed, mapping remains `PROPOSED_NOT_ADOPTED` |
| A1 | Seven-file scope reissue and remediation matrix | Completed as documentation-only draft |
| A2 | `plan/P2_T4_CONTRACT_FREEZE_DRAFT.md` | Ready for owner freeze decision; not frozen |
| B0 | Owner contract-freeze decision | Pending; not granted here |
| B1 | Separate approval naming exactly the seven implementation paths | Pending; not granted here |
| B2 | Seven-file offline implementation and independent fixture evidence | Not started and not authorized |
| C | Mapping/adoption, registry, session, runtime, Gate A, migration, Integration Sprint | Deferred; separate allocation/approval required |

No stage transition is implied by a document link or by the ready-for-owner-decision
status.

## 3. Inherited owner-approved values

| Decision | Inherited value | Boundary preserved in revision 5 |
|---|---|---|
| B0 | Option 3 reconciliation direction | Mapping remains proposed/not adopted; no mapping implementation |
| B5 | Remove `NOT_FUSIBLE` | Fused result statuses are exactly `FUSED | UPSTREAM_FAILURE` |
| B1 | Support-only narration | Narration supports/refutes Vision candidates and never creates candidates |
| B4 | Vision-only themes | Narration does not create or re-score themes |
| B6 | Exact cues `not`, `no`, `never`, `isn't`, `doesn't`, `didn't`; exact three match-view tokens | Draft records split apostrophe token sequences and per-segment window reset |
| B2 | Primary-only weighting | Support affects only primary selection among non-conflicting candidates |
| B3a | One-time `0.10` increment, cap `1.0` | Exact string is retained in the policy/hash; Decimal arithmetic does not stack |
| B3b | `AGREEMENT_WEIGHTED_V1` | Closed formula identity retained |
| B3c | `NOT_MEASURED` | Null source confidence remains null even with support |

## 4. Finding-by-finding remediation matrix

The matrix is the complete reissue disposition. The status vocabulary is closed to
`RESOLVED_IN_FREEZE_DRAFT`, `ALREADY_COVERED_AND_COPIED`, `STILL_AMBIGUOUS`,
`CONTRADICTORY`, and `REQUIRES_OWNER_DECISION`. No row remains in one of the latter
three states after this remediation; the owner freeze decision itself remains a separate
gate.

| ID | Prior finding / required remediation | Disposition and exact location | Status | Implementation action |
|---|---|---|---|---|
| R-01 | Contraction cue/token representation | Freeze draft section 7.2-7.3 defines punctuation-to-space behavior and exact `("isn", "t")`, `("doesn", "t")`, `("didn", "t")` sequences | `RESOLVED_IN_FREEZE_DRAFT` | None |
| R-02 | Sentence-boundary behavior | Freeze draft section 7.2 states there is no sentence tokenizer or sentence-boundary scope | `RESOLVED_IN_FREEZE_DRAFT` | None |
| R-03 | Primary-selection algorithm | Freeze draft section 8.2 defines grouping, support-first rank, finite-before-null confidence, and source observation ID final tie-break for all ties | `RESOLVED_IN_FREEZE_DRAFT` | None |
| R-04 | Safe typed input rejection | Freeze draft section 4 defines exact fields, closed codes, no raw echo, and identity/status allowlists | `RESOLVED_IN_FREEZE_DRAFT` | None |
| R-05 | Fusion-service input boundary | Freeze draft section 3 separates outer object classification from the exact validated P2 union boundary | `RESOLVED_IN_FREEZE_DRAFT` | None |
| R-06 | Canonicalization profile | Freeze draft section 9 defines projection, included/excluded values, enums, tuples, nulls, UTC datetimes, floats, arrays, CPython 3.13 JSON, and SHA-256 | `RESOLVED_IN_FREEZE_DRAFT` | None |
| R-07 | Confidence arithmetic/precision | Freeze draft section 8.1 and policy table define original-base comparison, exact `"0.10"` token, Decimal conversion, one conversion, cap, and no quantization | `RESOLVED_IN_FREEZE_DRAFT` | None |
| R-08 | Multi-span support/refutation | Freeze draft section 7.4 defines duplicate/overlap handling, mixed positive/refuting rows, canonical refs, and suppression rules | `RESOLVED_IN_FREEZE_DRAFT` | None |
| R-09 | Evidence-reference cardinality/order | Freeze draft sections 7.4, 8.3, and 9.2 define one source ref, one canonical claim ref, source-order arrays, and conflict/uncertainty sort keys | `RESOLVED_IN_FREEZE_DRAFT` | None |
| R-10 | Core rejection precedence | Freeze draft section 3 defines exact identity/version -> strict upstream-contract validation -> P2-T4 admissibility invariants -> correlation equality -> typed upstream status -> fusion precedence; first failure is terminal and ASR is checked before Vision where slot ordering applies | `RESOLVED_IN_FREEZE_DRAFT` | None |
| R-11 | Uncertainty decision table | Freeze draft section 6.4 and section 8.1 define `MEASURED`, `NOT_MEASURED`, and `NOT_APPLICABLE_CONFLICTING` with null rules | `RESOLVED_IN_FREEZE_DRAFT` | None |
| R-12 | Strictly-below confidence floor | Freeze draft section 8.1 defines `base < configured_floor` before adjustment; null is not below the floor | `RESOLVED_IN_FREEZE_DRAFT` | None |
| R-13 | Null-confidence semantics | Inherited B3c is copied in section 3 and the freeze draft; null remains `NOT_MEASURED`/null with support | `ALREADY_COVERED_AND_COPIED` | None |
| R-14 | Empty successful result | Freeze draft sections 6.5 and 10.2 define successful empty inputs as `FUSED` with empty collections and no failure ref | `RESOLVED_IN_FREEZE_DRAFT` | None |
| R-15 | One/both upstream failure references | Freeze draft sections 6.2 and 6.5 define ASR, Vision, and BOTH structural reference shapes and empty fused collections | `RESOLVED_IN_FREEZE_DRAFT` | None |
| R-16 | Seven-file implementation allowlist | Section 5 and the approval record copy the exact seven future paths; no path exists in this worktree | `ALREADY_COVERED_AND_COPIED` | None |
| R-17 | Exact future fixture paths | Every authorized record uses the repo-root-qualified fixture paths in section 5; non-qualified fixture references are removed | `RESOLVED_IN_FREEZE_DRAFT` | None |
| R-18 | ASR admissibility and canonical reference order | Freeze draft sections 3, 4, 5.1, and 7.1/7.4 define unique ASR indexes after strict validation, exact terminal rejection, closed enums, no raw echo, exact tuple ordering, deduplication, and source-order independence; Vision uniqueness remains upstream-owned | `RESOLVED_IN_FREEZE_DRAFT` | None |

No `STILL_AMBIGUOUS`, `CONTRADICTORY`, or `REQUIRES_OWNER_DECISION` finding remains
inside the documentation package. A separate owner choice to freeze or decline the
proposal is expected and is not a remediation defect.

## 5. Exact seven-file offline core direction

The following list is the complete future implementation allowlist for the offline core;
the strings are exact and are not authorization to touch the paths:

```text
backend/src/sketch2life/contracts/schemas/p2_t4_fusion.py
backend/src/sketch2life/application/services/p2_t4_fusion.py
backend/tests/contract/test_p2_t4_contract.py
backend/tests/unit/test_p2_t4_fusion.py
features/FEAT-003-multimodal-understanding/fixtures/p2-t4-fusion-v1/manifest-v1.json
features/FEAT-003-multimodal-understanding/fixtures/p2-t4-fusion-v1/cases-v1.json
features/FEAT-003-multimodal-understanding/fixtures/p2-t4-fusion-v1/expected-v1.json
```

The seven paths are an implementation allowlist, not the total documentation workflow.
No file in that list may be created, edited, stubbed, or pre-populated during this task.
In particular, this reissue does not create a placeholder schema, service, test, manifest,
case file, or expected file.

The future scope is limited to a pure offline fusion service over already validated P2
inputs, its namespaced P2T4 contract, contract/unit tests, and independent synthetic
fixtures. It contains no mapping adapter, preservation envelope, FEAT-018 bridge,
provider call, model/GPU/network operation, route, session, job, queue, database,
storage, mobile, Gate A, or P2-T5 CLI work.

## 6. Contract-freeze draft handoff

`plan/P2_T4_CONTRACT_FREEZE_DRAFT.md` is the companion normative proposal. The two confirmed
contract blockers were remediated in this reissue: all future fixture references are
repo-root-qualified, and the ASR admissibility/precedence/reference-order boundary is explicit.
The current package status is `DRAFT - READY FOR OWNER FREEZE DECISION`; the handoff is
complete when the owner reviews all of the following:

The future fixture artifacts bound by this handoff are exactly:

```text
features/FEAT-003-multimodal-understanding/fixtures/p2-t4-fusion-v1/manifest-v1.json
features/FEAT-003-multimodal-understanding/fixtures/p2-t4-fusion-v1/cases-v1.json
features/FEAT-003-multimodal-understanding/fixtures/p2-t4-fusion-v1/expected-v1.json
```

- active output `P2T4.P2T4FusedResultV1@1.0`, serialized as `P2T4FusedResultV1 / 1.0`,
  with prior `RawUnderstandingResultV1` wording explicitly historical only;
- exact accepted identities `P2.AsrResultV1@1.0` and
  `P2.VisionUnderstandingResultV1@1.0`, with Python unions
  `AsrSuccessV1 | AsrFailureV1` and
  `VisionUnderstandingSuccessV1 | VisionUnderstandingFailureV1`;
- exact rejection of `FEAT018.LiveAsrResultV1@1.0`,
  `FEAT018.LiveVisionUnderstandingResultV1@1.0`, P2 Vision V2, same-name wrong-family
  objects, provider payloads, and unknown/untyped inputs;
- per-segment matching of validated `AsrSegmentV1.text`, reset coordinates/window,
  no cross-segment spans, canonical `(segment_index, claim_start, claim_end)`, and
  non-authoritative `transcript_raw`;
- safe typed `P2T4FusionInputRejectionV1` outside `P2T4FusedResultV1`, with only closed
  identity/phase/code/slot/status/field tokens and no raw input, validation error,
  exception text, transcript, candidate label, path, provider payload, or metadata;
- terminal precedence exactly `identity/version -> strict upstream-contract validation ->
  P2-T4 admissibility invariants -> correlation equality -> typed upstream status -> fusion`,
  with an earlier rejection never masked and ASR checked before Vision where slot ordering
  applies;
- for `AsrSuccessV1`, all `AsrSegmentV1.index` values MUST be unique. A duplicate index is
  rejected with `status=REJECTED`, `phase=ADMISSIBILITY`, `code=INVALID_STRUCTURE`,
  `input_slot=ASR`, and `field_code=DUPLICATE_SEGMENT_INDEX`, after strict validation and before
  correlation or typed status. No duplicated index, transcript, input object, exception, or
  validation path is exposed; `ADMISSIBILITY` and `DUPLICATE_SEGMENT_INDEX` are closed-table
  additions and `INVALID_STRUCTURE` is reused;
- canonical narration references are ordered exactly by `(segment_index ASC, claim_start ASC,
  claim_end ASC)`. Deduplicate identical coordinate tuples before independently selecting the
  canonical earliest positive and earliest refuting reference; selection is independent of
  source tuple traversal order;
- Vision V1 global `observation_id` uniqueness across entities, actions, relations, themes,
  and ambiguous regions is enforced upstream through `_validate_observation_references`; T4
  adds no redundant Vision uniqueness rule or new owner decision;
- complete P2T4 field-level schema, requiredness/nullability, cross-field invariants,
  strictness, immutable nested containers, finite values, and naive-datetime rejection;
- exact match-view normalization, no sentence boundaries, ASCII/curly apostrophe token
  behavior, exact cue sequences, and a complete three-token preceding window;
- support-only narration, Vision-only themes, primary-only weighting, null confidence,
  `FUSED`/`UPSTREAM_FAILURE`, empty-success, ambiguous-region, and mixed-span rules;
- Decimal confidence adjustment with original-base floor comparison and final finite
  serialization; exact canonical JSON and conflict-ID bytes;
- candidate grouping/ranking/ties without input-order tie-break, same-label identity,
  zero-primary behavior, multi-span truth, evidence cardinality/order, independent
  hand-authored schema parity, evidence hash binding, and privacy sentinels.

The draft makes these rules implementable but does not claim they are frozen. A separate
owner freeze decision and a separate seven-file implementation approval remain required.

## 7. Evidence binding and independent parity requirement

Every future freeze or implementation evidence bundle must include a hand-authored
binding record with these fields:

| Field | Required format | Current docs-only record |
|---|---|---|
| `review_base_commit` | full 40-character lowercase Git commit for the post-sync reviewed source tree | `d706d88a70c6a9136e397bea10d29f96bafd190b` |
| `future_source_commit` | explicit non-hash marker until the future freeze/implementation source is reviewed, approved, and committed | `UNKNOWN_UNTIL_REVIEW_APPROVED_COMMITTED` |
| `freeze_draft_sha256` | lowercase SHA-256 of normalized UTF-8 freeze-draft bytes after removing its binding table and revision-history section | `a2bc165f270ad003a38874975e5499e4b021a1d193060ac3fd6f75022085535e` |
| `implementation_package_sha256` | lowercase SHA-256 of normalized UTF-8 document bytes after removing this binding table and revision-history section | `af2442cb46f373d28439c4722491dea54e0aaf94ad416e1327a44865e50c6a5f` |
| `dependency_lock_sha256` | lowercase SHA-256 of each dependency/lock input | `pnpm-lock.yaml=b406b4c36c1e5304cf0c43b175c426d50aa3b43dc9a2bb81be357ea2b80b1665`; `backend/pyproject.toml=9ca3a54905d11fdb7f30a84356d23741f256b2115b254bcc9fba4efacdf17df6` |
| `manifest_sha256` | SHA-256 of `features/FEAT-003-multimodal-understanding/fixtures/p2-t4-fusion-v1/manifest-v1.json` bytes | required when the future artifact exists |
| `cases_sha256` | SHA-256 of `features/FEAT-003-multimodal-understanding/fixtures/p2-t4-fusion-v1/cases-v1.json` bytes | required when the future artifact exists |
| `expected_sha256` | SHA-256 of `features/FEAT-003-multimodal-understanding/fixtures/p2-t4-fusion-v1/expected-v1.json` bytes | required when the future artifact exists |
| `final_evidence_sha256` | SHA-256 of final evidence manifest including all above and validator outputs | required when the future evidence bundle exists |

The freeze/package digest scopes exclude their own changing digest and revision lines.
The seven future artifacts and final evidence are intentionally absent from this
documentation-only task; this is a deferred evidence-production gate, not an unresolved
contract semantic.

For reproducibility, normalize `CRLF` and lone `CR` line endings to `LF`; remove the
complete table beginning with the exact header `| Field | Required format | Current docs-only record |`
through the blank line immediately after its final row; remove the complete section
beginning at the exact heading `## 12. Revision history` through end of file; then
UTF-8 encode the remaining text and hash those bytes. The freeze digest uses the same
steps with its exact binding-table header and `## 13. Revision history` heading.

The future contract test must contain an independent, hand-authored schema-parity oracle.
It must list every field, requiredness/nullability, enum, literal, cross-field invariant,
rejection precedence, canonical sort key, and privacy rule. It must not load a schema
snapshot, serialize the implementation model, introspect implementation fields, or
generate expected schemas from `p2_t4_fusion.py`. Expected JSON is hand-authored and
independently reviewed from the freeze draft.

## 8. Mapping and deferred-boundary record

The B0 compatibility work remains a separate documentation-only workstream. Its explicit
mapping family is still `P2T4_FEAT018_CONTRACT_FAMILY_MAPPING_V1@1.0` with status
`PROPOSED_NOT_ADOPTED`; the existing synthetic compatibility fixture and manifest are
not changed and are not T4 core cases.

The following remain deferred and unapproved:

- FEAT-018 mapping/adoption and any preservation mechanism;
- session/request/idempotency validation;
- registry rows or cutover;
- edge 3 from P2-T4 output to the FEAT-018 raw handoff;
- Gate A, P1, migration, rollback/cutover, or runtime/provider behavior;
- provider, model, GPU, Lightning, Runpod, network, download, or dependency work;
- changes to FEAT-017, FEAT-018, P2-T2, P2-T3, their evidence, or existing fixtures;
- P2-T5 CLI/evaluation and Integration Sprint allocation.

No mapping case is part of the seven-file T4 implementation proposal. No third fused
result status is introduced; structural input errors use the separate safe rejection
type and never become a fused-result status.

## 9. Required independent reviews

### Pass 1 - technical completeness

The reviewer must verify the active identities, historical-versus-active wording, exact
FEAT-018 rejection identities, complete fields, per-segment matching and reset rules,
short prefixes, duplicate/overlapping spans, mixed-span suppression, ranking/null ties,
canonical projection/bytes/IDs, evidence binding, independent parity, and deterministic
fixture coverage. The reviewer must exercise the rejection precedence, exact token
sequences, empty-success case, one/both failure cases, and privacy rules on paper before
implementation.

### Pass 2 - governance and security

The reviewer must verify:

- the package and freeze draft are documentation-only and ready for the owner freeze
  decision, not frozen or implementation-approved;
- the seven paths are exact and untouched;
- mapping remains `PROPOSED_NOT_ADOPTED`;
- no mapping module/test, preservation-envelope implementation, or mapping case is
  proposed for the Sprint-1 T4 core;
- no accidental authentication, provider, credential, endpoint, path, raw transcript,
  raw media, or real child-data content appears;
- the separate freeze decision and separate seven-file implementation approval remain
  explicit prerequisites.

### Review completion record - 2026-09-14

- Pass 1 technical/contract audit: **COMPLETE (post-remediation final audit)**. The audit verified
  the implemented FEAT-018 Raw/V2 mapper handoff, P2-T4 V1 input and fused-output proposal,
  exact repo-root-qualified fixture paths in all seven records, the ASR upstream duplicate-index
  fact and T4 admissibility invariant, the exact terminal pipeline and closed rejection fields,
  canonical reference ordering/deduplication/source-order independence, and the upstream Vision
  uniqueness attribution without a redundant T4 rule or new owner decision.
- Pass 2 governance/security/scope audit: **COMPLETE (post-remediation final audit)**. The audit
  verified the immutable pre-implementation B0 snapshot, `PROPOSED_NOT_ADOPTED` mapping, exact
  seven-document edit boundary, absence of all seven future implementation artifacts, preserved
  P2-T3/FEAT-018/FEAT-020 boundaries, absence of unauthorized code/fixture/lockfile changes, and
  separate freeze/implementation gates.
- These review completions do not grant the owner freeze decision or implementation approval.

## 10. Validation and non-actions

This reissue performs documentation review only. The required post-edit checks are:

```text
git diff --check
python tools/validate_harness.py
python tools/validate_architecture.py
python tools/validate_repository_security.py
python tools/validate_skeleton.py
```

No application tests, lint, type checks, provider runs, GPU runs, network calls, or
fixture generation are required or authorized because no code or fixture changes are
made. This task also does not stage, commit, push, or create a pull request.

Validation record for the final post-sync review on `d706d88a70c6a9136e397bea10d29f96bafd190b`:
`git diff --check`, `validate_harness.py`, `validate_repository_security.py`, and
`validate_skeleton.py` passed. `validate_architecture.py` reports one pre-existing violation in
the unchanged `backend/src/sketch2life/application/services/backend_ai_workflow.py`, where the
application service imports infrastructure catalogs/file inspection. This task makes no code
change and records that finding as a separately scoped architecture remediation; it does not
change the documentation-only `READY FOR OWNER FREEZE DECISION` status.

## 11. Final task status

**DRAFT - READY FOR OWNER FREEZE DECISION**

This status means the documentation reissue is ready for the owner decision. It does not
mean the contract is frozen or that implementation may begin.

## 12. Revision history

| Revision | Date | Disposition |
|---|---|---|
| 1 | 2026-09-13 | Initial draft with mapping-family analysis and conditional implementation proposal. |
| 2 | 2026-09-13 | Corrected identity, source, serialization, and scope wording. |
| 3 | 2026-09-13 | Split contract-design and conditional implementation stages; held pending freeze. |
| 4 | 2026-09-14 | Docs-only remediation: exact seven-file offline core, mapping/preservation-envelope removal, and companion freeze draft; no implementation approval. |
| 5 | 2026-09-14 | Synchronized owner-selected identity/semantics; added 16-row remediation matrix, complete handoff/evidence/parity requirements, and ready-for-owner-freeze status; no implementation added. |
| 6 | 2026-09-14 | Recorded final post-edit technical and governance/security review reruns and reproducible digest boundaries; no implementation added. |
| 7 | 2026-09-14 | Reconciled the post-sync implemented FEAT-018 Raw handoff, V1/V2 incompatibilities, B0 snapshot drift, review-base semantics, and current dependency hashes; held at `DRAFT - UPSTREAM RECONCILIATION REVIEW REQUIRED` for two final audits. |
| 8 | 2026-09-14 | Recorded the two passing post-sync final audits and restored owner-freeze-ready status; no contract or implementation approval was granted. |
| 9 | 2026-09-14 | Recorded final validator results, including the pre-existing out-of-scope architecture finding; no code change or status change. |
| 10 | 2026-09-14 | Preserved the exact intermediate reconciliation-review status in the history; no contract or implementation approval was granted. |
| 11 | 2026-09-14 | Reopened the package as `CONTRACT FREEZE BLOCKED` while remediating the exact future fixture paths and ASR admissibility/ordering blockers; no implementation approval was granted. |
| 12 | 2026-09-14 | Resolved the exact fixture-path, ASR admissibility/precedence, Vision upstream-uniqueness attribution, and canonical-reference ordering blockers; no implementation approval was granted. |
| 13 | 2026-09-14 | Recorded the post-remediation technical/contract and governance/security/scope audits, verified digest bindings, and restored owner-freeze-ready status; no contract or implementation approval was granted. |
