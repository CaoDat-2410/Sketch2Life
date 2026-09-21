"""Image-only Lightning Vision V2 service for the manually operated FEAT-018 demo.

Deploy this service in the configured Lightning environment. It exposes no audio, ASR, video,
or generated-media route. Provider output and temporary image files are never logged.
"""

from __future__ import annotations

import base64
import os
import sys
import tempfile
from hashlib import sha256
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, ConfigDict, Field

_REPO_ROOT = Path(__file__).resolve().parents[1]
_BACKEND_SRC = _REPO_ROOT / "backend" / "src"
if _BACKEND_SRC.is_dir() and str(_BACKEND_SRC) not in sys.path:
    sys.path.insert(0, str(_BACKEND_SRC))

from sketch2life.contracts.schemas.vision import VisionImageReferenceV1
from sketch2life.contracts.schemas.vision_v2 import (
    VisionUnderstandingRequestV2,
)
from sketch2life.infrastructure.ai.qwen_vision import QwenVisionAdapter
from sketch2life.infrastructure.ai.qwen_vision_runtime_config import (
    VISION_MODEL_DIR_ENV_VAR,
    QwenVisionRuntimeConfig,
)
from sketch2life.infrastructure.ai.vision_lexical_policy import (
    LexicalRegressionContentPolicy,
    synthetic_prohibited_lexicon,
)

MAX_INPUT_BYTES = 5_000_000
EXPECTED_AUTH = os.getenv("LIGHTNING_DEV_AUTH", "").strip()
VLM_ROOT = Path(os.getenv("SKETCH2LIFE_VLM_ROOT", "models/vlm/qwen3-vl-8b-instruct"))

_PROMPT = """Return exactly one strict JSON object and no surrounding text. Analyze visible marks in
this synthetic, non-child drawing. Do not infer a child's personality, emotions, intent, diagnosis,
ability, development, or mental state.
Use exactly these root keys: entities, actions, relations, themes, ambiguous_regions. Use arrays;
use [] when uncertain. Maximums: 5 entities, 2 actions, 3 relations, 2 themes, 2 ambiguous regions.
Every text value is an object with value and language. Use language {status: DECLARED, tags: [vi]}
for Vietnamese labels, or {status: NOT_DETERMINED, tags: []} when unknown. is_ground_truth must be
false if emitted.
Use a unique lowercase observation_id containing only a-z, 0-9, hyphens. Include confidence from
0 to 1. Entities: observation_id,label,confidence. Actions: observation_id,label,actor_ref,
object_ref,confidence; refs are entity IDs or null. Relations: observation_id,predicate,subject_ref,
object_ref,confidence; refs point to distinct entity/action IDs. Themes: observation_id,label,
evidence_refs,confidence; evidence refs point to entity/action/relation IDs. Ambiguous regions:
observation_id,note.
Do not add keys, markdown fences, geometry, or metadata. Omit uncertain observations instead of
inventing them."""


class _SourceImageV1(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    artifact_ref: str = Field(min_length=1, max_length=300)
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    content_type: Literal["image/jpeg", "image/png"]
    content_base64: str = Field(min_length=1, max_length=6_666_668)


class LightningVisionRequestV2(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    contract_name: Literal["LightningVisionRequestV2"] = "LightningVisionRequestV2"
    contract_version: Literal["2.0"] = "2.0"
    request: VisionUnderstandingRequestV2
    source_image: _SourceImageV1


app = FastAPI(title="Sketch2Life Lightning Vision V2", version="2.0.0", redoc_url=None)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "lightning-vision-v2"}


@app.post("/v2/vision")
def vision_v2(
    payload: LightningVisionRequestV2,
    authorization: str | None = Header(default=None),
) -> dict[str, object]:
    if not EXPECTED_AUTH:
        raise HTTPException(status_code=503, detail="provider authentication is not configured")
    if authorization != f"Bearer {EXPECTED_AUTH}":
        raise HTTPException(status_code=401, detail="unauthorized")

    reference = payload.request.source_image_ref
    artifact = payload.source_image
    if artifact.artifact_ref != reference.artifact_ref or artifact.sha256 != reference.sha256:
        raise HTTPException(status_code=422, detail="source identity mismatch")
    try:
        image = base64.b64decode(artifact.content_base64, validate=True)
    except (ValueError, TypeError):
        raise HTTPException(status_code=422, detail="invalid image payload") from None
    if not image or len(image) > MAX_INPUT_BYTES:
        raise HTTPException(status_code=413, detail="image size is outside the allowed range")
    if sha256(image).hexdigest() != artifact.sha256:
        raise HTTPException(status_code=422, detail="source digest mismatch")
    if artifact.content_type == "image/png" and not image.startswith(b"\x89PNG\r\n\x1a\n"):
        raise HTTPException(status_code=422, detail="image type mismatch")
    if artifact.content_type == "image/jpeg" and not image.startswith(b"\xff\xd8\xff"):
        raise HTTPException(status_code=422, detail="image type mismatch")
    if (
        payload.request.media_validation is None
        or payload.request.media_validation.decision != "PASS"
    ):
        raise HTTPException(status_code=422, detail="image admission is required")

    try:
        with tempfile.TemporaryDirectory(prefix="sketch2life-vision-") as temporary:
            suffix = ".png" if artifact.content_type == "image/png" else ".jpg"
            image_path = Path(temporary) / f"source{suffix}"
            image_path.write_bytes(image)
            relative_path = os.path.relpath(image_path.resolve(), start=Path.cwd())
            local_reference = VisionImageReferenceV1(
                artifact_ref=relative_path,
                sha256=artifact.sha256,
            )
            local_request = VisionUnderstandingRequestV2.model_validate(
                {
                    **payload.request.model_dump(mode="python"),
                    "source_image_ref": local_reference,
                }
            )
            runtime_env = dict(os.environ)
            runtime_env.setdefault(VISION_MODEL_DIR_ENV_VAR, str(VLM_ROOT))
            runtime = QwenVisionRuntimeConfig.from_env(runtime_env)
            adapter = QwenVisionAdapter(
                runtime,
                content_policy=LexicalRegressionContentPolicy(synthetic_prohibited_lexicon()),
                prompt=_PROMPT,
                enable_bounded_repair=False,
            )
            result = adapter.understand(local_request)
            wire_result = result.model_dump(mode="json")
            wire_result["source_image_ref"]["artifact_ref"] = artifact.artifact_ref
            return wire_result
    except (OSError, ValueError, RuntimeError):
        raise HTTPException(status_code=503, detail="vision runtime is unavailable") from None


__all__ = ["app", "vision_v2"]
