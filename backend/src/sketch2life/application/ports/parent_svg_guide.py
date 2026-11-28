"""Port for resolving curated source guides."""

from typing import Any, Protocol


class SourceGuideBuilder(Protocol):
    def __call__(self, subject: str, /) -> Any | None: ...
