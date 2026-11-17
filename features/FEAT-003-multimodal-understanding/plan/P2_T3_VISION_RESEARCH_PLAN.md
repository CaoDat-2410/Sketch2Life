# P2-T3 Qwen3-VL structured drawing understanding research plan

- Status: APPROVED — Phase A is implemented; Phase B is approved for the bounded B1–B5 scope in
  `evidence/notes/P2_T3_PHASE_B_APPROVAL_REQUEST.md`. All promotion remains separately gated.
- Owner: Person 2
- Parent plan: `PLAN.md`, revision 4, task P2-T3; allocation: `docs/adr/ADR-0006-parallel-sprint-allocation.md`, `features/FEAT-001-stack-and-team-plan/SPRINT_1_TASK_ALLOCATION.md`
- Input dependency: a `PASS` `MediaValidationResultV1` from P2-T1 for the immutable drawing reference
- Output boundary: provider-neutral `VisionUnderstandingResultV1` for P2-T4; never canonical meaning and never a Gate A decision
- Review record: `evidence/notes/P2_T3_VISION_CONSTRAINT_REVIEW.md`

## Approval status

The project owner explicitly approved P2-T3 Phase A on 2026-08-31 and the bounded Phase B B1–B5
scope on 2026-09-01. The authoritative record is `approvals/TASK_APPROVAL.md`;
`evidence/notes/P2_T3_PHASE_A_APPROVAL.md` records the Phase A decisions, and
`evidence/notes/P2_T3_PHASE_B_APPROVAL_REQUEST.md` records the Phase B decisions and constraints.
Phase B approval authorizes the real Qwen development study only within that dossier's explicit
scope. It does not authorize provider credentials, production/deployment, user-facing,
Integration Sprint, or Gate A use.

The approved Phase A scope was implemented on 2026-09-01; see
`evidence/notes/P2_T3_PHASE_A_IMPLEMENTATION.md` (`EV-003-T3-01`) for the delivered artifacts,
required-behavior-to-test mapping, and validation command results.

## Research question and decision to make

Can a vision-language model — the handbook baseline is Qwen3-VL-8B-Instruct — produce drawing
observations that are strictly structured, grounded in the image, and free of psychological
inference, reliably enough to feed deterministic fusion in P2-T4? The contract must hold that
boundary even when the model does not comply, so the primary deliverable of Phase A is the
contract and its failure behavior, not a model result.

A one-off cloud smoke test (Qwen3-VL-8B-Instruct on an NVIDIA L4 24GB against a synthetic shapes
image) was infrastructure reconnaissance only. It is not project evidence, not model selection,
and not approval; no evidence record exists for it in this feature, and none is claimed here.

## Scope, explicit non-goals, and the Phase A / Phase B boundary

**Phase A (approved and implemented):** freeze `VisionUnderstandingRequestV1`
and the discriminated `VisionUnderstandingResultV1`; define `VisionProfileCatalogV1` with
deterministic fake entries only; define `VisionUnderstandingPort` and the `ObservableContentPolicyV1`
boundary; implement a deterministic fixture fake adapter, the synthetic fixture manifest, and the
contract test suite; write feature-local evidence. No dependency install, no model weights, no
GPU/provider access, no live inference, no benchmark.

**Phase B (approved, bounded B1–B5 scope):** the real Qwen3-VL adapter, isolated runtime
configuration, weight/model provenance, exact-pinned dependencies, GPU preflight,
structured-output mapping measurement, and the controlled vision-only synthetic benchmark. Its
exact boundaries, V2 contract, safety limitation, and Lightning L4 compute cap are in
`evidence/notes/P2_T3_PHASE_B_APPROVAL_REQUEST.md`; Phase B does not authorize any promotion.

**Explicit non-goals in both phases of this task:** capture UI, Gate A UI or confirmation,
session/job state, FastAPI routes, queues, databases, object storage wiring, mobile integration,
provider credentials, and any real child data. Also out of scope: the standalone CLI and the
~20-fixture end-to-end multimodal report, which `SPRINT_1_TASK_ALLOCATION.md` assigns to P2-T5;
this plan's Phase B benchmark is narrowly scoped to vision profile evidence and does not replace
or duplicate that harness. No task identifier outside `P2-T1`..`P2-T5` is used.

## Contract baseline

### Reference and provenance value objects

An image reference is always **one nested object**, never a pair of flat fields:

```text
VisionImageReferenceV1:
  artifact_ref: str              # non-empty; never an absolute machine path
  sha256: str                    # lowercase, exactly 64 hexadecimal characters

ImageDerivationProvenanceV1:
  transform_name: str
  transform_config_version: str
  source_image_sha256: str       # must equal source_image_ref.sha256
  processing_image_sha256: str   # must equal processing_image_ref.sha256

VisionMediaValidationProvenanceV1:                 # the P2-T1 linkage
  validation_artifact_ref: str
  validation_artifact_sha256: str
  decision: Literal["PASS", "RECAPTURE"]
  validator_policy_version: str
```

`source_image_ref` is a `VisionImageReferenceV1` wherever it appears — on the request and on both
result branches — and its hash lives inside that object. Neither the request nor either result
branch carries a sibling flat hash field next to a reference. The only other place a hash string
appears is inside `ImageDerivationProvenanceV1`, where `source_image_sha256` and
`processing_image_sha256` exist solely to bind the derivation chain to the two references; they are
link assertions, not an alternative way to carry a reference's hash.

`VisionMediaValidationProvenanceV1` deliberately mirrors the shape P2-T2 already uses, but is
defined independently inside this feature's contracts: P2-T3 must not import from or depend on
P2-T2's modules. Unifying the two into one shared media-validation provenance contract is a
possible later refactor and would need its own approval; this plan does not assume it.

### Request boundary

```text
VisionUnderstandingRequestV1:
  contract_name: Literal["VisionUnderstandingRequestV1"]
  contract_version: Literal["1.0"]
  correlation_id: str                                        # no image content, no observation text
  source_image_ref: VisionImageReferenceV1                   # required, always populated
  processing_image_ref: VisionImageReferenceV1 | None        # Phase A: always null
  derivation_provenance: ImageDerivationProvenanceV1 | None  # Phase A: always absent
  media_validation: VisionMediaValidationProvenanceV1 | None
  requested_profile_id: VisionProfileId                      # closed catalog reference
```

Validation rules at request construction:

- `source_image_ref` is **always required and always populated in every phase**, including Phase A
  (from a synthetic image fixture that already carries a P2-T1 `PASS`). It always names the
  original, untouched image; no adapter may normalize, resize, crop, or overwrite it.
- `derivation_provenance` without `processing_image_ref` is rejected, and `processing_image_ref`
  without `derivation_provenance` is rejected. When both are present, the provenance hash chain must
  link back to `source_image_ref.sha256` and forward to `processing_image_ref.sha256`.
  **In Phase A, `processing_image_ref` is always `null` and `derivation_provenance` is always
  absent** — Phase A creates no working copy and no adapter may silently create one.
- `requested_profile_id` is a closed `VisionProfileId` value, never a free-form string. A raw
  unknown profile string is rejected deterministically at enum/request-schema validation, **before**
  `VisionUnderstandingPort` is invoked; that rejection is neither a `VisionUnderstandingFailureV1`
  nor `INPUT_NOT_VALIDATED`, and `profile_id` in every returned result is therefore always a
  resolved catalog entry.

  In Phase A the catalog contains an entry for every `VisionProfileId` member, so **no legal Phase A
  request can reach a catalog-miss**. `VisionProfileCatalogV1.resolve` still raises for an absent ID,
  but that path is a **defensive internal guard** covering future catalog/enum drift, not a branch a
  well-formed Phase A request can exercise. This plan does not add a reserved or test-only enum
  member to make it reachable — inventing an unusable member to satisfy a test would put a value in
  the contract that no caller may legitimately use.

`media_validation` is nullable at the schema level but is not optional in behavior: a request that
is otherwise well formed but carries no linked P2-T1 `PASS` produces the typed failure
`INPUT_NOT_VALIDATED` — a schema-valid `VisionUnderstandingFailureV1`, not a separate exception
type. It is a defensive second check only: the correct call path always gates on a P2-T1 `PASS`
first. This mirrors the convention already implemented for `AsrRequestV1` in
`backend/src/sketch2life/contracts/schemas/asr.py`, as a semantic precedent rather than a shared
dependency.

### Profile catalog and configuration hash

```text
VisionProfileId (StrEnum):                 # Phase A defines fake entries only
  FAKE_DETERMINISTIC_V1

VisionProfileV1:
  profile_id: VisionProfileId
  adapter_kind: Literal["DETERMINISTIC_FAKE"]        # Phase A: the only value
  task: Literal["structured_observation"]
  compute_profile: Literal["NONE"]                   # Phase A: no device is used
  timeout_seconds: float                             # strictly greater than 0
  structured_output_mode: Literal["STRICT_JSON_OBJECT"]
  adapter_version: str
  timeout_retry_policy: Literal["NEVER_RETRY"]

VisionProfileCatalogV1:
  contract_name: Literal["VisionProfileCatalogV1"]
  contract_version: Literal["1.0"]
  profiles: tuple[VisionProfileV1, ...]              # immutable; profile_id unique across entries
  resolve(profile_id) -> VisionProfileV1             # deterministic; raises when absent
```

Phase A contains **deterministic fake entries only**. No `model_identifier`, `model_revision`,
weight provenance, provider runtime version, GPU/compute descriptor, or Qwen placeholder entry
exists in the Phase A catalog — not even as an unusable stub. Real candidates are introduced only by
a future Phase B approval, additively.

`timeout_retry_policy` is typed as a single-value literal on purpose. It documents the policy
explicitly while making any retry-enabling value **unconstructible**, so it does not reopen the
timeout-retry question settled in the error matrix; widening it would require a separately approved
design that proves cancellation or worker cleanup.

```text
vision_profile_config_hash(profile) -> str
```

The hash is SHA-256 over the canonical JSON serialization of the **complete** `VisionProfileV1`
value — sorted keys, compact separators — covering every profile field and nothing else. It is
**computed from** the profile and stored on the result as `config_hash`; it is never a field inside
`VisionProfileV1` itself (which would be self-referential), and it never incorporates request data,
result data, observation text, or policy output.

```text
vision_profile_catalog_hash(catalog) -> str
```

A second, separate hash pins the **catalog snapshot**: SHA-256 over the canonical JSON
serialization of the complete `VisionProfileCatalogV1` value — its `contract_name`,
`contract_version`, and the full ordered tuple of profiles — with sorted keys and compact
separators. Like the profile hash it is computed from the catalog, is never a field inside
`VisionProfileCatalogV1` itself, and never incorporates request, result, observation, or
policy-output data.

The two hashes answer different questions and are not redundant. `config_hash` pins *which single
profile configuration produced this success* and is success-only, because a failed call may not
have used a profile's settings at all. `profile_catalog_hash` pins *which catalog snapshot resolved
this `profile_id`* and sits on the shared envelope, so a typed failure is still traceable to an
exact catalog content even though it carries no success-only provenance.

`profile_catalog_hash` is the **single** catalog-snapshot identifier on the result. No separate
catalog-version field is carried, because the hash already covers the complete canonical catalog
value — its contract name, its contract version, and every profile entry — so a second field would
be a redundant provenance value that could drift out of agreement with the hash. Both hashes come
from the adapter's constructor-injected static catalog, which is why the adapter can populate
`profile_catalog_hash` on an `INPUT_NOT_VALIDATED` result where nothing was inferred.

### Result boundary: a discriminated union

`VisionUnderstandingResultV1 = VisionUnderstandingSuccessV1 | VisionUnderstandingFailureV1`,
discriminated by `status` (`SUCCEEDED` / `FAILED`). It is not a flat schema with ambiguous optional
fields; a field belongs to the shared envelope, to the success branch, or to the failure branch.

**Shared envelope, required on both branches:**

```text
VisionResultEnvelopeV1:
  contract_name: Literal["VisionUnderstandingResultV1"]
  contract_version: Literal["1.0"]
  correlation_id: str                        # echoed from the request
  executed_at: datetime                      # timezone-aware
  source_image_ref: VisionImageReferenceV1   # unchanged from the request
  profile_id: VisionProfileId                # the resolved catalog entry
  profile_catalog_hash: str                  # vision_profile_catalog_hash(active_catalog)
  attempt_number: int                        # 0..2
  repair_attempted: bool
  content_policy_version: str
  policy_match_view_version: str
  policy_execution_state: Literal["NOT_EXECUTED", "PASSED", "BLOCKED"]
```

`source_image_ref` — the whole nested reference, artifact plus hash — is present on **every**
result, success and failure alike, including `INPUT_NOT_VALIDATED`.

`content_policy_version` and `policy_match_view_version` record the policy configuration that was
**active** for this call. They are always populated, including on results that never reached the
policy layer, because the configuration is known at construction; they are not by themselves a
claim that the policy ran. Whether it ran is carried separately by `policy_execution_state` (see
"Policy execution state" below).

**Success branch:** five observation collections — `entities`, `actions`, `relations`, `themes`,
and `ambiguous_regions` — as specified in "Candidate schema sketches" below, plus exactly two
provenance fields: `adapter_version` and `config_hash`. Each collection is a **required** field
that **may be empty**; omitting a collection is schema-invalid, while an empty collection is a
valid technical success. Confidence is carried per candidate; there is no result-level confidence
or uncertainty field.

**Phase A success carries only provenance that actually exists in Phase A.** `adapter_version` must
equal the resolved profile's `adapter_version`, and `config_hash` must equal
`vision_profile_config_hash(resolved_profile)`. There is **no** `model_identifier`, no
`model_revision`, and no `runtime_version` on a Phase A success — a deterministic fake has no model
and no provider runtime, so requiring those fields would force the fake adapter to fabricate model
provenance in order to produce any success at all. They are not present as nullable placeholders
either: no Phase A result may contain fake model provenance in any form, including `null` stand-ins.

Real-model provenance is a **Phase-B-only, separately approved additive contract change**. That
change must introduce an explicit model-provenance shape and decide any result-contract versioning
it requires at that time. This plan does not define, pre-approve, or reserve field names for that
future shape.

**Failure branch:**

```text
VisionProhibitedClaimCategory (StrEnum):   # exactly the six prohibited-claim categories
  PSYCHOLOGICAL_INFERENCE_CLAIM
  PERSONALITY_CLAIM
  DIAGNOSTIC_CLAIM
  MENTAL_STATE_CLAIM
  TRAUMA_CLAIM
  DEVELOPMENTAL_CLAIM

VisionNonPolicyErrorDetail (StrEnum):      # every other closed input/runtime/schema detail
  MEDIA_VALIDATION_NOT_PASSED
  MEDIA_VALIDATION_PROVENANCE_MISSING
  SOURCE_IMAGE_UNREADABLE
  SOURCE_IMAGE_HASH_MISMATCH
  MODEL_LOAD_FAILED
  DEVICE_UNAVAILABLE
  TIMEOUT_BUDGET_EXCEEDED
  TRANSIENT_RUNTIME_FAILURE
  PERMANENT_RUNTIME_FAILURE
  OUTPUT_MAPPING_FAILED
  DUPLICATE_OBSERVATION_ID
  REFERENCE_INTEGRITY_VIOLATION

VisionFailureDetail = VisionNonPolicyErrorDetail | VisionProhibitedClaimCategory

VisionUnderstandingFailureV1(VisionResultEnvelopeV1):
  status: Literal["FAILED"]
  error_code: VisionErrorCode        # closed enum
  error_detail: VisionFailureDetail  # closed union of two disjoint closed enums
  retryable: bool
```

The two closed sets are **disjoint**: no token appears in both, so a detail value alone identifies
which family it came from. The pairing is a structural invariant, enforceable as a validator:
`error_code == PROHIBITED_CLAIM_DETECTED` requires a `VisionProhibitedClaimCategory`, and **every
other** error code requires a `VisionNonPolicyErrorDetail`. No other combination is constructible.

`ProhibitedLexiconEntryV1.category` and a blocked result's `error_detail` are therefore the **same
closed type**, `VisionProhibitedClaimCategory` — a blocked result reports the matched entry's
category verbatim, and no mapping table between two parallel enums exists or is needed.

This split adds no new result field and discloses nothing further: a `BLOCKED` result still carries
only the category token, never the offending text, the derived match view, or the matched lexicon
entry itself.

`error_code` and `error_detail` come from closed enumerations only — never raw provider JSON, an
unbounded stack trace, a credential, or an endpoint URL. The failure branch never carries a
success-only field: no observation collection, no `adapter_version`, no `config_hash`, and no text
drawn from provider output.

Failure is traceable through the resolved `profile_id`, `profile_catalog_hash`, result contract
version, and policy configuration provenance. Every field that claim depends on is structurally
present on the shared envelope, so a failure needs no success-only provenance and must not borrow
any.

### Input integrity ownership

`VisionUnderstandingPort` is an **interface only**. It declares one method taking a
`VisionUnderstandingRequestV1` and returning a `VisionUnderstandingResultV1`. It never opens a file,
never reads image bytes, and never computes a hash — keeping filesystem access out of the port
keeps the application layer independent of infrastructure, per this repository's dependency rule.

All input verification happens at **adapter ingress**, before any inference attempt — the
deterministic fake in Phase A, a real model in Phase B — in this order:

1. resolve `requested_profile_id` against the injected static catalog;
2. verify the linked P2-T1 provenance exists and its `decision` is `PASS`;
3. open the source image and compare its computed SHA-256 against `source_image_ref.sha256`.

Any failure in steps 2 or 3 returns a typed `INPUT_NOT_VALIDATED` result with `attempt_number = 0`,
`repair_attempted = false`, and `policy_execution_state = NOT_EXECUTED` — never an uncaught
filesystem or hashing exception. This is the same ingress ordering the implemented
`FasterWhisperAsrAdapter` already follows for audio, reused here as a semantic precedent only.

The adapter receives its **static catalog** and its **active policy configuration** as constructor
dependencies. That is what lets it populate the complete shared envelope — including `profile_id`,
`profile_catalog_hash`, `content_policy_version`, and `policy_match_view_version` — even on a typed
input failure where nothing was inferred and the policy layer never ran. This is ordinary constructor
injection into the adapter; it is **not** dynamic per-request catalog injection (which would let one
`profile_id` validate differently at different call sites) and **not** port-owned file I/O.

**Strict schema everywhere.** Every provider-to-contract model in this feature is declared with
`extra="forbid"` (and frozen), matching `contracts/schemas/asr.py` and
`contracts/schemas/media_validation.py`. An unknown field at **any** nesting level — top level,
inside a candidate, or inside a nested value object — is rejected as `VISION_SCHEMA_INVALID` with
`OUTPUT_MAPPING_FAILED`. Unknown fields are never ignored, never retained, and never passed
through to P2-T4. The mirror rule applies to omissions: a **missing required field** — one of the
five success collections, or a candidate's `confidence` — is equally `VISION_SCHEMA_INVALID`, never
silently defaulted to an empty collection or to `null`.

### Text boundary

No unstructured free-form provider response, raw provider payload, SDK object, Markdown wrapper, or
provider rationale may become the public contract or cross the adapter boundary. Textual values are
permitted only inside explicitly declared structured fields — `label`, `predicate`, and `note` —
and those fields remain subject to schema validation, `ObservableContentPolicyV1`, provenance
requirements, and the taxonomy/label-language decision recorded as an open blocker below.

### Structured text and language declaration (proposed; blocker 2 is still open)

The convention below is the reviewed proposal for the open taxonomy/label-language blocker. It is
recorded here so the blocker can be decided against concrete wording; it is **not** an accepted
decision.

Every declared text field is an `ObservedTextV1`, not a bare string:

```text
ObservedTextV1:
  value: str                              # open text, normalized by vision-label-normalizer-v1
  language: TextLanguageDeclarationV1

TextLanguageDeclarationV1:
  status: Literal["DECLARED", "MIXED", "NOT_DETERMINED"]
  tags: tuple[str, ...]                   # each tag lowercase, 2..32 characters
  is_ground_truth: Literal[False] = False
```

`EntityCandidateV1.label`, `ActionCandidateV1.label`, `RelationCandidateV1.predicate`,
`ThemeCandidateV1.label`, and `AmbiguousRegionCandidateV1.note` all use this shape. The declaration
is attached **per text field, not per candidate**, because language is a property of a string; this
also makes the policy layer's target set structurally enumerable ("every `ObservedTextV1` in the
result") instead of a hand-maintained list of field names that a future field could silently miss.

`vision-label-normalizer-v1` is the only transformation applied to the stored `value`: Unicode NFC,
trim, and collapse of Unicode whitespace runs to a single `U+0020`. It performs **no** casefold, no
punctuation stripping, no diacritic removal (Vietnamese tone marks and `đ` are preserved), no
translation, no spelling correction, no synonym mapping, and no singular/plural normalization. The
stored value is the artifact; any caseless or otherwise derived comparison view is computed
separately and never written back — the same "raw preserved, derived view separate" split that
`DECISIONS.md` already records for `vi-asr-normalizer-v1`.

Language status semantics and validation:

| `status` | `tags` | Meaning |
|---|---|---|
| `DECLARED` | exactly one | The adapter declares this string is in one language |
| `MIXED` | two or more, pairwise distinct | Mixed-language text; never presented as single-language |
| `NOT_DETERMINED` | empty | Language unknown or not determinable — also the value for language-neutral text, proper names, symbols, and numerals |

`NOT_DETERMINED` is the safe default. Unknown and language-neutral are deliberately not split into
two states: forcing the adapter to distinguish them would itself be an unfounded inference, and
P2-T4's behavior is identical in both cases — assume no language.

Canonical tag handling: each tag is lowercased at the declaration boundary **before** any other
check; duplicates after that normalization are **rejected** as a validation error rather than
silently de-duplicated, because a duplicate is evidence of an adapter defect and silent coercion
would hide it (the same reject-don't-coerce stance as `AsrProfileCatalogV1`'s unique-profile-ID
validator); tag **order** carries no information and is normalized to ascending code-point order at
construction rather than rejected. The asymmetry is deliberate — normalize what is semantically
meaningless, reject what indicates a defect.

Canonical ordering guarantees deterministic serialization of the **result artifact**: two
content-equivalent declarations serialize byte-identically, so repeated runs of one fixture produce
identical output and round-trip tests are stable. `TextLanguageDeclarationV1.tags` are per-result
model output, **not** configuration: they do not participate in and cannot change a static
`vision_profile_config_hash`, which is computed from the profile alone.

`is_ground_truth` is fixed to `False` in the schema, following the `LanguageHintV1` precedent in
`backend/src/sketch2life/contracts/schemas/asr.py`. The declaration is adapter-declared metadata
about a text string — never verified fact, and never a statement about the drawing or the child.
P2-T4 must treat it as a non-authoritative matching hint: it may not require a language match in
order to match two observations, may not discard an observation because the status is
`NOT_DETERMINED`, must record in support/conflict provenance when the hint influenced a match, and
must never present a declared language as fact.

### Observation and reference model

`observation_id` is unique across the **entire** `VisionUnderstandingSuccessV1`, spanning all five
observation types — entity, action, relation, theme, and ambiguous region. The validator rejects
any duplicate regardless of candidate kind, so every reference resolves unambiguously.

| Reference field | Required? | Permitted target kinds | Explicitly forbidden targets |
|---|---|---|---|
| `RelationCandidateV1.subject_ref`, `object_ref` | Required | `ENTITY`, `ACTION` | `RELATION`, `THEME`, `AMBIGUOUS_REGION`; self-reference (`subject_ref == object_ref`) is rejected |
| `ActionCandidateV1.actor_ref`, `object_ref` | Optional | `ENTITY` | every other kind |
| `ThemeCandidateV1.evidence_refs` (min length 1) | Required | `ENTITY`, `ACTION`, `RELATION` | `THEME`, `AMBIGUOUS_REGION` |

Action endpoints are optional because an observable action may legitimately lack a confidently
attributable actor or object in a drawing; requiring them would pressure the adapter into
fabricating a linkage, which is the same failure mode the lossless-repair rule below prevents.

`AmbiguousRegionCandidateV1` carries `observation_id` and a `note` only. **It has no geometry in
Phase A** — no bounding box, mask, or coordinate convention is approved, and none is invented here.
Because it is not spatially grounded, it is **not a valid evidence target** for `evidence_refs` in
Phase A. Region geometry and region referencing require a separately approved
`AmbiguousRegionV1` design and can then be added additively.

Every reference violation — a dangling ID, a target of a forbidden kind, a self-referencing
relation, or a duplicate `observation_id` — is a `VISION_SCHEMA_INVALID` failure, never a silently
dropped field and never a `SUCCEEDED` result.

### Candidate schema sketches (Phase A)

All five models are frozen and declared `extra="forbid"`. `observation_id` follows the repository's
existing identifier convention (`^[a-z0-9-]+$`, as used by `AsrFixtureManifestEntryV1.fixture_id`
and `MediaFixtureManifestEntryV1.fixture_id`) and is unique across the whole result. Every text
field is an `ObservedTextV1` under the rules in "Structured text and language declaration". The
reference constraints are exactly those in the table above; nothing new is introduced here.

```text
VisionUnderstandingSuccessV1:                       # shared envelope fields omitted here
  status: Literal["SUCCEEDED"]
  entities: tuple[EntityCandidateV1, ...]           # required; may be empty
  actions: tuple[ActionCandidateV1, ...]            # required; may be empty
  relations: tuple[RelationCandidateV1, ...]        # required; may be empty
  themes: tuple[ThemeCandidateV1, ...]              # required; may be empty
  ambiguous_regions: tuple[AmbiguousRegionCandidateV1, ...]   # required; may be empty
  adapter_version: str        # equals the resolved profile's adapter_version
  config_hash: str            # equals vision_profile_config_hash(resolved_profile)
  # Phase A carries NO model_identifier, model_revision, or runtime_version —
  # a deterministic fake has none, and emitting them would fabricate provenance.
  # no result-level confidence or aggregate uncertainty field

EntityCandidateV1:
  observation_id: str            # ^[a-z0-9-]+$, globally unique in the result
  label: ObservedTextV1
  confidence: float | None       # REQUIRED field, nullable value; no default

ActionCandidateV1:
  observation_id: str
  label: ObservedTextV1
  actor_ref: str | None          # optional; when set, must resolve to an ENTITY
  object_ref: str | None         # optional; when set, must resolve to an ENTITY
  confidence: float | None       # REQUIRED field, nullable value; no default

RelationCandidateV1:
  observation_id: str
  predicate: ObservedTextV1
  subject_ref: str               # required; ENTITY or ACTION; != object_ref
  object_ref: str                # required; ENTITY or ACTION; != subject_ref
  confidence: float | None       # REQUIRED field, nullable value; no default

ThemeCandidateV1:
  observation_id: str
  label: ObservedTextV1
  evidence_refs: tuple[str, ...] # min length 1; each ENTITY, ACTION, or RELATION
  confidence: float | None       # REQUIRED field, nullable value; no default

AmbiguousRegionCandidateV1:
  observation_id: str
  note: ObservedTextV1
  # no geometry field in Phase A; no confidence field — see below
```

**Collection semantics.** All five collections are required and independently may be empty. A
missing collection is `VISION_SCHEMA_INVALID` with `OUTPUT_MAPPING_FAILED` — it is never treated as
an implicit empty collection, because "the adapter produced no entity" and "the adapter omitted the
entity field" are different facts and conflating them would let a malformed payload look like a
clean observation. All five being present and empty is a valid technical `SUCCEEDED`: it means the
pipeline ran to completion, the policy layer executed and passed, and no valid candidate was
produced. That is a legitimate outcome for a drawing the model could not describe within the
contract, and it must not be reshaped into a failure. In that case the policy layer still executes,
over an empty `ObservedTextV1` target set, and returns `PASSED` on that basis; this does not change
the metric-denominator rules already stated under "Provenance and metric comparability".

**Confidence and uncertainty semantics.** Confidence is **per candidate only**. Phase A defines no
result-level confidence or aggregate uncertainty score: any aggregate would be a derived number
with no agreed formula, and inventing one would fabricate a signal the model never produced — the
same prohibition the lossless-repair rule enforces.

On `EntityCandidateV1`, `ActionCandidateV1`, `RelationCandidateV1`, and `ThemeCandidateV1`,
`confidence` is a **required field with a nullable value** — declared without a default, so it is
always present in serialized output. Numeric values lie in the closed interval `0.0..1.0`. An
**omitted** `confidence` key is `VISION_SCHEMA_INVALID` and is never silently defaulted to `null`:
"the adapter reported no confidence" (`null`) and "the payload lacked the field" (malformed) are
distinct facts, and only the first is a valid observation.

`null` means **the adapter did not supply a confidence for this candidate**. It never means low
confidence. A consumer must not substitute `0.0` for `null`, must not treat `null` as ranking below
any supplied value, and must not compare a `null` against a numeric threshold — the same
"`NOT_MEASURED` is never `0`" discipline this plan applies to benchmark metrics and `DECISIONS.md`
already applies to the P2-T2 report.

Confidence is a model-declared signal about an observation candidate. It is not verified fact, not
a probability with any calibration guarantee, and never a psychological, clinical, developmental,
or diagnostic score. `AmbiguousRegionCandidateV1` deliberately carries **no** confidence field: it
declares that something could not be determined, so attaching a confidence to it would assert a
degree of belief about a non-determination.

No candidate field expresses canonical meaning, interpretation, or approval. The five models above
are the complete set of observation-bearing fields in `VisionUnderstandingSuccessV1`; any further
field requires a plan update and a new approval.

### Themes

`ThemeCandidateV1.label` is an **observable subject-matter motif** — for example nature, home,
family activity, or vehicles — and every theme must carry at least one `evidence_refs` entry
grounding it in observations present in the same result.

Psychological, personality, diagnostic, mental-state, trauma, and developmental interpretation
remains prohibited, in themes as in every other field. Labels such as abandonment, family conflict,
anxiety, depression, insecurity, trauma, or developmental delay are prohibited claims, not themes,
because they describe an inferred inner state rather than observable subject matter. This matches
the exclusion already recorded in `DECISIONS.md` and the `RawUnderstandingResultV1` constraint in
`PLAN.md`.

Visual-composition signals (dominant palette, symmetry, ink density, foreground/background ratio)
are a possible **separate future field**. They are not a replacement for `themes`, which `PLAN.md`
requires, and they are not in the proposed Phase A scope.

### Boundary with P2-T1

Vision-side diagnostics — low confidence, ambiguous regions, few or no observations — are model
diagnostics only. They never override P2-T1's `PASS`/`RECAPTURE` decision, never trigger a
self-initiated recapture, and never manufacture a failure in place of a typed result. Disagreement
between P2-T1's signals and P2-T3's observations is preserved as conflict/uncertainty evidence for
P2-T4, exactly as `DECISIONS.md` already requires for P2-T2's ASR diagnostics.

### Meaning of `SUCCEEDED`

`SUCCEEDED` is a **technical** status only: the output is schema-valid, referentially consistent,
provenance-preserving, and passed the known-violation policy layer. It is never canonical meaning,
never Gate A approval, and never a user-facing interpretation. P2-T4 may consume it only inside the
standalone fixture/controlled evaluation boundary that `PLAN.md` already defines for the
`T3 -> T4` dependency; the fused artifact remains "an AI proposal for future Gate A, never a
`CanonicalUnderstandingResult`".

## Safety boundary, policy limitation, and the Phase B semantic-safety gate

`ObservableContentPolicyV1` is defined as a replaceable port, not hard-coded to one matching
strategy, so a stronger mechanism can be layered in later without a breaking contract change. Its
Phase A implementation is a deterministic **known-violation lexical regression layer**: it rejects
values matching an approved closed list of prohibited terms/categories across every declared text
field (`label`, `predicate`, `note`).

**Stated limitation.** This layer is a regression check against violations that are already known
and enumerated. It is **not** a semantic-safety guarantee: a paraphrase of a prohibited
psychological claim that is absent from the approved list will not be detected by it. Nothing in
this plan should be read as claiming that lexical matching enforces the prohibited-claim boundary
in full. The design bias is to over-reject rather than under-reject, and the layer does not replace
human review at Gate A.

**Phase B semantic-safety gate (open, blocking for Phase B).** Before Phase B may be approved, the
project owner must decide how unknown paraphrases are handled. Candidate directions, none selected
here: (a) an approved second-pass semantic check, which needs its own dependency/model approval;
(b) mandatory human review before any real-model output leaves feature-local evidence; (c) a
narrower declared vocabulary that reduces the paraphrase surface. This gate blocks Phase B approval
and blocks any promotion of output to user-facing, Integration Sprint, or Gate A use. It does not
block the fake-only Phase A contract work, which never touches real model output.

**Execution order.** Schema validation (including any permitted lossless unwrap) runs first,
reference-integrity validation second, and `ObservableContentPolicyV1` last — so a structurally
invalid payload never reaches the policy layer, and a policy failure always describes an otherwise
valid structure.

**Non-disclosure.** A `PROHIBITED_CLAIM_DETECTED` failure carries a closed, non-sensitive category
token only. The offending source text is never echoed into the result, ordinary logs, or this
feature's `evidence/` directory.

### Derived match view and lexical match semantics (proposed; blocker 1 is still open)

The mechanics below are the reviewed proposal for the open lexicon-governance blocker, recorded so
the blocker can be decided against concrete wording. The **content** of the lexicon remains
undecided, and nothing here is an accepted decision.

`ObservableContentPolicyV1` never matches directly on `ObservedTextV1.value`. It matches on
**`vision-policy-match-view-v2`**, a versioned derived view computed in this exact order:

1. Unicode NFC;
2. collapse Unicode whitespace runs to a single `U+0020`, then trim;
3. casefold;
4. Unicode NFC again (casefold can leave the string denormalized);
5. map every character in Unicode category `P*` (`Pc Pd Ps Pe Pi Pf Po`) and `Z*`
   (`Zs Zl Zp`) to an ASCII space;
6. collapse the resulting whitespace runs to a single `U+0020`, then trim.

Unicode `S*` symbols (`Sm Sc Sk So`) are **content, not token boundaries**, and are left in place.
Vietnamese tone marks and `đ` are preserved at every step: in NFC they are letters (`L*`) or
combining marks (`Mn`), never `P*`/`Z*`, so they are never mapped to a boundary. The view performs
no translation, spelling correction, synonym expansion, stemming, diacritic stripping, or semantic
classification. It exists only in memory for comparison: it never modifies the stored
`ObservedTextV1.value`, is never a contract field, is never returned in a result, and is never
written to ordinary logs or `evidence/`.

Tokenization splits the view on the single ASCII space that step 6 guarantees. Only two match modes
exist, and **uncontrolled substring matching is forbidden**:

- `WHOLE_TOKEN_SEQUENCE` — the entry's token sequence appears as a contiguous, token-boundary-aligned
  subsequence of the field's token sequence. This is the proposed Phase A baseline, because a
  prohibited claim is commonly embedded inside a longer `note`, and it never matches inside a word;
- `WHOLE_FIELD` — the entry's token sequence equals the field's token sequence exactly.

The lexicon is a small versioned structure:

```text
ProhibitedLexiconEntryV1:
  term_normalized: str                       # stored already in the active match-view form
  category: VisionProhibitedClaimCategory    # the same closed enum a blocked result reports
  match_mode: Literal["WHOLE_TOKEN_SEQUENCE", "WHOLE_FIELD"]

ProhibitedLexiconV1:
  lexicon_version: str
  match_view_version: str
  entries: tuple[ProhibitedLexiconEntryV1, ...]
```

Entries are stored in the same match-view form as the field being compared, so matching is
symmetric. If a lexicon's declared `match_view_version` differs from the active view version, policy
construction fails deterministically as a configuration error — never a silent fallback, because an
entry normalized under a different view tokenizes differently and would silently corrupt matching.

**Deliberate consequences, recorded rather than hidden.** Mapping `P*` to boundaries means
underscores and hyphens become boundaries (`family_activity` tokenizes as `family activity`), and
punctuation *between* two phrase tokens no longer blocks a phrase match. This raises coverage for
known terms and slightly widens the false-positive surface for single-token entries that are common
words — a lexicon **content** consideration inside blocker 1, and consistent with the accepted
design bias of over-rejecting rather than under-detecting.

### Policy execution state

Carrying the active policy configuration on every result is **not** the same as claiming the policy
ran. A result rejected earlier in the pipeline — `INPUT_NOT_VALIDATED` at attempt `0`, a provider
failure, a timeout, or a schema/reference failure — never reaches the policy layer at all, because
the policy runs last (see "Execution order"). The shared envelope therefore carries one closed
field:

```text
policy_execution_state: Literal["NOT_EXECUTED", "PASSED", "BLOCKED"]
```

| Value | Exact meaning |
|---|---|
| `NOT_EXECUTED` | Processing ended before the policy layer; the policy did not inspect any text in this result |
| `PASSED` | The policy ran over every `ObservedTextV1` in the result and found no known violation |
| `BLOCKED` | The policy ran and blocked the result |

The value is fully determined by the outcome, so it is a structural invariant rather than prose:

| Outcome | Required `policy_execution_state` |
|---|---|
| `SUCCEEDED` | `PASSED` |
| `PROHIBITED_CLAIM_DETECTED` | `BLOCKED` |
| `INPUT_NOT_VALIDATED` | `NOT_EXECUTED` |
| `VISION_MODEL_UNAVAILABLE` | `NOT_EXECUTED` |
| `VISION_TIMEOUT` | `NOT_EXECUTED` |
| `VISION_PROVIDER_FAILURE` (transient and permanent) | `NOT_EXECUTED` |
| `VISION_SCHEMA_INVALID` | `NOT_EXECUTED` |

Equivalently, and enforceable as a validator: `status == SUCCEEDED` if and only if the state is
`PASSED`; `error_code == PROHIBITED_CLAIM_DETECTED` if and only if the state is `BLOCKED`; every
other failure is `NOT_EXECUTED`. No other combination is constructible.

`policy_execution_state` is a three-value status and nothing more. It never carries, and must never
be widened to carry, the matched text, the matched lexicon entry, a term count, or any excerpt —
`BLOCKED` results still disclose only the closed category token in `error_detail`.

**Provenance and metric comparability.** `content_policy_version` and `policy_match_view_version`
are recorded on **both** branches so that any result, blocked or not, is traceable to the policy
configuration that was active when it was produced; `policy_execution_state` then says whether that
configuration was actually applied. Measurements taken under different match-view versions are
different populations: a report must name the match-view version alongside
`known_policy_trigger_rate`, and must never merge or compare versions as one population without
naming both. A rate must also state its denominator population, since results with
`policy_execution_state = NOT_EXECUTED` were never inspected and cannot count as either a trigger or
a clean pass. Because Phase A is neither approved nor implemented, **no historic measurement
exists**; `vision-policy-match-view-v2` therefore supersedes the earlier v1 proposal at the planning
level only, and no data migration is implied.

## Typed error, retry, and repair matrix

### `attempt_number` and `repair_attempted` semantics

`attempt_number` counts adapter inference attempts — the deterministic fake in Phase A, a real
model invocation in Phase B. `repair_attempted` records whether the single permitted local
mapping repair was applied; a local repair never increments `attempt_number`. The canonical values:

- `INPUT_NOT_VALIDATED`: `attempt_number = 0` (rejected before any adapter call);
- ordinary first-attempt success, including a success reached through a permitted lossless fence
  unwrap: `attempt_number = 1`;
- success after exactly one transient-provider retry: `attempt_number = 2`;
- no path may produce a value above `2`.

### Lossless-only repair rule

The single permitted local repair is a **lossless unwrap**: removing a Markdown fence when the
content it encloses is already a complete JSON object that becomes schema-valid after the fence is
removed. Completing truncated JSON, closing delimiters, filling defaults, coercing enum values, or
inferring any value is prohibited, because it would fabricate observations that the model never
produced. Consequently:

- complete valid JSON inside a Markdown fence → `SUCCEEDED`, `repair_attempted = true`;
- truncated JSON, fenced or plain → `VISION_SCHEMA_INVALID`, `repair_attempted = false`;
- complete fenced JSON that still fails schema or reference validation → `VISION_SCHEMA_INVALID`,
  `repair_attempted = true`;
- plain JSON that fails schema or reference validation → `VISION_SCHEMA_INVALID`,
  `repair_attempted = false`.

### Matrix

Every `error_detail` in the first six rows is a `VisionNonPolicyErrorDetail`; only the last row's
tokens come from `VisionProhibitedClaimCategory`. The two sets are disjoint.

| Cause | `error_code` | Closed `error_detail` tokens | Retryable | `repair_attempted` | Max `attempt_number` | Owner |
|---|---|---|---|---|---|---|
| No linked P2-T1 `PASS`, missing provenance, unreadable source, or source hash mismatch | `INPUT_NOT_VALIDATED` | `MEDIA_VALIDATION_NOT_PASSED`, `MEDIA_VALIDATION_PROVENANCE_MISSING`, `SOURCE_IMAGE_UNREADABLE`, `SOURCE_IMAGE_HASH_MISMATCH` | No | Always false | `0` | Adapter ingress, before any inference attempt |
| Model/weights fail to load; device unavailable | `VISION_MODEL_UNAVAILABLE` | `MODEL_LOAD_FAILED`, `DEVICE_UNAVAILABLE` | No | Always false | `1` | Adapter, load time |
| Inference exceeds the configured timeout budget | `VISION_TIMEOUT` | `TIMEOUT_BUDGET_EXCEEDED` | **No, with no exception and no profile flag** | Always false | `1` | Adapter |
| Provider/runtime exception during inference, classified transient | `VISION_PROVIDER_FAILURE` | `TRANSIENT_RUNTIME_FAILURE` | Yes, at most once | Always false | `2` | Adapter |
| Provider/runtime exception during inference, classified permanent | `VISION_PROVIDER_FAILURE` | `PERMANENT_RUNTIME_FAILURE` | No | Always false | `1` | Adapter |
| Output cannot be mapped/validated: malformed or truncated JSON, missing required field, invalid enum, extra field, duplicate `observation_id`, or broken reference integrity | `VISION_SCHEMA_INVALID` | `OUTPUT_MAPPING_FAILED`, `DUPLICATE_OBSERVATION_ID`, `REFERENCE_INTEGRITY_VIOLATION` | No — the inference boundary is never re-invoked for this | True only after a lossless unwrap of complete fenced JSON; false otherwise | `1` | Adapter's local mapping/validation layer |
| Structure and references are valid, but a declared text field matches the approved prohibited lexicon | `PROHIBITED_CLAIM_DETECTED` | `PSYCHOLOGICAL_INFERENCE_CLAIM`, `PERSONALITY_CLAIM`, `DIAGNOSTIC_CLAIM`, `MENTAL_STATE_CLAIM`, `TRAUMA_CLAIM`, `DEVELOPMENTAL_CLAIM` | No | Always false | `1` | `ObservableContentPolicyV1` |

Every row above also carries the shared envelope, including `content_policy_version`,
`policy_match_view_version`, and the `policy_execution_state` value fixed for that outcome by the
table in "Policy execution state": `BLOCKED` for `PROHIBITED_CLAIM_DETECTED`, `PASSED` for a
`SUCCEEDED` result, and `NOT_EXECUTED` for every other row here.

The timeout row deliberately has no idempotent-retry escape hatch, and the vision profile contract
carries no flag that could enable one. `DECISIONS.md` already records why for P2-T2: a synchronous
upstream model call cannot be cancelled, so retrying while a timed-out worker may still be running
can overlap work, distort evidence, and exhaust device memory. That risk is at least as high for a
VLM. Any future timeout retry requires a separately approved design that proves cancellation or
worker cleanup.

Both retry and repair are enforced entirely inside the adapter. A caller must never add its own
retry on top of this table.

## Phase A fixture and contract-test matrix

Every case below runs with the deterministic fake adapter and synthetic fixtures, without a model,
GPU, network, mobile app, backend API, database, or queue.

| Invariant | Fixture cases |
|---|---|
| Attempt and repair semantics | complete fenced valid JSON → `SUCCEEDED`, attempt `1`, repair `true`; complete plain valid JSON → `SUCCEEDED`, attempt `1`, repair `false`; transient provider failure then success → `SUCCEEDED`, attempt `2`, repair `false`; transient provider failure then failure → `FAILED`, attempt `2`, repair `false`; truncated fenced JSON → `VISION_SCHEMA_INVALID`, attempt `1`, repair `false`; missing/failed P2-T1 provenance → `INPUT_NOT_VALIDATED`, attempt `0`, repair `false` |
| Unreadable source image | a synthetic manifest entry naming an image file that does not exist or cannot be opened → the **adapter** returns `INPUT_NOT_VALIDATED` with `SOURCE_IMAGE_UNREADABLE`, `attempt_number = 0`, `repair_attempted = false`, `policy_execution_state = NOT_EXECUTED`; no filesystem exception escapes |
| Source hash mismatch | a synthetic fixture whose on-disk bytes hash differently from `source_image_ref.sha256` → the **adapter** returns `INPUT_NOT_VALIDATED` with `SOURCE_IMAGE_HASH_MISMATCH`, `attempt_number = 0`, `repair_attempted = false`, `policy_execution_state = NOT_EXECUTED` |
| Port has no I/O | a structural test over `VisionUnderstandingPort`: the interface declares one request-to-result method and exposes no file, path, byte-reading, or hashing operation; a fake implementation satisfying it needs no filesystem access |
| Envelope on input failure | both input-failure cases above still carry every shared-envelope field — including the resolved `profile_id`, `profile_catalog_hash`, `content_policy_version`, and `policy_match_view_version` — proving the adapter's constructor-injected catalog and policy configuration are sufficient without any inference |
| Image reference round-trip | a nested `VisionImageReferenceV1` survives serialization unchanged on request, on `SUCCEEDED`, and on every failure branch; a test asserts the request and both result branches carry no flat hash field beside a reference, while `ImageDerivationProvenanceV1`'s two chain hashes remain intact |
| Invalid image reference | empty `artifact_ref`; uppercase hex, 63-character, and 65-character `sha256` → all rejected at schema validation |
| Derivation pairing | `processing_image_ref` without `derivation_provenance`, `derivation_provenance` without `processing_image_ref`, and a provenance whose hash chain does not link to both references → all rejected; Phase A fixtures never set either field |
| Catalog integrity | a catalog built with two entries sharing one `profile_id` → rejected; `resolve` returns the same entry deterministically across repeated calls and raises for an absent ID |
| Unknown profile string | a request built with a raw unknown profile string → deterministic enum/request-schema validation error before `VisionUnderstandingPort` is invoked, asserted as neither a `VisionUnderstandingFailureV1` nor `INPUT_NOT_VALIDATED`. The test does **not** claim a legal `VisionProfileId` value can miss the catalog: in Phase A every enum member has a catalog entry, so `resolve`'s absent branch is covered separately as a defensive guard by constructing a catalog that omits an entry directly |
| Config hash determinism | `vision_profile_config_hash` returns the same digest across repeated calls and process runs for one profile; changing **any** single profile field — including `timeout_seconds`, `structured_output_mode`, or `adapter_version` — changes the digest; the digest is absent from `VisionProfileV1` itself and unaffected by request, result, observation, or policy-output data |
| Phase A success provenance | a fake `SUCCEEDED` carries `adapter_version` equal to the resolved profile's `adapter_version` and `config_hash` equal to `vision_profile_config_hash(resolved_profile)`; changing a profile field changes the success `config_hash` accordingly |
| No fabricated model provenance | a fake `SUCCEEDED` contains no `model_identifier`, `model_revision`, or `runtime_version` key in its serialized form — not even as `null`; a payload attempting to supply any of the three is rejected by `extra="forbid"` as `VISION_SCHEMA_INVALID` |
| Failure excludes success provenance | every failure branch result carries neither `adapter_version` nor `config_hash`; supplying either is rejected by `extra="forbid"`, while `profile_id`, `profile_catalog_hash`, the result contract version, and the policy provenance fields still make the failure traceable |
| Catalog snapshot on both branches | every result — `SUCCEEDED` and each failure row, including `INPUT_NOT_VALIDATED` at attempt `0` — carries `profile_catalog_hash`, populated from the adapter's constructor-injected catalog without any inference; no separate catalog-version field exists on the result |
| Catalog hash determinism | `vision_profile_catalog_hash` returns the same digest across repeated calls and process runs for one catalog; adding a profile, removing a profile, reordering the tuple, changing any single profile field, or changing the catalog's own `contract_version` each change the digest; the digest is absent from `VisionProfileCatalogV1` itself and unaffected by request, image, result, observation, or policy-output data |
| Policy execution state | `SUCCEEDED` → `PASSED`; `PROHIBITED_CLAIM_DETECTED` → `BLOCKED`; each of `INPUT_NOT_VALIDATED`, `VISION_MODEL_UNAVAILABLE`, `VISION_TIMEOUT`, both `VISION_PROVIDER_FAILURE` classifications, and `VISION_SCHEMA_INVALID` → `NOT_EXECUTED`; no other status/state combination is constructible |
| Strict schema — unknown top-level field | provider output carrying an unrecognized top-level key alongside valid content → `VISION_SCHEMA_INVALID` with `OUTPUT_MAPPING_FAILED`; the key is neither retained nor passed through |
| Strict schema — unknown nested field | provider output whose entity/action/relation/theme/region object carries an unrecognized field, and one whose nested `ObservedTextV1` carries one → `VISION_SCHEMA_INVALID` with `OUTPUT_MAPPING_FAILED` in both cases |
| Required collections — all empty | all five collections present and empty → schema-valid `SUCCEEDED`, `policy_execution_state = PASSED`, attempt `1`; asserted as a legitimate outcome, never reshaped into a failure. The policy layer runs over an empty `ObservedTextV1` target set and returns `PASSED` on that basis |
| Required collections — one missing | a payload omitting `entities`, and separately one omitting each of `actions`, `relations`, `themes`, `ambiguous_regions` → `VISION_SCHEMA_INVALID` with `OUTPUT_MAPPING_FAILED`; a test asserts the missing collection is never defaulted to an empty tuple |
| Confidence presence | for each of `EntityCandidateV1`, `ActionCandidateV1`, `RelationCandidateV1`, and `ThemeCandidateV1`, a candidate omitting the `confidence` key → `VISION_SCHEMA_INVALID`; an explicit `confidence = null` on the same candidate → valid, and a test asserts the two cases are distinguishable rather than both arriving as `null` |
| Confidence values | `confidence = null`, `0.0`, and `1.0` all accepted and round-trip unchanged; `-0.1` and `1.1` rejected; a test asserts `null` is never coerced to `0.0` and never ordered below a supplied value; `AmbiguousRegionCandidateV1` has no confidence field to set, and supplying one is an unknown field → `VISION_SCHEMA_INVALID` |
| Global ID uniqueness | an entity and a theme sharing one `observation_id` → `DUPLICATE_OBSERVATION_ID` |
| Relation endpoints | valid entity–entity and entity–action; missing required endpoint; unknown ID; target of a forbidden kind (theme or ambiguous region); self-reference → all invalid cases `REFERENCE_INTEGRITY_VIOLATION` |
| Action endpoints | no refs at all (valid); valid entity ref; ref to a relation (forbidden kind) |
| Theme evidence | valid refs to an entity, an action, and a relation; ref to an ambiguous region (forbidden kind); ref to another theme (forbidden kind); unknown ID; empty `evidence_refs` |
| Text boundary | declared `label`/`predicate`/`note` values pass; a provider payload carrying unstructured commentary, an extra top-level key, or a Markdown wrapper as the contract is rejected — no SDK object, raw payload, or provider rationale crosses the boundary |
| Policy layer | compliant text passes; text matching the approved prohibited lexicon → `PROHIBITED_CLAIM_DETECTED` with a category token only, plus a test asserting the offending string never appears in the serialized result |
| Detail-set disjointness | a `PROHIBITED_CLAIM_DETECTED` result carries a `VisionProhibitedClaimCategory` and is rejected if given a `VisionNonPolicyErrorDetail`; every other error code is rejected if given a `VisionProhibitedClaimCategory`; a test asserts the two token sets share no member, and that a blocked result's `error_detail` equals the matched lexicon entry's `category` without any intermediate mapping |
| Language declaration | `DECLARED` with one tag, `MIXED` with two distinct tags, `NOT_DETERMINED` with none — all valid; `DECLARED` with zero or two tags, `MIXED` with one tag, and `NOT_DETERMINED` with any tag → validation error; duplicate tags including case-variant duplicates → rejected, never de-duplicated; reversed tag input serializes byte-identically to the canonical order; language tags leave a static `vision_profile_config_hash` unchanged |
| Match view — case | a known one-token term in lowercase, title case, and uppercase → the same closed category |
| Match view — punctuation | the same term followed by, wrapped in, or surrounded by common punctuation → the same category |
| Match view — phrase boundaries | a known multi-word phrase with punctuation at its boundaries, and with punctuation between its tokens → the same category |
| Match view — non-adjacent tokens | the same phrase with an unrelated token between its two tokens → no trigger |
| Match view — substring negative | a single-token entry such as `cam` against the field `camera` → no trigger; no in-word match is ever produced |
| Match view — Vietnamese diacritics | diacritic-bearing terms including `đ`, in lower and upper case, with adjacent punctuation → the same category, with diacritics intact in both the stored value and the derived view |
| Match view — `S*` symbols | a field containing `★` or `+` between tokens → the symbol does not create a token boundary |
| Match view — stored value immutability | for every policy case above, `ObservedTextV1.value` is unchanged: not casefolded, not punctuation-mapped; only the in-memory derived view differs |
| Match view — version mismatch | a lexicon declaring a different `match_view_version` than the active view → deterministic policy-construction failure, no fallback |
| Policy provenance propagation | every result, success and failure alike, carries `content_policy_version`, `policy_match_view_version`, and `policy_execution_state`; neither the source string nor the derived match view nor the matched lexicon entry appears in the result, logs, or evidence, and `policy_execution_state` exposes only its three-value status |
| Execution order | input that is both schema-invalid and would match the lexicon → resolves as `VISION_SCHEMA_INVALID` and never reaches the policy layer |
| Timeout and availability | simulated timeout → `TIMEOUT_BUDGET_EXCEEDED`, attempt `1`, no retry branch exists; simulated load failure → `VISION_MODEL_UNAVAILABLE` with `MODEL_LOAD_FAILED`, and simulated device unavailability → `VISION_MODEL_UNAVAILABLE` with `DEVICE_UNAVAILABLE`, both attempt `1` with no retry |
| Permanent provider failure | a fake outcome classified non-transient → `VISION_PROVIDER_FAILURE` with `PERMANENT_RUNTIME_FAILURE`, `retryable = false`, attempt `1`, repair `false` — asserting the transient retry branch is not taken |
| Provenance | `source_image_ref` and hash unchanged on every success and every failure row; schema round-trip for both branches; identical output across repeated runs of the same fixture |
| Scope shape | `VisionUnderstandingSuccessV1` carries no field expressing canonical meaning, Gate A approval, or user-facing interpretation |

## Phase B research work packages (approved B1–B5 scope; no promotion implied)

The B0 dossier is `evidence/notes/P2_T3_PHASE_B_APPROVAL_REQUEST.md` (`EV-003-T3-PLAN-04`),
approved on 2026-09-01 for exactly B1–B5. It refines V1 below in one respect the owner should note:
real-model provenance is proposed as a **new versioned V2 result contract** rather than as added
fields on the Phase A V1 contract, because adding even a `null`-valued field to `VisionProfileV1`
would change `vision_profile_config_hash` for an unchanged fake profile. The authoritative scope
and constraints are in `approvals/TASK_APPROVAL.md`.

**V1 — Reproducible candidate profiles.** Record model identifier and revision, weight provenance
and license, adapter and runtime versions, device class, precision, structured-output parameters,
timeout budget, and the configuration hash for every proposed catalog candidate. Surfacing any of
that model provenance on the **result** contract is an additive Phase-B contract change in its own
right: it must define an explicit model-provenance shape, decide any result-contract versioning it
needs, and be approved before use. Phase A's success contract deliberately has no such fields and
must not be given `null` placeholders for them in the meantime. No profile is frozen and no runtime
default is selected by this work package; that is a separate ADR and Integration Sprint decision.

**V2 — GPU preflight.** Preflight must invoke the real adapter — a real model load plus one
synthetic inference — not an isolated driver or CLI check. Load and device failures map to
`VISION_MODEL_UNAVAILABLE` with `MODEL_LOAD_FAILED` / `DEVICE_UNAVAILABLE`. Dependencies are
exact-pinned before install, with the rationale recorded in the ADR required by V5, following the
documented `faster-whisper`/CTranslate2 precedent.

**V3 — Structured-output mapping behavior.** Measure how the real model's output actually arrives:
rates of fenced output, truncation, extra keys, invalid enum values, and broken reference
integrity; the share rescued by the permitted lossless unwrap; and `known_policy_trigger_rate`.
Constrained decoding is treated as a mitigation, never as a guarantee.

**V4 — Benchmark design.** A held-out, versioned manifest of synthetic drawing fixtures with
immutable hashes. Measure: schema-valid result rate; typed-failure counts by code; entity, action,
and relation coverage/accuracy against a published matching rule; `known_policy_trigger_rate`;
per-stage p50/p95 latency with cold start reported separately; and peak device memory where the
environment exposes it.

Safety metric terminology is fixed to avoid overclaiming:

| Metric | Meaning | Measurability |
|---|---|---|
| `known_policy_trigger_rate` | Share of outputs that trigger the approved lexical regression policy | Measurable once a versioned lexical policy exists; always reported with both `content_policy_version` and `policy_match_view_version`, and never merged across match-view versions |
| `semantic_safety_coverage` | Coverage of an approved semantic-safety mechanism over the prohibited-expression space | `NOT_MEASURED` until both an approved mechanism and a dedicated held-out set exist |
| `semantic_safety_recall` | Share of true semantic violations detected on a labelled held-out set | `NOT_MEASURED` until both an approved mechanism and a dedicated held-out set exist |

`known_policy_trigger_rate` describes behavior against known violations only; semantic safety must
never be inferred from it. Unavailable measurements are reported as `NOT_MEASURED`, never as `0`
and never silently omitted — the same rule already applied to the P2-T2 Round-1 report. Evidence
interpretation must state that fixtures are synthetic and that no result is evidence about real
children's drawings.

**V5 — Review gate and recommendation.** One recommendation table comparing candidates on quality,
latency, runtime compatibility, operational risk, and known limitations. A profile may be proposed
for freeze only with reproducible configuration/provenance, schema-valid outputs, held-out results,
and an explicit reviewer decision recorded in an ADR. If evidence is insufficient, the fake profile
remains the only usable entry.

## Exit criteria

### A. Readiness to hold this plan as a reviewed research document

- [x] Every contract in the Phase A scope has a written schema sketch: the request, the shared envelope, both result branches, all five candidate types, the reference/provenance value objects, and the profile catalog. No field is mentioned in prose without a definition.
- [x] An image reference is one nested `VisionImageReferenceV1` everywhere; the request and both result branches carry no flat hash field beside a reference, and the only other hash strings are `ImageDerivationProvenanceV1`'s two explicit chain-link assertions.
- [x] `vision_profile_config_hash` is defined as SHA-256 over canonical JSON of the complete profile, computed from the profile rather than stored inside it, and excluding request, result, and policy-output data.
- [x] Every traceability claim is backed by a field that structurally exists on the branch making it: failure is traceable through the resolved `profile_id`, `profile_catalog_hash`, result contract version, and policy configuration provenance — all on the shared envelope — and `vision_profile_catalog_hash` is defined as SHA-256 over canonical JSON of the complete catalog, computed from the catalog rather than stored inside it. `profile_catalog_hash` is the single catalog-snapshot identifier; no redundant catalog-version field is carried on the result.
- [x] Phase A success provenance is limited to what exists in Phase A — `adapter_version` and `config_hash`, both derived from the resolved fake profile. No `model_identifier`, `model_revision`, or `runtime_version` appears on a Phase A result, not even as a `null` placeholder, so the fake adapter never fabricates model provenance; real-model provenance is deferred to a separately approved additive Phase B change whose shape this plan does not define.
- [x] Input integrity ownership is unambiguous: the port is interface-only with no file or hash operation, and the adapter verifies profile, P2-T1 provenance, and source hash at ingress, returning typed `INPUT_NOT_VALIDATED` at attempt `0`. The owner column, request prose, fixture matrix, and provenance wording all say the same thing.
- [x] Failure detail tokens are split into two disjoint closed enums — `VisionProhibitedClaimCategory` for the six prohibited-claim categories and `VisionNonPolicyErrorDetail` for every other token — combined as `VisionFailureDetail`, with the code-to-family pairing stated as a structural invariant and the lexicon entry's `category` typed identically to a blocked result's `error_detail`, so no parallel enums or mapping table exist.
- [x] No fixture claims a branch the contract cannot reach: Phase A's catalog covers every `VisionProfileId` member, so the unknown-profile case is stated as raw-string enum/schema rejection, and `resolve`'s absent branch is documented as a defensive guard covered by constructing an incomplete catalog directly rather than by a reserved enum member.
- [x] Every row of the typed error matrix has at least one corresponding row in the Phase A fixture matrix. The six `PROHIBITED_CLAIM_DETECTED` category fixtures must use only the synthetic, owner-approved lexicon governance below; completing their concrete fixture entries is an implementation acceptance criterion, never evidence of a semantic-safety guarantee.
- [x] The result contract is a discriminated union with no ambiguous shared-optional fields.
- [x] `VisionUnderstandingSuccessV1` and all five candidate types have complete Phase A schema sketches. The five observation collections are required and independently may be empty; a missing collection is `VISION_SCHEMA_INVALID`, an all-empty result is a valid technical success, and there is no result-level confidence or aggregate uncertainty field.
- [x] Confidence is per-candidate on entity/action/relation/theme as a required nullable field declared without a default, `0.0..1.0` inclusive, with `null` defined as "not supplied" and never "low confidence", an omitted key as `VISION_SCHEMA_INVALID` rather than an implicit `null`, and no confidence field on ambiguous regions. No candidate field expresses psychological inference or canonical meaning.
- [x] Every contract model is `extra="forbid"`, and unknown fields at any nesting level are `VISION_SCHEMA_INVALID` rather than ignored, retained, or passed through; a missing required field is equally `VISION_SCHEMA_INVALID` rather than silently defaulted.
- [x] Policy configuration provenance is separated from a policy verdict: `content_policy_version`/`policy_match_view_version` record the active configuration, while `policy_execution_state` records whether the layer ran, with one required value fixed per outcome and no leakage of matched text or lexicon entries.
- [x] `observation_id` uniqueness is global, and every reference field declares its permitted and forbidden target kinds identically everywhere.
- [x] The text boundary distinguishes prohibited unstructured provider output from permitted declared structured text fields.
- [x] `attempt_number` and `repair_attempted` follow one canonical rule, applied identically in the matrix and the fixture matrix.
- [x] Repair is lossless unwrap only; no path completes, infers, or adds a value.
- [x] Timeout never retries, and no contract field could enable a retry.
- [x] The safety layer is described as a known-violation regression check, never as a semantic-safety guarantee, with the Phase B gate recorded.
- [x] Benchmark safety metrics are named precisely, with `NOT_MEASURED` rules stated.
- [x] Declared text fields carry a non-ground-truth language declaration with `DECLARED`/`MIXED`/`NOT_DETERMINED`, canonical tag handling, and an explicit statement that per-result tags never alter a static `vision_profile_config_hash`.
- [x] The lexical match view, its token-boundary rules, its two match modes, its version-agreement requirement, and its provenance/metric-comparability rules are specified without claiming semantic coverage.

### B. Phase A approval decisions — accepted 2026-08-31

- [x] **Prohibited-lexicon governance:** Phase A uses a synthetic-only, deterministic, versioned lexical regression set. It may exercise only the six closed category identifiers already defined by this plan; it contains no real child data. The project owner is its reviewer. Every change to the category set, policy/match-view contract, or governance requires a new plan-and-approval review; any synthetic-entry change must bump `lexicon_version` and be recorded in feature-local evidence.
- [x] **Taxonomy and label-language:** `label`, `predicate`, and `note` remain open normalized structured text in Phase A, represented by the proposed `ObservedTextV1` / `TextLanguageDeclarationV1` value objects. Their language declaration is non-ground-truth and does not authorize translation, inference, or cross-modal semantic matching.
- [x] **Deferred region geometry:** `AmbiguousRegionCandidateV1` deliberately carries no geometry in Phase A and cannot be an evidence-reference target. Adding geometry is a future additive contract change requiring separate approval.

## Blocking decisions

### Phase A owner decisions — accepted

The three former Phase A blockers are resolved by the owner decisions in Exit criteria B and the
approval record. They constrain Phase A only; they do not broaden P2-T3 into a semantic-safety,
real-model, or integration capability.

### Phase B promotion blockers

1. **Semantic-safety mechanism for unknown paraphrases**, per the gate above.
2. **Phase B runtime and profile evidence decisions**: model identifier and revision, weight
   provenance and license, compute/precision profile, structured-output parameters, timeout budget,
   exact dependency pins, and the accompanying ADR.

The synthetic-only owner-review control and the bounded runtime/profile decisions now permit the
approved B1–B5 study. They still block promotion of output to user-facing, Integration Sprint, or
Gate A use until a separately approved semantic-safety mechanism and sufficient runtime/profile
evidence exist.

Both are carried into `evidence/notes/P2_T3_PHASE_B_APPROVAL_REQUEST.md` as explicit owner
decisions and constraints (D-1/D-2 for semantic safety and lexicon policy, D-3/D-4 for execution
location and model identity). The third former blocker — Phase A completion — is closed by
`evidence/notes/P2_T3_PHASE_A_IMPLEMENTATION.md` (`EV-003-T3-01`).

## Approved Phase A implementation scope

Freeze `VisionImageReferenceV1`, `ImageDerivationProvenanceV1`,
`VisionMediaValidationProvenanceV1`, `VisionUnderstandingRequestV1`, and the discriminated
`VisionUnderstandingResultV1` (shared envelope plus both branches) as described above, including
`ObservedTextV1`/`TextLanguageDeclarationV1` for declared text fields; define `VisionProfileV1`,
`VisionProfileCatalogV1` with deterministic fake entries only, `vision_profile_config_hash`,
`vision_profile_catalog_hash`, and
construction-time profile validation; define the interface-only `VisionUnderstandingPort` and the
`ObservableContentPolicyV1` port with one lexical regression implementation over
`vision-policy-match-view-v2` and a versioned `ProhibitedLexiconV1`; implement adapter-ingress input
verification and the typed error/retry/repair matrix inside a deterministic fixture fake adapter
that receives its catalog and policy configuration by constructor injection; add the synthetic
fixture manifest and the contract test matrix; write one feature-local evidence note. No dependency, model
weight, GPU, provider call, runtime configuration, CLI, API, UI, mobile, database, queue, storage,
or real child data.

The project owner approved this exact Phase A scope on 2026-08-31. Implementation met the
fixture/contract acceptance matrix and recorded feature-local evidence. Phase B was subsequently
approved for its bounded B1–B5 scope on 2026-09-01; that later approval does not broaden Phase A.

This scope was implemented on 2026-09-01 and met the fixture/contract acceptance matrix above;
see `evidence/notes/P2_T3_PHASE_A_IMPLEMENTATION.md` (`EV-003-T3-01`).

## Phase B B1 implementation status (2026-09-01)

The owner-approved Phase B B1 slice — local code/configuration and no-GPU tests only — is
implemented and recorded in `evidence/notes/P2_T3_PHASE_B_B1_IMPLEMENTATION.md`
(`EV-003-T3-02`) and ADR-0007. It adds disjoint V2 contracts and hashes, one static Qwen3-VL
candidate profile with immutable provenance, isolated runtime configuration, a lazy typed
adapter skeleton with a killable subprocess timeout boundary, an exact-pinned optional extra,
and the placeholder-only environment example. The frozen V1 module and fake path are unchanged.

B2 model/runtime verification, B3 synthetic fixture/ground-truth preparation, B4 execution and
benchmarking, and B5 reporting are not executed by this B1 change. No dependency or model was
installed/downloaded, and no profile freeze or runtime default was selected.

A B1 contract-consistency correction subsequently aligned the Qwen adapter's repair flag with the
fake adapter for complete fenced non-object JSON roots; its focused regression and final validation
are recorded in `EV-003-T3-02`.

## Phase B B2 environment setup status (2026-09-01)

The internal environment-readiness slice is implemented and recorded in
`evidence/notes/P2_T3_PHASE_B_B2_ENVIRONMENT_SETUP.md` (`EV-003-T3-03`). It verifies the explicit
ignored runtime configuration, exact profile-derived pins, CUDA/device index, BF16 capability,
normalized Lightning L4 class, local model presence, and immutable local snapshot metadata without
importing Transformers, loading weights, or running inference. Its sanitized result contains no
local path or raw provider data and structurally records `model_load_performed=false` and
`inference_performed=false`.

This setup result is not the V2 GPU preflight acceptance evidence. B2 still requires one real model
load and one synthetic inference through the adapter plus latency, VRAM, and worker/device cleanup
evidence. B3–B5 remain unexecuted by this setup slice.
