"""Rights-gated FEAT-028 frame extraction and short-lived Pixi read capabilities."""

from __future__ import annotations

import hashlib
import io
import json
import logging
import math
import re
import secrets
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from threading import RLock
from typing import cast

from PIL import Image

from sketch2life.contracts.schemas.pixi_motion_cycle import (
    PixiSpriteCycleReadV1,
    PixiSpriteCycleReasonCodeV1,
)
from sketch2life.contracts.schemas.pixi_show import PixiShowAssetReadV1
from sketch2life.contracts.schemas.pixi_topic_asset_selection import TopicAssetDescriptorV1

_MAX_FRAME_BYTES = 1_000_000
_CAPABILITY_TTL = timedelta(minutes=5)
_CAPABILITY_READS = 4
_LOGGER = logging.getLogger(__name__)
_MOTION_BEHAVIOR_IDS = frozenset(
    {
        "walker.biped", "walker.quadruped", "walker.avian", "runner.biped", "runner.quadruped",
        "hopper", "flyer", "glider", "swimmer", "crawler", "slitherer", "climber", "waver",
        "reacher", "dancer", "turner", "swaying_plant", "growing", "blooming", "drifting",
        "falling", "flowing", "flickering", "roller", "rotator", "swinger", "bouncer",
        "slider", "opener_closer",
    }
)


class PixiShowAssetUnavailable(Exception):
    """A selected frame is unreviewed, rights-blocked, or unavailable."""

    CODES = frozenset(
        {
            "ASSET_UNAVAILABLE",
            "INVALID_CYCLE_REQUEST",
            "UNKNOWN_CYCLE",
            "VISUAL_REVIEW_REQUIRED",
            "RIGHTS_NOT_CLEARED",
            "FRAME_QA_REQUIRED",
            "CATALOG_NOT_REGISTERED",
            "RENDERER_NOT_VERIFIED",
            "RUNTIME_NOT_ELIGIBLE",
            "FRAME_QA_FAILED",
        }
    )

    def __init__(self, reason_code: str = "ASSET_UNAVAILABLE") -> None:
        self.reason_code = cast(
            PixiSpriteCycleReasonCodeV1,
            reason_code if reason_code in self.CODES else "ASSET_UNAVAILABLE",
        )
        super().__init__(self.reason_code)


@dataclass(slots=True)
class _Grant:
    asset_id: str
    content: bytes
    digest: str
    expires_at: datetime
    remaining_reads: int


class PixiShowAssetService:
    def __init__(
        self,
        *,
        feature_root: Path,
        assets: tuple[TopicAssetDescriptorV1, ...],
        motion_cycle_manifest_path: Path | None = None,
        motion_cycle_dev_preview_catalog_path: Path | None = None,
        allow_dev_preview: bool = False,
        now: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self._feature_root = feature_root.resolve()
        self._assets = {asset.asset_id: asset for asset in assets}
        self._now = now
        self._motion_cycle_manifest_path = motion_cycle_manifest_path
        self._motion_cycle_dev_preview_catalog_path = motion_cycle_dev_preview_catalog_path
        self._allow_dev_preview = allow_dev_preview
        self._grants: dict[str, _Grant] = {}
        self._lock = RLock()

    def issue_reads(self, asset_ids: tuple[str, ...]) -> tuple[PixiShowAssetReadV1, ...]:
        if not asset_ids:
            return ()
        if len(asset_ids) > 3 or len(set(asset_ids)) != len(asset_ids):
            raise PixiShowAssetUnavailable from None
        prepared: list[tuple[str, bytes, str]] = []
        for asset_id in asset_ids:
            asset = self._assets.get(asset_id)
            if (
                asset is None
                or not asset.runtime_eligible
                or asset.review_status not in {"APPROVED", "APPLIED"}
                or asset.provenance.license_status != "CLEARED"
            ):
                raise PixiShowAssetUnavailable from None
            prepared.append((asset_id, self._extract_frame(asset), "image/png"))

        issued: list[PixiShowAssetReadV1] = []
        now = self._now()
        with self._lock:
            self._grants = {
                token: grant
                for token, grant in self._grants.items()
                if grant.expires_at > now and grant.remaining_reads > 0
            }
            for asset_id, content, content_type in prepared:
                token = secrets.token_urlsafe(48)
                digest = hashlib.sha256(content).hexdigest()
                self._grants[token] = _Grant(
                    asset_id=asset_id,
                    content=content,
                    digest=digest,
                    expires_at=now + _CAPABILITY_TTL,
                    remaining_reads=_CAPABILITY_READS,
                )
                issued.append(
                    PixiShowAssetReadV1(
                        assetId=asset_id,
                        readEndpoint="/v1/renderer/pixi-asset",
                        readCapability=token,
                        sha256=digest,
                        byteLength=len(content),
                        contentType=content_type,
                    )
                )
        return tuple(issued)

    def issue_motion_cycle_read(
        self,
        cycle_id: str,
        *,
        start_seconds: float,
        end_seconds: float,
        x: float,
        y: float,
        scale: float = 0.4,
        frame_rate: int = 6,
        loop_mode: str = "LOOP",
    ) -> PixiSpriteCycleReadV1:
        """Issue frame capabilities only after every independent motion asset gate passes."""
        if (
            not isinstance(cycle_id, str)
            or len(cycle_id) > 100
            or re.fullmatch(r"motion\.[a-z0-9.-]+", cycle_id) is None
            or isinstance(frame_rate, bool)
            or not isinstance(frame_rate, int)
            or not 1 <= frame_rate <= 12
            or loop_mode not in {"LOOP", "ONCE"}
            or not all(
                isinstance(value, (int, float))
                and not isinstance(value, bool)
                and math.isfinite(value)
                for value in (start_seconds, end_seconds, x, y, scale)
            )
            or not 0 <= start_seconds < end_seconds <= 30
            or not 0.12 <= x <= 0.88
            or not 0.12 <= y <= 0.88
            or not 0.2 <= scale <= 0.6
        ):
            raise PixiShowAssetUnavailable("INVALID_CYCLE_REQUEST") from None
        cycle = self._motion_cycle_record(cycle_id)
        if cycle is None:
            _LOGGER.info(
                "pixi_sprite_cycle_blocked cycle_id=%s reason=UNKNOWN_CYCLE",
                _safe_cycle_log_id(cycle_id),
            )
            raise PixiShowAssetUnavailable("UNKNOWN_CYCLE") from None
        if (
            cycle.get("behaviorClassId") not in _MOTION_BEHAVIOR_IDS
            or not isinstance(cycle.get("variantId"), str)
            or re.fullmatch(r"[a-z0-9-]{1,60}", cycle["variantId"]) is None
            or cycle.get("playbackKind") not in {None, "FRAME_SEQUENCE", "TRANSFORM_DRIVEN"}
            or (
                cycle.get("playbackKind") == "TRANSFORM_DRIVEN"
                and cycle.get("behaviorClassId") != "slider"
            )
        ):
            raise PixiShowAssetUnavailable("FRAME_QA_FAILED") from None
        manifest = self._read_motion_cycle_manifest()
        gates = manifest.get("commonGates", {})
        dev_preview = self._allow_dev_preview
        if dev_preview:
            if not self._is_dev_preview_registered(cycle, manifest):
                _LOGGER.info(
                    "pixi_sprite_cycle_blocked cycle_id=%s behavior_class=%s "
                    "reason=CATALOG_NOT_REGISTERED",
                    _safe_cycle_log_id(cycle_id),
                    _safe_registry_id(cycle.get("behaviorClassId")),
                )
                raise PixiShowAssetUnavailable("CATALOG_NOT_REGISTERED") from None
        else:
            checks = (
                (
                    manifest.get("ownerVisualApproval", {}).get("decision") == "APPROVED",
                    "VISUAL_REVIEW_REQUIRED",
                ),
                (
                    str(cycle.get("visualReview", "")).startswith("VISUAL_APPROVED"),
                    "VISUAL_REVIEW_REQUIRED",
                ),
                (gates.get("rightsStatus") == "CLEARED", "RIGHTS_NOT_CLEARED"),
                (gates.get("cropPivotLoopStatus") == "QA_PASSED", "FRAME_QA_REQUIRED"),
                (gates.get("catalogStatus") == "REGISTERED", "CATALOG_NOT_REGISTERED"),
                (gates.get("rendererStatus") == "VERIFIED", "RENDERER_NOT_VERIFIED"),
                (
                    gates.get("runtimeEligible") is True
                    and manifest.get("runtimeEligible") is True,
                    "RUNTIME_NOT_ELIGIBLE",
                ),
            )
            for passed, reason in checks:
                if not passed:
                    _LOGGER.info(
                        "pixi_sprite_cycle_blocked cycle_id=%s behavior_class=%s reason=%s",
                        _safe_cycle_log_id(cycle_id),
                        _safe_registry_id(cycle.get("behaviorClassId")),
                        reason,
                    )
                    raise PixiShowAssetUnavailable(reason) from None

        try:
            frame_payloads = self._extract_motion_cycle_frames(
                cycle,
                asset_directory="applied" if dev_preview else "approved",
            )
            playback_kind = (
                "TRANSFORM_DRIVEN"
                if cycle.get("playbackKind") == "TRANSFORM_DRIVEN"
                else "FRAME_SEQUENCE"
            )
            if playback_kind == "TRANSFORM_DRIVEN":
                frame_payloads = frame_payloads[:1]
            if len(frame_payloads) != (1 if playback_kind == "TRANSFORM_DRIVEN" else 4):
                raise PixiShowAssetUnavailable
            now = self._now()
            reads: list[PixiShowAssetReadV1] = []
            with self._lock:
                self._prune_grants(now)
                for index, content in enumerate(frame_payloads, start=1):
                    frame_id = f"{cycle_id}.frame-{index:02d}"
                    reads.append(self._issue_png_read(frame_id, content, now))
        except PixiShowAssetUnavailable as error:
            reason = getattr(error, "reason_code", "FRAME_QA_FAILED")
            _LOGGER.info(
                "pixi_sprite_cycle_blocked cycle_id=%s reason=%s",
                _safe_cycle_log_id(cycle_id),
                reason,
            )
            raise PixiShowAssetUnavailable(reason) from None

        result = PixiSpriteCycleReadV1(
            cycleId=cycle_id,
            behaviorClassId=cycle["behaviorClassId"],
            variantId=cycle["variantId"],
            playbackKind=playback_kind,
            loopMode=loop_mode,
            frameRate=frame_rate,
            startSeconds=start_seconds,
            endSeconds=end_seconds,
            x=x,
            y=y,
            scale=scale,
            frameReads=tuple(reads),
        )
        _LOGGER.info(
            "pixi_sprite_cycle_capabilities_issued "
            "cycle_id=%s behavior_class=%s frames=%d playback_kind=%s scope=%s",
            _safe_cycle_log_id(cycle_id),
            _safe_registry_id(cycle.get("behaviorClassId")),
            len(reads),
            playback_kind,
            "LOCAL_DEV_PREVIEW" if dev_preview else "CLEARED_RUNTIME",
        )
        return result

    def read(self, capability: str) -> tuple[bytes, str]:
        now = self._now()
        with self._lock:
            grant = self._grants.get(capability)
            if grant is None or grant.expires_at <= now or grant.remaining_reads <= 0:
                self._grants.pop(capability, None)
                raise PixiShowAssetUnavailable from None
            grant.remaining_reads -= 1
            if grant.remaining_reads == 0:
                self._grants.pop(capability, None)
            content, digest, asset_id = grant.content, grant.digest, grant.asset_id
        frame_id = _safe_frame_log_id(asset_id)
        if frame_id is not None:
            _LOGGER.info(
                "pixi_sprite_cycle_frame_read status=SUCCEEDED frame_id=%s bytes=%d",
                frame_id,
                len(content),
            )
        return content, digest

    def _read_motion_cycle_manifest(self) -> dict[str, object]:
        path = self._motion_cycle_manifest_path
        if path is None:
            raise PixiShowAssetUnavailable from None
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            raise PixiShowAssetUnavailable from None
        if (
            not isinstance(payload, dict)
            or not isinstance(payload.get("commonGates"), dict)
            or not isinstance(payload.get("ownerVisualApproval"), dict)
        ):
            raise PixiShowAssetUnavailable from None
        return payload

    def _motion_cycle_record(self, cycle_id: str) -> dict[str, object] | None:
        manifest = self._read_motion_cycle_manifest()
        cycles = manifest.get("cycles")
        if not isinstance(cycles, list):
            return None
        return next(
            (item for item in cycles if isinstance(item, dict) and item.get("cycleId") == cycle_id),
            None,
        )

    def _is_dev_preview_registered(
        self,
        cycle: dict[str, object],
        manifest: dict[str, object],
    ) -> bool:
        if (
            manifest.get("ownerVisualApproval", {}).get("decision") != "APPROVED"
            or not str(cycle.get("visualReview", "")).startswith("VISUAL_APPROVED")
        ):
            return False
        path = self._motion_cycle_dev_preview_catalog_path
        if path is None:
            return False
        try:
            catalog = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return False
        if (
            not isinstance(catalog, dict)
            or catalog.get("schemaName") != "PixiMotionCycleLocalPreviewCatalog"
            or catalog.get("schemaVersion") != "1.0"
            or catalog.get("activationScope") != "LOCAL_ANDROID_DEV_PREVIEW"
            or catalog.get("rightsStatus") != "REVIEW_REQUIRED"
            or catalog.get("productionRuntimeEligible") is not False
            or catalog.get("runtimeEligible") is not False
            or catalog.get("commonGatesRemainClosed") is not True
        ):
            return False
        entries = catalog.get("cycles")
        if not isinstance(entries, list):
            return False
        entry = next(
            (
                item
                for item in entries
                if isinstance(item, dict) and item.get("cycleId") == cycle.get("cycleId")
            ),
            None,
        )
        return bool(
            entry
            and entry.get("devPreviewStatus") == "QA_PASSED_LOCAL_PREVIEW"
            and entry.get("assetFile") == cycle.get("assetFile")
            and isinstance(entry.get("sha256"), str)
            and entry["sha256"].lower() == str(cycle.get("sha256", "")).lower()
            and entry.get("behaviorClassId") == cycle.get("behaviorClassId")
            and entry.get("variantId") == cycle.get("variantId")
            and entry.get("frameCount") == 4
            and entry.get("layout") == cycle.get("layout")
        )

    def _extract_motion_cycle_frames(
        self,
        cycle: dict[str, object],
        *,
        asset_directory: str = "approved",
    ) -> tuple[bytes, ...]:
        asset_file = cycle.get("assetFile")
        expected_sha = cycle.get("sha256")
        canvas = cycle.get("canvas")
        layout = cycle.get("layout")
        frame_count = cycle.get("frameCount")
        if (
            not isinstance(asset_file, str)
            or Path(asset_file).name != asset_file
            or not isinstance(expected_sha, str)
            or not isinstance(canvas, list)
            or len(canvas) != 2
            or not all(isinstance(value, int) and value > 0 for value in canvas)
            or layout not in {"STRIP_1X4", "GRID_2X2"}
            or not isinstance(frame_count, int)
            or frame_count != 4
        ):
            raise PixiShowAssetUnavailable from None
        if asset_directory not in {"approved", "applied"}:
            raise PixiShowAssetUnavailable from None
        asset_root = (self._feature_root / "assets" / asset_directory).resolve()
        atlas_path = (asset_root / asset_file).resolve()
        try:
            atlas_path.relative_to(asset_root)
            atlas_bytes = atlas_path.read_bytes()
            if hashlib.sha256(atlas_bytes).hexdigest() != expected_sha.lower():
                raise PixiShowAssetUnavailable
            with Image.open(io.BytesIO(atlas_bytes)) as image_file:
                atlas = image_file.convert("RGBA")
                if [atlas.width, atlas.height] != canvas:
                    raise PixiShowAssetUnavailable
                columns, rows = (4, 1) if layout == "STRIP_1X4" else (2, 2)
                frames: list[bytes] = []
                visible_frame_count = 0
                for index in range(4):
                    column, row = index % columns, index // columns
                    x0 = round(column * atlas.width / columns)
                    x1 = round((column + 1) * atlas.width / columns)
                    y0 = round(row * atlas.height / rows)
                    y1 = round((row + 1) * atlas.height / rows)
                    crop = atlas.crop((x0, y0, x1, y1))
                    has_pixels = crop.getchannel("A").getbbox() is not None
                    visible_frame_count += int(has_pixels)
                    if not has_pixels and cycle.get("behaviorClassId") != "flickering":
                        raise PixiShowAssetUnavailable
                    output = io.BytesIO()
                    crop.save(output, format="PNG", optimize=True)
                    content = output.getvalue()
                    if not content or len(content) > _MAX_FRAME_BYTES:
                        raise PixiShowAssetUnavailable
                    frames.append(content)
                if visible_frame_count < 2:
                    raise PixiShowAssetUnavailable
                return tuple(frames)
        except (OSError, ValueError, PixiShowAssetUnavailable):
            raise PixiShowAssetUnavailable from None

    def _prune_grants(self, now: datetime) -> None:
        self._grants = {
            token: grant
            for token, grant in self._grants.items()
            if grant.expires_at > now and grant.remaining_reads > 0
        }

    def _issue_png_read(self, asset_id: str, content: bytes, now: datetime) -> PixiShowAssetReadV1:
        if not content or len(content) > _MAX_FRAME_BYTES:
            raise PixiShowAssetUnavailable from None
        token = secrets.token_urlsafe(48)
        digest = hashlib.sha256(content).hexdigest()
        self._grants[token] = _Grant(
            asset_id=asset_id,
            content=content,
            digest=digest,
            expires_at=now + _CAPABILITY_TTL,
            remaining_reads=_CAPABILITY_READS,
        )
        return PixiShowAssetReadV1(
            assetId=asset_id,
            readEndpoint="/v1/renderer/pixi-asset",
            readCapability=token,
            sha256=digest,
            byteLength=len(content),
            contentType="image/png",
        )

    def _extract_frame(self, asset: TopicAssetDescriptorV1) -> bytes:
        atlas_path = (self._feature_root / asset.provenance.asset_file).resolve()
        try:
            atlas_path.relative_to(self._feature_root)
            atlas_bytes = atlas_path.read_bytes()
            if hashlib.sha256(atlas_bytes).hexdigest() != asset.provenance.atlas_sha256:
                raise PixiShowAssetUnavailable
            with Image.open(io.BytesIO(atlas_bytes)) as atlas_file:
                atlas = atlas_file.convert("RGBA")
                frame = asset.frame
                if frame.x + frame.width > atlas.width or frame.y + frame.height > atlas.height:
                    raise PixiShowAssetUnavailable
                crop = atlas.crop((frame.x, frame.y, frame.x + frame.width, frame.y + frame.height))
            output = io.BytesIO()
            crop.save(output, format="PNG", optimize=True)
            content = output.getvalue()
        except (OSError, ValueError, PixiShowAssetUnavailable):
            raise PixiShowAssetUnavailable from None
        if not content or len(content) > _MAX_FRAME_BYTES:
            raise PixiShowAssetUnavailable from None
        return content


__all__ = ["PixiShowAssetService", "PixiShowAssetUnavailable"]


def _safe_cycle_log_id(value: object) -> str:
    if isinstance(value, str) and re.fullmatch(r"motion\.[a-z0-9.-]{1,90}", value):
        return value
    return "unknown"


def _safe_registry_id(value: object) -> str:
    if isinstance(value, str) and re.fullmatch(r"[a-z][a-z0-9_.-]{0,39}", value):
        return value
    return "unknown"


def _safe_frame_log_id(value: str) -> str | None:
    if re.fullmatch(r"motion\.[a-z0-9.-]{1,84}\.frame-[0-9]{2}", value):
        return value
    return None
