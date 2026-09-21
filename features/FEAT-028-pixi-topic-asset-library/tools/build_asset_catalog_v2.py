"""Build the additive FEAT-028 semantic catalog without mutating catalog v1."""

from __future__ import annotations

import hashlib
import json
import struct
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "assets" / "generated"
SOURCE = GENERATED / "asset-catalog.v1.json"
DATA = ROOT / "assets" / "generated" / "REV2_ASSET_ROWS.tsv"
OUTPUT = GENERATED / "asset-catalog.v2.json"


def png_size(path: Path) -> tuple[int, int]:
    with path.open("rb") as stream:
        header = stream.read(24)
    if header[:8] != b"\x89PNG\r\n\x1a\n" or len(header) != 24:
        raise ValueError(f"invalid PNG header: {path.name}")
    return struct.unpack(">II", header[16:24])


def parse_rows() -> list[dict[str, Any]]:
    packs: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    for raw in DATA.read_text(encoding="utf-8").splitlines():
        if not raw or raw.startswith("#"):
            continue
        parts = raw.split("|")
        if parts[0] == "@":
            if len(parts) != 7:
                raise ValueError(f"invalid pack row: {raw}")
            current = {
                "atlasId": parts[1], "family": parts[2], "file": parts[3],
                "outputId": parts[4], "generatedAtUtc": parts[5],
                "promptId": parts[6], "sprites": [],
            }
            packs.append(current)
            continue
        if current is None or len(parts) not in {10, 11}:
            raise ValueError(f"invalid sprite row: {raw}")
        if len(parts) == 11:
            key, en, vi, aliases_en, aliases_vi, description_en, description_vi, tags, role, confusions, use = parts
        else:
            key, en, vi, aliases_en, aliases_vi, description_en, tags, role, confusions, use = parts
            description_vi = ""
        current["sprites"].append({
            "key": key, "label": {"en": en, "vi": vi},
            "aliases": {"en": aliases_en.split(";"), "vi": aliases_vi.split(";")},
            "descriptionEn": description_en, "descriptionVi": description_vi,
            "topicTags": tags.split(";"), "renderRole": role,
            "confusableWith": [x for x in confusions.split(";") if x],
            "intendedUse": use,
        })
    if len(packs) != 12 or any(len(pack["sprites"]) != 6 for pack in packs):
        raise ValueError("expected 12 new packs with six sprites each")
    return packs


def old_role(family: str) -> str:
    if family in {"weather-sky", "land-water-environments", "homes-buildings-places"}:
        return "ENVIRONMENT"
    if family == "motion-marks-effects":
        return "EFFECT"
    if family in {"everyday-classroom-household", "art-craft-play-montessori"}:
        return "PROP"
    return "SUBJECT"


def build() -> dict[str, Any]:
    old = json.loads(SOURCE.read_text(encoding="utf-8"))
    atlases: list[dict[str, Any]] = []
    assets: list[dict[str, Any]] = []
    for atlas in old["atlases"]:
        path = GENERATED / atlas["file"]
        width, height = png_size(path)
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest != atlas["sha256"]:
            raise ValueError(f"catalog-v1 hash mismatch: {path.name}")
        ids = []
        for sprite in atlas["sprites"]:
            index = sprite["frameIndex"]
            asset_id = sprite["id"]
            ids.append(asset_id)
            family = atlas["family"]
            label = sprite["label"]
            assets.append({
                "assetId": asset_id, "atlasId": atlas["atlasId"], "family": family,
                "semanticCategory": family, "label": label, "aliases": sprite["aliases"],
                "visualDescription": {
                    "en": f"One isolated flat 2D sticker of {label['en']}; only the named subject and defining parts.",
                    "vi": f"Một hình dán 2D phẳng, tách riêng của {label['vi']}; chỉ gồm chủ thể và các bộ phận đặc trưng.",
                },
                "topicTags": sorted({family.replace("-", " "), *sprite["aliases"]["en"]}),
                "renderRole": old_role(family), "confusableWith": [],
                "intendedUse": "Supplement only an adult-confirmed matching topic; never replace or redraw original child art.",
                "styleProfileIds": ["flat-childlike-doodle-v1"],
                "frame": {"x": (index % 2) * 512, "y": (index // 2) * 512, "width": 512, "height": 512},
                "reviewStatus": "REVIEW_PENDING", "runtimeEligible": False,
                "provenance": {
                    "sourceType": "BUILTIN_IMAGEGEN_OUTPUT",
                    "sourceManifest": "assets/generated/GENERATION_MANIFEST.md",
                    "assetFile": f"assets/generated/{atlas['file']}", "atlasSha256": digest,
                    "licenseStatus": "REVIEW_REQUIRED",
                    "rightsBasis": "ORIGINAL_GENERATED_DRAFT_REVIEW_REQUIRED",
                },
            })
        atlases.append({
            "atlasId": atlas["atlasId"], "family": atlas["family"], "file": atlas["file"],
            "width": width, "height": height, "sha256": digest,
            "reviewStatus": "REVIEW_PENDING", "generatorOutputId": None, "sprites": ids,
        })

    for pack in parse_rows():
        path = GENERATED / pack["file"]
        width, height = png_size(path)
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        ids = []
        for index, sprite in enumerate(pack["sprites"]):
            asset_id = f"topic.{pack['family']}.{sprite['key']}.v1"
            ids.append(asset_id)
            y = (index // 2) * 512
            vi = sprite["label"]["vi"]
            assets.append({
                "assetId": asset_id, "atlasId": pack["atlasId"], "family": pack["family"],
                "semanticCategory": pack["family"], "label": sprite["label"],
                "aliases": sprite["aliases"],
                "visualDescription": {
                    "en": sprite["descriptionEn"],
                    "vi": sprite["descriptionVi"] or f"Hình minh họa 2D phẳng, tách riêng: {vi}.",
                },
                "topicTags": sprite["topicTags"], "renderRole": sprite["renderRole"],
                "confusableWith": sprite["confusableWith"],
                "intendedUse": sprite["intendedUse"],
                "styleProfileIds": ["flat-childlike-doodle-v1"],
                "frame": {"x": (index % 2) * 512, "y": y, "width": 512, "height": min(512, height - y)},
                "reviewStatus": "REVIEW_PENDING", "runtimeEligible": False,
                "provenance": {
                    "sourceType": "BUILTIN_IMAGEGEN_OUTPUT", "generatorOutputId": pack["outputId"],
                    "generatedAtUtc": pack["generatedAtUtc"], "promptId": pack["promptId"],
                    "assetFile": f"assets/generated/{pack['file']}", "atlasSha256": digest,
                    "licenseStatus": "REVIEW_REQUIRED",
                    "rightsBasis": "ORIGINAL_GENERATED_DRAFT_REVIEW_REQUIRED",
                },
            })
        atlases.append({
            "atlasId": pack["atlasId"], "family": pack["family"], "file": pack["file"],
            "width": width, "height": height, "sha256": digest,
            "reviewStatus": "REVIEW_PENDING", "generatorOutputId": pack["outputId"],
            "generatedAtUtc": pack["generatedAtUtc"], "promptId": pack["promptId"],
            "sprites": ids,
        })

    ids = [item["assetId"] for item in assets]
    if len(ids) != 144 or len(set(ids)) != 144:
        raise ValueError("expected 144 unique stable asset IDs")
    return {
        "catalogId": "sketch2life.pixi.topic-assets", "schemaName": "PixiTopicAssetCatalogV2",
        "schemaVersion": "2.0", "catalogVersion": "2.0.0",
        "catalogStatus": "REVIEW_PENDING", "runtimeEligible": False,
        "generatedDate": "2026-09-17", "languages": ["en", "vi"],
        "selectionPolicy": {
            "sourceOfTruth": "ADULT_CONFIRMED_TOPIC",
            "aiInput": "CONFIRMED_TEXT_AND_TOP_K_DESCRIPTORS_ONLY_NO_SOURCE_IMAGE",
            "aiOutput": "CANDIDATE_ASSET_IDS_ONLY", "maxCandidates": 8,
            "runtimeEligibility": ["APPROVED", "APPLIED"],
            "noMatch": "PRESERVE_ORIGINAL_AND_QUEUE_AUTHORING_REVIEW",
            "providerCalls": False,
        },
        "styleProfile": {
            "styleProfileId": "flat-childlike-doodle-v1",
            "outline": "bold dark hand-drawn outline", "silhouette": "rounded and simple",
            "detail": "limited isolated sticker", "profileMatch": "GENERIC_NOT_CHILD_SPECIFIC",
        },
        "frameGrid": {
            "columns": 2, "rows": 3, "nominalCellWidth": 512, "nominalCellHeight": 512,
            "order": "row-major", "coordinatesOrigin": "top-left",
            "perFrameBoundsAreAuthoritative": True,
        },
        "atlases": atlases, "assets": assets,
        "usageGate": "All assets are drafts; runtime is forbidden until each sprite is visually approved and promoted.",
    }


if __name__ == "__main__":
    OUTPUT.write_text(json.dumps(build(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {OUTPUT.relative_to(ROOT)}")
