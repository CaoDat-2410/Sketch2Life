"""Allowlisted synthetic fixture input loader for local live-AI smoke tests."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from sketch2life.contracts.schemas.media_validation import SourceMediaReferenceV1


@dataclass(frozen=True, slots=True)
class FixtureInputs:
    fixture_id: str
    image: SourceMediaReferenceV1
    audio: SourceMediaReferenceV1
    files: Mapping[str, bytes]

    @classmethod
    def load(cls, root: Path, fixture_id: str) -> FixtureInputs:
        manifest_path = (root / "manifest.json").resolve()
        resolved_root = root.resolve()
        if manifest_path.parent != resolved_root:
            raise ValueError("fixture root must resolve to its manifest directory")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest.get("fixture_id") != fixture_id or manifest.get("synthetic_data") is not True:
            raise ValueError("only the declared synthetic fixture may be used")
        references: dict[str, SourceMediaReferenceV1] = {}
        files: dict[str, bytes] = {}
        for source in manifest.get("source_media", ()):
            relative_path = Path(str(source["path"]))
            path = (resolved_root / relative_path).resolve()
            if resolved_root not in path.parents:
                raise ValueError("fixture source escapes the fixture root")
            content = path.read_bytes()
            digest = hashlib.sha256(content).hexdigest()
            if digest != source.get("sha256"):
                raise ValueError("fixture source hash mismatch")
            artifact_id = str(source["artifact_id"])
            references[artifact_id] = SourceMediaReferenceV1(
                artifact_ref=artifact_id,
                sha256=digest,
                source_status="AVAILABLE",
            )
            files[artifact_id] = content
        try:
            image = references["child-drawing-001"]
            audio = references["child-narration-001"]
        except KeyError as exc:
            raise ValueError("fixture is missing required drawing or narration") from exc
        return cls(fixture_id=fixture_id, image=image, audio=audio, files=files)

    def read(self, artifact_ref: str) -> bytes:
        try:
            return self.files[artifact_ref]
        except KeyError as exc:
            raise ValueError("artifact is not allowlisted by the fixture manifest") from exc
