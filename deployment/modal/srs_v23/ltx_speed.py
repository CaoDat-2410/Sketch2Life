"""Speed profile of the LTX-2.5 scene renderer (FEAT-094, ADR-0026). No torch import, so it is unit tested.

``fast`` keeps the transformer and VAE builds on the GPU, encodes the prompts of a whole video once and compiles the
video decoder. It peaks near the L40S memory limit, so a render that runs out of memory is repeated once with ``safe``
(the earlier CPU offload settings) and the container stays on it.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, Final, TypeVar

FAST: Final = "fast"
SAFE: Final = "safe"
MAX_PROMPTS: Final = 15
MAX_PROMPT_CHARS: Final = 1_500
_Result = TypeVar("_Result")


class PromptCache:
    """Stands in for the pipeline's prompt encoder: one text-encoder load serves every scene of a video."""

    def __init__(self, encoder: Any, *, limit: int = MAX_PROMPTS) -> None:
        self._encoder = encoder
        self._limit = limit
        self._known: dict[str, Any] = {}

    def prepare(self, prompts: list[str]) -> None:
        missing = [prompt for prompt in dict.fromkeys(prompts) if prompt not in self._known]
        if not missing:
            return
        self._known.update(zip(missing, self._encoder(missing), strict=True))
        while len(self._known) > self._limit:
            self._known.pop(next(iter(self._known)))

    def cached_prompts(self) -> tuple[str, ...]:
        return tuple(self._known)

    def __call__(self, prompts: list[str], **options: Any) -> list[Any]:
        if options.get("enhance_first_prompt"):
            raise ValueError("LTX_PROMPT_ENHANCEMENT_NOT_SUPPORTED")
        self.prepare(list(prompts))
        return [self._known[prompt] for prompt in prompts]

    def __getattr__(self, name: str) -> Any:
        return getattr(self._encoder, name)


def is_out_of_memory(error: BaseException) -> bool:
    return type(error).__name__ == "OutOfMemoryError" or "out of memory" in str(error).lower()


class ProfileSwitch:
    """Which profile this container renders with; it only ever moves from fast to safe."""

    def __init__(self) -> None:
        self.current = FAST

    def fall_back(self) -> None:
        self.current = SAFE


def render_with_fallback(
    profiles: ProfileSwitch, render: Callable[[], _Result], *, release: Callable[[], None]
) -> _Result:
    """Run ``render``; on out of memory in the fast profile, free the GPU and run it once more."""

    try:
        return render()
    except Exception as error:
        if profiles.current != FAST or not is_out_of_memory(error):
            raise
    # Outside the except block, so the failed call's frames no longer hold GPU tensors.
    profiles.fall_back()
    release()
    return render()


def warm_up_prompts(payload: dict[str, Any]) -> list[str] | None:
    """The prompts of a warm-up request, or None when the payload is a job."""

    if payload.get("warmup") is not True:
        return None
    prompts = payload.get("prompts", [])
    if (
        not set(payload) <= {"warmup", "prompts"}
        or not isinstance(prompts, list)
        or len(prompts) > MAX_PROMPTS
        or any(
            not isinstance(prompt, str) or not prompt.strip() or len(prompt) > MAX_PROMPT_CHARS
            for prompt in prompts
        )
    ):
        raise ValueError("MODAL_INPUT_NOT_ALLOWED")
    return list(prompts)


__all__ = [
    "FAST",
    "SAFE",
    "ProfileSwitch",
    "PromptCache",
    "is_out_of_memory",
    "render_with_fallback",
    "warm_up_prompts",
]
