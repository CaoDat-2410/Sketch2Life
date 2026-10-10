"""Offline test boundary only; not wired to HTTP, Gate A/B or real inference."""
from dataclasses import dataclass
from typing import Literal, Protocol


@dataclass(frozen=True)
class IllustrationReference:
    role: Literal["SOURCE", "STYLE", "CHARACTER"]
    sha256: str
    artifact_ref: str

    def __post_init__(self) -> None:
        if self.role not in {"SOURCE", "STYLE", "CHARACTER"}:
            raise ValueError("REFERENCE_ROLE_INVALID")
        if len(self.sha256) != 64 or any(c not in "0123456789abcdef" for c in self.sha256):
            raise ValueError("REFERENCE_HASH_INVALID")
        if not self.artifact_ref.strip():
            raise ValueError("REFERENCE_REQUIRED")


@dataclass(frozen=True)
class IllustrationEditRequest:
    prompt: str
    model_profile: str
    references: tuple[IllustrationReference, ...]

    def __post_init__(self) -> None:
        if not self.prompt.strip() or not self.model_profile.strip():
            raise ValueError("EDIT_CONFIGURATION_REQUIRED")
        if sum(ref.role == "SOURCE" for ref in self.references) != 1:
            raise ValueError("EXACTLY_ONE_SOURCE_REQUIRED")


@dataclass(frozen=True)
class IllustrationEditReceipt:
    status: Literal["MOCK_ONLY", "BLOCKED"]
    reference_hashes: tuple[str, ...]
    detail: str


class IllustrationEditPort(Protocol):
    def prepare(self, request: IllustrationEditRequest) -> IllustrationEditReceipt: ...


class MockIllustrationEditAdapter:
    """Echo metadata without opening references or generating images."""

    def prepare(self, request: IllustrationEditRequest) -> IllustrationEditReceipt:
        return IllustrationEditReceipt(
            status="MOCK_ONLY",
            reference_hashes=tuple(ref.sha256 for ref in request.references),
            detail="No image generated; real multi-reference adapter requires model approval",
        )
