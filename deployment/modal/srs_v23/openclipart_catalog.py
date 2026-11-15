"""Openclipart Volume catalog import, lookup, and bounded SVG parsing."""

from __future__ import annotations

import hashlib
import html
import json
import os
from pathlib import Path, PurePosixPath
import re
import sqlite3
from urllib.parse import urlsplit
import xml.etree.ElementTree as ET
from typing import Any, Iterable


CATALOG_SCHEMA = "Sketch2LifeOpenclipartVolumeCatalogV1"
CATALOG_ROOT_NAME = "openclipart-catalog"
CATALOG_ACTIVE_FILE = "active.json"
CATALOG_MANIFEST_FILE = "catalog-manifest.json"
CATALOG_DATABASE_FILE = "catalog.sqlite3"
MAX_GUIDE_SOURCE_BYTES = 128 * 1024
MAX_GUIDE_PATHS = 32
MAX_GUIDE_PATH_DATA_CHARS = 8192
MAX_GUIDE_TOTAL_PATH_CHARS = 128 * 1024
_SOURCE_PATH = re.compile(r"\Aassets/[0-9a-f]{2}/[0-9a-f]{64}\.svg\Z")
_SHA256 = re.compile(r"\A[0-9a-f]{64}\Z")
_SEARCH_PATTERN = re.compile(r"[^\W_]+", re.UNICODE)
_PATH_PATTERN = re.compile(
    r"[MmZzLlHhVvCcSsQqTtAa]|[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?"
)
_ALLOWED_CHILDREN = {"g", "path", "title", "desc", "metadata"}
_SAFE_GROUP_ATTRS = {
    "id", "style", "fill", "stroke", "stroke-width", "stroke-linecap", "stroke-linejoin"
}
_SAFE_PATH_ATTRS = {
    "id", "d", "style", "fill", "stroke", "stroke-width", "stroke-linecap", "stroke-linejoin"
}
_SAFE_STYLE_PROPERTIES = {"fill", "stroke", "stroke-width", "stroke-linecap", "stroke-linejoin"}
_SVG_NS = "http://www.w3.org/2000/svg"


class OpenclipartCatalogError(ValueError):
    """A bounded catalog operation or source SVG failed validation."""


def normalize_search_terms(values: Iterable[str], *, limit: int = 12) -> list[str]:
    terms: list[str] = []
    seen: set[str] = set()
    for value in values:
        if not isinstance(value, str):
            continue
        for token in _SEARCH_PATTERN.findall(value.casefold()):
            token = token.strip()
            if len(token) < 2 or token in seen:
                continue
            seen.add(token)
            terms.append(token)
            if len(terms) >= limit:
                return terms
    return terms


def parse_safe_guide_svg(svg_bytes: bytes) -> dict[str, Any]:
    """Extract exact path geometry only from a deliberately small static SVG subset."""
    if not isinstance(svg_bytes, bytes) or not svg_bytes or len(svg_bytes) > MAX_GUIDE_SOURCE_BYTES:
        raise OpenclipartCatalogError("SVG_CATALOG_SOURCE_SIZE_REJECTED")
    lowered = svg_bytes.lower()
    if any(marker in lowered for marker in (b"<!doctype", b"<!entity", b"<script", b"javascript:", b"url(", b"foreignobject")):
        raise OpenclipartCatalogError("SVG_CATALOG_ACTIVE_CONTENT_REJECTED")
    try:
        root = ET.fromstring(svg_bytes)
    except ET.ParseError as exc:
        raise OpenclipartCatalogError("SVG_CATALOG_XML_INVALID") from exc
    if _local_name(root.tag) != "svg" or _namespace(root.tag) not in ("", _SVG_NS):
        raise OpenclipartCatalogError("SVG_CATALOG_ROOT_REJECTED")
    if any(_local_name(key).lower().startswith("on") for key in root.attrib):
        raise OpenclipartCatalogError("SVG_CATALOG_EVENT_ATTRIBUTE_REJECTED")
    view_box = _parse_view_box(root.attrib.get("viewBox") or root.attrib.get("viewbox"))
    paths: list[dict[str, Any]] = []
    total_chars = 0
    root_style = _parse_inline_style(root.attrib.get("style", ""))
    inherited_fill = root_style.get("fill", root.attrib.get("fill", "#000000"))
    inherited_stroke = root_style.get("stroke", root.attrib.get("stroke", "none"))
    inherited_width = root_style.get("stroke-width", root.attrib.get("stroke-width", "1"))
    inherited_cap = root_style.get("stroke-linecap", root.attrib.get("stroke-linecap"))
    inherited_join = root_style.get("stroke-linejoin", root.attrib.get("stroke-linejoin"))
    if not _is_safe_color(inherited_fill) or not _is_safe_color(inherited_stroke):
        raise OpenclipartCatalogError("SVG_CATALOG_COLOR_REJECTED")

    def walk(
        node: ET.Element,
        inherited_fill: str,
        inherited_stroke: str,
        inherited_width: str,
        inherited_cap: str | None,
        inherited_join: str | None,
    ) -> None:
        nonlocal total_chars
        for child in list(node):
            name = _local_name(child.tag)
            if name not in _ALLOWED_CHILDREN or _namespace(child.tag) not in ("", _SVG_NS):
                raise OpenclipartCatalogError("SVG_CATALOG_ELEMENT_REJECTED")
            if name in {"title", "desc", "metadata"}:
                continue
            if any(_local_name(key).lower().startswith("on") for key in child.attrib):
                raise OpenclipartCatalogError("SVG_CATALOG_EVENT_ATTRIBUTE_REJECTED")
            if name == "g":
                if set(child.attrib) - _SAFE_GROUP_ATTRS:
                    raise OpenclipartCatalogError("SVG_CATALOG_GROUP_ATTRIBUTE_REJECTED")
                group_style = _parse_inline_style(child.attrib.get("style", ""))
                group_fill = group_style.get("fill", child.attrib.get("fill", inherited_fill))
                group_stroke = group_style.get("stroke", child.attrib.get("stroke", inherited_stroke))
                group_width = group_style.get("stroke-width", child.attrib.get("stroke-width", inherited_width))
                group_cap = group_style.get("stroke-linecap", child.attrib.get("stroke-linecap", inherited_cap))
                group_join = group_style.get("stroke-linejoin", child.attrib.get("stroke-linejoin", inherited_join))
                if not _is_safe_color(group_fill) or not _is_safe_color(group_stroke):
                    raise OpenclipartCatalogError("SVG_CATALOG_COLOR_REJECTED")
                walk(child, group_fill, group_stroke, group_width, group_cap, group_join)
                continue
            if set(child.attrib) - _SAFE_PATH_ATTRS or child.text and child.text.strip():
                raise OpenclipartCatalogError("SVG_CATALOG_PATH_ATTRIBUTE_REJECTED")
            path_data = child.attrib.get("d", "").strip()
            if not _is_bounded_path_data(path_data):
                raise OpenclipartCatalogError("SVG_CATALOG_PATH_DATA_REJECTED")
            total_chars += len(path_data)
            if total_chars > MAX_GUIDE_TOTAL_PATH_CHARS:
                raise OpenclipartCatalogError("SVG_CATALOG_PATH_COMPLEXITY_REJECTED")
            fill = child.attrib.get("fill", inherited_fill)
            stroke = child.attrib.get("stroke", inherited_stroke)
            path_style = _parse_inline_style(child.attrib.get("style", ""))
            fill = path_style.get("fill", fill)
            stroke = path_style.get("stroke", stroke)
            stroke_width = _parse_stroke_width(
                child.attrib.get("stroke-width", path_style.get("stroke-width", inherited_width))
            )
            if not _is_safe_color(fill) or not _is_safe_color(stroke):
                raise OpenclipartCatalogError("SVG_CATALOG_COLOR_REJECTED")
            paths.append(
                {
                    "path_id": f"oc_path_{len(paths) + 1:03d}",
                    "d": path_data,
                    "fill": fill,
                    "stroke": stroke,
                    "stroke_width": stroke_width,
                    "stroke_linecap": _safe_linecap(
                        child.attrib.get("stroke-linecap", path_style.get("stroke-linecap", inherited_cap))
                    ),
                    "stroke_linejoin": _safe_linejoin(
                        child.attrib.get("stroke-linejoin", path_style.get("stroke-linejoin", inherited_join))
                    ),
                }
            )
            if len(paths) > MAX_GUIDE_PATHS:
                raise OpenclipartCatalogError("SVG_CATALOG_PATH_COUNT_REJECTED")

    walk(root, inherited_fill, inherited_stroke, inherited_width, inherited_cap, inherited_join)
    if not 4 <= len(paths) <= MAX_GUIDE_PATHS:
        raise OpenclipartCatalogError("SVG_CATALOG_PATH_COUNT_REJECTED")
    return {"view_box": view_box, "paths": paths, "source_path_count": len(paths)}


def initialize_catalog_database(connection: sqlite3.Connection) -> None:
    connection.execute("PRAGMA journal_mode=WAL")
    connection.execute(
        """CREATE TABLE IF NOT EXISTS source_assets (
            source_id TEXT PRIMARY KEY,
            asset_id TEXT NOT NULL,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            tags TEXT NOT NULL,
            artist_name TEXT NOT NULL,
            page_url TEXT NOT NULL,
            license_id TEXT NOT NULL,
            source_sha256 TEXT NOT NULL,
            asset_path TEXT NOT NULL,
            eligible INTEGER NOT NULL,
            eligibility_reason TEXT NOT NULL,
            shard_name TEXT NOT NULL
        )"""
    )
    connection.execute(
        "CREATE INDEX IF NOT EXISTS source_assets_eligible_idx ON source_assets(eligible, asset_id)"
    )
    connection.execute(
        """CREATE VIRTUAL TABLE IF NOT EXISTS source_assets_fts USING fts5(
            source_id UNINDEXED,
            title,
            description,
            tags,
            tokenize='unicode61 remove_diacritics 2'
        )"""
    )
    connection.commit()


def index_source_record(
    connection: sqlite3.Connection,
    *,
    record: dict[str, Any],
    shard_name: str,
    catalog_root: Path,
) -> tuple[bool, bool, str]:
    license_id = str(record.get("license", "")).strip().upper()
    if license_id not in {"CC0", "CC0-1.0"}:
        return False, False, "LICENSE_NOT_CC0"
    svg = record.get("svg_content")
    page_url = str(record.get("page_url", "")).strip()
    if not isinstance(svg, str) or not svg or not _is_openclipart_page(page_url):
        return False, False, "SOURCE_RECORD_INVALID"
    svg_bytes = svg.encode("utf-8")
    source_sha256 = hashlib.sha256(svg_bytes).hexdigest()
    source_id = hashlib.sha256(f"{page_url}\n{source_sha256}".encode("utf-8")).hexdigest()
    asset_id = _asset_id_from_url(page_url, source_sha256)
    relative_path = f"assets/{source_sha256[:2]}/{source_sha256}.svg"
    destination = catalog_root / relative_path
    destination.parent.mkdir(parents=True, exist_ok=True)
    if not destination.exists() or _sha256_file(destination) != source_sha256:
        temporary = destination.with_name(f".{destination.name}.{os.getpid()}.tmp")
        temporary.write_bytes(svg_bytes)
        os.replace(temporary, destination)

    eligible = False
    reason = "SVG_NOT_GUIDE_ELIGIBLE"
    try:
        parse_safe_guide_svg(svg_bytes)
        eligible = True
        reason = "ELIGIBLE"
    except OpenclipartCatalogError as exc:
        reason = str(exc)

    title = _bounded_text(record.get("title"), 300)
    description = _bounded_text(record.get("description"), 2_000)
    raw_tags = record.get("tags")
    tags = " ".join(_bounded_text(item, 80) for item in raw_tags[:80]) if isinstance(raw_tags, list) else ""
    artist = _bounded_text(record.get("artist_name"), 120)
    connection.execute("DELETE FROM source_assets_fts WHERE source_id = ?", (source_id,))
    connection.execute(
        """INSERT OR REPLACE INTO source_assets (
            source_id, asset_id, title, description, tags, artist_name, page_url,
            license_id, source_sha256, asset_path, eligible, eligibility_reason, shard_name
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            source_id,
            asset_id,
            title,
            description,
            tags,
            artist,
            page_url,
            "CC0-1.0",
            source_sha256,
            relative_path,
            int(eligible),
            reason,
            shard_name,
        ),
    )
    connection.execute(
        "INSERT INTO source_assets_fts(source_id, title, description, tags) VALUES (?, ?, ?, ?)",
        (source_id, title, description, tags),
    )
    return True, eligible, reason


def search_guide_candidates(
    catalog_root: Path,
    search_terms: Iterable[str],
    *,
    limit: int = 8,
) -> list[dict[str, Any]]:
    terms = normalize_search_terms(search_terms)
    if not terms:
        return []
    manifest_path = catalog_root / CATALOG_ACTIVE_FILE
    try:
        active = json.loads(manifest_path.read_text(encoding="utf-8"))
        revision = active["dataset_revision"]
        revision_root = catalog_root / revision
        manifest = json.loads((revision_root / CATALOG_MANIFEST_FILE).read_text(encoding="utf-8"))
    except (OSError, KeyError, TypeError, json.JSONDecodeError) as exc:
        raise OpenclipartCatalogError("SVG_CATALOG_NOT_READY") from exc
    if (
        manifest.get("schema_version") != CATALOG_SCHEMA
        or manifest.get("status") != "READY"
        or manifest.get("dataset_revision") != revision
    ):
        raise OpenclipartCatalogError("SVG_CATALOG_NOT_READY")
    expression = " OR ".join(f'"{term.replace(chr(34), "")}"' for term in terms)
    database_path = revision_root / CATALOG_DATABASE_FILE
    # Volume mounts are read-only in the inference worker. immutable=1 avoids
    # SQLite trying to create WAL/SHM sidecars beside the catalog database.
    with sqlite3.connect(f"file:{database_path.as_posix()}?mode=ro&immutable=1", uri=True) as connection:
        rows = connection.execute(
            """SELECT source_assets.source_id, source_assets.asset_id, source_assets.title,
                      source_assets.description, source_assets.tags, source_assets.artist_name,
                      source_assets.page_url, source_assets.license_id, source_assets.source_sha256,
                      source_assets.asset_path, source_assets.shard_name, bm25(source_assets_fts) AS rank
               FROM source_assets_fts
               JOIN source_assets USING (source_id)
               WHERE source_assets_fts MATCH ? AND source_assets.eligible = 1
               ORDER BY rank ASC, source_assets.source_id ASC
               LIMIT ?""",
            (expression, max(1, min(limit, 16))),
        ).fetchall()
    candidates: list[dict[str, Any]] = []
    for row in rows:
        candidate = dict(
            zip(
                (
                    "source_id", "asset_id", "title", "description", "tags", "artist_name",
                    "page_url", "license_id", "source_sha256", "asset_path", "shard_name", "rank",
                ),
                row,
                strict=True,
            )
        )
        asset_path = str(candidate["asset_path"])
        if _SOURCE_PATH.fullmatch(asset_path) is None or not _is_openclipart_page(candidate["page_url"]):
            continue
        svg_bytes = (revision_root / PurePosixPath(asset_path)).read_bytes()
        if hashlib.sha256(svg_bytes).hexdigest() != candidate["source_sha256"]:
            raise OpenclipartCatalogError("SVG_CATALOG_ASSET_HASH_MISMATCH")
        candidate["svg_bytes"] = svg_bytes
        candidate["dataset_revision"] = revision
        candidate["dataset_manifest"] = manifest
        try:
            candidate["parsed_svg"] = parse_safe_guide_svg(svg_bytes)
        except OpenclipartCatalogError:
            continue
        candidates.append(candidate)
    return candidates


def read_catalog_manifest(catalog_root: Path) -> dict[str, Any] | None:
    try:
        active_path = catalog_root / CATALOG_ACTIVE_FILE
        active = json.loads(active_path.read_text(encoding="utf-8"))
        revision_root = catalog_root / active["dataset_revision"]
        manifest_path = revision_root / CATALOG_MANIFEST_FILE
        if active.get("manifest_sha256") != _sha256_file(manifest_path):
            return None
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, KeyError, TypeError, json.JSONDecodeError):
        return None
    return manifest if manifest.get("schema_version") == CATALOG_SCHEMA else None


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def source_reference_metadata(candidate: dict[str, Any]) -> dict[str, Any]:
    return {
        "asset_id": candidate["asset_id"],
        "dataset_name": "Openclipart",
        "dataset_revision": candidate["dataset_revision"],
        "dataset_doi": None,
        "dataset_uri": candidate["page_url"],
        "source_sha256": candidate["source_sha256"],
        "license_id": "CC0-1.0",
        "license_uri": "https://creativecommons.org/publicdomain/zero/1.0/",
    }


def _is_bounded_path_data(value: str) -> bool:
    if not value or len(value) > MAX_GUIDE_PATH_DATA_CHARS or "<" in value or ">" in value:
        return False
    tokens = _PATH_PATTERN.findall(value)
    return bool(tokens) and "".join(tokens).replace("+", "") == re.sub(r"[\s,]+", "", value).replace("+", "")


def _parse_view_box(value: str | None) -> str:
    if not isinstance(value, str):
        raise OpenclipartCatalogError("SVG_CATALOG_VIEWBOX_MISSING")
    parts = value.replace(",", " ").split()
    if len(parts) != 4:
        raise OpenclipartCatalogError("SVG_CATALOG_VIEWBOX_INVALID")
    try:
        numbers = [float(part) for part in parts]
    except ValueError as exc:
        raise OpenclipartCatalogError("SVG_CATALOG_VIEWBOX_INVALID") from exc
    if any(not (number == number and abs(number) <= 1_000_000) for number in numbers):
        raise OpenclipartCatalogError("SVG_CATALOG_VIEWBOX_INVALID")
    if numbers[2] <= 0 or numbers[3] <= 0 or numbers[2] > 100_000 or numbers[3] > 100_000:
        raise OpenclipartCatalogError("SVG_CATALOG_VIEWBOX_INVALID")
    return " ".join(_format_number(number) for number in numbers)


def _parse_stroke_width(value: str) -> float:
    if isinstance(value, str) and value.endswith("px"):
        value = value[:-2].strip()
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise OpenclipartCatalogError("SVG_CATALOG_STROKE_WIDTH_INVALID") from exc
    if not 0 < result <= 64:
        raise OpenclipartCatalogError("SVG_CATALOG_STROKE_WIDTH_INVALID")
    return result


def _parse_inline_style(value: str) -> dict[str, str]:
    if not value:
        return {}
    if len(value) > 512 or any(marker in value.casefold() for marker in ("url(", "!important", "@", "{", "}")):
        raise OpenclipartCatalogError("SVG_CATALOG_STYLE_REJECTED")
    result: dict[str, str] = {}
    for declaration in value.split(";"):
        declaration = declaration.strip()
        if not declaration:
            continue
        if ":" not in declaration:
            raise OpenclipartCatalogError("SVG_CATALOG_STYLE_REJECTED")
        key, raw = declaration.split(":", 1)
        key = key.strip().casefold()
        raw = raw.strip()
        if key not in _SAFE_STYLE_PROPERTIES or not raw or key in result:
            raise OpenclipartCatalogError("SVG_CATALOG_STYLE_REJECTED")
        if key in {"fill", "stroke"} and not _is_safe_color(raw):
            raise OpenclipartCatalogError("SVG_CATALOG_COLOR_REJECTED")
        if key == "stroke-width":
            _parse_stroke_width(raw)
        if key == "stroke-linecap" and raw not in {"butt", "round", "square"}:
            raise OpenclipartCatalogError("SVG_CATALOG_STYLE_REJECTED")
        if key == "stroke-linejoin" and raw not in {"miter", "round", "bevel"}:
            raise OpenclipartCatalogError("SVG_CATALOG_STYLE_REJECTED")
        result[key] = raw
    return result


def _is_safe_color(value: str) -> bool:
    if value == "none":
        return True
    if re.fullmatch(r"#[0-9a-fA-F]{6}", value):
        return True
    if re.fullmatch(r"#[0-9a-fA-F]{3}", value):
        return True
    return value.casefold() in {
        "black", "white", "red", "green", "blue", "yellow", "orange", "purple", "gray", "grey",
        "pink", "brown", "navy", "teal", "lime", "maroon", "olive", "silver", "aqua", "fuchsia",
    }


def _safe_linecap(value: str | None) -> str:
    if value is None:
        return "round"
    if value not in {"butt", "round", "square"}:
        raise OpenclipartCatalogError("SVG_CATALOG_LINECAP_REJECTED")
    return value


def _safe_linejoin(value: str | None) -> str:
    if value is None:
        return "round"
    if value not in {"miter", "round", "bevel"}:
        raise OpenclipartCatalogError("SVG_CATALOG_LINEJOIN_REJECTED")
    return value


def _is_openclipart_page(value: str) -> bool:
    if not isinstance(value, str) or len(value) > 2048:
        return False
    parsed = urlsplit(value)
    return parsed.scheme == "https" and parsed.hostname == "openclipart.org" and not parsed.username and not parsed.password


def _asset_id_from_url(page_url: str, source_sha256: str) -> str:
    tail = page_url.rstrip("/").rsplit("/", 1)[-1]
    slug = re.sub(r"[^A-Za-z0-9._:-]", "_", tail)[:64].strip("._:-")
    return f"openclipart-{slug or source_sha256[:24]}"


def _bounded_text(value: Any, max_chars: int) -> str:
    if isinstance(value, list):
        value = " ".join(str(item) for item in value)
    if not isinstance(value, str):
        return ""
    value = re.sub(r"<[^>]{0,512}>", " ", html.unescape(value))
    return " ".join(value.split())[:max_chars]


def _format_number(value: float) -> str:
    return str(int(value)) if value.is_integer() else format(value, ".8g")


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _namespace(tag: str) -> str:
    return tag[1:].split("}", 1)[0] if tag.startswith("{") else ""
