"""vLLM engine for the shared Qwen worker (FEAT-093 Amendment C, ADR-0025).

``VllmTextModel`` offers the part of the transformers ``generate`` interface the Qwen handlers use, so the handlers keep
their prompts, schemas, quality gates and diagnostics. ``run_with_quality_retries`` generates again when a quality gate
rejects an output; later attempts sample, because greedy decoding would repeat the rejected text.

Nothing here imports vLLM or torch at module level, so the module loads in every worker image and in offline tests.
"""

from __future__ import annotations

import contextlib
import json
from collections.abc import Callable, Iterator
from contextvars import ContextVar
from dataclasses import dataclass
from typing import Any, Final

ENGINE_ENV: Final = "SKETCH2LIFE_QWEN_ENGINE"
ENGINE_NAME: Final = "vllm"
MAX_ATTEMPTS: Final = 3
SAMPLED_TEMPERATURE: Final = 0.6
SAMPLED_TOP_P: Final = 0.8
SAMPLED_TOP_K: Final = 20
_RETRYABLE_PREFIXES: Final = ("MODAL_MODEL_OUTPUT_", "TIMELINE_DRAFT_")
_IMAGE_INPUT_KEYS: Final = ("pixel_values", "image_grid_thw", "pixel_values_videos", "video_grid_thw")
# These write open text; sampling on the first attempt gives better prose, and a repeated request can differ.
CREATIVE_WORKLOADS: Final = frozenset({"story.generate", "parent.activity.suggest"})
ENGINE_FAILED_CODE: Final = "MODAL_QWEN_ENGINE_FAILED"


def engine_options(*, min_pixels: int, max_pixels: int) -> dict[str, Any]:
    """Measured on L40S (evidence M12): MTP doubles single-stream speed; the FP8 KV cache crashes the hybrid layers."""

    return {
        "max_model_len": 32_768,
        "gpu_memory_utilization": 0.92,
        "max_num_seqs": 1,
        "speculative_config": {"method": "mtp", "num_speculative_tokens": 3},
        "limit_mm_per_prompt": {"image": 1},
        # Compact JSON only: free whitespace let one run emit line breaks until the token budget was spent.
        "structured_outputs_config": {"backend": "xgrammar", "disable_any_whitespace": True},
        "mm_processor_kwargs": {"min_pixels": min_pixels, "max_pixels": max_pixels},
    }


@dataclass(frozen=True, slots=True)
class Attempt:
    number: int = 1
    creative: bool = False


_ATTEMPT: ContextVar[Attempt] = ContextVar("qwen_generation_attempt", default=Attempt())


def current_attempt() -> Attempt:
    return _ATTEMPT.get()


@contextlib.contextmanager
def generation_attempt(number: int, *, creative: bool = False) -> Iterator[None]:
    token = _ATTEMPT.set(Attempt(number, creative))
    try:
        yield
    finally:
        _ATTEMPT.reset(token)


def is_quality_rejection(error: BaseException) -> bool:
    """A rejected model output: every such worker error (some are ``ValueError``) carries one of these codes."""

    return isinstance(error, (RuntimeError, ValueError)) and str(error).startswith(_RETRYABLE_PREFIXES)


def run_with_quality_retries(handler: Callable[[Any], Any], payload: Any, *, creative: bool) -> Any:
    for number in range(1, MAX_ATTEMPTS + 1):
        try:
            with generation_attempt(number, creative=creative):
                return handler(payload)
        except (RuntimeError, ValueError) as error:
            if number == MAX_ATTEMPTS or not is_quality_rejection(error):
                raise
            print(
                json.dumps(
                    {
                        "event": "qwen_output_regenerated",
                        "rejected_attempt": number,
                        "reason_code": str(getattr(error, "reason_code", error))[:64],
                    },
                    sort_keys=True,
                ),
                flush=True,
            )
    raise AssertionError("unreachable")


class JsonSchemaConstraint:
    """Stands where the handlers pass a ``prefix_allowed_tokens_fn``; vLLM constrains from the schema itself."""

    def __init__(self, schema: dict[str, Any]) -> None:
        self.schema = schema
        self.decoder_diagnostics: dict[str, Any] = {}


def _vllm_params(**options: Any) -> Any:
    from vllm import SamplingParams
    from vllm.sampling_params import StructuredOutputsParams

    schema = options.pop("json_schema", None)
    if schema is not None:
        options["structured_outputs"] = StructuredOutputsParams(json=schema)
    return SamplingParams(**options)


def _stop_container() -> None:
    import modal.experimental

    modal.experimental.stop_fetching_inputs()


def _torch_tensor(rows: list[list[int]]) -> Any:
    import torch

    return torch.tensor(rows, dtype=torch.long)


class VllmTextModel:
    """One loaded vLLM engine; ``device`` is ``cpu`` because the handlers only move prompt tensors to it."""

    device = "cpu"
    accepts_images = True

    def __init__(
        self,
        llm: Any,
        generation_config: Any,
        *,
        make_params: Callable[..., Any] = _vllm_params,
        to_tensor: Callable[[list[list[int]]], Any] = _torch_tensor,
        on_engine_dead: Callable[[], None] = _stop_container,
    ) -> None:
        self._on_engine_dead = on_engine_dead
        self._llm = llm
        self.generation_config = generation_config
        self._make_params = make_params
        self._to_tensor = to_tensor

    def generate(
        self,
        input_ids: Any = None,
        *,
        generation_config: Any = None,
        prefix_allowed_tokens_fn: Any = None,
        **options: Any,
    ) -> Any:
        if any(options.get(key) is not None for key in _IMAGE_INPUT_KEYS):
            raise RuntimeError("MODAL_QWEN_ENGINE_IMAGE_INPUT_UNSUPPORTED")
        if prefix_allowed_tokens_fn is not None and not isinstance(prefix_allowed_tokens_fn, JsonSchemaConstraint):
            raise RuntimeError("MODAL_QWEN_ENGINE_CONSTRAINT_UNSUPPORTED")
        rows = input_ids.tolist() if hasattr(input_ids, "tolist") else input_ids
        if len(rows) != 1:
            raise RuntimeError("MODAL_TEXT_MODEL_INPUT_INVALID")
        prompt_ids = [int(token) for token in rows[0]]
        config = generation_config if generation_config is not None else self.generation_config

        def setting(name: str) -> Any:
            value = options.get(name)
            return value if value is not None else getattr(config, name, None)

        sampling = self._sampling(
            do_sample=bool(setting("do_sample")),
            temperature=setting("temperature"),
            top_p=setting("top_p"),
            top_k=setting("top_k"),
        )
        params = self._request(
            sampling,
            max_new_tokens=int(setting("max_new_tokens")),
            min_new_tokens=setting("min_new_tokens"),
            constraint=prefix_allowed_tokens_fn,
        )
        result = self._run({"prompt_token_ids": prompt_ids}, params)
        output = self._to_tensor([prompt_ids + [int(token) for token in result.outputs[0].token_ids]])
        for criterion in options.get("stopping_criteria") or ():
            criterion(output, None)  # transformers calls these per token; here only the final count is known
        return output

    def generate_from_image(
        self,
        prompt: str,
        image: Any,
        *,
        schema: dict[str, Any],
        max_new_tokens: int,
        min_new_tokens: int | None = None,
    ) -> tuple[Any, Any]:
        """``(input_ids, output_ids)`` for one prompt with one image; vLLM expands the image placeholder itself."""

        params = self._request(
            self._sampling(do_sample=False),
            max_new_tokens=max_new_tokens,
            min_new_tokens=min_new_tokens,
            constraint=JsonSchemaConstraint(schema),
        )
        request = {"prompt": prompt, "multi_modal_data": {"image": image}}
        result = self._run(request, params)
        prompt_ids = [int(token) for token in result.prompt_token_ids]
        answer_ids = [int(token) for token in result.outputs[0].token_ids]
        return self._to_tensor([prompt_ids]), self._to_tensor([prompt_ids + answer_ids])

    def _run(self, request: dict[str, Any], params: Any) -> Any:
        try:
            return self._llm.generate([request], params, use_tqdm=False)[0]
        except Exception as error:
            if "EngineDead" not in type(error).__name__:
                raise
            # A dead engine never recovers in this process: stop taking inputs so the next call gets a fresh one.
            with contextlib.suppress(Exception):
                self._on_engine_dead()
            raise RuntimeError(ENGINE_FAILED_CODE) from None

    def _sampling(
        self, *, do_sample: bool, temperature: float | None = None, top_p: float | None = None, top_k: int | None = None
    ) -> dict[str, Any]:
        attempt = current_attempt()
        if attempt.number > 1 or attempt.creative:
            return {"temperature": SAMPLED_TEMPERATURE, "top_p": SAMPLED_TOP_P, "top_k": SAMPLED_TOP_K}
        if not do_sample:
            return {"temperature": 0.0}
        values = {"temperature": temperature, "top_p": top_p, "top_k": top_k}
        return {name: value for name, value in values.items() if value is not None}

    def _request(
        self,
        sampling: dict[str, Any],
        *,
        max_new_tokens: int,
        min_new_tokens: int | None,
        constraint: JsonSchemaConstraint | None,
    ) -> Any:
        options: dict[str, Any] = {"max_tokens": max_new_tokens, **sampling}
        if min_new_tokens:
            options["min_tokens"] = int(min_new_tokens)
        options["json_schema"] = constraint.schema if constraint is not None else None
        return self._make_params(**options)


__all__ = [
    "CREATIVE_WORKLOADS",
    "ENGINE_ENV",
    "ENGINE_NAME",
    "MAX_ATTEMPTS",
    "SAMPLED_TEMPERATURE",
    "Attempt",
    "JsonSchemaConstraint",
    "VllmTextModel",
    "current_attempt",
    "engine_options",
    "generation_attempt",
    "is_quality_rejection",
    "run_with_quality_retries",
]
