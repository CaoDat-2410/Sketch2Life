# FEAT-003 P2-T4 implementation-approval package draft - reissued

- Status: **HOLD - NOT APPROVED**
- Revision: 16
- Reissued: 2026-09-15
- Owner: Person 2
- Package purpose: docs-only successor for the verified Vision match-view contract gap
- Final task status: **HOLD - NOT APPROVED**
- Independent review status: **NOT YET PERFORMED**
- Supersedes: `evidence/notes/P2_T4_IMPLEMENTATION_APPROVAL_PACKAGE_DRAFT_20260913.md` revision 15,
  approved and committed at `18d0c33d35431ca96a76692a68c6b992098699e7`, normalized SHA-256
  `6821755722daf3bce622fe98eaf39124adb835c6854661143d79f48a943030d7`. Revision 15 remains
  byte-identical at its own path as immutable G1 history; this document does not edit it and
  is a new, separate, standalone file. Its companion freeze successor is
  `plan/P2_T4_CONTRACT_FREEZE_REVISION_12.md` (freeze revision 12).

This package is a review handoff. It is **not an implementation approval**, **not a
contract freeze**, **not a runtime authorization**, **not a migration/adoption decision**,
and **not an Integration Sprint allocation**. No implementation is performed by this
revision.

The filename retains the 2026-09-13 draft lineage through revision 15. This revision 16 is a
new standalone file at a new path, reissued to address a verified post-checkpoint contract gap.
The prior B0 report, manifest, technical review, governance review, follow-up impact record, and
revisions 1-15 of this package remain committed historical evidence and are not modified here.

## 1. Authority, selected semantics, and approval meaning

This reissue follows the current task, `AGENTS.md`, ADR-0006, the source register, the
P2-T2/P2-T3 schemas, the dated P2-T4 decisions, `plan/P2_T4_MATCH_VIEW_REMEDIATION_PLAN.md`, and
the feature-local B0 evidence. The current task authorizes creation of exactly this file and its
companion freeze successor, plus the governance-record updates listed in
`approvals/TASK_APPROVAL.md`'s 2026-09-15 match-view successor-decisions entry.

### 1.0 Reason for this successor and the five owner decisions

Package revision 15 and its companion freeze revision 11 were approved as G1 at commit
`18d0c33d35431ca96a76692a68c6b992098699e7`, and G2 then approved the exact seven-file offline
implementation, which was committed at `064ba62f32f1ffb964bc2208577eb0650b98e26a`. A
post-checkpoint contract audit found a **VERIFIED_DEFECT**: the frozen requirement that
"successful fusion requires the declared v2 match view" (freeze revision 11, section 5.2) has no
conforming enforcement, and checkpoint `064ba62` performs no check, so a schema-valid Vision
success carrying a non-canonical `policy_match_view_version` reaches `FUSED`. Full evidence and
the option analysis are in `plan/P2_T4_MATCH_VIEW_REMEDIATION_PLAN.md`.

The project owner recorded five decisions in `approvals/TASK_APPROVAL.md` (2026-09-15):

- **MV-1 = B:** add closed field code `POLICY_MATCH_VIEW_VERSION` at `ADMISSIBILITY`.
- **MV-2 = S2:** enforce the invariant for `VisionUnderstandingSuccessV1` only.
- **MV-3 = T1:** compare exactly against the upstream constant
  `VISION_POLICY_MATCH_VIEW_VERSION` (`vision-policy-match-view-v2`); the T4 policy literal and
  `fusion_policy_config_hash` are unchanged.
- **MV-4 = V2:** keep `P2T4.P2T4FusedResultV1@1.0`; replace the outer rejection contract with
  `P2T4.P2T4FusionInputRejectionV2@2.0`, superseding V1 for every outer-boundary rejection.
- **MV-5:** issue standalone successor artifacts (this file and the freeze successor); never
  edit revision 11/15 in place.

Recording these decisions and issuing this package for independent review does not itself grant
a successor-freeze approval or an implementation approval. Both remain separate, required gates.

The owner selected these values for synchronization in this documentation reissue (**unchanged
from revision 15** unless annotated):

- active proposed output identity: exactly `P2T4.P2T4FusedResultV1@1.0`, serialized as
  `P2T4FusedResultV1 / 1.0` (**unchanged**);
- **the outer safe-rejection identity is now `P2T4.P2T4FusionInputRejectionV2@2.0`, superseding
  `P2T4.P2T4FusionInputRejectionV1@1.0` (new in this successor, MV-4)**;
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
  AsrSegmentV1.index values MUST be unique.` **The current Vision V1 contract permits any
  non-empty `policy_match_view_version`, so a second T4 admissibility invariant now applies: for
  `VisionUnderstandingSuccessV1`, `policy_match_view_version` MUST equal
  `VISION_POLICY_MATCH_VIEW_VERSION` (`vision-policy-match-view-v2`) exactly (new in this
  successor, MV-1/MV-2/MV-3); a `VisionUnderstandingFailureV1` is not subject to it.** The
  current Vision V1 validator enforces global `observation_id` uniqueness across entities,
  actions, relations, themes, and ambiguous regions through `_validate_observation_references`;
  T4 adds no redundant Vision uniqueness rule or new owner decision.
- terminal pipeline: exactly `identity/version -> strict upstream-contract validation ->
  P2-T4 admissibility invariants -> correlation equality -> typed upstream status -> fusion`;
  the first failing stage is terminal and ASR is checked before Vision where slot ordering
  applies. **Within admissibility, the ASR duplicate-index invariant is checked before the
  Vision match-view invariant.**
- canonical narration references: exact order `(segment_index ASC, claim_start ASC,
  claim_end ASC)`; identical coordinate tuples are deduplicated before independently selecting
  the canonical earliest positive and earliest refuting reference, with selection independent
  of source tuple traversal order.
- CF-B1 certainty is derived from original validated source values. Positive/refuting evidence
  and conflicts are derived before any adjustment; primary selection occurs before adjustment
  using conflict eligibility, positive-support rank, original source confidence, then
  `observation_id`. Adjusted certainty never participates in grouping, ranking, primary
  eligibility, conflict detection, or low-confidence classification. Every finite-confidence,
  non-conflicting candidate defaults to `certainty = base`; a supported non-primary candidate
  retains `certainty = base`. Only `primary_interpretation == true`, eligible positive
  narration support, and no conflict receive the one-time exact value
  `float(min(Decimal("1.0"), Decimal(str(base)) + Decimal("0.10")))`, with no quantization or
  intermediate float conversion. **This entire CF-B1 paragraph is unaffected by MV-1..MV-5; the
  match-view fix is an admissibility-stage input gate, not a fusion/certainty change.**
- CF-B1 certainty assignment is exhaustive and mutually exclusive, with the following
  precedence:
  1. Conflict status has the highest certainty-status precedence.
  2. Any conflicting candidate, regardless of whether source confidence is finite or null,
     has `certainty_status=NOT_APPLICABLE_CONFLICTING` and `certainty=null`.
  3. Otherwise, a non-conflicting candidate with null source confidence has
     `certainty_status=NOT_MEASURED` and `certainty=null`.
  4. Otherwise, a finite-confidence, non-conflicting candidate has
     `certainty_status=MEASURED` and `certainty=base` by default, or the already-frozen
     primary-only adjusted value when all eligibility conditions hold.
  A null-confidence candidate with a contradiction is governed by rule 2, not rule 3.
- Low-confidence classification uses original `base < configured_floor` before adjustment.
- Support adjustment occurs after primary selection and MUST NOT change grouping, ranking,
  primary eligibility, conflict detection, or low-confidence classification. B2 remains
  `Primary-only weighting`; no other closed owner decision is reopened.

These selected values are recorded for the successor-freeze decision. They do not approve the
contract, implementation, mapping, migration, or runtime behavior.

The owner authorization recorded in `approvals/TASK_APPROVAL.md` on 2026-09-15 authorizes only:

1. recording the five MV-1 through MV-5 decisions;
2. creation of this package and its companion freeze successor as new, standalone files;
3. corresponding governance-record updates in `CONTEXT.md`, `DECISIONS.md`, `plan/PLAN.md`, and
   `plan/P2_T4_FUSION_RESEARCH_PLAN.md`, and relocation of the match-view approval request from
   its ignored `evidence/notes/` location to a publishable `plan/` path; and
4. a `.gitignore` exception limited to the one new package path named above.

It does not approve this successor freeze, the seven-file remediation implementation, any schema
or service code, any test or fixture file, mapping adoption, migration, runtime wiring,
registry work, provider/GPU/network work, or a cross-feature allocation.

The B0 mapping family `P2T4_FEAT018_CONTRACT_FAMILY_MAPPING_V1@1.0` remains
`PROPOSED_NOT_ADOPTED`. Existing B0 artifacts remain immutable. No mapping module,
mapping test, preservation envelope, mapping case, or FEAT-018 consumer behavior is
introduced by this reissue.

## 1.1 Post-sync FEAT-018 implementation fact and incompatibility boundary

The review base for this successor is `064ba62f32f1ffb964bc2208577eb0650b98e26a`, the committed
G3-G5 offline-core checkpoint. That tree contains the current FEAT-018 P2-T2 implementation: the
FEAT-018-owned, frozen/implemented live-development handoff is `RawUnderstandingResultV1 / 1.0`,
with its schema, port, mapper, and focused contract/unit tests. Its bounded offline closure was
approved at `11468d3a5a327697a491f09251a3210987337da0`. None of these FEAT-018/FEAT-020 facts
changed since revision 15's review base (`d706d88a70c6a9136e397bea10d29f96bafd190b`); only the
P2-T4 offline core itself is new in the tree, and it is the subject of this successor.

The current FEAT-018 handoff is neither an alias of nor a replacement for the proposed P2-T4
output. The actual incompatibilities are:

| Concern | Proposed P2-T4 direction | Current FEAT-018 implementation |
|---|---|---|
| Vision input | P2 `VisionUnderstandingResultV1@1.0` | Raw mapper consumes FEAT-003 `VisionUnderstandingResultV2@2.0`; optional input is P2 `AsrResultV1` |
| Output identity/status | `P2T4FusedResultV1@1.0`; `FUSED | UPSTREAM_FAILURE` | `RawUnderstandingResultV1@1.0`; discriminated `SUCCEEDED | FAILED` |
| Required envelope/provenance | P2 source-result refs/digests, correlation, and fusion-policy hash | Required `session_id`, `source_image_ref`, `gate_a_required=true`, and V2 profile/catalog/model provenance |
| Ambiguity/fused claims | Ambiguous regions omitted from fused observations; no `fused_claims` array | Ambiguous observations preserved; `fused_claims` carries source refs and confidence |
| Conflicts/confidence/uncertainty | P2-T4 conflict reason/observation/claim-reference rows and per-observation certainty statuses | `RawConflictV1` claim-reference/code rows, required Vision candidate confidence, nullable ASR claim confidence, and scalar uncertainty/status invariant |
| Failure shape | Typed ASR/Vision/BOTH upstream references or separate input rejection (now `P2T4FusionInputRejectionV2`) | Typed `RawFailureV1` in a `FAILED` branch, with different codes and optional failure provenance |

These are semantic and structural incompatibilities, not documentation-only naming differences.
No alias, replacement, or silent projection is valid. The immutable B0 report, manifest, and review
records predate the implemented FEAT-018 Raw module; they remain an old snapshot and are not
edited or silently upgraded. The B0 mapping remains `PROPOSED_NOT_ADOPTED`; separately approved
integration reconciliation is required before adoption, registry change, consumer update, or
edge-3 handoff.

This successor's status remains `HOLD - NOT APPROVED` pending independent review and then a
separate owner freeze decision. This is not a contract freeze or implementation approval. The
future remediation-implementation source commit is `UNKNOWN_UNTIL_REVIEW_APPROVED_COMMITTED`,
distinct from the review base and the existing FEAT-018 closure commit; no future or
self-referential digest is asserted.

## 2. Stage model

| Stage | Artifact/action | Status in this task |
|---|---|---|
| A0 | Existing B0 reconciliation evidence and reviews | Historical, committed, mapping remains `PROPOSED_NOT_ADOPTED` |
| A1 | G1 freeze/package (revision 11/15) and G2 seven-file offline implementation | Approved and committed at `18d0c33`/`064ba62` |
| A2 | Post-checkpoint match-view contract-gap audit | Complete; `VERIFIED_DEFECT` (`plan/P2_T4_MATCH_VIEW_REMEDIATION_PLAN.md`) |
| A3 | Five MV-1..MV-5 owner decisions | Recorded 2026-09-15 in `approvals/TASK_APPROVAL.md` |
| A4 | This successor package (revision 16) and its companion freeze (revision 12) | `HOLD - NOT APPROVED`; available for independent review; not frozen |
| B0 | Independent successor-freeze review | Pending; not performed |
| B1 | Owner successor-freeze approval (new "G1 successor" gate) | Pending; not granted here |
| B2 | Separate remediation-implementation approval naming exactly the seven existing paths | Pending; not granted here |
| B3 | Remediation implementation and independent fixture evidence | Not started and not authorized |
| C | Mapping/adoption, registry, session, runtime, Gate A, migration, Integration Sprint | Deferred; separate allocation/approval required |

No stage transition is implied by a document link or by the ready-for-owner-decision
status.

## 3. Inherited owner-approved values

| Decision | Inherited value | Boundary preserved in this successor |
|---|---|---|
| B0 | Option 3 reconciliation direction | Mapping remains proposed/not adopted; no mapping implementation |
| B5 | Remove `NOT_FUSIBLE` | Fused result statuses are exactly `FUSED | UPSTREAM_FAILURE` |
| B1 | Support-only narration | Narration supports/refutes Vision candidates and never creates candidates |
| B4 | Vision-only themes | Narration does not create or re-score themes |
| B6 | Exact cues `not`, `no`, `never`, `isn't`, `doesn't`, `didn't`; exact three match-view tokens | Unchanged; the recipe (section 7.2 of the freeze) is distinct from the new admissibility comparator |
| B2 | Primary-only weighting | Support affects only primary selection among non-conflicting candidates |
| B3a | One-time `0.10` increment, cap `1.0` | Exact string is retained in the policy/hash; Decimal arithmetic does not stack |
| B3b | `AGREEMENT_WEIGHTED_V1` | Closed formula identity retained |
| B3c | `NOT_MEASURED` | Non-conflicting null source confidence remains `NOT_MEASURED`/`null` even with support; conflicting null-confidence candidates use conflict precedence |
| MV-1..MV-5 | See section 1.0 | New in this successor; recorded in `approvals/TASK_APPROVAL.md` |

## 4. Finding-by-finding remediation matrix

The matrix below repeats revisions 1-20 of the prior remediation matrix (all `RESOLVED_IN_FREEZE_DRAFT`
or `ALREADY_COVERED_AND_COPIED` as of revision 15, unaffected by this successor) and adds row
`R-21` for the match-view contract gap. The status vocabulary is closed to
`RESOLVED_IN_FREEZE_DRAFT`, `ALREADY_COVERED_AND_COPIED`, `STILL_AMBIGUOUS`,
`CONTRADICTORY`, and `REQUIRES_OWNER_DECISION`. No row is in one of the latter
three states after this successor; the owner successor-freeze decision itself remains a separate
gate.

| ID | Prior finding / required remediation | Disposition and exact location | Status | Implementation action |
|---|---|---|---|---|
| R-01 | Contraction cue/token representation | Freeze section 7.2-7.3 defines punctuation-to-space behavior and exact `("isn", "t")`, `("doesn", "t")`, `("didn", "t")` sequences | `RESOLVED_IN_FREEZE_DRAFT` | None |
| R-02 | Sentence-boundary behavior | Freeze section 7.2 states there is no sentence tokenizer or sentence-boundary scope | `RESOLVED_IN_FREEZE_DRAFT` | None |
| R-03 | Primary-selection algorithm | Freeze section 8.2 defines grouping, support-first rank, finite-before-null confidence, and source observation ID final tie-break for all ties | `RESOLVED_IN_FREEZE_DRAFT` | None |
| R-04 | Safe typed input rejection | Freeze section 4 defines exact fields, closed codes, no raw echo, and identity/status allowlists | `RESOLVED_IN_FREEZE_DRAFT` | None |
| R-05 | Fusion-service input boundary | Freeze section 3 separates outer object classification from the exact validated P2 union boundary | `RESOLVED_IN_FREEZE_DRAFT` | None |
| R-06 | Canonicalization profile | Freeze section 9 defines projection, included/excluded values, enums, tuples, nulls, UTC datetimes, floats, arrays, CPython 3.13 JSON, and SHA-256 | `RESOLVED_IN_FREEZE_DRAFT` | None |
| R-07 | Confidence arithmetic/precision | Freeze section 8.1 and policy table define original-base comparison, exact `"0.10"` token, Decimal conversion, one conversion, cap, and no quantization | `RESOLVED_IN_FREEZE_DRAFT` | None |
| R-08 | Multi-span support/refutation | Freeze section 7.4 defines duplicate/overlap handling, mixed positive/refuting rows, canonical refs, and suppression rules | `RESOLVED_IN_FREEZE_DRAFT` | None |
| R-09 | Evidence-reference cardinality/order | Freeze sections 7.4, 8.3, and 9.2 define one source ref, one canonical claim ref, source-order arrays, and conflict/uncertainty sort keys | `RESOLVED_IN_FREEZE_DRAFT` | None |
| R-10 | Core rejection precedence | Freeze section 3 defines exact identity/version -> strict upstream-contract validation -> P2-T4 admissibility invariants -> correlation equality -> typed upstream status -> fusion precedence; first failure is terminal and ASR is checked before Vision where slot ordering applies | `RESOLVED_IN_FREEZE_DRAFT` | None |
| R-11 | Uncertainty decision table | Freeze section 6.4 and section 8.1 define mutually exclusive conflict-first precedence for `MEASURED`, `NOT_MEASURED`, and `NOT_APPLICABLE_CONFLICTING` with null rules | `RESOLVED_IN_FREEZE_DRAFT` | None |
| R-12 | Strictly-below confidence floor | Freeze section 8.1 defines `base < configured_floor` before adjustment; null is not below the floor | `RESOLVED_IN_FREEZE_DRAFT` | None |
| R-13 | Null-confidence semantics | Inherited B3c is copied in section 3 and the freeze; non-conflicting null remains `NOT_MEASURED`/null with support, while conflicting null uses conflict precedence | `ALREADY_COVERED_AND_COPIED` | None |
| R-14 | Empty successful result | Freeze sections 6.5 and 10.2 define successful empty inputs as `FUSED` with empty collections and no failure ref | `RESOLVED_IN_FREEZE_DRAFT` | None |
| R-15 | One/both upstream failure references | Freeze sections 6.2 and 6.5 define ASR, Vision, and BOTH structural reference shapes and empty fused collections | `RESOLVED_IN_FREEZE_DRAFT` | None |
| R-16 | Seven-file implementation allowlist | Section 5/10.2 and the approval record copy the exact seven paths; the paths already hold the G2-approved implementation as of checkpoint `064ba62` | `ALREADY_COVERED_AND_COPIED` | None |
| R-17 | Exact fixture paths | Every authorized record uses the repo-root-qualified fixture paths in section 5 | `RESOLVED_IN_FREEZE_DRAFT` | None |
| R-18 | ASR admissibility and canonical reference order | Freeze sections 3, 4, 5.1, and 7.1/7.4 define unique ASR indexes after strict validation, exact terminal rejection, closed enums, no raw echo, exact tuple ordering, deduplication, and source-order independence; Vision uniqueness remains upstream-owned | `RESOLVED_IN_FREEZE_DRAFT` | None |
| R-19 | CF-B1 certainty and primary-selection semantics | Freeze sections 8.1-8.2 define original-source evidence/conflict derivation, primary-before-adjustment ranking, mutually exclusive conflict-first certainty precedence, exact Decimal formula, strict original-base floor comparison, and no feedback from adjustment | `RESOLVED_IN_FREEZE_DRAFT` | None |
| R-20 | CF-B2 revision and digest reconciliation | Freeze revision 11 and package revision 15 recorded matching final precedence/digest-refresh history records; both normalized binding digests were recomputed after all non-binding bytes were final | `RESOLVED_IN_FREEZE_DRAFT` | None |
| R-21 | Vision match-view contract gap (`plan/P2_T4_MATCH_VIEW_REMEDIATION_PLAN.md`, `VERIFIED_DEFECT`) | Freeze successor (revision 12) section 3.3 defines the exact T4 admissibility invariant for `VisionUnderstandingSuccessV1` against the upstream `VISION_POLICY_MATCH_VIEW_VERSION` constant (MV-2/MV-3); section 4 defines the new `POLICY_MATCH_VIEW_VERSION` field code and the exact Vision `ADMISSIBILITY` rejection form under the new `P2T4.P2T4FusionInputRejectionV2@2.0` identity (MV-1/MV-4); section 10.2 defines the six new required fixture scenarios and the fact that all 16 existing `REJECTED` expected entries change identity/version bytes while the 26 non-rejected entries stay byte-identical | `RESOLVED_IN_FREEZE_DRAFT` | Remediation-implementation scope only (section 6 below); no code, test, or fixture path is created or edited by this docs-only successor |

No `STILL_AMBIGUOUS`, `CONTRADICTORY`, or `REQUIRES_OWNER_DECISION` finding remains
inside the documentation package. A separate owner choice to freeze or decline this successor is
expected and is not a remediation defect.

## 5. Exact seven-file offline core direction

The following list is the complete remediation-implementation allowlist; the strings are
exact and are not authorization to touch the paths. Unlike revision 15 (where these paths did
not yet exist), all seven paths already exist and hold the G2-approved offline-core
implementation as of checkpoint `064ba62f32f1ffb964bc2208577eb0650b98e26a`:

```text
backend/src/sketch2life/contracts/schemas/p2_t4_fusion.py
backend/src/sketch2life/application/services/p2_t4_fusion.py
backend/tests/contract/test_p2_t4_contract.py
backend/tests/unit/test_p2_t4_fusion.py
features/FEAT-003-multimodal-understanding/fixtures/p2-t4-fusion-v1/manifest-v1.json
features/FEAT-003-multimodal-understanding/fixtures/p2-t4-fusion-v1/cases-v1.json
features/FEAT-003-multimodal-understanding/fixtures/p2-t4-fusion-v1/expected-v1.json
```

The seven paths are the complete remediation-implementation allowlist, not the total
documentation workflow. No file in that list may be created, edited, stubbed, or pre-populated
by this docs-only successor.

The remediation scope is limited to closing the Vision match-view admissibility gap inside the
existing pure offline fusion service, its namespaced P2T4 contracts, contract/unit tests, and
independent synthetic fixtures. It contains no mapping adapter, preservation envelope, FEAT-018
bridge, provider call, model/GPU/network operation, route, session, job, queue, database,
storage, mobile, Gate A, or P2-T5 CLI work.

## 6. Contract-freeze successor handoff

`plan/P2_T4_CONTRACT_FREEZE_REVISION_12.md` is the companion normative successor. It supersedes
`plan/P2_T4_CONTRACT_FREEZE_DRAFT.md` revision 11 for the Vision match-view semantics only; every
other CF-B1/B2/B3 rule, matching/negation rule, and canonicalization rule it restates is
unchanged from revision 11. The current package status is `HOLD - NOT APPROVED`; the handoff is
complete when the owner reviews all of the following:

The fixture artifacts bound by this handoff, once remediated, are exactly:

```text
features/FEAT-003-multimodal-understanding/fixtures/p2-t4-fusion-v1/manifest-v1.json
features/FEAT-003-multimodal-understanding/fixtures/p2-t4-fusion-v1/cases-v1.json
features/FEAT-003-multimodal-understanding/fixtures/p2-t4-fusion-v1/expected-v1.json
```

- active output `P2T4.P2T4FusedResultV1@1.0`, serialized as `P2T4FusedResultV1 / 1.0`
  (**unchanged**), with prior `RawUnderstandingResultV1` wording explicitly historical only;
- **the outer safe rejection identity is now `P2T4.P2T4FusionInputRejectionV2@2.0`, superseding
  `P2T4.P2T4FusionInputRejectionV1@1.0` for every outer-boundary rejection — no mixed V1/V2
  rejection union (MV-4)**;
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
- safe typed `P2T4FusionInputRejectionV2` outside `P2T4FusedResultV1`, with only closed
  identity/phase/code/slot/status/field tokens and no raw input, validation error,
  exception text, transcript, candidate label, path, provider payload, metadata, or (new) the
  observed non-canonical `policy_match_view_version` value;
- terminal precedence exactly `identity/version -> strict upstream-contract validation ->
  P2-T4 admissibility invariants -> correlation equality -> typed upstream status -> fusion`,
  with an earlier rejection never masked and ASR checked before Vision where slot ordering
  applies, **including within admissibility itself: the ASR duplicate-index invariant is checked
  before the Vision match-view invariant**;
- for `AsrSuccessV1`, all `AsrSegmentV1.index` values MUST be unique. A duplicate index is
  rejected with `status=REJECTED`, `phase=ADMISSIBILITY`, `code=INVALID_STRUCTURE`,
  `input_slot=ASR`, and `field_code=DUPLICATE_SEGMENT_INDEX`, after strict validation and before
  correlation or typed status;
- **for `VisionUnderstandingSuccessV1` only, `policy_match_view_version` MUST equal
  `VISION_POLICY_MATCH_VIEW_VERSION` (`vision-policy-match-view-v2`) exactly. A mismatch is
  rejected with `status=REJECTED`, `phase=ADMISSIBILITY`, `code=INVALID_STRUCTURE`,
  `input_slot=VISION`, and `field_code=POLICY_MATCH_VIEW_VERSION`, after strict validation, after
  the ASR admissibility check, and before correlation or typed status. A
  `VisionUnderstandingFailureV1` is not subject to this check (MV-2). The observed token is never
  exposed (new in this successor, MV-1/MV-2/MV-3)**; `ADMISSIBILITY` and
  `DUPLICATE_SEGMENT_INDEX`/`POLICY_MATCH_VIEW_VERSION` are closed-table
  additions and `INVALID_STRUCTURE` is reused for both exact forms;
- canonical narration references are ordered exactly by `(segment_index ASC, claim_start ASC,
  claim_end ASC)`. Deduplicate identical coordinate tuples before independently selecting the
  canonical earliest positive and earliest refuting reference; selection is independent of
  source tuple traversal order;
- Vision V1 global `observation_id` uniqueness across entities, actions, relations, themes,
  and ambiguous regions is enforced upstream through `_validate_observation_references`; T4
  adds no redundant Vision uniqueness rule or new owner decision;
- CF-B1 certainty uses the same exhaustive, mutually exclusive precedence as revision 15
  (**entirely unaffected by this successor**): conflict status has
  the highest certainty-status precedence; any conflicting candidate, finite or null confidence,
  uses `NOT_APPLICABLE_CONFLICTING`/`null`; otherwise a non-conflicting null-confidence candidate
  uses `NOT_MEASURED`/`null`; otherwise a finite-confidence, non-conflicting candidate uses
  `MEASURED`/`base` by default or the already-frozen primary-only adjustment. A
  null-confidence candidate with a contradiction is governed by the conflict rule, not the
  non-conflicting null rule. Primary selection precedes adjustment, uses conflict eligibility,
  positive support, original confidence, and observation ID, and adjusted certainty never feeds
  back into grouping, ranking, eligibility, conflict detection, or low-confidence classification.
  B2 remains `Primary-only weighting` and no other closed owner decision is reopened;
- complete P2T4 field-level schema, requiredness/nullability, cross-field invariants,
  strictness, immutable nested containers, finite values, and naive-datetime rejection;
- exact match-view *recipe* (section 7.2 of the freeze successor — unchanged narration-matching
  tokenization), no sentence boundaries, ASCII/curly apostrophe token behavior, exact cue
  sequences, and a complete three-token preceding window, **kept explicitly distinct from the new
  admissibility *comparator* in freeze section 3.3**;
- support-only narration, Vision-only themes, primary-only weighting, null confidence,
  `FUSED`/`UPSTREAM_FAILURE`, empty-success, ambiguous-region, and mixed-span rules
  (**unchanged**);
- Decimal confidence adjustment with original-base floor comparison and final finite
  serialization; exact canonical JSON and conflict-ID bytes (**unchanged; applies identically to
  `P2T4FusionInputRejectionV2` instances**);
- candidate grouping/ranking/ties without input-order tie-break, same-label identity,
  zero-primary behavior, multi-span truth, evidence cardinality/order, independent
  hand-authored schema parity (**now for `P2T4FusionInputRejectionV2`**), evidence hash binding,
  and privacy sentinels (**now also covering the observed match-view token**).

The successor makes these rules implementable but does not claim they are frozen. A separate
owner successor-freeze decision and a separate seven-file remediation-implementation approval
remain required.

## 7. Evidence binding and independent parity requirement

Every future remediation-implementation evidence bundle must include a hand-authored
binding record with these fields:

| Field | Required format | Current docs-only record |
|---|---|---|
| `review_base_commit` | full 40-character lowercase Git commit for the reviewed source tree this successor was authored against | `064ba62f32f1ffb964bc2208577eb0650b98e26a` |
| `future_source_commit` | explicit non-hash marker until the future remediation-implementation source is reviewed, approved, and committed | `UNKNOWN_UNTIL_REVIEW_APPROVED_COMMITTED` |
| `predecessor_freeze_commit` | the immutable G1 freeze commit this successor supersedes | `18d0c33d35431ca96a76692a68c6b992098699e7` |
| `predecessor_freeze_sha256` | normalized SHA-256 of freeze revision 11 at its own path, confirmed byte-identical and untouched | `be96b32aa675b7b6e46eea30effb2dbb91c718dc68ba7ce36d4d627ad6058ee2` |
| `predecessor_package_sha256` | normalized SHA-256 of package revision 15 at its own path, confirmed byte-identical and untouched | `6821755722daf3bce622fe98eaf39124adb835c6854661143d79f48a943030d7` |
| `freeze_draft_sha256` | lowercase SHA-256 of normalized UTF-8 freeze-successor bytes after removing its binding table and revision-history section (freeze revision 12's own digest) | `d592b135d2d8a90024d48d1b8335321660e8d7f089873e48687707c760e3d3e9` |
| `implementation_package_sha256` | lowercase SHA-256 of normalized UTF-8 document bytes after removing this binding table and revision-history section (this document's own digest) | `ad886d261d2807bcc95264d05d6a385dc79cd2f0cad44e2b4f004531b8097d4f` |
| `dependency_lock_sha256` | lowercase SHA-256 of each dependency/lock input; unchanged from revision 15 | `pnpm-lock.yaml=b406b4c36c1e5304cf0c43b175c426d50aa3b43dc9a2bb81be357ea2b80b1665`; `backend/pyproject.toml=9ca3a54905d11fdb7f30a84356d23741f256b2115b254bcc9fba4efacdf17df6` |
| `manifest_sha256` | SHA-256 of `features/FEAT-003-multimodal-understanding/fixtures/p2-t4-fusion-v1/manifest-v1.json` bytes, once remediated | required once the remediated artifact exists; not bound to the pre-remediation bytes at `064ba62` |
| `cases_sha256` | SHA-256 of `features/FEAT-003-multimodal-understanding/fixtures/p2-t4-fusion-v1/cases-v1.json` bytes, once remediated | required once the remediated artifact exists; not bound to the pre-remediation bytes |
| `expected_sha256` | SHA-256 of `features/FEAT-003-multimodal-understanding/fixtures/p2-t4-fusion-v1/expected-v1.json` bytes, once remediated | required once the remediated artifact exists; not bound to the pre-remediation bytes, whose 16 `REJECTED` entries still carry the superseded V1 rejection identity |
| `final_evidence_sha256` | SHA-256 of final evidence manifest including all above and validator outputs | required when the future evidence bundle exists |

The freeze/package digest scopes exclude their own changing digest and revision lines.
The remediated fixtures and final evidence are intentionally absent from this
documentation-only successor; this is a deferred evidence-production gate, not an unresolved
contract semantic.

For reproducibility, normalize `CRLF` and lone `CR` line endings to `LF`; remove the
complete table beginning with the exact header `| Field | Required format | Current docs-only record |`
through the blank line immediately after its final row; remove the complete section
beginning at the exact heading `## 12. Revision history` through end of file; then
UTF-8 encode the remaining text and hash those bytes. The freeze digest uses the same
steps with its exact binding-table header and `## 13. Revision history` heading.

The future contract test must contain an independent, hand-authored schema-parity oracle for
`P2T4FusionInputRejectionV2` (superseding the `P2T4FusionInputRejectionV1` oracle entries in the
current checkpoint). It must list every field, requiredness/nullability, enum, literal,
cross-field invariant, rejection precedence, canonical sort key, and privacy rule. It must not
load a schema snapshot, serialize the implementation model, introspect implementation fields, or
generate expected schemas from `p2_t4_fusion.py`. Expected JSON is hand-authored and
independently reviewed from the freeze successor.

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

No mapping case is part of the seven-file T4 remediation scope. No third fused
result status is introduced; structural input errors use the separate safe rejection
type (now `P2T4FusionInputRejectionV2`) and never become a fused-result status.

## 9. Required independent reviews (not yet performed)

### Pass 1 - technical completeness

The reviewer must verify the active identities (fused-result unchanged, outer rejection now V2),
historical-versus-active wording, exact FEAT-018 rejection identities, complete fields,
per-segment matching and reset rules, short prefixes, duplicate/overlapping spans, mixed-span
suppression, ranking/null ties, canonical projection/bytes/IDs, evidence binding, independent
parity, and deterministic fixture coverage including the six new match-view scenarios. The
reviewer must exercise the rejection precedence (including the ASR-before-Vision order inside
admissibility), exact token sequences, empty-success case, one/both failure cases, the
Vision-failure-is-unaffected case (MV-2), and privacy rules — including that the observed
non-canonical token never appears anywhere — on paper before implementation. The reviewer must
also confirm that exactly 16 of the 42 existing fixture entries (the `REJECTED` ones) are
expected to change canonical bytes under remediation, and that the other 26 are expected to stay
byte-identical.

### Pass 2 - governance and security

The reviewer must verify:

- this package and its companion freeze successor remain `HOLD - NOT APPROVED` for
  independent review, not frozen or implementation-approved;
- revision 15 and freeze revision 11 remain byte-identical and untouched at their own paths;
- the seven remediation-implementation paths are exact, match the existing G2 allowlist, and are
  untouched by this docs-only successor;
- mapping remains `PROPOSED_NOT_ADOPTED`;
- no mapping module/test, preservation-envelope implementation, or mapping case is
  proposed for the Sprint-1 T4 core;
- no accidental authentication, provider, credential, endpoint, path, raw transcript,
  raw media, or real child-data content appears;
- the five MV-1 through MV-5 decisions match `approvals/TASK_APPROVAL.md` exactly;
- the separate successor-freeze decision and separate remediation-implementation approval
  remain explicit prerequisites.

### Review completion record

- Pass 1 technical/contract audit: **NOT YET PERFORMED.** This task authored the successor
  content only; independent review is a separate, required step.
- Pass 2 governance/security/scope audit: **NOT YET PERFORMED.**
- Neither review's completion is claimed by this document. Its authorship does not grant the
  successor-freeze decision or the remediation-implementation approval.

## 10. Validation and non-actions

This successor performs documentation authorship only. The required post-edit checks are:

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

Validation record for this docs-only successor task, run against the worktree at checkpoint
`064ba62f32f1ffb964bc2208577eb0650b98e26a` plus this task's documentation-only changes: see
`plan/P2_T4_MATCH_VIEW_REMEDIATION_PLAN.md` and the task's final report for the actual command
output. `validate_architecture.py` is expected to continue reporting exactly one pre-existing
violation in the unchanged `backend/src/sketch2life/application/services/backend_ai_workflow.py`
(Architecture Policy B baseline); this task makes no code change and that finding is unrelated to
the documentation-only `HOLD - NOT APPROVED` status.

## 11. Final task status

**HOLD - NOT APPROVED**

This status means this successor package is ready for independent review and then the owner's
successor-freeze decision. It does not mean the contract is frozen or that implementation may
begin.

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
| 14 | 2026-09-14 | Applied CF-B1 original-source certainty/primary-selection semantics and CF-B2 revision/digest reconciliation; status remains `HOLD - NOT APPROVED`, with no freeze or implementation approval. |
| 15 | 2026-09-14 | Clarified mutually exclusive certainty precedence for conflicting and null-confidence candidates and refreshed normalized digest bindings; no freeze or implementation approval. **Approved as G1 at commit `18d0c33d35431ca96a76692a68c6b992098699e7` on 2026-09-15, and its exact seven-file offline core was then separately approved as G2 and implemented/committed at `064ba62f32f1ffb964bc2208577eb0650b98e26a`. Revision 15 remains immutable history at its own path and is not edited by this or any later revision.** |
| 16 | 2026-09-15 | **Standalone successor** (this document, at a new path). Records the five MV-1..MV-5 match-view decisions; adds remediation-matrix row R-21 for the `VERIFIED_DEFECT` Vision match-view contract gap; synchronizes the companion freeze successor's new `P2T4.P2T4FusionInputRejectionV2@2.0` identity, the `POLICY_MATCH_VIEW_VERSION` field code, and the exact Vision `ADMISSIBILITY` rejection form; updates the evidence-binding table to the `064ba62` review base with predecessor-digest rows; documents that remediation changes the canonical bytes of the 16 existing `REJECTED` fixture entries while the 26 non-rejected entries stay byte-identical; leaves revision 15 byte-identical and untouched at its own path. Status remains `HOLD - NOT APPROVED`; no freeze or implementation approval is granted, and no independent review of it has yet occurred. |
