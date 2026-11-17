from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest
from PIL import Image, ImageDraw

from sketch2life.infrastructure.catalog.pixi_show_assets import (
    PixiShowAssetService,
    PixiShowAssetUnavailable,
)

_ROOT = Path(__file__).resolve().parents[3]
_FEATURE_ROOT = _ROOT / "features" / "FEAT-028-pixi-topic-asset-library"
_MANIFEST = _FEATURE_ROOT / "assets" / "generated" / "motion-cycle-review-manifest.rev1.json"


def _synthetic_atlas() -> bytes:
    from io import BytesIO

    image = Image.new("RGBA", (64, 16), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    colors = ((250, 70, 50, 255), (40, 180, 90, 255), (50, 90, 230, 255), (240, 180, 20, 255))
    for index, color in enumerate(colors):
        x = index * 16
        draw.ellipse((x + 4, 4, x + 11, 11), fill=color)
    output = BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()


def _eligible_manifest(atlas: bytes) -> dict[str, Any]:
    return {
        "schemaName": "PixiMotionCycleDraftManifest",
        "schemaVersion": "1.0",
        "ownerVisualApproval": {"decision": "APPROVED"},
        "runtimeEligible": True,
        "commonGates": {
            "rightsStatus": "CLEARED",
            "cropPivotLoopStatus": "QA_PASSED",
            "catalogStatus": "REGISTERED",
            "rendererStatus": "VERIFIED",
            "runtimeEligible": True,
        },
        "cycles": [
            {
                "cycleId": "motion.flyer-fixture.v1",
                "behaviorClassId": "flyer",
                "variantId": "bird-fixture",
                "assetFile": "fixture.png",
                "sha256": hashlib.sha256(atlas).hexdigest(),
                "canvas": [64, 16],
                "frameCount": 4,
                "layout": "STRIP_1X4",
                "visualReview": "VISUAL_APPROVED_OWNER_TEST",
            }
        ],
    }


def _local_preview_catalog(atlas: bytes) -> dict[str, Any]:
    return {
        "schemaName": "PixiMotionCycleLocalPreviewCatalog",
        "schemaVersion": "1.0",
        "activationScope": "LOCAL_ANDROID_DEV_PREVIEW",
        "rightsStatus": "REVIEW_REQUIRED",
        "productionRuntimeEligible": False,
        "runtimeEligible": False,
        "commonGatesRemainClosed": True,
        "cycles": [
            {
                "cycleId": "motion.flyer-fixture.v1",
                "behaviorClassId": "flyer",
                "variantId": "bird-fixture",
                "assetFile": "fixture.png",
                "sha256": hashlib.sha256(atlas).hexdigest(),
                "frameCount": 4,
                "layout": "STRIP_1X4",
                "devPreviewStatus": "QA_PASSED_LOCAL_PREVIEW",
            }
        ],
    }


def test_real_expansion_manifest_fails_closed_on_unresolved_rights() -> None:
    service = PixiShowAssetService(
        feature_root=_FEATURE_ROOT,
        assets=(),
        motion_cycle_manifest_path=_MANIFEST,
    )

    with pytest.raises(PixiShowAssetUnavailable) as error:
        service.issue_motion_cycle_read(
            "motion.flyer-songbird.v2",
            start_seconds=0,
            end_seconds=5,
            x=0.82,
            y=0.82,
        )

    assert error.value.reason_code == "RIGHTS_NOT_CLEARED"


@pytest.mark.parametrize(
    ("gate", "expected_reason"),
    [
        ("visual", "VISUAL_REVIEW_REQUIRED"),
        ("rights", "RIGHTS_NOT_CLEARED"),
        ("crop", "FRAME_QA_REQUIRED"),
        ("catalog", "CATALOG_NOT_REGISTERED"),
        ("renderer", "RENDERER_NOT_VERIFIED"),
        ("runtime", "RUNTIME_NOT_ELIGIBLE"),
    ],
)
def test_each_independent_runtime_gate_fails_closed(
    tmp_path: Path,
    gate: str,
    expected_reason: str,
) -> None:
    atlas = _synthetic_atlas()
    feature_root = tmp_path / "feature"
    approved_dir = feature_root / "assets" / "approved"
    approved_dir.mkdir(parents=True)
    (approved_dir / "fixture.png").write_bytes(atlas)
    manifest = _eligible_manifest(atlas)
    gates = manifest["commonGates"]
    if gate == "visual":
        manifest["ownerVisualApproval"]["decision"] = "PENDING"
    elif gate == "rights":
        gates["rightsStatus"] = "REVIEW_REQUIRED"
    elif gate == "crop":
        gates["cropPivotLoopStatus"] = "NOT_QA_VERIFIED"
    elif gate == "catalog":
        gates["catalogStatus"] = "NOT_REGISTERED"
    elif gate == "renderer":
        gates["rendererStatus"] = "NOT_VERIFIED"
    else:
        gates["runtimeEligible"] = False
    manifest_path = tmp_path / "motion-manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    service = PixiShowAssetService(
        feature_root=feature_root,
        assets=(),
        motion_cycle_manifest_path=manifest_path,
    )

    with pytest.raises(PixiShowAssetUnavailable) as error:
        service.issue_motion_cycle_read(
            "motion.flyer-fixture.v1",
            start_seconds=0,
            end_seconds=5,
            x=0.82,
            y=0.82,
        )

    assert error.value.reason_code == expected_reason
    assert service._grants == {}


def test_cycle_issue_rejects_bad_bounds_before_creating_capabilities() -> None:
    service = PixiShowAssetService(feature_root=_FEATURE_ROOT, assets=())

    with pytest.raises(PixiShowAssetUnavailable) as error:
        service.issue_motion_cycle_read(
            "motion.unknown\nsecret",
            start_seconds=0,
            end_seconds=99,
            x=2,
            y=0.8,
        )

    assert error.value.reason_code == "INVALID_CYCLE_REQUEST"


def test_eligible_cycle_issues_ordered_frame_hashes_and_expires_capabilities(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    from io import BytesIO

    atlas = _synthetic_atlas()
    feature_root = tmp_path / "feature"
    approved_dir = feature_root / "assets" / "approved"
    approved_dir.mkdir(parents=True)
    (approved_dir / "fixture.png").write_bytes(atlas)
    manifest_path = tmp_path / "motion-manifest.json"
    manifest_path.write_text(json.dumps(_eligible_manifest(atlas)), encoding="utf-8")
    current_time = [datetime(2026, 10, 2, tzinfo=UTC)]
    service = PixiShowAssetService(
        feature_root=feature_root,
        assets=(),
        motion_cycle_manifest_path=manifest_path,
        now=lambda: current_time[0],
    )

    caplog.set_level("INFO")
    cycle = service.issue_motion_cycle_read(
        "motion.flyer-fixture.v1",
        start_seconds=1,
        end_seconds=6,
        x=0.82,
        y=0.82,
    )

    assert [frame.asset_id for frame in cycle.frame_reads] == [
        f"motion.flyer-fixture.v1.frame-{index:02d}" for index in range(1, 5)
    ]
    assert all(frame.byte_length <= 1_000_000 for frame in cycle.frame_reads)
    for frame in cycle.frame_reads:
        content, digest = service.read(frame.read_capability)
        assert hashlib.sha256(content).hexdigest() == digest == frame.sha256
        with Image.open(BytesIO(content)) as decoded:
            assert decoded.size == (16, 16)
    assert "pixi_sprite_cycle_frame_read status=SUCCEEDED" in caplog.text
    assert "motion.flyer-fixture.v1.frame-01" in caplog.text
    assert all(frame.read_capability not in caplog.text for frame in cycle.frame_reads)

    current_time[0] += timedelta(minutes=6)
    with pytest.raises(PixiShowAssetUnavailable):
        service.read(cycle.frame_reads[0].read_capability)


def test_local_dev_preview_reads_allowlisted_applied_sprite_with_production_gates_closed(
    tmp_path: Path,
) -> None:
    from io import BytesIO

    atlas = _synthetic_atlas()
    feature_root = tmp_path / "feature"
    applied_dir = feature_root / "assets" / "applied"
    applied_dir.mkdir(parents=True)
    (applied_dir / "fixture.png").write_bytes(atlas)
    manifest = _eligible_manifest(atlas)
    manifest["runtimeEligible"] = False
    manifest["commonGates"].update(
        {
            "rightsStatus": "REVIEW_REQUIRED",
            "cropPivotLoopStatus": "NOT_QA_VERIFIED",
            "catalogStatus": "NOT_REGISTERED",
            "rendererStatus": "NOT_VERIFIED",
            "runtimeEligible": False,
        }
    )
    manifest_path = tmp_path / "motion-manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    catalog_path = applied_dir / "motion-cycle-local-preview-catalog.v1.json"
    catalog_path.write_text(json.dumps(_local_preview_catalog(atlas)), encoding="utf-8")
    service = PixiShowAssetService(
        feature_root=feature_root,
        assets=(),
        motion_cycle_manifest_path=manifest_path,
        motion_cycle_dev_preview_catalog_path=catalog_path,
        allow_dev_preview=True,
    )

    cycle = service.issue_motion_cycle_read(
        "motion.flyer-fixture.v1",
        start_seconds=0,
        end_seconds=5,
        x=0.82,
        y=0.82,
    )

    assert len(cycle.frame_reads) == 4
    for frame in cycle.frame_reads:
        payload, digest = service.read(frame.read_capability)
        assert hashlib.sha256(payload).hexdigest() == digest
        with Image.open(BytesIO(payload)) as image:
            assert image.size == (16, 16)


def test_local_dev_preview_is_default_off_even_when_catalog_is_present(tmp_path: Path) -> None:
    atlas = _synthetic_atlas()
    feature_root = tmp_path / "feature"
    applied_dir = feature_root / "assets" / "applied"
    applied_dir.mkdir(parents=True)
    (applied_dir / "fixture.png").write_bytes(atlas)
    manifest_path = tmp_path / "motion-manifest.json"
    manifest = _eligible_manifest(atlas)
    manifest["commonGates"]["rightsStatus"] = "REVIEW_REQUIRED"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    catalog_path = applied_dir / "motion-cycle-local-preview-catalog.v1.json"
    catalog_path.write_text(json.dumps(_local_preview_catalog(atlas)), encoding="utf-8")
    service = PixiShowAssetService(
        feature_root=feature_root,
        assets=(),
        motion_cycle_manifest_path=manifest_path,
        motion_cycle_dev_preview_catalog_path=catalog_path,
    )

    with pytest.raises(PixiShowAssetUnavailable) as error:
        service.issue_motion_cycle_read(
            "motion.flyer-fixture.v1",
            start_seconds=0,
            end_seconds=5,
            x=0.82,
            y=0.82,
        )

    assert error.value.reason_code == "RIGHTS_NOT_CLEARED"
    assert service._grants == {}


def test_local_dev_preview_rejects_cycles_missing_from_allowlist(tmp_path: Path) -> None:
    atlas = _synthetic_atlas()
    feature_root = tmp_path / "feature"
    applied_dir = feature_root / "assets" / "applied"
    applied_dir.mkdir(parents=True)
    (applied_dir / "fixture.png").write_bytes(atlas)
    manifest_path = tmp_path / "motion-manifest.json"
    manifest_path.write_text(json.dumps(_eligible_manifest(atlas)), encoding="utf-8")
    catalog = _local_preview_catalog(atlas)
    catalog["cycles"] = []
    catalog_path = applied_dir / "motion-cycle-local-preview-catalog.v1.json"
    catalog_path.write_text(json.dumps(catalog), encoding="utf-8")
    service = PixiShowAssetService(
        feature_root=feature_root,
        assets=(),
        motion_cycle_manifest_path=manifest_path,
        motion_cycle_dev_preview_catalog_path=catalog_path,
        allow_dev_preview=True,
    )

    with pytest.raises(PixiShowAssetUnavailable) as error:
        service.issue_motion_cycle_read(
            "motion.flyer-fixture.v1",
            start_seconds=0,
            end_seconds=5,
            x=0.82,
            y=0.82,
        )

    assert error.value.reason_code == "CATALOG_NOT_REGISTERED"
    assert service._grants == {}


@pytest.mark.parametrize(
    "cycle_id",
    ["motion.walker-avian.v1", "motion.walker-corgi.v2"],
)
def test_real_applied_preview_catalog_issues_verified_frame_capabilities(
    cycle_id: str,
    caplog: pytest.LogCaptureFixture,
) -> None:
    feature_root = _FEATURE_ROOT.resolve()
    applied_root = feature_root / "assets" / "applied"
    service = PixiShowAssetService(
        feature_root=feature_root,
        assets=(),
        motion_cycle_manifest_path=_MANIFEST,
        motion_cycle_dev_preview_catalog_path=(
            applied_root / "motion-cycle-local-preview-catalog.v1.json"
        ),
        allow_dev_preview=True,
    )

    caplog.set_level("INFO")
    cycle = service.issue_motion_cycle_read(
        cycle_id,
        start_seconds=0,
        end_seconds=5,
        x=0.82,
        y=0.82,
    )

    assert cycle.cycle_id == cycle_id
    assert len(cycle.frame_reads) == 4
    assert "pixi_sprite_cycle_capabilities_issued" in caplog.text
    assert "scope=LOCAL_DEV_PREVIEW" in caplog.text
    for frame in cycle.frame_reads:
        payload, digest = service.read(frame.read_capability)
        assert hashlib.sha256(payload).hexdigest() == digest == frame.sha256


def test_real_preview_catalog_rejects_qa_blocked_flyer_cycle() -> None:
    feature_root = _FEATURE_ROOT.resolve()
    service = PixiShowAssetService(
        feature_root=feature_root,
        assets=(),
        motion_cycle_manifest_path=_MANIFEST,
        motion_cycle_dev_preview_catalog_path=(
            feature_root / "assets" / "applied" / "motion-cycle-local-preview-catalog.v1.json"
        ),
        allow_dev_preview=True,
    )

    with pytest.raises(PixiShowAssetUnavailable) as error:
        service.issue_motion_cycle_read(
            "motion.flyer-songbird.v2",
            start_seconds=0,
            end_seconds=5,
            x=0.82,
            y=0.82,
        )

    assert error.value.reason_code == "CATALOG_NOT_REGISTERED"
    assert service._grants == {}
