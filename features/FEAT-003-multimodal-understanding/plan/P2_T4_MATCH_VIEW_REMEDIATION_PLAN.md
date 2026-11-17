# P2-T4 Vision match-view contract-gap remediation plan

- Status: **ANALYSIS COMPLETE - OWNER DECISIONS RECORDED 2026-09-15 - SUCCESSOR CONTRACT FREEZE
  APPROVED 2026-09-15 - INDEPENDENT ERRATUM REVIEW COMPLETE/PASS 2026-09-16 - RENEWED CORRECTED
  BINDINGS APPROVED - FOUR-FILE STATUS SYNCHRONIZATION APPROVED - REMEDIATION-IMPLEMENTATION
  APPROVAL NOT GRANTED**
- Date: 2026-09-15
- Owner: Person 2
- Feature: FEAT-003 Multimodal understanding, task P2-T4
- Audit verdict: **VERIFIED_DEFECT** (frozen-semantic conformance gap; the remedy required owner
  interpretation and a successor freeze)
- Audited implementation checkpoint: `064ba62f32f1ffb964bc2208577eb0650b98e26a` (parent
  `d9a13d2c51a16702c705795a3c7b497b61d945c0`, the G2 approval-record commit)
- Immutable G1 freeze source: `18d0c33d35431ca96a76692a68c6b992098699e7`, containing
  `plan/P2_T4_CONTRACT_FREEZE_DRAFT.md` revision 11 (normalized SHA-256
  `be96b32aa675b7b6e46eea30effb2dbb91c718dc68ba7ce36d4d627ad6058ee2`) and
  `evidence/notes/P2_T4_IMPLEMENTATION_APPROVAL_PACKAGE_DRAFT_20260913.md` revision 15
  (normalized SHA-256 `6821755722daf3bce622fe98eaf39124adb835c6854661143d79f48a943030d7`).
  Both remain byte-identical and untouched, verified after this task's edits.
- Companion request: `plan/P2_T4_MATCH_VIEW_REMEDIATION_APPROVAL_REQUEST_20260915.md`. It was
  relocated from its prior ignored `evidence/notes/` path to this publishable `plan/` path; its
  status now reflects the successor-freeze approval, the PASS review, the renewed corrected
  bindings, and the four-file status synchronization below (remediation-implementation approval
  remains **NOT GRANTED**).
- **Owner decisions (recorded 2026-09-15 in `approvals/TASK_APPROVAL.md`): MV-1 = B, MV-2 = S2,
  MV-3 = T1, MV-4 = V2 (differs from this plan's own section 7 recommendation of V1 — the owner
  is entitled to select differently from a recommendation), MV-5 = standalone successor
  artifacts.** The successor documents implementing these decisions are
  `plan/P2_T4_CONTRACT_FREEZE_REVISION_12.md` (normalized SHA-256
  `d592b135d2d8a90024d48d1b8335321660e8d7f089873e48687707c760e3d3e9`) and
  `evidence/notes/P2_T4_IMPLEMENTATION_APPROVAL_PACKAGE_REVISION_16.md` (normalized SHA-256
  `ad886d261d2807bcc95264d05d6a385dc79cd2f0cad44e2b4f004531b8097d4f`). As issued, their own
  internal status text read `HOLD - NOT APPROVED`; that text is a historical artifact of their
  authoring date and, per the same convention already used for the original G1 freeze/package,
  is not edited in place. **The owner has since approved both documents** — the P2-T4 successor
  contract freeze ("G1 successor") is **APPROVED**, bound to all four normalized SHA-256
  identities (the two above plus the two immutable predecessor digests), recorded in
  `approvals/TASK_APPROVAL.md` ("P2-T4 successor contract-freeze approval", 2026-09-15) and
  cross-cited in `CONTEXT.md`, `DECISIONS.md`, `plan/PLAN.md`, and
  `plan/P2_T4_FUSION_RESEARCH_PLAN.md`. This is a **governance/freeze checkpoint, not an
  implementation checkpoint**: the exact-seven-file remediation implementation remains
  **NOT APPROVED / NOT STARTED**.
- **Digest-binding integrity defect (accepted 2026-09-16):** the normalized SHA-256 values that
  this document cites for freeze revisions 11/12 and package revisions 15/16 are legacy
  first-substring digests that bind only a prefix of each document. The owner accepted the finding
  and selected Option A (`approvals/TASK_APPROVAL.md`, 2026-09-16). The erratum
  `plan/P2_T4_DIGEST_BINDING_ERRATUM_20260915.md` records corrected normalized, raw-file, and Git
  identities were independently reviewed **COMPLETE/PASS**, and their corrected bindings received
  renewed **APPROVED** binding. The legacy values in this document are historical and
  non-canonical; the digest decision is **BINDING CORRECTION ONLY**. No implementation authority
  has been granted.

This document is the original contract and governance analysis. Sections 1-6 below (finding,
evidence, reproduction, rejection phase, and the token-comparator and MV-1 option comparisons)
are unaffected by which option the owner selected and remain the analytical record. Sections 7-12
described recommendations and a proposed strategy; where the owner's actual decision differs from
a recommendation (MV-4 = V2, not the recommended V1), this document is annotated rather than
silently rewritten, and the authoritative successor content is in the two documents named above.
This document itself is not a contract freeze, a successor freeze, an implementation approval, a
remediation approval, an evidence record, or a runtime authorization, and it still changes no
implementation, fixture, freeze, package, or approval file.

## 1. Finding and verdict

G1 freeze section 5.2 says this about the Vision envelope field `policy_match_view_version`:
"successful fusion requires the declared v2 match view". The upstream P2 Vision V1 contract
declares the canonical token `vision-policy-match-view-v2`, but it accepts any non-empty string in
that field, and the G3-G5 implementation performs no check. As a result, a schema-valid
`VisionUnderstandingSuccessV1` carrying any other non-empty match-view token reaches
`P2T4FusedResultV1.status=FUSED` through both service boundaries.

The verdict is **VERIFIED_DEFECT**. Every factual element of the finding was confirmed from the
committed bytes and reproduced locally. No owner record approves non-enforcement: the manifest
note "adds no Vision-side rejection" was an implementation-time choice, not an owner decision.

The root cause is a gap in the G1 contract, not only an implementation omission. G1 states the
requirement but gives it no pipeline placement, no closed rejection encoding, and no fixture
obligation. It also spells the policy token differently from the upstream token. A conforming fix
therefore cannot be derived from G1 alone, so the owner must decide the rejection semantics,
scope, token comparator, contract-version disposition, and successor-artifact strategy
(decisions MV-1 through MV-5 below). The existing G2 approval does not cover a fix, because any
fix needs semantics that G1 does not define.

## 2. Evidence (committed bytes at `064ba62`)

### 2.1 The frozen requirement and its missing encoding

| Location | Fact |
|---|---|
| `plan/P2_T4_CONTRACT_FREEZE_DRAFT.md:278` | `policy_match_view_version` / non-empty string / "successful fusion requires the declared v2 match view". |
| `plan/P2_T4_CONTRACT_FREEZE_DRAFT.md:277`, `:279` | The neighbouring rows read "retained through the source digest only" (`content_policy_version`) and "success requires `PASSED`". The contrast shows that row 278 was written as a requirement, not as digest-only provenance. |
| `plan/P2_T4_CONTRACT_FREEZE_DRAFT.md:120-152` | The terminal pipeline is `identity/version -> strict upstream-contract validation -> P2-T4 admissibility invariants -> correlation equality -> typed upstream status -> fusion`. Stage 3 requires "every T4-only invariant" but names only the ASR duplicate-index invariant. Strict validation is the upstream contract's own rules and is explicitly distinct from T4 admissibility. |
| `plan/P2_T4_CONTRACT_FREEZE_DRAFT.md:160-177`, `:179-197`, `:204-209` | The closed rejection vocabulary has no match-view field code. `ADMISSIBILITY` exists only in the exact ASR duplicate-index form, and `INVALID_STRUCTURE` is used for strict failures and "the T4 admissibility failure above" (singular). |
| `plan/P2_T4_CONTRACT_FREEZE_DRAFT.md:213-215` | T4 consumes the existing P2 V1 models and "does not widen or redefine them". |
| `plan/P2_T4_CONTRACT_FREEZE_DRAFT.md:412`, `:587` | The T4 policy literal is `vision_policy_match_view-v2` (with underscores), described as "the existing `vision_policy_match_view-v2` recipe". |
| `plan/P2_T4_CONTRACT_FREEZE_DRAFT.md:546-559` | The section 6.5 result invariants do not mention the match view. They list identity, strict-validation, and correlation rejections but omit admissibility. |
| `plan/P2_T4_CONTRACT_FREEZE_DRAFT.md:892-903` | The section 10.2 fixture coverage list contains no match-view case. |

### 2.2 Upstream permissiveness and producer path

| Location | Fact |
|---|---|
| `backend/src/sketch2life/contracts/schemas/vision.py:16` | `VISION_POLICY_MATCH_VIEW_VERSION = "vision-policy-match-view-v2"` (with hyphens). |
| `backend/src/sketch2life/contracts/schemas/vision.py:330` | `policy_match_view_version: str = Field(min_length=1)`, so any non-empty string validates. |
| `backend/src/sketch2life/contracts/schemas/vision.py:341-362` | The `VisionUnderstandingSuccessV1` validators check only `policy_execution_state=PASSED` and observation references. |
| `backend/src/sketch2life/application/ports/vision_content_policy.py:14-19` | `ObservableContentPolicyV1` is a replaceable protocol that exposes an arbitrary `policy_match_view_version` string. |
| `backend/src/sketch2life/infrastructure/ai/vision_lexical_policy.py:25-31`, `:38-40` | Only the lexical implementation enforces the canonical token, and only at construction time on the adapter side. |
| `backend/src/sketch2life/infrastructure/ai/fake_vision.py:66-74`, `:186-203` | The V1 adapter accepts any injected `ObservableContentPolicyV1`, copies its token into a `PASSED` success, and validates the result as `VisionUnderstandingSuccessV1`. A non-canonical token can therefore come from an in-repository code path, not only from hand-built payloads. |
| `backend/src/sketch2life/contracts/schemas/vision_v2.py:288`; `backend/tests/unit/test_raw_understanding.py:73`, `:109`; `backend/tests/unit/test_semantic_personalization_v2.py:167` | V2 has the same permissive field, and existing repository tests build schema-valid results with tokens such as `policy-view-v1` and `unit-view`. |

### 2.3 P2-T4 implementation

| Location | Fact |
|---|---|
| `backend/src/sketch2life/application/services/p2_t4_fusion.py:306-319` | `_admissibility_stage(asr)` checks only for duplicate ASR segment indexes. |
| `backend/src/sketch2life/application/services/p2_t4_fusion.py:322-337` | `_admit` runs ASR admissibility and then correlation. No Vision admissibility check exists. |
| `backend/src/sketch2life/application/services/p2_t4_fusion.py:340-369`, `:375-413` | `validate_and_fuse` and typed `fuse` both call `_admit`, and a success/success pair goes directly to `_fuse_successes`. The service never reads `vision.policy_match_view_version` or `policy.match_view_version`; the match-view recipe functions are used only at `:56-62`, `:480-485`, and `:554-592`. |
| `backend/src/sketch2life/contracts/schemas/p2_t4_fusion.py:252-265` | `P2T4FusionPolicyConfigV1.match_view_version: Literal["vision_policy_match_view-v2"]`. The value only feeds the policy hash. |
| `backend/src/sketch2life/contracts/schemas/p2_t4_fusion.py:105-114`, `:190-219` | The field-code enum has no match-view token, and the rejection validator forces every `ADMISSIBILITY` rejection into the exact ASR duplicate-index form. |
| `backend/tests/contract/test_p2_t4_contract.py:244-254`, `:701-710` | The oracle's closed field-code list has no match-view token, and one invariant asserts that a Vision-slot `ADMISSIBILITY` rejection is invalid. |
| `features/FEAT-003-multimodal-understanding/fixtures/p2-t4-fusion-v1/manifest-v1.json:30` | "Policy `match_view_version` is the frozen literal `vision_policy_match_view-v2`; T4 applies the existing vision-policy-match-view-v2 recipe once per segment/candidate text and adds no Vision-side rejection." |
| `features/FEAT-003-multimodal-understanding/fixtures/p2-t4-fusion-v1/cases-v1.json:17`, `:73` | The fixture policy uses the underscored literal, while the shared Vision envelope uses the hyphenated upstream token. No case varies the Vision token. |

## 3. Reproduction and failure scenario

### 3.1 Method

A scratch script outside the repository did the following:

1. Imported the committed fixture builders from `backend/tests/unit/test_p2_t4_fusion.py`.
2. Expanded the case `agreement-all-kinds` and overrode only the Vision
   `policy_match_view_version`.
3. Called the committed service.

The script ran in the backend development virtual environment (CPython 3.12.10) with bytecode
writing disabled. It printed only closed tokens, type names, booleans, counts, and field names,
and it wrote nothing to the repository. This is a reachability reproduction. It is neither G6
verification nor CPython 3.13.x canonicalization evidence. The focused P2-T4 test suite was
deliberately not run, so that no G6 activity occurred.

### 3.2 Results

| Vision `policy_match_view_version` | Upstream V1 schema | `validate_and_fuse` outcome | Output difference from the canonical-token run |
|---|---|---|---|
| `vision-policy-match-view-v2` (canonical baseline) | valid | `FUSED` | none |
| `vision-policy-match-view-v1` | valid | `FUSED` | only `source_vision_result_ref` (digest) |
| `unit-view` | valid | `FUSED` | only `source_vision_result_ref` (digest) |
| `vision_policy_match_view-v2` (the T4 policy literal) | valid | `FUSED` | only `source_vision_result_ref` (digest) |
| empty string | invalid | `REJECTED` `VISION`/`STRICT_VALIDATION`/`INVALID_STRUCTURE`/`NONE` | not applicable |

Typed `fuse()` with a typed non-canonical success also returned `FUSED` without raising. A Vision
failure (`PROHIBITED_CLAIM_DETECTED`, `BLOCKED`) carrying a non-canonical token returned
`UPSTREAM_FAILURE`. The normalized G1 freeze and package digests were recomputed from both the
working tree and `18d0c33`, and both match the approved values.

### 3.3 Failure scenario

1. A Vision V1 producer is configured with an `ObservableContentPolicyV1` other than the
   synthetic lexical policy, or with a future match-view revision.
2. It emits a `VisionUnderstandingSuccessV1` whose `policy_execution_state=PASSED` was evaluated
   under a different normalization recipe.
3. T4 matches narration under the v2 recipe, fuses the result, and returns `FUSED`.

Nothing in the fused output reveals the mismatch; the only change is the opaque source digest. A
reviewer therefore cannot tell that the upstream policy result and T4 matching used different
match views. This fails open against an explicit frozen requirement on a safety-adjacent
provenance field. The P2-T3 Phase B dossier already treats `policy_match_view_version` as a
provenance dimension across which results are never merged (`CONTEXT.md`, P2-T3 B0 dossier
summary).

## 4. Earliest correct rejection phase

The earliest correct phase is **`ADMISSIBILITY`**. The check runs after ASR admissibility and
before correlation equality and typed upstream status.

- **`IDENTITY_VERSION` is wrong.** That stage may inspect only closed identity, version, and
  discriminator values (freeze `:99-103`), and the match-view token is not part of family
  identity.
- **`STRICT_VALIDATION` is earlier but also wrong.** The value is valid under the upstream V1
  contract, and G1 forbids widening or redefining the upstream models (`:213-215`). G1 already
  separates a T4-only rule on a strictly valid input from strict validation: that is the ASR
  duplicate-index precedent (`:149-152`). Placing the check in strict validation would blame
  upstream malformation for the failure and move it ahead of ASR admissibility.
- **`ADMISSIBILITY` is correct.** It is the stage G1 defines for "every T4-only invariant" after
  strict validation.

The resulting precedence under the recommended success-only scope (S2):

| Inputs | Terminal outcome |
|---|---|
| duplicate ASR segment index + non-canonical Vision success | ASR `ADMISSIBILITY` / `DUPLICATE_SEGMENT_INDEX` (ASR is checked before Vision) |
| valid ASR + non-canonical Vision success + correlation mismatch | Vision `ADMISSIBILITY` (checked before correlation) |
| ASR typed failure + non-canonical Vision success | Vision `ADMISSIBILITY` (checked before typed status; today this is `UPSTREAM_FAILURE`) |
| valid ASR + non-canonical Vision failure | `UPSTREAM_FAILURE` under S2; Vision `ADMISSIBILITY` under S1 |
| empty or otherwise malformed Vision token | Vision `STRICT_VALIDATION`, unchanged |
| wrong family or version | `IDENTITY_VERSION`, unchanged |

The typed `fuse()` boundary would raise `P2T4FusionInputError` carrying the same rejection,
because it reuses `_admit`.

**Scope options (owner decision MV-2):**

- **S1 - check every Vision V1 result.** Both branches are checked. A `BLOCKED` prohibited-claim
  failure under a non-canonical view would become a closed rejection and lose its typed failure
  provenance.
- **S2 - check `VisionUnderstandingSuccessV1` only (recommended).** This matches "successful
  fusion requires" and mirrors the ASR invariant ("For `AsrSuccessV1`, ..."). Failures keep
  flowing to `UPSTREAM_FAILURE`, which never fuses Vision content.
- **Not recommended: a rule that fires only when both inputs succeed.** It would need a new
  cross-slot stage after typed status, which G1's pipeline does not have.

## 5. Token identity (owner decision MV-3)

The policy literal `vision_policy_match_view-v2` is not equal to the upstream token
`vision-policy-match-view-v2`. A scratch simulation over the 42 committed fixture cases (current
outcomes: 23 `FUSED`, 3 `UPSTREAM_FAILURE`, 16 `REJECTED`) measured how many outcomes each
comparator would change:

| Comparator | Changed outcomes under S1 | Changed outcomes under S2 |
|---|---|---|
| upstream `VISION_POLICY_MATCH_VIEW_VERSION` | 0 | 0 |
| naive `policy.match_view_version` | 27 (23 `FUSED`, 3 `UPSTREAM_FAILURE`, 1 correlation rejection) | 24 (23 `FUSED`, 1 `UPSTREAM_FAILURE`) |

- **T1 (recommended):** compare byte for byte with the upstream constant
  `VISION_POLICY_MATCH_VIEW_VERSION`, imported from `sketch2life.contracts.schemas.vision`. The
  frozen policy literal and policy hash stay unchanged. The successor freeze states explicitly
  that the policy literal names the recipe whose upstream declaration token is
  `vision-policy-match-view-v2`. No existing fixture outcome, digest, or policy hash changes.
- **T2:** change the policy literal to `vision-policy-match-view-v2` and compare against it. This
  changes `P2T4FusionPolicyConfigV1` and `fusion_policy_config_hash`. It also changes the
  canonical digest of all 26 non-rejected expected results, the contract-oracle literals, and the
  fixture policy.

Both comparators use exact string equality, with no trimming, casefolding, or Unicode
normalization.

## 6. Option comparison (owner decision MV-1)

Every option contradicts G1 revision 11 as written, so every option needs a successor freeze.
Under A1, A2, and B, the observed token is never echoed. A string supplied by an arbitrary policy
implementation could be unbounded or sensitive, and G1 section 4 forbids echoing such values.

| Aspect | A1: existing fields at `ADMISSIBILITY` | A2: existing fields at `STRICT_VALIDATION` | **B: new `POLICY_MATCH_VIEW_VERSION` field code (recommended)** | C: relax or remove the requirement |
|---|---|---|---|---|
| Rejection shape | `VISION`/`ADMISSIBILITY`/`INVALID_STRUCTURE`/`field_code=NONE`, P2 Vision identity, `observed_status=SUCCEEDED` | `VISION`/`STRICT_VALIDATION`/`INVALID_STRUCTURE`/`NONE` (already constructible) | `VISION`/`ADMISSIBILITY`/`INVALID_STRUCTURE`/`POLICY_MATCH_VIEW_VERSION`, P2 Vision identity, `observed_status=SUCCEEDED` | None; the input fuses. |
| Contract impact | Vocabulary unchanged. The rejection cross-field invariant is widened. Freeze sections 3, 4, 5.2, 6.5, 7.2, and 10.2 change. | No rejection-model change. Freeze sections 3 and 5.2 change the meaning of strict validation. | Adds one closed field code, following the same precedent as the 2026-09-14 `ADMISSIBILITY`/`DUPLICATE_SEGMENT_INDEX` additions. The invariant is generalized to two exact admissibility forms. Freeze sections 3, 4, 5.2, 6.5, 7.2, and 10.2 change. | The section 5.2 row becomes digest-only provenance and section 7.2 is clarified. No model change. |
| Schema (`contracts/schemas/p2_t4_fusion.py`) | Validator only | None | Enum member and validator | None |
| Service (`application/services/p2_t4_fusion.py`) | Vision check in admissibility | Vision check inside the strict stage | Vision check in admissibility | None |
| Tests | Replace the ASR-only admissibility invariant; add unit cases. | Unit cases only. | Oracle field-code list, precedence test, exact-form invariants, and unit cases. | None |
| Fixtures | New cases and expected results; manifest note, coverage, and binding. | Same as A1. | Same as A1. | Manifest note and binding only. |
| Effect on the 42 existing outcomes | Unchanged with T1 | Unchanged with T1 | Unchanged with T1 | Unchanged |
| Compatibility | No external consumer exists. A strict v1.0 rejection validator would reject the new instance. | The rejection is indistinguishable from malformed upstream input, and ASR admissibility loses precedence. | No external consumer exists. A strict v1.0 consumer would reject the unknown token and the new form. | Nothing breaks. |
| Diagnosability | The reason is hidden behind `NONE`, which becomes ambiguous if another Vision admissibility rule is ever added. | The phase is misattributed. | Self-describing. | The mismatch is invisible. |
| Privacy | Closed tokens only | Closed tokens only | Closed tokens only | No new output, but provenance fails open. |
| Relation to G1 | Enforces row 278 but contradicts section 4's exact admissibility form. | Contradicts section 3's distinction between strict validation and admissibility, and its precedence. | Enforces row 278 with G1's own admissibility mechanism. | Reverses row 278. |
| Fails closed? | Yes | Yes | Yes | No |

**Considered and excluded:** tightening upstream `VisionResultEnvelopeV1.policy_match_view_version`
to a literal. That would change the frozen P2-T3 V1 contract and its evidence baseline, which
P2-T4 has no authority to do: G2 and the research plan both exclude P2-T2/P2-T3 contract changes.

**Why B rather than the others:**

- A1 saves one enum token but still needs the same schema-invariant, test, and fixture edits. It
  encodes the reason implicitly through `NONE`, which becomes ambiguous if a second Vision
  admissibility rule is ever added.
- A2 has the smallest diff, but it puts the rule in the wrong phase and changes precedence.
- C leaves the fail-open behavior in place.

## 7. Contract-version disposition (owner decision MV-4) — **owner selected V2**

- **V1 - retain identities (this plan's recommendation).** Keep `P2T4.P2T4FusedResultV1@1.0` and
  `P2T4.P2T4FusionInputRejectionV1@1.0`, and issue a successor freeze that supersedes revision 11
  before anything consumes it.
  - This was justified because no G7 evidence, consumer, adoption, runtime, or P2-T5 use exists.
  - Repository precedent: the P2-T3 Phase A correction tightened the V1 Vision contract before
    consumption without changing its version.
  - Evidence must bind the successor's normalized digest, which distinguishes the two revisions.
  - The canonical bytes of the 42 existing expected results would not change.
- **V2 - bump the rejection identity — SELECTED.** The owner selected V2
  (`approvals/TASK_APPROVAL.md`, 2026-09-15). The rejection identity becomes
  `P2T4.P2T4FusionInputRejectionV2@2.0`, superseding V1 for every outer-boundary rejection — not
  only the new match-view case; the fused result stays at `P2T4.P2T4FusedResultV1@1.0`
  (unchanged). This is a repository precedent of a new major-named contract. It changes:
  - the canonical projection and digest of all 16 `REJECTED` expected results, including the 15
    unrelated to the match-view fix, because their `contract_name`/`contract_version` fields
    change;
  - the class name and literals in both code files and both tests;
  - the freeze identity table (section 2 of the freeze successor).

  V2 is the larger change than V1 would have been, but identity alone now pins the rejection
  semantics going forward. The full implementing content is in
  `plan/P2_T4_CONTRACT_FREEZE_REVISION_12.md` sections 1.0, 2, and 4.

## 8. Combination actually selected, and the issued successor-freeze strategy

The owner selected **B + S2 + T1 + V2** (`approvals/TASK_APPROVAL.md`, 2026-09-15), which differs
from this plan's own recommendation of B + S2 + T1 + V1 only in MV-4. Two standalone successor
documents (owner decision MV-5) were created and are now the authoritative successor content:

### 8.1 Successor artifacts (issued)

| Path | Content | Historical normalized SHA-256 | Current approval state |
|---|---|---|---|
| `features/FEAT-003-multimodal-understanding/plan/P2_T4_CONTRACT_FREEZE_REVISION_12.md` | A complete standalone successor to freeze revision 11, numbered revision 12. Own internal status text (issued, not edited in place): `HOLD - NOT APPROVED`. | `d592b135d2d8a90024d48d1b8335321660e8d7f089873e48687707c760e3d3e9` | **RENEWED CORRECTED BINDING APPROVED**; the listed legacy value is historical/non-canonical. |
| `features/FEAT-003-multimodal-understanding/evidence/notes/P2_T4_IMPLEMENTATION_APPROVAL_PACKAGE_REVISION_16.md` | A complete standalone successor to package revision 15, numbered revision 16. Same internal-status convention. | `ad886d261d2807bcc95264d05d6a385dc79cd2f0cad44e2b4f004531b8097d4f` | **RENEWED CORRECTED BINDING APPROVED**; the listed legacy value is historical/non-canonical. |

The documents' own internal status text (`HOLD - NOT APPROVED`) reflects their authoring date
and is a historical artifact only, per the same convention already used for the original G1
freeze/package; it is not the current gate state. The current gate state is **successor freeze
approved, independent erratum review complete/pass, renewed corrected bindings approved, four-file
status synchronization approved, and remediation implementation not approved/not started** (see
section 10 below).

Both digests were computed with the exact section 10.1/section 7 normalization algorithm,
reproduced independently twice with two differently coded implementations, and the algorithm
itself was cross-checked by re-deriving the already-approved revision-11/15 digests from the same
two implementations (both matched). The revision-11 and revision-15 files were verified
byte-identical against the immutable commit `18d0c33d35431ca96a76692a68c6b992098699e7` after this
task's edits, so every existing G1 citation and digest recomputation remains valid at HEAD.

**Correction note (historical issuance state, 2026-09-16; superseded for current status by
checkpoint `23992c54c8b19c0eb0a707ec0934599bddb97560`):** the digest method described in the
paragraph above was defective.
Both implementations located the revision-history heading with a first-substring search, which
matched an inline mention of the heading in each document's algorithm prose. The digests in this
table, and the revision-11/15 values they were cross-checked against, are therefore legacy values
that bind only a prefix of each document. The owner accepted this finding. The corrected identities
are recorded in `plan/P2_T4_DIGEST_BINDING_ERRATUM_20260915.md`. The erratum's issuance wording is
historical; its independent review is **COMPLETE/PASS** and the renewed corrected bindings are
**APPROVED** in the superseding governance records.

The alternative strategy for MV-5 (writing revisions 12/16 into the existing paths in a new
commit) was not used, per the owner's selection, because HEAD would then no longer match the G1
digests.

### 8.2 Successor-freeze changes actually made (recommended combination, with MV-4 = V2)

1. **Section 1(.0):** records the lineage (supersedes revision 11 at `18d0c33`, normalized
   SHA-256 `be96b32aa675b7b6e46eea30effb2dbb91c718dc68ba7ce36d4d627ad6058ee2`, never consumed),
   the reason for the successor, and the five MV-1..MV-5 decisions.
2. **Section 2:** the outer rejection identity row now reads
   `P2T4.P2T4FusionInputRejectionV2@2.0`, `contract_name="P2T4FusionInputRejectionV2"`,
   `contract_version="2.0"`; the fusion-output row is unchanged.
3. **Section 3, stage 3:** adds the exact invariant `For VisionUnderstandingSuccessV1,
   policy_match_view_version MUST equal "vision-policy-match-view-v2" exactly`, checked after the
   ASR invariant and before correlation/typed status; states it changes no upstream model, and
   that the typed `fuse()` boundary raises the same (now V2) rejection.
4. **Section 4:** every outer-boundary rejection form (identity/version, strict-validation, both
   `ADMISSIBILITY` forms, correlation) now carries `contract_name=P2T4FusionInputRejectionV2`,
   `contract_version=2.0`; adds `POLICY_MATCH_VIEW_VERSION` to the `field_code` allowlist and the
   exact Vision admissibility form; states `ADMISSIBILITY` is valid in exactly two forms and that
   the observed token is never echoed.
5. **Section 5.2 row:** replaced the requirement text with a pointer to the section 3 invariant.
6. **Sections 6.2 and 7.2:** state that the policy literal `vision_policy_match_view-v2`
   identifies the recipe, while the admissibility comparison uses the upstream declaration token.
7. **Section 6.5:** states that `FUSED` additionally requires every admissibility invariant to
   pass, and lists admissibility among the rejection sources.
8. **Section 10.1:** binding table with `review_base_commit`
   `064ba62f32f1ffb964bc2208577eb0650b98e26a`, `future_source_commit`
   `UNKNOWN_UNTIL_REVIEW_APPROVED_COMMITTED`, unchanged dependency digests, and new
   `predecessor_freeze_commit`/`predecessor_freeze_sha256`/`predecessor_package_sha256` rows
   binding the immutable predecessor.
9. **Section 10.2:** adds fixture coverage for match-view admissibility; ASR admissibility
   checked before Vision admissibility; Vision admissibility checked before correlation; a
   non-canonical Vision failure staying `UPSTREAM_FAILURE` (proving S2); and the policy-literal
   token itself being rejected because it is not the upstream token (proving T1). It also states
   precisely that all 16 existing `REJECTED` fixture entries change canonical bytes under V2,
   while the 26 non-rejected entries stay byte-identical.
10. **Sections 12 and 13:** carried a pre-review status at issuance; that issuance-state wording
    is historical and superseded for current status by checkpoint
    `23992c54c8b19c0eb0a707ec0934599bddb97560`, and a revision-12 history row was appended. Section
    numbering and headings were kept identical to the predecessor so the section 10.1 digest
    algorithm applies unchanged.

Package revision 16 received matching changes: the section 1 selected-semantics bullets now
state MV-4 = V2 and the new rejection identity; a remediation-matrix row `R-21`
(`RESOLVED_IN_FREEZE_DRAFT`) was added; the section 6 handoff bullets were updated to the V2
identity and the exact rejection forms; the section 7 binding table matches the freeze
successor's; and a revision-16 history row was appended.

## 9. Remediation implementation scope (updated for the actual V2 selection)

The remediation still uses exactly the existing seven G2 paths and adds no new implementation,
helper, evidence, or fixture path. Under the owner's actual MV-4 = V2 selection, the footprint is
larger than a pure addition would have been under V1:

| Path | Required change |
|---|---|
| `backend/src/sketch2life/contracts/schemas/p2_t4_fusion.py` | Rename `P2T4FusionInputRejectionV1` to `P2T4FusionInputRejectionV2` (`contract_name` literal `"P2T4FusionInputRejectionV2"`, `contract_version` literal `"2.0"`); add `P2T4RejectionFieldCode.POLICY_MATCH_VIEW_VERSION`; generalize `_requires_closed_consistency` to the two exact admissibility forms; refresh the freeze reference in the module docstring to cite revision 12. |
| `backend/src/sketch2life/application/services/p2_t4_fusion.py` | Every constructed rejection (all phases, not only admissibility) now builds a `P2T4FusionInputRejectionV2`; import `VISION_POLICY_MATCH_VIEW_VERSION` from `sketch2life.contracts.schemas.vision`; extend admissibility to run the ASR check then the Vision success check; keep `_admit` shared by both boundaries; `P2T4FusionInputError` now carries a `P2T4FusionInputRejectionV2`; refresh the module docstring. |
| `backend/tests/contract/test_p2_t4_contract.py` | Rename every `P2T4FusionInputRejectionV1` reference (imports, `MODELS`, `SAMPLES`, oracle literals/fields) to `P2T4FusionInputRejectionV2`/`"2.0"`; add the token to the oracle field-code list; add the Vision form to the phase/precedence test; replace "ADMISSIBILITY requires the ASR slot" with exact-form invariants. |
| `backend/tests/unit/test_p2_t4_fusion.py` | Update every fixture-driven and hand-written assertion that constructs or compares a `P2T4FusionInputRejectionV1` (imports and assertions) to `P2T4FusionInputRejectionV2`; verify typed `fuse()` raises `P2T4FusionInputError` carrying the new type for a non-canonical success; verify the observed token never appears in any output; verify precedence against ASR admissibility and correlation; verify a non-canonical failure stays `UPSTREAM_FAILURE`. |
| `features/FEAT-003-multimodal-understanding/fixtures/p2-t4-fusion-v1/manifest-v1.json` | Change `rejection_contract` from `"P2T4.P2T4FusionInputRejectionV1@1.0"` to `"P2T4.P2T4FusionInputRejectionV2@2.0"`; replace the line-30 note; add cases and coverage tags; rebind to the approved successor freeze/package digests and the remediation approval. |
| `features/FEAT-003-multimodal-understanding/fixtures/p2-t4-fusion-v1/cases-v1.json` | Add hand-authored cases: non-canonical success rejection, policy-literal token rejection, ASR admissibility before Vision admissibility, Vision admissibility before correlation, and a non-canonical failure. |
| `features/FEAT-003-multimodal-understanding/fixtures/p2-t4-fusion-v1/expected-v1.json` | **All 16 existing `REJECTED` entries' `result.contract_name`/`result.contract_version` change from `P2T4FusionInputRejectionV1`/`1.0` to `P2T4FusionInputRejectionV2`/`2.0`, and each entry's `canonical_sha256` must be recomputed** — this applies even to the 15 entries unrelated to the match-view fix, because the outer rejection type itself changed. Add hand-authored expected results for the new match-view cases. The 26 non-rejected (`FUSED`/`UPSTREAM_FAILURE`) entries must remain byte-identical, since neither their outcome nor their content references the outer rejection type. |

The following stay explicitly unchanged: `vision.py`, `vision_v2.py`, the content-policy port and
lexical policy, all adapters, FEAT-018 and FEAT-020 code, the B0 mapping, and every other fixture.
The service must not import from `sketch2life.infrastructure`, because Architecture Policy B allows
exactly one existing finding and no new ones.

Before the remediation checkpoint can be accepted, all of the following are required:

- focused P2-T4 tests;
- the full backend suite, reporting its actual pre-existing baseline;
- Ruff and strict mypy;
- the harness, repository-security, skeleton, and architecture validators, with architecture
  under Policy B (validator SHA-256
  `fa236c8d389b608251153d601fc370efe3f3e2479446ca4a56a3d395f892e0b5`, exactly one baseline
  finding);
- `git diff --check`;
- CPython 3.13.x canonicalization checks;
- an independent diff, contract, privacy, and governance review before a separate commit.

## 10. Gate reconciliation

| Gate | Current state |
|---|---|
| G1 (original) | Approved. Freeze revision 11 and package revision 15 at `18d0c33` remain immutable history; their normalized digests were recomputed after every later edit round and still match. |
| G2 | Approved (`approvals/TASK_APPROVAL.md`, 2026-09-15 G2 record; commit `d9a13d2`). Its scope is used up by the checkpoint and does not cover the remediation. |
| G3-G5 | The checkpoint exists: `064ba62` changes exactly the seven paths (parent `d9a13d2`). The gap is present in that checkpoint. There is no G4 review record in the repository, because evidence artifacts were not authorized. |
| Successor decisions (MV-1..MV-5) | **Recorded** in `approvals/TASK_APPROVAL.md`, 2026-09-15. |
| Successor documents (freeze revision 12 / package revision 16) | **Issued.** Their own internal status text (as authored) reads `HOLD - NOT APPROVED`; that text is a historical artifact and is not edited in place. |
| Successor-freeze approval ("G1 successor") | **APPROVED** — `approvals/TASK_APPROVAL.md`, "P2-T4 successor contract-freeze approval", 2026-09-15, bound to all four normalized SHA-256 identities (successor freeze `d592b135…`, successor package `ad886d26…`, immutable predecessor freeze `be96b32a…`, immutable predecessor package `68217557…`). This is a governance/freeze checkpoint only. |
| Digest-binding integrity defect | **Accepted** 2026-09-16 (`approvals/TASK_APPROVAL.md`); Option A selected. The four normalized identities cited in the row above are legacy first-substring digests and are historical and non-canonical. |
| Digest-binding erratum (`plan/P2_T4_DIGEST_BINDING_ERRATUM_20260915.md`) | **ISSUED / COMPLETE**; independent erratum review **COMPLETE/PASS**. The erratum remains byte-immutable. |
| Renewed corrected binding approval | **COMPLETE / APPROVED**. This is a binding correction only; successor semantics are **PREVIOUSLY APPROVED / UNCHANGED**. |
| Four-file renewed-binding status synchronization | **APPROVED / COMPLETE** at checkpoint `23992c54c8b19c0eb0a707ec0934599bddb97560`; documentation-only. |
| Remediation-implementation approval | **NOT GRANTED**. The seven-file remediation remains **NOT APPROVED / NOT STARTED**. |
| G6 | **PAUSED**. It will restart only on a separately approved remediation commit after implementation and independent review. |
| G7 | **PAUSED**. No evidence has been produced or authorized. |
| G8-G9 | **PAUSED**. |
| Runtime, integration, provider/model, GPU, Lightning, network, migration, production, live | **NOT APPROVED.** |

`P2T4.P2T4FusedResultV1@1.0` is unchanged by the successor-freeze approval. Predecessor
revisions 11/15 remain immutable historical artifacts.

## 11. Required order (steps 1-5c complete; remediation remains gated)

```text
1. owner reviews this analysis and the companion request                      [COMPLETE]
2. owner chooses MV-1 rejection semantics, MV-2 scope, MV-3 comparator,
   MV-4 version, MV-5 artifact strategy                                       [COMPLETE - MV-1=B, MV-2=S2, MV-3=T1, MV-4=V2, MV-5=standalone]
3. docs-only task issues the successor freeze and package revisions
   with normalized digests                                                    [COMPLETE]
4. independent successor-freeze review (technical/contract and
   governance/scope, including digest recomputation and predecessor
   byte-immutability)                                                         [COMPLETE - performed as part of the successor-freeze approval task]
5. owner approves the exact successor freeze commit, digests, and identity    [COMPLETE - OWNER APPROVED 2026-09-15, approvals/TASK_APPROVAL.md]
5a. independent review of the digest-binding erratum                          [COMPLETE / PASS]
5b. owner renewed binding decision on the corrected identities                [COMPLETE / APPROVED]
5c. four-file renewed-binding status synchronization                           [APPROVED / COMPLETE - this task]
6. owner separately approves the narrow implementation remediation for
   exactly the seven paths                                                     [NOT GRANTED]
7. fix schema, service, tests, and fixtures within those paths only            [NOT APPROVED / NOT STARTED]
8. independent review of the candidate tree, then a separate remediation
   commit                                                                      [NOT STARTED]
9. restart G6 on that commit, then G7, G8, G9                                  [PAUSED]
```

No step authorizes any later step. Completing steps 1-5c does not imply or grant step 6. The
successor-freeze approval (step 5) is a governance/freeze checkpoint only — it is not an
implementation approval and does not itself authorize touching any of the seven
remediation-implementation paths.

Steps 5a and 5b completed on 2026-09-16 after the owner accepted the digest-binding integrity
defect and selected Option A; step 5c records this exact four-file documentation status
synchronization at checkpoint `23992c54c8b19c0eb0a707ec0934599bddb97560`. The digests cited in step
5 are legacy first-substring values, while the renewed approval binds the corrected identities in
the immutable erratum. Steps 5a-5c grant no implementation authority. Step 6 remains **NOT
GRANTED**, step 7 remains **NOT APPROVED / NOT STARTED**, and G6-G9 remain **PAUSED**.

## 12. Non-actions of the successor-issuance task (historical)

This subsection describes the boundaries of the docs-only task that recorded the five MV-1..MV-5
decisions and issued the two standalone successor documents — a historical record, not the
current gate state (see section 10 above for current state). That task's authorized work was
recording the five decisions, issuing exactly the two new standalone successor documents,
relocating the match-view approval request to a publishable path, updating
`approvals/TASK_APPROVAL.md` with the decision/authorization record (not a freeze or
implementation approval at that time), reconciling gate-state wording in `CONTEXT.md`,
`DECISIONS.md`, `plan/PLAN.md`, and `plan/P2_T4_FUSION_RESEARCH_PLAN.md`, and one `.gitignore`
exception for the new package path. It did not edit the seven remediation-implementation paths,
the original freeze (revision 11), or the original package (revision 15) — both were verified
byte-identical against the immutable commit after its edits. It produced no G6 verification and
no G7 evidence, and it did not itself grant a successor-freeze approval or a
remediation-implementation approval. It made no commit, push, branch, or pull request, and
performed no runtime, provider, model, GPU, Lightning, network, migration, integration, or P2-T5
work.

**Since that task**, the owner separately approved the successor contract freeze (section 10
above); the remediation-implementation approval remains a separate, not-yet-granted action.

## P2-T4 renewed digest-binding approval after independent erratum review - 2026-09-16

- The independent erratum review is **PASS**. The four corrected normalized and raw-file SHA-256
  hashes were reproduced independently; their source paths, source commits, Git blob IDs, byte/line
  counts, and binding-table/heading ranges were verified against erratum sections 4.1-4.4 and 5.
  The immutable erratum raw-file SHA-256 `8975d94b0d9be8e78935b66e1e851493c1cff5b2f1b83cdf49acfe7f9929276e`
  and Git blob ID `4b7ed999fed45e176d57c395e63fe62e8f12accc` were verified.
- The owner renewed approval exactly as follows:

  > I approve the P2-T4 renewed digest-binding decision exactly as written above.

- The previously approved successor semantics include P2T4.P2T4FusedResultV1@1.0 and P2T4.P2T4FusionInputRejectionV2@2.0; they remain unchanged, with no semantic reapproval.
- No implementation authority is granted by this binding approval.
- Renewed corrected artifact bindings are **APPROVED** against erratum sections 4.1-4.4. The renewed
  approval binds the corrected normalized/raw/blob/source/path identity tuples in erratum section 4.
  The legacy first-substring digests are historical, non-canonical, and incomplete. The original
  freeze/package artifacts and the issued erratum remain byte-immutable; the erratum was not edited.
- This decision corrects bindings only. The successor semantics previously approved are unchanged,
  with no semantic reapproval. The exact governance checkpoint allowlist is the six existing
  governance documents plus the immutable erratum. Separately, the exact seven-path remediation
  allowlist from `064ba62f32f1ffb964bc2208577eb0650b98e26a` remains unchanged, and none of those
  seven remediation files was modified in this checkpoint.
- The seven-file remediation is **NOT APPROVED / NOT STARTED**. G6-G9 remain **PAUSED**.
  Integration, runtime, provider/model, GPU, Lightning, network, migration, production, and live
  execution remain **NOT APPROVED**.
- No future checkpoint commit SHA is written into tracked files. The executor will report the
  resulting local governance commit SHA in the final handoff. This renewal record is superseded for
  active status by the four-file synchronization record below; earlier records and the immutable
  erratum preserve the historical issuance state.

## P2-T4 four-file renewed-binding status synchronization - 2026-09-16

- **Current state:** erratum issued **COMPLETE**; independent erratum review **COMPLETE/PASS**;
  renewed corrected binding approval **COMPLETE/APPROVED**; successor semantics **PREVIOUSLY
  APPROVED / UNCHANGED**; digest decision **BINDING CORRECTION ONLY**; four-file status
  synchronization **APPROVED / COMPLETE** at checkpoint
  `23992c54c8b19c0eb0a707ec0934599bddb97560`.
- Remediation-implementation approval is **NOT GRANTED**; the seven-file remediation is **NOT
  APPROVED / NOT STARTED**. G6-G9 remain **PAUSED**.
- Integration, runtime, provider/model, GPU, Lightning, network, migration, production, and live
  execution remain **NOT APPROVED**. The next step is a separately approved remediation task; this
  record grants no implementation, evidence, or execution authority.
