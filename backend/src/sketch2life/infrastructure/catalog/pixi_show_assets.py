"""Rights-gated FEAT-028 frame extraction and short-lived Pixi read capabilities."""

from __future__ import annotations

import hashlib
import io
import secrets
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from threading import RLock

from PIL import Image

from sketch2life.contracts.schemas.pixi_show import PixiShowAssetReadV1
from sketch2life.contracts.schemas.pixi_topic_asset_selection import TopicAssetDescriptorV1

_MAX_FRAME_BYTES = 1_000_000
_CAPABILITY_TTL = timedelta(minutes=5)
_CAPABILITY_READS = 4


class PixiShowAssetUnavailable(Exception):
    """A selected frame is unreviewed, rights-blocked, or unavailable."""


@dataclass(slots=True)
class _Grant:
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
        now: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self._feature_root = feature_root.resolve()
        self._assets = {asset.asset_id: asset for asset in assets}
        self._now = now
        self._grants: dict[str, _Grant] = {}
        self._lock = RLock()

    def issue_reads(self, asset_ids: tuple[str, ...]) -> tuple[PixiShowAssetReadV1, ...]:
        if not asset_ids or len(asset_ids) > 3 or len(set(asset_ids)) != len(asset_ids):
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
            return grant.content, grant.digest

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
