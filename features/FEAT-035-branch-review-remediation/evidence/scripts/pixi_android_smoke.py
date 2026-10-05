"""Offline Android Chromium probe of the real renderer and preview frame service.

Run with the backend venv from the repository root. No model calls or child data.
This isolated loopback server is a test harness, not an application API route.
"""

from __future__ import annotations

import hashlib
import io
import secrets
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "backend" / "src"))

import uvicorn
from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from PIL import Image, ImageChops, ImageDraw
from sketch2life.application.services.auto_rig import (
    build_animation_plan,
    build_template_rig,
)
from sketch2life.contracts.schemas.auto_rig import (
    RigArchetype,
    RigDeliveryTier,
    RiggedArtworkPackageV1,
)
from sketch2life.contracts.schemas.p1_experience import VersionedRefV1
from sketch2life.contracts.schemas.pixi_show import PixiShowPlanV2
from sketch2life.contracts.schemas.scene_exploration import SourceRegionV1
from sketch2life.infrastructure.catalog.pixi_show_assets import PixiShowAssetService

app = FastAPI()
events: list[dict] = []
feature = ROOT / "features" / "FEAT-028-pixi-topic-asset-library"
dist = ROOT / "packages" / "art-renderer" / "dist-demo"
service = PixiShowAssetService(
    feature_root=feature,
    assets=(),
    motion_cycle_manifest_path=feature
    / "assets/generated/motion-cycle-review-manifest.rev1.json",
    motion_cycle_dev_preview_catalog_path=(
        feature / "assets/applied/motion-cycle-local-preview-catalog.v1.json"
    ),
    allow_dev_preview=True,
)


def png(image: Image.Image) -> bytes:
    stream = io.BytesIO()
    image.save(stream, format="PNG")
    return stream.getvalue()


source = Image.new("RGB", (800, 600), "white")
draw = ImageDraw.Draw(source)
draw.rounded_rectangle(
    (305, 210, 495, 450), radius=50, fill="#ad713e", outline="#412b1c", width=5
)
draw.ellipse((310, 115, 490, 300), fill="#ad713e", outline="#412b1c", width=5)
draw.polygon([(320, 170), (300, 80), (375, 130)], fill="#ad713e", outline="#412b1c")
draw.polygon([(425, 130), (500, 80), (480, 170)], fill="#ad713e", outline="#412b1c")
draw.ellipse((345, 170, 365, 190), fill="black")
draw.ellipse((435, 170, 455, 190), fill="black")
draw.ellipse((365, 205, 435, 265), fill="#fff6e2")
draw.ellipse((385, 215, 415, 235), fill="black")
mask = ImageChops.difference(source, Image.new("RGB", source.size, "white"))
mask = mask.convert("L").point(lambda pixel: 255 if pixel > 0 else 0).convert("RGB")
source_bytes, mask_bytes = png(source), png(mask)
source_hash = hashlib.sha256(source_bytes).hexdigest()
mask_hash = hashlib.sha256(mask_bytes).hexdigest()
region = SourceRegionV1(x=0.375, y=0.13, width=0.25, height=0.63)
ref = VersionedRefV1(id="synthetic-spec", version=1)
rig = build_template_rig(archetype=RigArchetype.GENERIC_ORGANIC, source_region=region)
plan = build_animation_plan(
    plan_id="synthetic-visual",
    session_id="synthetic-session",
    experience_spec_ref=ref,
    package_id="synthetic-rig",
    archetype=RigArchetype.GENERIC_ORGANIC,
    learning_bridge_vi="Offline synthetic sprite verification.",
    tier=RigDeliveryTier.CUTOUT_MICRO_MOTION,
)
package = RiggedArtworkPackageV1.model_validate(
    {
        "contractName": "RiggedArtworkPackageV1",
        "contractVersion": "1.0",
        "packageId": "synthetic-rig",
        "sessionId": "synthetic-session",
        "sourceArtifactRef": "synthetic-source",
        "sourceSha256": source_hash,
        "target": {
            "canonicalEntityId": "synthetic-dog",
            "normalizedLabel": "con cho",
            "confidence": 1,
        },
        "archetype": "generic_organic",
        "tier": "CUTOUT_MICRO_MOTION",
        "rig": rig,
        "derivedArtifacts": [
            {
                "artifactRef": "synthetic-mask",
                "sha256": mask_hash,
                "contentType": "image/png",
                "byteLength": len(mask_bytes),
                "role": "ORIGINAL_DERIVED_MASK",
                "sourceSha256": source_hash,
                "operation": "synthetic-fixture",
                "operationVersion": "1",
            }
        ],
        "validation": {
            "contractName": "RigValidationResultV1",
            "contractVersion": "1.0",
            "valid": True,
            "selectedTier": "CUTOUT_MICRO_MOTION",
            "validatorVersion": "1",
        },
        "pipelineVersion": "1",
        "createdAt": datetime.now(UTC),
    }
)
package_bytes = package.model_dump_json(by_alias=True, exclude_none=True).encode()
show = PixiShowPlanV2.model_validate(
    {
        "contractName": "PixiShowPlanV2",
        "contractVersion": "2.0",
        "planId": "synthetic-show",
        "sessionId": "synthetic-session",
        "packageId": "synthetic-rig",
        "sourceSha256": source_hash,
        "sourceSubjectRegion": region,
        "experienceSpecRef": ref,
        "confirmedSubjectId": "synthetic-dog",
        "visualSubjectHintId": "QUADRUPED",
        "behaviorClass": "WALKER",
        "durationSeconds": 20,
        "selectedAssetIds": [],
        "beats": [
            {
                "beatId": "notice",
                "startSeconds": 0,
                "endSeconds": 4,
                "action": "NOTICE",
                "targetRole": "SOURCE_SUBJECT",
            },
            {
                "beatId": "look",
                "startSeconds": 5,
                "endSeconds": 9,
                "action": "NOTICE",
                "targetRole": "SOURCE_SUBJECT",
            },
            {
                "beatId": "settle",
                "startSeconds": 12,
                "endSeconds": 17,
                "action": "SETTLE",
                "targetRole": "SOURCE_SUBJECT",
            },
        ],
        "endingStill": True,
    }
)
tokens = {key: secrets.token_urlsafe(48) for key in ("source", "package", "mask")}


@app.get("/launch")
def launch() -> dict:
    cycle = service.issue_motion_cycle_read(
        "motion.walker-corgi.v2",
        start_seconds=0,
        end_seconds=4,
        x=0.78,
        y=0.58,
        scale=0.30,
    )
    return {
        "contractName": "RendererLoadCommandV5",
        "contractVersion": "5.0",
        "protocolVersion": "5",
        "sequence": 1,
        "rendererInstanceId": "android-smoke",
        "sessionId": "synthetic-session",
        "expectedSessionVersion": 1,
        "experienceSpecRef": ref.model_dump(),
        "sourceReadEndpoint": "/v1/renderer/source",
        "sourceReadCapability": tokens["source"],
        "sourceSha256": source_hash,
        "packageReadEndpoint": "/v1/renderer/rig-package",
        "packageReadCapability": tokens["package"],
        "packageSha256": hashlib.sha256(package_bytes).hexdigest(),
        "maskReadEndpoint": "/v1/renderer/rig-mask",
        "maskReadCapability": tokens["mask"],
        "maskSha256": mask_hash,
        "animationPlan": plan.model_dump(mode="json", by_alias=True),
        "showPlan": show.model_dump(mode="json", by_alias=True, exclude_none=True),
        "assetReads": [],
        "spriteCycleStatus": "READY",
        "spriteCycle": cycle.model_dump(mode="json", by_alias=True),
    }


def protected(
    body: bytes, key: str, capability: str | None, media_type: str
) -> Response:
    if capability is None or not secrets.compare_digest(tokens[key], capability):
        raise HTTPException(403)
    return Response(
        body,
        media_type=media_type,
        headers={"X-Content-SHA256": hashlib.sha256(body).hexdigest()},
    )


@app.get("/v1/renderer/source")
def read_source(
    x_render_source_capability: str | None = Header(default=None),
) -> Response:
    return protected(source_bytes, "source", x_render_source_capability, "image/png")


@app.get("/v1/renderer/rig-package")
def read_package(
    x_rig_package_capability: str | None = Header(default=None),
) -> Response:
    return protected(
        package_bytes, "package", x_rig_package_capability, "application/json"
    )


@app.get("/v1/renderer/rig-mask")
def read_mask(x_rig_mask_capability: str | None = Header(default=None)) -> Response:
    return protected(mask_bytes, "mask", x_rig_mask_capability, "image/png")


@app.get("/v1/renderer/pixi-asset")
def read_frame(x_pixi_asset_capability: str = Header()) -> Response:
    body, digest = service.read(x_pixi_asset_capability)
    return Response(body, media_type="image/png", headers={"X-Content-SHA256": digest})


@app.post("/events")
def record_event(value: dict) -> dict:
    safe = {
        key: value[key]
        for key in (
            "type",
            "event",
            "state",
            "interactionPhase",
            "positionSeconds",
            "frameIndex",
            "reason",
        )
        if key in value
    }
    events.append(safe)
    return {"count": len(events)}


@app.get("/events")
def read_events() -> list[dict]:
    return events


@app.get("/renderer/mobile.html")
def renderer_page() -> HTMLResponse:
    html = (dist / "mobile.html").read_text(encoding="utf-8")
    bridge = """<script>
window.ReactNativeWebView={postMessage:value=>parent.postMessage(value,location.origin)};
const originalInfo=console.info;
console.info=(...args)=>{originalInfo(...args);if(args[0]==='[pixi-cycle]')parent.postMessage(JSON.stringify({diagnostic:JSON.parse(args[1])}),location.origin)};
</script>"""
    return HTMLResponse(html.replace("<head>", "<head>" + bridge))


@app.get("/")
def host() -> HTMLResponse:
    return HTMLResponse("""<!doctype html><html><meta name="viewport" content="width=device-width,initial-scale=1"><style>
body{margin:0;background:#eef7ff;font:16px sans-serif}iframe{width:100%;height:78vh;border:0}button{padding:12px;margin:5px}#state{padding:8px}
</style><div id="state">Offline Android sprite probe</div><button onclick="control('PLAY')">Play</button><button onclick="control('PAUSE')">Pause</button><button onclick="control('REPLAY')">Replay</button><button onclick="control('SEEK_TO_SECONDS',1)">Seek 1s</button><button onclick="document.querySelector('iframe').remove()">Teardown</button><iframe src="/renderer/mobile.html?rendererInstanceId=android-smoke"></iframe><script>
let command,sequence=2,paused=false;
const ready=fetch('/launch').then(r=>r.json()).then(c=>command=c);
function control(action,seconds){const c={protocolVersion:'1',rendererInstanceId:'android-smoke',sequence:sequence++,type:'PLAYBACK_CONTROL',action};if(seconds!==undefined)c.seconds=seconds;document.querySelector('iframe').contentWindow.__sketch2lifeReceiveNativeMessage(JSON.stringify(c))}
window.addEventListener('message',async e=>{if(e.origin!==location.origin)return;const v=JSON.parse(e.data);if(v.rendererInstanceId==='android-smoke'&&!v.type&&!v.event&&!v.diagnostic){await ready;document.querySelector('iframe').contentWindow.__sketch2lifeReceiveNativeMessage(JSON.stringify(command))}const safe=v.diagnostic||v.event||v;fetch('/events',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(safe)});if(v.type==='PLAYBACK_STATE'){document.querySelector('#state').textContent=v.state+' '+v.positionSeconds.toFixed(2)+'s / '+v.durationSeconds+'s';if(v.state==='PLAYING'&&v.positionSeconds>=2&&!paused){paused=true;control('PAUSE')}}});
</script></html>""")


app.mount("/renderer", StaticFiles(directory=dist, html=True))

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8002, access_log=False)
