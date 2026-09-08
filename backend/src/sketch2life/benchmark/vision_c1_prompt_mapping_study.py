"""Internal (non-CLI) P2-T3 Phase B B3 Follow-up (C1): reviewed structured-output prompt.

C1 stays inside the already-approved B1-B5 Phase B scope: B3 is defined as the "structured-
output mapping study" in ``approvals/TASK_APPROVAL.md``, and ``QwenVisionAdapter`` has always
supported an explicit ``prompt``/``prompt_builder`` constructor seam
(``qwen_vision.py:_default_prompt_builder`` returns ``""`` precisely so a caller injects the
reviewed prompt explicitly). C1's only change from B3-C0 is exercising that existing seam with
one owner-reviewed static prompt; every frozen B1/B2/B3 constraint (single candidate profile,
greedy decoding, ``max_new_tokens=512``, 120-second ``NEVER_RETRY`` timeout, lossless-fence-
unwrap-only repair, ``CLASSIFY_ONLY``-default raw handling) is unchanged here.

The reviewed prompt is a **benchmark protocol configuration artifact**, never a
``VisionProfileV2`` field: it is injected explicitly per call by whatever constructs the real
``QwenVisionAdapter`` for a C1 run, and ``qwen_vision.py``'s ``_default_prompt_builder`` is never
touched by this module, so the adapter's default construction path stays exactly as empty as it
was for B3-C0.

Prompt-binding integrity is structural, not a documentation promise: :func:`run_c1_pass` never
accepts an already-built adapter. It accepts a :data:`C1AdapterFactory` -- a
``(prompt, on_raw_output) -> VisionUnderstandingPortV2`` callable -- and is the *only* caller of
that factory, always with the selected :class:`C1PromptProtocol`'s prompt text (``C1_PROMPT_V1``
by default, or another explicitly passed protocol) and ``collector.hook`` as the arguments. There
is no parameter through which a caller can hand ``run_c1_pass`` a pre-built adapter (whatever
prompt it happens to carry) and have it labeled with C1's prompt identity; the identity on
:class:`C1PassReport` is always the identity of the exact text the factory was actually called
with, because :func:`run_c1_pass` resolves and verifies that text against the protocol's declared
``(protocol_id, prompt_sha256)`` -- against the closed canonical allowlist of approved identities,
and against the text's own recomputed SHA-256 -- before the factory (or any fixture/provider
action) ever runs, raising :class:`C1PromptBindingError` closed on any mismatch. This is what
prevents a caller from constructing a :class:`C1PromptProtocol` that merely *claims* a canonical
``protocol_id``/``prompt_sha256`` pair while actually supplying different (or empty) text.
:func:`qwen_c1_adapter_factory` is the real production factory, constructing ``QwenVisionAdapter``
with the dispatched prompt injected explicitly -- ``_default_prompt_builder`` is never reached on
this path.

Only the safe identity helpers -- :func:`c1_prompt_protocol_id`/:func:`c1_prompt_sha256` for v1,
:func:`c1_prompt_protocol_id_v2`/:func:`c1_prompt_sha256_v2` for v2,
:func:`c1_prompt_protocol_id_v3`/:func:`c1_prompt_sha256_v3` for v3, and the shared
:func:`c1_prompt_schema_target` -- are safe to place in a report, log, or evidence artifact; this
applies equally to whichever protocol is actually selected for a given run. The prompt body
itself is returned only by :func:`c1_prompt_text` (v1), :func:`c1_prompt_text_v2` (v2), or
:func:`c1_prompt_text_v3` (v3), each of which exists to be passed to an adapter constructor --
never serialized, logged, or embedded in any dataclass defined below.

C1 reuses :func:`sketch2life.benchmark.vision_b3_mapping_study.run_b3_mapping_study` unchanged,
including its own default eight-fixture builder (the same eight deterministic geometric
synthetic B3 fixtures -- never B4's separate, owner-approved held-out set, which this module
neither reads nor writes), its real per-fixture P2-T1 gate, its one-call-per-fixture-no-retry
loop, its ``CLASSIFY_ONLY``-default raw-output collector, and its scratch cleanup. This module
only adds the C1 prompt-identity wrapper (:func:`run_c1_pass`) and the pre-registered,
owner-confirmed mapping-readiness gate (:func:`evaluate_c1_readiness`) applied to two independent
passes (``C1_PASS_1``, ``C1_REPEAT_1``) -- never pooled into a combined denominator, matching this
project's standing no-pooling rule for distinct benchmark runs (B3-C0 vs. C1; ASR Round-1 vs. its
repeat run).

Registering a reviewed prompt identity here is not the same as authorizing it to run here.
:data:`C1_PROMPT_V3` is registered for **reviewed identity and binding verification only**: it
carries its approved protocol ID, text, and SHA-256, and is on the canonical binding allowlist,
but it is deliberately excluded from :data:`_C1_EXECUTION_ELIGIBLE_PROMPT_IDENTITIES`, so
:func:`run_c1_pass` and :func:`evaluate_c1_readiness` both fail closed on it with
:class:`C1PromptOutOfExperimentScopeError`. Its live execution awaits its own separately approved
runner, run labels, and newly authored fixture package -- none of which exists in this module.

Gate rule (owner-confirmed before any GPU execution, not derived from output after the fact):

- ``mapping-valid`` = ``SUCCEEDED`` or ``PROHIBITED_CLAIM_DETECTED`` (both prove the raw output
  mapped onto the strict V2 JSON contract; a policy block is a content decision made *after*
  successful mapping, not a mapping failure).
- Each pass independently needs ``>=7/8`` mapping-valid results.
- Systemic truncation is ``truncated_count >= 2/8`` in either pass.
- Config drift (mismatched profile/catalog/prompt identity between the two passes, or either
  pass not carrying the expected C1 protocol), an input-integrity failure, or a runtime/device
  failure in either pass blocks readiness outright, independent of the numeric threshold.
- Systemic truncation blocks readiness too, but must never be read as license to widen
  ``max_new_tokens`` or the repair/parser rule here: that needs its own separately approved
  amendment after a static token-budget analysis, never a silent in-place patch mid-run.
- Each pass must establish *exactly* eight attempted runs and exactly eight run records before
  any numeric readiness logic applies at all. A malformed/partial report (e.g. seven attempted
  runs, or ``attempted_runs`` disagreeing with the number of run records) can never pass on the
  strength of a numerator alone -- it is rejected with ``C1BlockingReason.INCOMPLETE_RUN_SET``,
  a module-local reason, never a new public V1/V2 token.

This module never runs a GPU/model/provider call, installs a dependency, touches
``.vision.env``, changes a V1/V2 public contract, changes decoding/timeout/retry/repair/parsing,
or reads/writes B4's held-out fixtures.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from hashlib import sha256
from pathlib import Path
from typing import Literal

from sketch2life.application.ports.vision_content_policy import ObservableContentPolicyV1
from sketch2life.application.ports.vision_understanding_v2 import VisionUnderstandingPortV2
from sketch2life.benchmark.vision_b3_mapping_study import (
    B3MappingStudyReport,
    B3RawOutputCollector,
    run_b3_mapping_study,
)
from sketch2life.contracts.schemas.vision import VisionErrorCode
from sketch2life.contracts.schemas.vision_v2 import (
    VisionNonPolicyErrorDetailV2,
    VisionProfileIdV2,
    vision_profile_catalog_hash_v2,
    vision_profile_catalog_v2,
)
from sketch2life.infrastructure.ai.qwen_vision import (
    QwenGenerationRunner,
    QwenVisionAdapter,
    RawOutputHook,
)
from sketch2life.infrastructure.ai.qwen_vision_runtime_config import QwenVisionRuntimeConfig

C1RunLabel = Literal["C1_PASS_1", "C1_REPEAT_1"]

C1AdapterFactory = Callable[[str, RawOutputHook], VisionUnderstandingPortV2]
"""Builds the adapter for one C1 pass from an explicit prompt and raw-output hook.

``run_c1_pass`` is the only caller of a ``C1AdapterFactory`` and always supplies the selected
:class:`C1PromptProtocol`'s prompt text (``C1_PROMPT_V1``'s ``c1_prompt_text()`` by default, or
another protocol's text when one is explicitly passed) and ``collector.hook`` as its two
arguments -- there is no other way to produce a :class:`C1PassReport`. A test fake matching this
signature can observe and assert the exact prompt/hook it was dispatched, which is what ties a
report's prompt identity to what the adapter actually received rather than to an unverified
caller claim.
"""

_C1_PROMPT_PROTOCOL_ID = "vision-v2-structured-output-prompt-v1"
_C1_PROMPT_SCHEMA_TARGET = "VisionUnderstandingResultV2"

_C1_PROMPT_LINES: tuple[str, ...] = (
    "Return exactly one compact JSON object and nothing else. Describe only directly "
    "observable visual content; do not infer personality, emotion, intent, "
    "symbolic/story/canonical meaning.",
    "Root keys must be exactly entities, actions, relations, themes, ambiguous_regions; "
    "all are arrays and no other keys exist.",
    "Use [] when empty. Maximum: 3 entities, 1 action, 1 relation, 1 theme, 1 ambiguous "
    "region. Prefer fewer. Text values are 1-3 lower-case English words. Every confidence "
    "is null.",
    "IDs are globally unique and match ^[a-z0-9-]+$.",
    'Every label/predicate/note is {"value":"...","language":{"status":"DECLARED",'
    '"tags":["en"]}}.',
    "Entity keys: observation_id,label,confidence.",
    "Action keys: observation_id,label,actor_ref,object_ref,confidence; refs are entity "
    "IDs or null.",
    "Relation keys: observation_id,predicate,subject_ref,object_ref,confidence; refs are "
    "distinct entity/action IDs.",
    "Theme keys: observation_id,label,evidence_refs,confidence; evidence_refs contains "
    ">=1 entity/action/relation ID.",
    "Ambiguous-region keys: observation_id,note only; it is never referenced and has no "
    "confidence/geometry.",
    "Prefer unfenced compact JSON. No prose, comments, duplicate keys, metadata, "
    "type/kind/description/bbox/geometry fields, trailing commas, or non-JSON values.",
)

_C1_PROMPT_TEXT = "\n".join(_C1_PROMPT_LINES)

_MIN_MAPPING_VALID_COUNT = 7
_SYSTEMIC_TRUNCATION_THRESHOLD = 2
_EXPECTED_ATTEMPTED_RUNS = 8

_RUNTIME_OR_DEVICE_ERROR_CODES = frozenset(
    {
        VisionErrorCode.VISION_MODEL_UNAVAILABLE.value,
        VisionErrorCode.VISION_TIMEOUT.value,
        VisionErrorCode.VISION_PROVIDER_FAILURE.value,
    }
)
_INPUT_INTEGRITY_ERROR_DETAILS = frozenset(
    {
        VisionNonPolicyErrorDetailV2.SOURCE_IMAGE_UNREADABLE.value,
        VisionNonPolicyErrorDetailV2.SOURCE_IMAGE_HASH_MISMATCH.value,
    }
)

_DEFAULT_C1_FIXTURES_DIR: dict[C1RunLabel, Path] = {
    "C1_PASS_1": Path("data/runtime/vision-c1-pass-1"),
    "C1_REPEAT_1": Path("data/runtime/vision-c1-repeat-1"),
}


def c1_prompt_protocol_id() -> str:
    """Safe identifier: fine for any report, log, or evidence artifact."""

    return _C1_PROMPT_PROTOCOL_ID


def c1_prompt_schema_target() -> str:
    """The V2 result contract this prompt is written against. Safe to persist."""

    return _C1_PROMPT_SCHEMA_TARGET


def c1_prompt_sha256() -> str:
    """SHA-256 of the canonical prompt text. Safe to persist; the text itself is not."""

    return sha256(_C1_PROMPT_TEXT.encode("utf-8")).hexdigest()


def c1_prompt_text() -> str:
    """The reviewed static C1-v1 prompt body, for adapter-construction injection only.

    This is the one function in this module that returns the v1 prompt body. Callers must pass
    it straight into ``QwenVisionAdapter(..., prompt=c1_prompt_text())`` (or an equivalent fake
    for tests) and must never place its return value into a dataclass, report, or log defined
    here.
    """

    return _C1_PROMPT_TEXT


# --- C1-v2: distinct protocol identity, per the owner-approved local proposal
# (`evidence/notes/P2_T3_PHASE_B_B3_C1_V2_PROMPT_PROPOSAL.md`, Section 2). Implements exactly
# that section's two rule changes (entity `label`/`confidence` shape); nothing else. v1's own
# constants/functions above are untouched -- v2 is purely additive.

_C1_PROMPT_PROTOCOL_ID_V2 = "vision-v2-structured-output-prompt-v2"

_C1_PROMPT_LINES_V2: tuple[str, ...] = (
    "Return exactly one compact JSON object and nothing else. Describe only directly "
    "observable visual content; do not infer personality, emotion, intent, "
    "symbolic/story/canonical meaning.",
    "Root keys must be exactly entities, actions, relations, themes, ambiguous_regions; "
    "all are arrays and no other keys exist.",
    "Use [] when empty. Maximum: 3 entities, 1 action, 1 relation, 1 theme, 1 ambiguous "
    "region. Prefer fewer. Text values are 1-3 lower-case English words. Every confidence "
    "is null.",
    "IDs are globally unique and match ^[a-z0-9-]+$.",
    'Every label/predicate/note is {"value":"...","language":{"status":"DECLARED",'
    '"tags":["en"]}}.',
    "Entity keys: observation_id,label,confidence. label is always the nested object from "
    "rule 5 -- never a plain string. confidence is always the JSON literal null -- never a "
    "number, never a string, never omitted. Structural shape only (not scene content): "
    '{"observation_id":"e1","label":{"value":"word","language":{"status":"DECLARED",'
    '"tags":["en"]}},"confidence":null}.',
    "Action keys: observation_id,label,actor_ref,object_ref,confidence; refs are entity "
    "IDs or null.",
    "Relation keys: observation_id,predicate,subject_ref,object_ref,confidence; refs are "
    "distinct entity/action IDs.",
    "Theme keys: observation_id,label,evidence_refs,confidence; evidence_refs contains "
    ">=1 entity/action/relation ID.",
    "Ambiguous-region keys: observation_id,note only; it is never referenced and has no "
    "confidence/geometry.",
    "Prefer unfenced compact JSON. No prose, comments, duplicate keys, metadata, "
    "type/kind/description/bbox/geometry fields, trailing commas, or non-JSON values. Never "
    "substitute a bare word or number for an object field defined in rule 5, and never "
    "substitute a number or string for a field rule 3 defines as null.",
)

_C1_PROMPT_TEXT_V2 = "\n".join(_C1_PROMPT_LINES_V2)


def c1_prompt_protocol_id_v2() -> str:
    """Safe identifier for the v2 protocol: fine for any report, log, or evidence artifact."""

    return _C1_PROMPT_PROTOCOL_ID_V2


def c1_prompt_sha256_v2() -> str:
    """SHA-256 of the canonical v2 prompt text. Safe to persist; the text itself is not."""

    return sha256(_C1_PROMPT_TEXT_V2.encode("utf-8")).hexdigest()


def c1_prompt_text_v2() -> str:
    """The reviewed static C1-v2 prompt body, for adapter-construction injection only.

    This is the one function in this module that returns the v2 prompt body. Same discipline as
    :func:`c1_prompt_text`: callers must pass it straight into adapter construction and must
    never place its return value into a dataclass, report, or log defined here. The schema
    target is unchanged from v1 (:func:`c1_prompt_schema_target`); only two rules differ from v1
    (entity ``label``/``confidence`` shape) -- see the module-level comment above
    :data:`_C1_PROMPT_PROTOCOL_ID_V2` for the source proposal.
    """

    return _C1_PROMPT_TEXT_V2


# --- C1-v3: distinct protocol identity, per the owner-approved Direction A proposal
# (`evidence/notes/P2_T3_PHASE_B_B4_DIRECTION_A_PROMPT_V3_PROPOSAL.md`, Section 2, approved
# verbatim by the owner). Implements exactly that section's five rule changes and nothing else:
# rules 6-10 each gain one leading generic collection-search sentence and are otherwise
# byte-identical to v2; rules 1-5 and 11 are byte-identical to v2. v1's and v2's own constants,
# functions, hashes, defaults, and behavior above are untouched -- v3 is purely additive, exactly
# as v2 was added alongside v1. This module still never runs a GPU/model/provider call, and v3,
# like v1/v2, is only ever injected explicitly (never a ``QwenVisionAdapter`` default).

_C1_PROMPT_PROTOCOL_ID_V3 = "vision-v2-structured-output-prompt-v3"

_C1_PROMPT_LINES_V3: tuple[str, ...] = (
    "Return exactly one compact JSON object and nothing else. Describe only directly "
    "observable visual content; do not infer personality, emotion, intent, "
    "symbolic/story/canonical meaning.",
    "Root keys must be exactly entities, actions, relations, themes, ambiguous_regions; "
    "all are arrays and no other keys exist.",
    "Use [] when empty. Maximum: 3 entities, 1 action, 1 relation, 1 theme, 1 ambiguous "
    "region. Prefer fewer. Text values are 1-3 lower-case English words. Every confidence "
    "is null.",
    "IDs are globally unique and match ^[a-z0-9-]+$.",
    'Every label/predicate/note is {"value":"...","language":{"status":"DECLARED",'
    '"tags":["en"]}}.',
    "Actively look for every directly observable entity, up to the maximum in rule 3, "
    "before deciding the array is empty. Entity keys: observation_id,label,confidence. "
    "label is always the nested object from rule 5 -- never a plain string. confidence is "
    "always the JSON literal null -- never a number, never a string, never omitted. "
    "Structural shape only (not scene content): "
    '{"observation_id":"e1","label":{"value":"word","language":{"status":"DECLARED",'
    '"tags":["en"]}},"confidence":null}.',
    "Actively look for a directly observable action before deciding the array is empty. "
    "Action keys: observation_id,label,actor_ref,object_ref,confidence; refs are entity "
    "IDs or null.",
    "Actively look for a directly observable relation between two entities or actions "
    "before deciding the array is empty. Relation keys: observation_id,predicate,"
    "subject_ref,object_ref,confidence; refs are distinct entity/action IDs.",
    "Actively look for a theme suggested by the observed entities, actions, or relations "
    "before deciding the array is empty. Theme keys: observation_id,label,evidence_refs,"
    "confidence; evidence_refs contains >=1 entity/action/relation ID.",
    "Actively look for a visually ambiguous or overlapping region before deciding the "
    "array is empty. Ambiguous-region keys: observation_id,note only; it is never "
    "referenced and has no confidence/geometry.",
    "Prefer unfenced compact JSON. No prose, comments, duplicate keys, metadata, "
    "type/kind/description/bbox/geometry fields, trailing commas, or non-JSON values. Never "
    "substitute a bare word or number for an object field defined in rule 5, and never "
    "substitute a number or string for a field rule 3 defines as null.",
)

_C1_PROMPT_TEXT_V3 = "\n".join(_C1_PROMPT_LINES_V3)


def c1_prompt_protocol_id_v3() -> str:
    """Safe identifier for the v3 protocol: fine for any report, log, or evidence artifact."""

    return _C1_PROMPT_PROTOCOL_ID_V3


def c1_prompt_sha256_v3() -> str:
    """SHA-256 of the canonical v3 prompt text. Safe to persist; the text itself is not."""

    return sha256(_C1_PROMPT_TEXT_V3.encode("utf-8")).hexdigest()


def c1_prompt_text_v3() -> str:
    """The reviewed static C1-v3 prompt body, for adapter-construction injection only.

    This is the one function in this module that returns the v3 prompt body. Same discipline as
    :func:`c1_prompt_text`/:func:`c1_prompt_text_v2`: callers must pass it straight into adapter
    construction and must never place its return value into a dataclass, report, or log defined
    here. The schema target is unchanged from v1/v2 (:func:`c1_prompt_schema_target`); only five
    rules differ from v2 (rules 6-10 each gain one leading generic collection-search sentence)
    -- see the module-level comment above :data:`_C1_PROMPT_PROTOCOL_ID_V3` for the source
    proposal.
    """

    return _C1_PROMPT_TEXT_V3


@dataclass(frozen=True, slots=True)
class C1PromptProtocol:
    """Identifies one reviewed C1 prompt protocol, safe fields plus a text-injection callable.

    ``protocol_id``/``prompt_sha256`` are exactly what :func:`c1_prompt_protocol_id`/
    :func:`c1_prompt_sha256` (or their ``_v2`` counterparts) return -- safe to persist in any
    report, log, or evidence artifact. ``prompt_text_provider`` is a **callable**, never a stored
    string: it exists to be invoked exactly once per :func:`run_c1_pass` call, for
    adapter-construction injection only, and must never be read into a report, log, or evidence
    artifact. This makes the selected protocol an explicit, typed argument to
    :func:`run_c1_pass`/:func:`evaluate_c1_readiness` instead of a hardcoded module-level choice.
    """

    protocol_id: str
    prompt_sha256: str
    prompt_text_provider: Callable[[], str]


C1_PROMPT_V1 = C1PromptProtocol(
    protocol_id=_C1_PROMPT_PROTOCOL_ID,
    prompt_sha256=c1_prompt_sha256(),
    prompt_text_provider=c1_prompt_text,
)
"""The original, frozen C1 protocol. Default for every ``run_c1_pass``/``evaluate_c1_readiness``
call that does not explicitly select a different protocol -- preserves all v1 callable behavior,
reports, and tests exactly as before v2 existed."""

C1_PROMPT_V2 = C1PromptProtocol(
    protocol_id=_C1_PROMPT_PROTOCOL_ID_V2,
    prompt_sha256=c1_prompt_sha256_v2(),
    prompt_text_provider=c1_prompt_text_v2,
)
"""The v2 protocol from the owner-approved local proposal. Must be passed explicitly (never
becomes a default) to ``run_c1_pass``/``evaluate_c1_readiness`` to be used."""

C1_PROMPT_V3 = C1PromptProtocol(
    protocol_id=_C1_PROMPT_PROTOCOL_ID_V3,
    prompt_sha256=c1_prompt_sha256_v3(),
    prompt_text_provider=c1_prompt_text_v3,
)
"""The v3 protocol from the owner-approved Direction A proposal, registered for **reviewed
identity and binding verification only**.

Adding it changes no existing call site: ``prompt``/``expected_prompt`` still default to
:data:`C1_PROMPT_V1`. It is *not* runnable through this module -- ``run_c1_pass`` and
``evaluate_c1_readiness`` both reject it with :class:`C1PromptOutOfExperimentScopeError`, because
v3's approved plan is a separate experiment with its own runner, ``V3_PASS_1``/``V3_REPEAT_1``
labels, and newly authored fixture package. See
:data:`_C1_EXECUTION_ELIGIBLE_PROMPT_IDENTITIES`."""


class C1PromptBindingError(Exception):
    """Raised when a :class:`C1PromptProtocol`'s declared identity cannot be trusted.

    A module-local reason, never a new public V1/V2 error token -- exactly like
    :class:`C1BlockingReason`, this stays private to this benchmark module rather than joining
    the shared ``VisionErrorCode``/``VisionNonPolicyErrorDetailV2`` contracts. :func:`run_c1_pass`
    raises this, closed, before ``adapter_factory``, fixture generation, or any provider action,
    when a :class:`C1PromptProtocol`'s ``(protocol_id, prompt_sha256)`` pair is not one of the
    three canonical approved identities (:data:`C1_PROMPT_V1`, :data:`C1_PROMPT_V2`,
    :data:`C1_PROMPT_V3`), or when the
    SHA-256 of the text ``prompt_text_provider()`` actually returns does not match the protocol's
    declared ``prompt_sha256``. The message never includes the prompt text itself -- only
    ``protocol_id`` and hash values, both already documented as safe to persist by
    :func:`c1_prompt_sha256`/:func:`c1_prompt_sha256_v2`.

    Deliberately absent from this module's ``__all__``: it is an internal binding-integrity
    signal, not part of the module's public surface. It remains directly importable by name
    (``from ... import C1PromptBindingError``) for tests and any caller that needs to catch it
    specifically -- omission from ``__all__`` only affects ``from ... import *``.
    """


_CANONICAL_C1_PROMPT_IDENTITIES: frozenset[tuple[str, str]] = frozenset(
    {
        (C1_PROMPT_V1.protocol_id, C1_PROMPT_V1.prompt_sha256),
        (C1_PROMPT_V2.protocol_id, C1_PROMPT_V2.prompt_sha256),
        (C1_PROMPT_V3.protocol_id, C1_PROMPT_V3.prompt_sha256),
    }
)
"""The closed allowlist of approved ``(protocol_id, prompt_sha256)`` pairs. Nothing outside this
module may extend it; adding a new approved protocol requires its own reviewed constant here,
mirroring how :data:`C1_PROMPT_V1`/:data:`C1_PROMPT_V2`/:data:`C1_PROMPT_V3` were each added
deliberately.

Membership here means only "this is a reviewed identity whose declared hash matches its text" --
it is deliberately *not* the same question as "may this protocol be executed by this module's C1
functions", which :data:`_C1_EXECUTION_ELIGIBLE_PROMPT_IDENTITIES` answers separately."""


_C1_EXECUTION_ELIGIBLE_PROMPT_IDENTITIES: frozenset[tuple[str, str]] = frozenset(
    {
        (C1_PROMPT_V1.protocol_id, C1_PROMPT_V1.prompt_sha256),
        (C1_PROMPT_V2.protocol_id, C1_PROMPT_V2.prompt_sha256),
    }
)
""":data:`C1_PROMPT_V3` is deliberately absent: it is registered for reviewed identity/binding
only, not for execution by this module.

``run_c1_pass``/``evaluate_c1_readiness`` are the C1 experiment: two fixed run labels
(``C1_PASS_1``/``C1_REPEAT_1``) over ``run_b3_mapping_study``'s own eight generated B3 fixtures.
The owner-approved v3 plan requires a *different* experiment -- its own future runner, its own
``V3_PASS_1``/``V3_REPEAT_1`` labels, and exactly eight newly authored synthetic fixtures disjoint
from B4 -- so letting v3 run here would produce correctly hashed but wrongly scoped evidence: a
C1-labelled ``MAPPING_READY`` verdict over B3 fixtures, cited later as if it were v3's approved
mapping validation. That runner and fixture package are not implemented, so v3 fails closed at
both C1 entry points until they exist and are separately approved."""


class C1PromptOutOfExperimentScopeError(Exception):
    """A reviewed prompt identity was supplied to a C1 function it is not in scope for.

    A module-local reason, never a new public V1/V2 error token -- exactly like
    :class:`C1PromptBindingError` and :class:`C1BlockingReason`, and deliberately absent from
    ``__all__``. Raised closed by :func:`run_c1_pass` (before ``adapter_factory``, fixture
    generation, scratch creation, or any provider action) and by :func:`evaluate_c1_readiness`
    (before any readiness logic, so such a prompt can never reach a ``MAPPING_READY`` verdict)
    when the supplied protocol is not in :data:`_C1_EXECUTION_ELIGIBLE_PROMPT_IDENTITIES`.

    Today that means :data:`C1_PROMPT_V3`: it is a fully reviewed, canonically bound identity, but
    its approved plan runs a separate experiment (its own runner, its own ``V3_PASS_1``/
    ``V3_REPEAT_1`` labels, and its own newly authored fixture package), none of which exists yet.
    The message carries only ``protocol_id`` and ``prompt_sha256`` -- both already documented safe
    to persist -- and never the prompt text or any raw output.
    """


def _require_c1_execution_scope(prompt: C1PromptProtocol) -> None:
    """Fail closed when ``prompt`` is a *canonical* identity that C1 may not execute.

    Deliberately narrow: it fires only for an identity on the canonical allowlist that is absent
    from :data:`_C1_EXECUTION_ELIGIBLE_PROMPT_IDENTITIES` (today, exactly
    :data:`C1_PROMPT_V3`). An unknown or forged identity is *not* handled here -- it stays a
    binding-integrity failure and still raises :class:`C1PromptBindingError` from
    :func:`_resolve_verified_c1_prompt_text`, exactly as before this gate existed.

    Checked on the caller's *declared* identity, before the prompt provider is invoked and before
    any adapter/fixture/scratch/provider action, so a v3-identified protocol can never reach the
    C1 execution or readiness paths at all.
    """

    identity = (prompt.protocol_id, prompt.prompt_sha256)
    if (
        identity in _CANONICAL_C1_PROMPT_IDENTITIES
        and identity not in _C1_EXECUTION_ELIGIBLE_PROMPT_IDENTITIES
    ):
        raise C1PromptOutOfExperimentScopeError(
            "Out-of-scope C1 prompt identity: "
            f"protocol_id={prompt.protocol_id!r} (prompt_sha256={prompt.prompt_sha256}) is not "
            "eligible for a C1 pass or readiness evaluation. C1 runs only C1_PASS_1/C1_REPEAT_1 "
            "over the B3 fixture set; a protocol approved for a different experiment needs that "
            "experiment's own runner, run labels, and fixture package."
        )


def _resolve_verified_c1_prompt_text(prompt: C1PromptProtocol) -> str:
    """Resolve ``prompt``'s text exactly once, verified against its declared identity.

    Fails closed with :class:`C1PromptBindingError` -- before any adapter, fixture, or provider
    action -- when ``(protocol_id, prompt_sha256)`` is not one of the three canonical approved
    identities, or when the SHA-256 of the text ``prompt_text_provider()`` actually returns does
    not match the declared ``prompt_sha256``. This is what ties a :class:`C1PassReport`'s stamped
    identity to the exact text an adapter factory receives, rather than to an unverified caller
    claim on :class:`C1PromptProtocol`.
    """

    identity = (prompt.protocol_id, prompt.prompt_sha256)
    if identity not in _CANONICAL_C1_PROMPT_IDENTITIES:
        raise C1PromptBindingError(
            "Unknown C1 prompt identity: "
            f"protocol_id={prompt.protocol_id!r} is not paired with a canonical approved "
            "prompt_sha256 in the closed C1 prompt allowlist."
        )

    text = prompt.prompt_text_provider()
    computed_sha256 = sha256(text.encode("utf-8")).hexdigest()
    if computed_sha256 != prompt.prompt_sha256:
        raise C1PromptBindingError(
            "C1 prompt text/hash mismatch: the resolved prompt text's SHA-256 does not match "
            f"the declared prompt_sha256 for protocol_id={prompt.protocol_id!r}."
        )

    return text


def qwen_c1_adapter_factory(
    runtime_config: QwenVisionRuntimeConfig,
    content_policy: ObservableContentPolicyV1,
    *,
    generation_runner: QwenGenerationRunner | None = None,
) -> C1AdapterFactory:
    """The real production :data:`C1AdapterFactory` for a Lightning C1 run.

    Returns a closure matching ``C1AdapterFactory``: called by ``run_c1_pass`` with the selected,
    verified :class:`C1PromptProtocol`'s prompt text (``c1_prompt_text()`` for ``C1_PROMPT_V1``
    by default, or another explicitly passed protocol's text) and ``collector.hook``, it
    constructs a fresh ``QwenVisionAdapter`` with ``prompt``/``on_raw_output`` set to exactly
    those two values. ``QwenVisionAdapter``'s own
    default (empty) ``_default_prompt_builder`` is never reached through this factory --
    ``prompt=`` is always supplied explicitly, once per call. ``generation_runner`` exists only so
    tests can inject a fake generation seam without a GPU; a real Lightning run omits it and gets
    the adapter's own default killable-subprocess runner.
    """

    def factory(prompt: str, on_raw_output: RawOutputHook) -> VisionUnderstandingPortV2:
        return QwenVisionAdapter(
            runtime_config,
            content_policy=content_policy,
            prompt=prompt,
            generation_runner=generation_runner,
            on_raw_output=on_raw_output,
        )

    return factory


@dataclass(frozen=True, slots=True)
class C1PassReport:
    """One C1 pass's safe report: prompt identity plus the reused B3 mapping report.

    Never carries the prompt body, raw model output, or a local path -- only what
    :class:`~sketch2life.benchmark.vision_b3_mapping_study.B3MappingStudyReport` already
    guarantees, plus the C1 prompt's safe identifiers.
    """

    run_label: C1RunLabel
    prompt_protocol_id: str
    prompt_sha256: str
    mapping: B3MappingStudyReport


def run_c1_pass(
    adapter_factory: C1AdapterFactory,
    collector: B3RawOutputCollector,
    *,
    run_label: C1RunLabel,
    prompt: C1PromptProtocol = C1_PROMPT_V1,
    profile_id: VisionProfileIdV2 = VisionProfileIdV2.QWEN3_VL_8B_INSTRUCT_BF16_V1,
    sample_vram: bool = True,
    fixtures_dir: Path | None = None,
) -> C1PassReport:
    """Execute one C1 pass: the existing eight B3 fixtures, one adapter call each, no retry.

    ``prompt``'s declared identity is resolved and verified exactly once, here, by
    :func:`_resolve_verified_c1_prompt_text` -- against the closed canonical allowlist of
    approved ``(protocol_id, prompt_sha256)`` pairs and against the SHA-256 of the text
    ``prompt.prompt_text_provider()`` actually returns -- before ``adapter_factory`` is called,
    raising :class:`C1PromptBindingError` closed on any mismatch. Only once that check passes is
    ``adapter_factory`` called, exactly once, with the verified text and ``collector.hook`` --
    never with anything else -- to build the adapter that ``run_b3_mapping_study`` then drives.
    ``prompt`` defaults to :data:`C1_PROMPT_V1`, so every existing call site that does not pass
    ``prompt`` explicitly keeps running the original v1 protocol with unchanged behavior; passing
    :data:`C1_PROMPT_V2` (or another :class:`C1PromptProtocol`) makes the selected protocol an
    explicit argument rather than a silent default swap. There is no way to obtain a
    :class:`C1PassReport` from an already-built adapter: the factory is the only construction
    seam, so the prompt identity stamped on the returned report always matches what the factory
    actually received and what the verification step confirmed, not an unverified caller claim on
    ``prompt.protocol_id``/``prompt.prompt_sha256``. This function never touches
    ``qwen_vision.py``'s default (empty) prompt builder itself -- see
    :func:`qwen_c1_adapter_factory` for the real production factory, which is itself
    protocol-agnostic: it constructs whatever prompt string it is called with.

    Delegates entirely to ``run_b3_mapping_study`` -- including that function's own default
    eight-fixture builder, real P2-T1 gate, one-call-per-fixture-no-retry loop, and scratch
    cleanup -- and adds only the C1 prompt-verification/dispatch/identity wrapper and a distinct
    default scratch directory per ``run_label`` so ``C1_PASS_1`` and ``C1_REPEAT_1`` never
    collide when run in the same working directory.
    """

    _require_c1_execution_scope(prompt)
    prompt_text = _resolve_verified_c1_prompt_text(prompt)
    adapter = adapter_factory(prompt_text, collector.hook)
    resolved_fixtures_dir = fixtures_dir or _DEFAULT_C1_FIXTURES_DIR[run_label]
    mapping = run_b3_mapping_study(
        adapter,
        collector,
        profile_id=profile_id,
        correlation_id_prefix=f"vision-{run_label.lower().replace('_', '-')}",
        sample_vram=sample_vram,
        fixtures_dir=resolved_fixtures_dir,
    )
    return C1PassReport(
        run_label=run_label,
        prompt_protocol_id=prompt.protocol_id,
        prompt_sha256=prompt.prompt_sha256,
        mapping=mapping,
    )


class C1BlockingReason(StrEnum):
    """Closed set of reasons :func:`evaluate_c1_readiness` may cite for a non-ready verdict."""

    MAPPING_VALID_BELOW_THRESHOLD = "MAPPING_VALID_BELOW_THRESHOLD"
    SYSTEMIC_TRUNCATION_STOP_FOR_OUTPUT_BUDGET_ANALYSIS = (
        "SYSTEMIC_TRUNCATION_STOP_FOR_OUTPUT_BUDGET_ANALYSIS"
    )
    CONFIG_DRIFT = "CONFIG_DRIFT"
    INPUT_INTEGRITY_FAILURE = "INPUT_INTEGRITY_FAILURE"
    RUNTIME_OR_DEVICE_FAILURE = "RUNTIME_OR_DEVICE_FAILURE"
    INCOMPLETE_RUN_SET = "INCOMPLETE_RUN_SET"


@dataclass(frozen=True, slots=True)
class C1PassEvaluation:
    """Derived, safe-only figures for one pass; never carries raw text or a path.

    ``is_complete`` is ``True`` only when both ``attempted_runs`` and ``run_record_count`` equal
    exactly eight; ``mapping_valid_ok`` is structurally forced ``False`` whenever the pass is
    incomplete, so a malformed report (e.g. a partial 7/7 run, or ``attempted_runs`` disagreeing
    with the number of run records) can never satisfy the numeric threshold on the strength of a
    numerator alone.
    """

    run_label: C1RunLabel
    attempted_runs: int
    run_record_count: int
    is_complete: bool
    mapping_valid_count: int
    truncated_count: int
    mapping_valid_ok: bool
    systemic_truncation: bool


@dataclass(frozen=True, slots=True)
class C1ReadinessVerdict:
    """The pre-registered C1 mapping-readiness gate applied to two independent passes.

    Never pools ``pass_1``/``repeat_1`` into a combined denominator: each must independently
    satisfy the mapping-valid threshold, matching the project's standing no-pooling rule for
    distinct benchmark runs.
    """

    prompt_protocol_id: str
    prompt_sha256: str
    pass_1: C1PassEvaluation
    repeat_1: C1PassEvaluation
    overall: Literal["MAPPING_READY", "MAPPING_NOT_READY"]
    blocking_reasons: tuple[C1BlockingReason, ...]


def _mapping_valid_count(report: B3MappingStudyReport) -> int:
    """``SUCCEEDED`` or ``PROHIBITED_CLAIM_DETECTED`` both count as mapping-valid for C1.

    Both outcomes prove the model's raw output mapped onto the strict V2 JSON contract; a
    policy block is a content decision made *after* successful mapping, not a mapping failure.
    """

    return sum(
        1
        for run in report.runs
        if run.status == "SUCCEEDED"
        or run.error_code == VisionErrorCode.PROHIBITED_CLAIM_DETECTED.value
    )


def _has_runtime_or_device_failure(report: B3MappingStudyReport) -> bool:
    return any(run.error_code in _RUNTIME_OR_DEVICE_ERROR_CODES for run in report.runs)


def _has_input_integrity_failure(report: B3MappingStudyReport) -> bool:
    return any(run.error_detail in _INPUT_INTEGRITY_ERROR_DETAILS for run in report.runs)


def _evaluate_pass(pass_report: C1PassReport) -> C1PassEvaluation:
    mapping = pass_report.mapping
    valid_count = _mapping_valid_count(mapping)
    run_record_count = len(mapping.runs)
    is_complete = (
        mapping.attempted_runs == _EXPECTED_ATTEMPTED_RUNS
        and run_record_count == _EXPECTED_ATTEMPTED_RUNS
    )
    return C1PassEvaluation(
        run_label=pass_report.run_label,
        attempted_runs=mapping.attempted_runs,
        run_record_count=run_record_count,
        is_complete=is_complete,
        mapping_valid_count=valid_count,
        truncated_count=mapping.truncated_count,
        mapping_valid_ok=is_complete and valid_count >= _MIN_MAPPING_VALID_COUNT,
        systemic_truncation=mapping.truncated_count >= _SYSTEMIC_TRUNCATION_THRESHOLD,
    )


def evaluate_c1_readiness(
    pass_1: C1PassReport,
    repeat_1: C1PassReport,
    *,
    expected_prompt: C1PromptProtocol = C1_PROMPT_V1,
) -> C1ReadinessVerdict:
    """Apply the pre-registered C1 mapping-readiness gate to two independent passes.

    ``expected_prompt`` defaults to :data:`C1_PROMPT_V1`, so every existing call site keeps
    checking passes against the original v1 identity unchanged. Passing :data:`C1_PROMPT_V2`
    checks both passes against the v2 identity instead; a pass carrying the *other* protocol's
    ``prompt_protocol_id``/``prompt_sha256`` (a v1 report evaluated against
    ``expected_prompt=C1_PROMPT_V2``, or vice versa) fails the identity comparison below exactly
    like any other config drift -- there is no separate v1/v2-mismatch code path, because the
    existing drift check already covers it once the expected identity is a parameter.

    Before anything else, ``expected_prompt`` itself is resolved and verified through the same
    :func:`_resolve_verified_c1_prompt_text` binding check :func:`run_c1_pass` uses -- against the
    closed canonical allowlist and against the SHA-256 of the text its
    ``prompt_text_provider()`` actually returns, calling that provider at most once. This closes
    the readiness-bypass a directly constructed, unverified ``expected_prompt`` would otherwise
    open: without it, two directly constructed :class:`C1PassReport` values could carry any
    arbitrary claimed identity and evaluate as ``MAPPING_READY`` against an ``expected_prompt``
    that merely echoes that same unverified claim. The resolved text itself is discarded
    immediately -- it is never stored, compared further, or placed on :class:`C1ReadinessVerdict`
    -- so this call exists purely to raise :class:`C1PromptBindingError` closed on any mismatch,
    before any readiness logic below runs.

    See the module docstring for the full gate rule. This function does not detect whether raw
    output was ever persisted -- that guarantee is structural, enforced by
    ``B3RawOutputCollector``/``run_b3_mapping_study`` and covered by their own tests, not
    re-derived from a report here.
    """

    if pass_1.run_label == repeat_1.run_label:
        raise ValueError("pass_1 and repeat_1 must carry distinct run labels")

    _require_c1_execution_scope(expected_prompt)
    _resolve_verified_c1_prompt_text(expected_prompt)

    expected_catalog_hash = vision_profile_catalog_hash_v2(vision_profile_catalog_v2())
    expected_profile_id = VisionProfileIdV2.QWEN3_VL_8B_INSTRUCT_BF16_V1.value
    expected_prompt_sha256 = expected_prompt.prompt_sha256
    expected_protocol_id = expected_prompt.protocol_id

    config_drift = (
        pass_1.mapping.profile_id != expected_profile_id
        or repeat_1.mapping.profile_id != expected_profile_id
        or pass_1.mapping.profile_catalog_hash != expected_catalog_hash
        or repeat_1.mapping.profile_catalog_hash != expected_catalog_hash
        or pass_1.prompt_protocol_id != expected_protocol_id
        or repeat_1.prompt_protocol_id != expected_protocol_id
        or pass_1.prompt_sha256 != expected_prompt_sha256
        or repeat_1.prompt_sha256 != expected_prompt_sha256
    )
    integrity_failure = _has_input_integrity_failure(
        pass_1.mapping
    ) or _has_input_integrity_failure(repeat_1.mapping)
    runtime_failure = _has_runtime_or_device_failure(
        pass_1.mapping
    ) or _has_runtime_or_device_failure(repeat_1.mapping)

    pass_1_evaluation = _evaluate_pass(pass_1)
    repeat_1_evaluation = _evaluate_pass(repeat_1)

    incomplete = not pass_1_evaluation.is_complete or not repeat_1_evaluation.is_complete
    mapping_valid_ok = pass_1_evaluation.mapping_valid_ok and repeat_1_evaluation.mapping_valid_ok
    systemic_truncation = (
        pass_1_evaluation.systemic_truncation or repeat_1_evaluation.systemic_truncation
    )

    blocking: list[C1BlockingReason] = []
    if config_drift:
        blocking.append(C1BlockingReason.CONFIG_DRIFT)
    if integrity_failure:
        blocking.append(C1BlockingReason.INPUT_INTEGRITY_FAILURE)
    if runtime_failure:
        blocking.append(C1BlockingReason.RUNTIME_OR_DEVICE_FAILURE)
    if incomplete:
        # A malformed/partial run set makes the numeric threshold meaningless -- cite this
        # reason instead of (never in addition to) MAPPING_VALID_BELOW_THRESHOLD below.
        blocking.append(C1BlockingReason.INCOMPLETE_RUN_SET)
    if systemic_truncation:
        blocking.append(C1BlockingReason.SYSTEMIC_TRUNCATION_STOP_FOR_OUTPUT_BUDGET_ANALYSIS)
    if not incomplete and not mapping_valid_ok:
        blocking.append(C1BlockingReason.MAPPING_VALID_BELOW_THRESHOLD)

    overall: Literal["MAPPING_READY", "MAPPING_NOT_READY"] = (
        "MAPPING_NOT_READY" if blocking else "MAPPING_READY"
    )

    return C1ReadinessVerdict(
        prompt_protocol_id=expected_protocol_id,
        prompt_sha256=expected_prompt_sha256,
        pass_1=pass_1_evaluation,
        repeat_1=repeat_1_evaluation,
        overall=overall,
        blocking_reasons=tuple(blocking),
    )


__all__ = [
    "C1AdapterFactory",
    "C1BlockingReason",
    "C1PassEvaluation",
    "C1PassReport",
    "C1PromptProtocol",
    "C1ReadinessVerdict",
    "C1RunLabel",
    "C1_PROMPT_V1",
    "C1_PROMPT_V2",
    "C1_PROMPT_V3",
    "c1_prompt_protocol_id",
    "c1_prompt_protocol_id_v2",
    "c1_prompt_protocol_id_v3",
    "c1_prompt_schema_target",
    "c1_prompt_sha256",
    "c1_prompt_sha256_v2",
    "c1_prompt_sha256_v3",
    "c1_prompt_text",
    "c1_prompt_text_v2",
    "c1_prompt_text_v3",
    "evaluate_c1_readiness",
    "qwen_c1_adapter_factory",
    "run_c1_pass",
]
