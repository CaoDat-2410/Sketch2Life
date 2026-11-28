"""Local/provider-neutral boundary for presentation SVG drafts (no network policy here)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class PresentationSvgDraftInput:
    schema_version: str
    activity_title: str
    subject_text: str


@dataclass(frozen=True, slots=True)
class PresentationSvgDraftOutput:
    source: bytes
    generator_name: str
    generator_version: str
    license_id: str


class PresentationSvgDrafterUnavailable(RuntimeError):
    """A bounded drafter call timed out or its provider was temporarily unavailable."""


class PresentationSvgDrafter(Protocol):
    """Return bounded source/provenance or raise the typed error for timeout/provider outage.

    Implementations must enforce a finite wall-clock timeout; callers map the typed unavailable
    result to a retryable 503 and map malformed provider output to a non-retryable 502.
    """

    def draft(self, request: PresentationSvgDraftInput) -> PresentationSvgDraftOutput: ...


__all__ = [
    "PresentationSvgDraftInput",
    "PresentationSvgDraftOutput",
    "PresentationSvgDrafterUnavailable",
    "PresentationSvgDrafter",
]
