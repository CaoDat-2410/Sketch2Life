"""Pure rules for Teacher lesson presentations (SRS FR-T-19..22, BR-43/44)."""

from __future__ import annotations

import copy
import hashlib
import json
import re
from collections.abc import Mapping, Sequence
from typing import Any, cast
from urllib.parse import parse_qsl, urlsplit

MAX_SLIDES = 100
MAX_OPERATIONS = 50
MAX_PRESENTATION_JSON_BYTES = 1_048_576
MAX_TITLE_CHARS = 200
MAX_BODY_CHARS = 2_000
MAX_ALT_TEXT_CHARS = 300
MAX_VIDEO_URL_CHARS = 2_048
YOUTUBE_VIDEO_ID = re.compile(r"^[A-Za-z0-9_-]{11}$")
VIMEO_VIDEO_ID = re.compile(r"^[0-9]{1,12}$")


class PresentationRuleError(ValueError):
    """A deterministic domain refusal with the request field that caused it."""

    def __init__(self, code: str, field: str | None = None) -> None:
        self.code = code
        self.field = field
        super().__init__(code)


def canonical_json(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def _jsonb_sized(value: Any) -> bytes:
    # PostgreSQL's jsonb::text includes separators; enforce a conservative matching cap.
    return json.dumps(value, ensure_ascii=False, sort_keys=True).encode("utf-8")


def content_hash(value: Any) -> str:
    return hashlib.sha256(canonical_json(value)).hexdigest()


def command_fingerprint(
    *, method: str, route: str, ids: Mapping[str, str], if_match: str | None, body: Any
) -> str:
    """Bind replay to the route identity, concurrency fence and normalized body."""
    return content_hash(
        {
            "method": method.upper(),
            "route": route,
            "ids": dict(ids),
            "if_match": if_match,
            "body": body,
        }
    )


def parse_video_url(raw: str, *, field: str = "media.url") -> dict[str, str]:
    """Parse an allowlisted HTTPS YouTube/Vimeo URL without resolving or fetching it."""
    if (
        not isinstance(raw, str)
        or not raw
        or len(raw) > MAX_VIDEO_URL_CHARS
        or not raw.isascii()
        or any(ord(char) <= 0x20 or ord(char) >= 0x7F for char in raw)
    ):
        raise PresentationRuleError("INVALID_FORMAT", field)
    try:
        parsed = urlsplit(raw)
        host = parsed.hostname
        port = parsed.port
    except ValueError:
        raise PresentationRuleError("INVALID_FORMAT", field) from None
    if (
        "#" in raw
        or parsed.scheme.lower() != "https"
        or not host
        or not host.isascii()
        or parsed.username is not None
        or parsed.password is not None
        or port is not None
        or ":" in parsed.netloc
        or parsed.fragment
    ):
        raise PresentationRuleError("INVALID_FORMAT", field)
    host = host.lower()
    path = parsed.path
    provider: str | None = None
    video_id: str | None = None
    if host in {"youtube.com", "www.youtube.com", "m.youtube.com"}:
        if path == "/watch":
            try:
                pairs = parse_qsl(parsed.query, keep_blank_values=True, strict_parsing=True)
            except ValueError:
                raise PresentationRuleError("INVALID_FORMAT", field) from None
            if len(pairs) == 1 and pairs[0][0] == "v":
                video_id = pairs[0][1]
                provider = "YOUTUBE"
        elif path.startswith("/embed/") and not parsed.query:
            video_id = path[len("/embed/") :]
            provider = "YOUTUBE"
        if provider == "YOUTUBE" and (video_id is None or not YOUTUBE_VIDEO_ID.fullmatch(video_id)):
            video_id = None
    elif host == "youtu.be" and not parsed.query:
        candidate = path[1:] if path.startswith("/") else ""
        if "/" not in candidate and YOUTUBE_VIDEO_ID.fullmatch(candidate):
            provider, video_id = "YOUTUBE", candidate
    elif host in {"youtube-nocookie.com", "www.youtube-nocookie.com"} and not parsed.query:
        if path.startswith("/embed/"):
            candidate = path[len("/embed/") :]
            if "/" not in candidate and YOUTUBE_VIDEO_ID.fullmatch(candidate):
                provider, video_id = "YOUTUBE", candidate
    elif host == "vimeo.com" and not parsed.query:
        candidate = path[1:] if path.startswith("/") else ""
        if "/" not in candidate and VIMEO_VIDEO_ID.fullmatch(candidate):
            provider, video_id = "VIMEO", candidate
    elif host == "player.vimeo.com" and not parsed.query:
        prefix = "/video/"
        candidate = path[len(prefix) :] if path.startswith(prefix) else ""
        if "/" not in candidate and VIMEO_VIDEO_ID.fullmatch(candidate):
            provider, video_id = "VIMEO", candidate
    if provider is None or video_id is None:
        raise PresentationRuleError("INVALID_FORMAT", field)
    return {"provider": provider, "video_id": video_id}


def embed_url(provider: str, video_id: str) -> str:
    if provider == "YOUTUBE" and YOUTUBE_VIDEO_ID.fullmatch(video_id):
        return f"https://www.youtube-nocookie.com/embed/{video_id}"
    if provider == "VIMEO" and VIMEO_VIDEO_ID.fullmatch(video_id):
        return f"https://player.vimeo.com/video/{video_id}"
    raise PresentationRuleError("INVALID_FORMAT")


def validate_subject_text(value: str) -> str:
    if not isinstance(value, str) or not 1 <= len(value) <= 80:
        raise PresentationRuleError("INVALID_FORMAT", "subject_text")
    if not all(char.isalpha() or char.isdigit() or char in " -" for char in value):
        raise PresentationRuleError("INVALID_FORMAT", "subject_text")
    return value


def seed_slides(activities: Sequence[Mapping[str, Any]], *, seed: str) -> list[dict[str, Any]]:
    if seed == "BLANK":
        return [make_slide("", "", 1)]
    if seed != "PLAN_ACTIVITIES":
        raise PresentationRuleError("INVALID_FORMAT", "seed")
    if not activities:
        return [make_slide("", "", 1)]
    if len(activities) > MAX_SLIDES:
        raise PresentationRuleError("OUT_OF_RANGE", "seed")
    slides: list[dict[str, Any]] = []
    for index, activity in enumerate(activities, 1):
        title = activity.get("title")
        body = activity.get("description")
        if not isinstance(title, str) or not isinstance(body, str):
            raise PresentationRuleError("INVALID_FORMAT", f"activities[{index - 1}]")
        slides.append(make_slide(title[:MAX_TITLE_CHARS], body[:MAX_BODY_CHARS], index))
    return slides


def make_slide(
    title: str,
    body_text: str,
    position: int,
    *,
    slide_id: str | None = None,
) -> dict[str, Any]:
    from uuid import uuid4

    return {
        "slide_id": slide_id or str(uuid4()),
        "position": position,
        "title": title,
        "body_text": body_text,
        "media": None,
    }


def _slide_index(slides: list[dict[str, Any]], slide_id: Any, field: str) -> int:
    if not isinstance(slide_id, str):
        raise PresentationRuleError("INVALID_FORMAT", field)
    for index, slide in enumerate(slides):
        if slide.get("slide_id") == slide_id:
            return index
    raise PresentationRuleError("INVALID_FORMAT", field)


def _renumber(slides: list[dict[str, Any]]) -> None:
    for index, slide in enumerate(slides, 1):
        slide["position"] = index


def normalize_media(media: Mapping[str, Any], *, field: str = "media") -> dict[str, Any]:
    """Convert media input to the JSON-only, provider-free revision representation."""
    kind = media.get("kind")
    alt_text = media.get("alt_text", "")
    if not isinstance(alt_text, str) or len(alt_text) > MAX_ALT_TEXT_CHARS:
        raise PresentationRuleError("INVALID_FORMAT", f"{field}.alt_text")
    if kind == "IMAGE":
        asset_ref = media.get("asset_ref")
        if not isinstance(asset_ref, str) or not asset_ref.startswith("upl_"):
            raise PresentationRuleError("INVALID_FORMAT", f"{field}.asset_ref")
        result = {"kind": "IMAGE", "upload_id": asset_ref[4:], "alt_text": alt_text}
        for metadata in ("media_type", "width", "height"):
            if metadata in media:
                result[metadata] = media[metadata]
        return result
    if kind == "SVG_CATALOG":
        entry_id = media.get("catalog_entry_id")
        if not isinstance(entry_id, str) or not entry_id:
            raise PresentationRuleError("INVALID_FORMAT", f"{field}.catalog_entry_id")
        result = {"kind": kind, "catalog_entry_id": entry_id, "alt_text": alt_text}
        if "canonical_sha256" in media:
            result["canonical_sha256"] = media["canonical_sha256"]
        return result
    if kind == "SVG_AI":
        draft_id = media.get("svg_draft_id")
        if not isinstance(draft_id, str) or not draft_id:
            raise PresentationRuleError("INVALID_FORMAT", f"{field}.svg_draft_id")
        result = {"kind": kind, "svg_draft_id": draft_id, "alt_text": alt_text}
        if "canonical_sha256" in media:
            result["canonical_sha256"] = media["canonical_sha256"]
        return result
    if kind == "VIDEO_EMBED":
        parsed = parse_video_url(cast("str", media.get("url")), field=f"{field}.url")
        return {"kind": kind, **parsed, "alt_text": ""}
    raise PresentationRuleError("INVALID_FORMAT", f"{field}.kind")


def apply_operations(
    current_slides: Sequence[Mapping[str, Any]],
    operations: Sequence[Mapping[str, Any]],
    *,
    operation_index_offset: int = 0,
) -> list[dict[str, Any]]:
    """Apply a bounded ordered edit list on a copy; callers persist only on full success."""
    if not 1 <= len(operations) <= MAX_OPERATIONS:
        raise PresentationRuleError("OUT_OF_RANGE", "operations")
    slides = copy.deepcopy([dict(slide) for slide in current_slides])
    for local_index, operation in enumerate(operations):
        index = operation_index_offset + local_index
        op = operation.get("op")
        prefix = f"operations[{index}]"
        if op == "UPDATE_SLIDE":
            position = _slide_index(slides, operation.get("slide_id"), f"{prefix}.slide_id")
            for name, maximum in (("title", MAX_TITLE_CHARS), ("body_text", MAX_BODY_CHARS)):
                value = operation.get(name)
                if value is not None:
                    if not isinstance(value, str) or len(value) > maximum:
                        raise PresentationRuleError("INVALID_FORMAT", f"{prefix}.{name}")
                    slides[position][name] = value
        elif op == "ADD_SLIDE":
            if len(slides) >= MAX_SLIDES:
                raise PresentationRuleError("OUT_OF_RANGE", prefix)
            title, body = operation.get("title"), operation.get("body_text")
            if not isinstance(title, str) or len(title) > MAX_TITLE_CHARS:
                raise PresentationRuleError("INVALID_FORMAT", f"{prefix}.title")
            if not isinstance(body, str) or len(body) > MAX_BODY_CHARS:
                raise PresentationRuleError("INVALID_FORMAT", f"{prefix}.body_text")
            after = operation.get("after_slide_id")
            if after is None:
                insert_at = 0
            else:
                insert_at = _slide_index(slides, after, f"{prefix}.after_slide_id") + 1
            slides.insert(insert_at, make_slide(title, body, 1))
            _renumber(slides)
        elif op == "DELETE_SLIDE":
            position = _slide_index(slides, operation.get("slide_id"), f"{prefix}.slide_id")
            if len(slides) == 1:
                raise PresentationRuleError("OUT_OF_RANGE", f"{prefix}.slide_id")
            del slides[position]
            _renumber(slides)
        elif op == "MOVE_SLIDE":
            position = _slide_index(slides, operation.get("slide_id"), f"{prefix}.slide_id")
            target = operation.get("to_position")
            if (
                isinstance(target, bool)
                or not isinstance(target, int)
                or not 1 <= target <= len(slides)
            ):
                raise PresentationRuleError("OUT_OF_RANGE", f"{prefix}.to_position")
            slide = slides.pop(position)
            slides.insert(target - 1, slide)
            _renumber(slides)
        elif op == "SET_MEDIA":
            position = _slide_index(slides, operation.get("slide_id"), f"{prefix}.slide_id")
            placement = operation.get("placement")
            if placement not in {"FULL", "LEFT", "RIGHT"}:
                raise PresentationRuleError("INVALID_FORMAT", f"{prefix}.placement")
            media = operation.get("media")
            if not isinstance(media, Mapping):
                raise PresentationRuleError("INVALID_FORMAT", f"{prefix}.media")
            slides[position]["media"] = {
                **normalize_media(media, field=f"{prefix}.media"),
                "placement": placement,
            }
        elif op == "CLEAR_MEDIA":
            position = _slide_index(slides, operation.get("slide_id"), f"{prefix}.slide_id")
            slides[position]["media"] = None
        else:
            raise PresentationRuleError("INVALID_FORMAT", f"{prefix}.op")
        if len(slides) > MAX_SLIDES:
            raise PresentationRuleError("OUT_OF_RANGE", prefix)
    if len(_jsonb_sized(slides)) > MAX_PRESENTATION_JSON_BYTES:
        raise PresentationRuleError("OUT_OF_RANGE", "operations")
    return slides


def media_state(
    media: Mapping[str, Any] | None,
    *,
    catalog_states: Mapping[str, str] | None = None,
    draft_states: Mapping[str, str] | None = None,
) -> str | None:
    if media is None:
        return None
    if media.get("kind") == "SVG_CATALOG":
        return (
            "CURRENT"
            if (catalog_states or {}).get(str(media.get("catalog_entry_id"))) == "ACTIVE"
            else "STALE"
        )
    if media.get("kind") == "SVG_AI":
        return (
            "CURRENT"
            if (draft_states or {}).get(str(media.get("svg_draft_id"))) == "ACCEPTED"
            else "STALE"
        )
    return "CURRENT"


def stale_reasons(
    *,
    pinned_plan_revision_id: str,
    current_plan_revision_id: str | None,
    slides: Sequence[Mapping[str, Any]],
    catalog_states: Mapping[str, str] | None = None,
    draft_states: Mapping[str, str] | None = None,
) -> list[str]:
    reasons: list[str] = []
    if current_plan_revision_id != pinned_plan_revision_id:
        reasons.append("PLAN_REVISION_CHANGED")
    if any(
        media_state(
            slide.get("media"), catalog_states=catalog_states, draft_states=draft_states
        ) == "STALE"
        for slide in slides
    ):
        reasons.append("MEDIA_SOURCE_CHANGED")
    return reasons


def etag(revision: int) -> str:
    return f'"{revision}"'


__all__ = [
    "MAX_ALT_TEXT_CHARS",
    "MAX_BODY_CHARS",
    "MAX_OPERATIONS",
    "MAX_PRESENTATION_JSON_BYTES",
    "MAX_SLIDES",
    "MAX_TITLE_CHARS",
    "MAX_VIDEO_URL_CHARS",
    "PresentationRuleError",
    "apply_operations",
    "canonical_json",
    "command_fingerprint",
    "content_hash",
    "embed_url",
    "etag",
    "make_slide",
    "media_state",
    "normalize_media",
    "parse_video_url",
    "seed_slides",
    "stale_reasons",
    "validate_subject_text",
]
