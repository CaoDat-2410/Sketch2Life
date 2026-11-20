"""Startup guard for the StoryRun-lite main demo (FEAT-066 T0.5, TD-18).

With the demo flag on, the StoryRun-lite router answers `/v1/story-runs*` and
`/v1/upload-sessions*` and the real routers that own the same literal paths are not
mounted. This module computes which real routes are replaced so the application can
refuse to start unless the developer acknowledges the replacement.

Everything here is pure: it reads route tables and an environment mapping only. It never
returns environment values, so its messages are safe to log.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass

ACKNOWLEDGEMENT_ENV = "STORYRUN_LITE_MAIN_DEMO_REPLACES_PARENT_ROUTER"
_PARAMETER = re.compile(r"\{[^}]*\}")
_EXAMPLE_LIMIT = 3


@dataclass(frozen=True)
class StoryDemoReplacement:
    """Real routes affected when the StoryRun-lite demo replaces a real router."""

    collides: tuple[str, ...] = ()
    """Real `METHOD path` labels that a demo route answers instead (same method, same shape)."""
    unmounted: tuple[str, ...] = ()
    """Every real `METHOD path` label whose router is not mounted while the demo is on."""

    @property
    def replaces_real_routes(self) -> bool:
        return bool(self.collides or self.unmounted)


def read_replacement_acknowledgement(environ: Mapping[str, str]) -> bool:
    """Return the acknowledgement flag; only `0` or `1` is accepted (value never echoed)."""
    raw = environ.get(ACKNOWLEDGEMENT_ENV, "0")
    if raw not in {"0", "1"}:
        raise ValueError(f"{ACKNOWLEDGEMENT_ENV} must be 0 or 1")
    return raw == "1"


def route_labels(routes: Iterable[object]) -> list[tuple[str, str]]:
    """Return `(METHOD, path)` pairs for routes that declare methods (mounts are skipped)."""
    pairs: list[tuple[str, str]] = []
    for route in routes:
        methods = getattr(route, "methods", None)
        path = getattr(route, "path", None)
        if not methods or not isinstance(path, str):
            continue
        pairs.extend((method, path) for method in sorted(methods))
    return pairs


def normalise_path(path: str) -> str:
    """Replace every path parameter name with a bare `{}` placeholder."""
    return _PARAMETER.sub("{}", path)


def paths_overlap(first: str, second: str) -> bool:
    """True when one request path can match both route paths.

    Parameter names are ignored (`{run_id}` equals `{run_ref}`), and a parameter segment
    overlaps a literal segment (`/readiness` against `/{run_id}`).
    """
    left = normalise_path(first).strip("/").split("/")
    right = normalise_path(second).strip("/").split("/")
    if len(left) != len(right):
        return False
    return all(a == b or a == "{}" or b == "{}" for a, b in zip(left, right, strict=True))


def shadowed_routes(
    real_routes: Iterable[object], demo_routes: Iterable[object]
) -> StoryDemoReplacement:
    """Compare the real route tables that the demo displaces with the demo route table."""
    demo = route_labels(demo_routes)
    real = route_labels(real_routes)
    collides = tuple(
        f"{method} {path}"
        for method, path in real
        if any(
            method == other_method and paths_overlap(path, other_path)
            for other_method, other_path in demo
        )
    )
    return StoryDemoReplacement(
        collides=collides,
        unmounted=tuple(f"{method} {path}" for method, path in real),
    )


def replacement_summary(replacement: StoryDemoReplacement) -> str:
    """Counts only, in the shape used by the startup warning."""
    return (
        f"collides={len(replacement.collides)} real_routes_unmounted={len(replacement.unmounted)}"
    )


def replacement_error_message(replacement: StoryDemoReplacement) -> str:
    """Startup error naming counts, at most three routes and the acknowledgement variable."""
    examples = (replacement.collides or replacement.unmounted)[:_EXAMPLE_LIMIT]
    return (
        "StoryRun-lite main demo replaces real routes "
        f"({replacement_summary(replacement)}; examples: {', '.join(examples)}). "
        f"Set {ACKNOWLEDGEMENT_ENV}=1 to acknowledge the replacement."
    )
