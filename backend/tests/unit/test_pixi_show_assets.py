from __future__ import annotations

import hashlib
from datetime import UTC, datetime, timedelta
from io import BytesIO
from pathlib import Path

import pytest
from PIL import Image, ImageDraw

from sketch2life.contracts.schemas.pixi_topic_asset_selection import TopicAssetDescriptorV1
from sketch2life.infrastructure.ai.pixi_subject_crop import (
    PixiSubjectCropUnavailable,
    build_pixi_subject_crop,
)
from sketch2life.infrastructure.catalog.pixi_show_assets import (
    PixiShowAssetService,
    PixiShowAssetUnavailable,
)


def _png(image: Image.Image) -> bytes:
    output = BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()


def _asset(atlas: bytes, *, license_status: str = "CLEARED") -> TopicAssetDescriptorV1:
    return TopicAssetDescriptorV1.model_validate(
        {
            "assetId": "flower-yellow-01",
            "atlasId": "garden-atlas",
            "family": "flower",
            "semanticCategory": "nature.flower",
            "label": {"en": "yellow flower", "vi": "bông hoa vàng"},
            "aliases": {"en": ["flower"], "vi": ["hoa"]},
            "visualDescription": {"en": "A small yellow flower.", "vi": "Một bông hoa vàng nhỏ."},
            "topicTags": ["flower", "garden", "hoa", "vườn"],
            "renderRole": "PROP",
            "confusableWith": [],
            "intendedUse": "A static companion beat.",
            "styleProfileIds": ["flat-childlike-doodle-v1"],
            "frame": {"x": 4, "y": 3, "width": 12, "height": 10},
            "reviewStatus": "APPROVED",
            "runtimeEligible": True,
            "provenance": {
                "sourceType": "BUILTIN_IMAGEGEN_OUTPUT",
                "sourceManifest": "local-review",
                "generatorOutputId": "synthetic-fixture",
                "generatedAtUtc": "2026-10-01T00:00:00Z",
                "promptId": "fixture",
                "assetFile": "atlas.png",
                "atlasSha256": hashlib.sha256(atlas).hexdigest(),
                "licenseStatus": license_status,
                "rightsBasis": "Synthetic test fixture only.",
            },
        }
    )


def test_subject_crop_is_mask_bounded_and_returns_full_frame_region() -> None:
    source = Image.new("RGB", (80, 64), "white")
    ImageDraw.Draw(source).ellipse((20, 12, 59, 52), fill=(20, 100, 220))
    mask = Image.new("L", source.size, 0)
    ImageDraw.Draw(mask).ellipse((23, 16, 56, 49), fill=255)

    crop, content_type, region = build_pixi_subject_crop(_png(source), _png(mask))

    assert content_type == "image/png"
    assert crop.startswith(b"\x89PNG\r\n\x1a\n")
    assert region.x == pytest.approx(23 / 80)
    assert region.y == pytest.approx(16 / 64)
    with Image.open(BytesIO(crop)) as decoded:
        assert max(decoded.size) <= 512
        assert decoded.size != source.size


def test_subject_crop_rejects_mismatched_and_near_full_frame_masks() -> None:
    source = _png(Image.new("RGB", (64, 64), "white"))
    other_size = _png(Image.new("L", (32, 32), 255))
    with pytest.raises(PixiSubjectCropUnavailable):
        build_pixi_subject_crop(source, other_size)

    full_mask = _png(Image.new("L", (64, 64), 255))
    with pytest.raises(PixiSubjectCropUnavailable):
        build_pixi_subject_crop(source, full_mask)


def test_asset_service_requires_approved_cleared_frame_and_issues_bounded_reads(
    monkeypatch,
) -> None:
    atlas_image = Image.new("RGBA", (24, 20), (0, 0, 0, 0))
    ImageDraw.Draw(atlas_image).rectangle((4, 3, 15, 12), fill=(250, 180, 20, 255))
    atlas = _png(atlas_image)
    feature_root = Path(__file__).parent / "_virtual_pixi_asset_root"
    original_read_bytes = Path.read_bytes

    def read_fixture(path: Path) -> bytes:
        if path == feature_root / "atlas.png":
            return atlas
        return original_read_bytes(path)

    monkeypatch.setattr(Path, "read_bytes", read_fixture)
    current = [datetime(2026, 10, 1, tzinfo=UTC)]
    service = PixiShowAssetService(
        feature_root=feature_root,
        assets=(_asset(atlas),),
        now=lambda: current[0],
    )

    reads = service.issue_reads(("flower-yellow-01",))
    assert len(reads) == 1
    read = reads[0]
    content, digest = service.read(read.read_capability)
    assert digest == hashlib.sha256(content).hexdigest() == read.sha256
    with Image.open(BytesIO(content)) as decoded:
        assert decoded.size == (12, 10)

    current[0] += timedelta(minutes=6)
    with pytest.raises(PixiShowAssetUnavailable):
        service.read(read.read_capability)


def test_asset_service_accepts_empty_reads_for_subject_only_show() -> None:
    service = PixiShowAssetService(feature_root=Path(__file__).parent, assets=())

    assert service.issue_reads(()) == ()


def test_asset_service_returns_small_ephemeral_previews_for_runtime_eligible_assets(
    monkeypatch,
) -> None:
    atlas_image = Image.new("RGBA", (24, 20), (0, 0, 0, 0))
    ImageDraw.Draw(atlas_image).rectangle((4, 3, 15, 12), fill=(250, 180, 20, 255))
    atlas = _png(atlas_image)
    feature_root = Path(__file__).parent / "_virtual_pixi_asset_root"
    original_read_bytes = Path.read_bytes

    def read_fixture(path: Path) -> bytes:
        if path == feature_root / "atlas.png":
            return atlas
        return original_read_bytes(path)

    monkeypatch.setattr(Path, "read_bytes", read_fixture)
    service = PixiShowAssetService(feature_root=feature_root, assets=(_asset(atlas),))

    previews = service.preview_candidates(("flower-yellow-01",))

    assert tuple(previews) == ("flower-yellow-01",)
    assert len(previews["flower-yellow-01"]) <= 30_000
    with Image.open(BytesIO(previews["flower-yellow-01"])) as preview:
        assert preview.size == (144, 108)
        assert preview.mode == "P"


def test_asset_service_does_not_preview_subject_or_rights_blocked_assets(monkeypatch) -> None:
    atlas = _png(Image.new("RGBA", (24, 20), (0, 0, 0, 0)))
    feature_root = Path(__file__).parent / "_virtual_pixi_asset_root"
    original_read_bytes = Path.read_bytes

    def read_fixture(path: Path) -> bytes:
        if path == feature_root / "atlas.png":
            return atlas
        return original_read_bytes(path)

    monkeypatch.setattr(Path, "read_bytes", read_fixture)
    subject = _asset(atlas).model_copy(update={"render_role": "SUBJECT"})
    service = PixiShowAssetService(feature_root=feature_root, assets=(subject,))
    with pytest.raises(PixiShowAssetUnavailable):
        service.preview_candidates(("flower-yellow-01",))


def test_asset_service_rejects_unreviewed_or_rights_blocked_assets(monkeypatch) -> None:
    atlas = _png(Image.new("RGBA", (24, 20), (0, 0, 0, 0)))
    feature_root = Path(__file__).parent / "_virtual_pixi_asset_root"
    original_read_bytes = Path.read_bytes

    def read_fixture(path: Path) -> bytes:
        if path == feature_root / "atlas.png":
            return atlas
        return original_read_bytes(path)

    monkeypatch.setattr(Path, "read_bytes", read_fixture)
    asset = _asset(atlas)
    blocked_provenance = asset.provenance.model_copy(update={"license_status": "REVIEW_REQUIRED"})
    blocked = asset.model_copy(update={"provenance": blocked_provenance})
    service = PixiShowAssetService(feature_root=feature_root, assets=(blocked,))
    with pytest.raises(PixiShowAssetUnavailable):
        service.issue_reads(("flower-yellow-01",))

    with pytest.raises(PixiShowAssetUnavailable):
        service.issue_reads(("missing-asset",))
