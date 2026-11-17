"""One synthetic demo-backend smoke check; provider credentials stay in the backend."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import time
from datetime import UTC, datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from uuid import uuid4

from pydantic import ValidationError
from sketch2life.contracts.schemas.image_demo import ImageAdmissionReceiptV2
from sketch2life.contracts.schemas.mobile_workflow import (
    MobileWorkflowCommandV1,
    MobileWorkflowResultV1,
)
from sketch2life.contracts.schemas.raw_understanding import (
    RawUnderstandingFailureV1,
    RawUnderstandingSuccessV1,
)
from sketch2life.contracts.schemas.vision_v2 import (
    VisionProfileIdV2,
    vision_profile_catalog_hash_v2,
    vision_profile_catalog_v2,
    vision_profile_config_hash_v2,
)

HERE = Path(__file__).resolve().parent
FEATURE = HERE.parents[1]
STATE = HERE / "state.json"
RESERVATION = HERE / "understanding-reserved.json"
REPORT = HERE / "results.jsonl"
BASE = "http://127.0.0.1:8001"
SOURCE = FEATURE / "assets/generated/crayon-controls-v1/03-house-and-sun.png"
SOURCE_SHA = "2846a1b6a710e931da6abccf8c9858a938cbd021c0325bbd3f0c98d513fd0c36"


class ProbeStopped(Exception):
    """A sanitized check code; never include a response body in this exception."""


def require(condition: bool, code: str) -> None:
    if not condition:
        raise ProbeStopped(code)


def persist(path: Path, value: dict, *, exclusive: bool = False) -> None:
    with path.open("x" if exclusive else "w", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=True, indent=2)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())


def record(phase: str, **metadata: object) -> None:
    item = {"phase": phase, "recorded_at_utc": datetime.now(UTC).isoformat(), **metadata}
    line = json.dumps(item, ensure_ascii=True, sort_keys=True)
    with REPORT.open("a", encoding="utf-8") as stream:
        stream.write(line + "\n")
    print(line, flush=True)


def http(path: str, *, data: bytes | None = None, headers: dict | None = None) -> tuple:
    request = Request(BASE + path, data=data, headers=headers or {})
    try:
        with urlopen(request, timeout=150 if path.endswith("/understanding") else 20) as result:
            status = result.status
            body = result.read(2_000_001)
    except HTTPError as error:
        raise ProbeStopped(f"HTTP_{error.code}") from None
    except (URLError, TimeoutError):
        raise ProbeStopped("HTTP_TRANSPORT_FAILED_NO_RETRY") from None
    require(len(body) <= 2_000_000, "RESPONSE_TOO_LARGE")
    return status, json.loads(body)


def command(session_id: str, version: int, operation: str, **payload: object) -> dict:
    return MobileWorkflowCommandV1(
        request_id=f"modal-dev-{operation.lower()}-{uuid4().hex}",
        idempotency_key=f"modal-dev-{uuid4().hex}",
        session_id=session_id,
        expected_session_version=version,
        actor_ref="demo:local",
        payload={"operation": operation, **payload},
    ).model_dump(mode="json")


def post_command(path: str, value: dict) -> tuple[int, MobileWorkflowResultV1]:
    status, body = http(
        path,
        data=json.dumps(value).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    require(
        body.get("contract_name") == "MobileWorkflowResultV1"
        and body.get("contract_version") == "1.0",
        "WORKFLOW_WIRE_CONTRACT_MISMATCH",
    )
    result = MobileWorkflowResultV1.model_validate(body)
    require(result.request_id == value["request_id"], "REQUEST_ID_MISMATCH")
    require(result.session_id == value["session_id"], "SESSION_ID_MISMATCH")
    require(
        result.expected_session_version == value["expected_session_version"], "VERSION_MISMATCH"
    )
    return status, result


def prepare() -> None:
    require(not STATE.exists(), "PREPARATION_ALREADY_RECORDED_NO_NEW_SESSION")
    _, spec = http("/openapi.json")
    for path in (
        "/v1/sessions",
        "/v1/sessions/{session_id}/media/image",
        "/v1/sessions/{session_id}/understanding",
    ):
        require("post" in spec.get("paths", {}).get(path, {}), "DEMO_ROUTE_MISSING")
    image = SOURCE.read_bytes()
    require(hashlib.sha256(image).hexdigest() == SOURCE_SHA, "SYNTHETIC_SOURCE_HASH_MISMATCH")
    require(len(image) <= 5_000_000, "SOURCE_TOO_LARGE")
    session_id = str(uuid4())
    create = command(session_id, 0, "CREATE_SESSION")
    state = {"stage": "PREPARING", "create_command": create, "understanding_reserved": False}
    persist(STATE, state, exclusive=True)
    code, created = post_command("/v1/sessions", create)
    require(code == 201 and created.status == "SUCCEEDED", "SESSION_CREATE_NOT_SUCCEEDED")
    upload_id = "modal-dev-upload-" + uuid4().hex
    upload_key = "modal-dev-upload-key-" + uuid4().hex
    state.update(upload_request_id=upload_id, upload_idempotency_key=upload_key)
    persist(STATE, state)
    boundary = "modal-dev-" + uuid4().hex
    fields = b"".join(
        (
            f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n{value}\r\n'
        ).encode("ascii")
        for name, value in (
            ("source_media_type", "image/png"),
            ("normalization_policy", "IDENTITY_V1"),
        )
    )
    body = (
        fields
        + (
            f'--{boundary}\r\nContent-Disposition: form-data; name="image"; '
            'filename="synthetic-crayon-house-sun.png"\r\nContent-Type: image/png\r\n\r\n'
        ).encode("ascii")
        + image
        + f"\r\n--{boundary}--\r\n".encode("ascii")
    )
    code, uploaded_body = http(
        f"/v1/sessions/{session_id}/media/image",
        data=body,
        headers={
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "X-Request-ID": upload_id,
            "X-Expected-Session-Version": str(created.observed_session_version),
            "Idempotency-Key": upload_key,
            "X-Actor-Ref": "demo:local",
            "X-Synthetic-Non-Child-Confirmed": "true",
        },
    )
    require(
        uploaded_body.get("contract_name") == "MobileWorkflowResultV1"
        and uploaded_body.get("contract_version") == "1.0",
        "UPLOAD_WIRE_CONTRACT_MISMATCH",
    )
    uploaded = MobileWorkflowResultV1.model_validate(uploaded_body)
    require(code == 200 and uploaded.status == "SUCCEEDED", "UPLOAD_NOT_SUCCEEDED")
    require(
        uploaded.session_id == session_id and uploaded.request_id == upload_id, "UPLOAD_ID_MISMATCH"
    )
    require(
        uploaded.payload is not None
        and uploaded.payload.get("contract_name") == "ImageAdmissionReceiptV2"
        and uploaded.payload.get("contract_version") == "2.0",
        "ADMISSION_WIRE_CONTRACT_MISMATCH",
    )
    admission = ImageAdmissionReceiptV2.model_validate(uploaded.payload)
    require(admission.session_id == session_id and admission.decision == "ADMITTED", "NOT_ADMITTED")
    require(admission.source_image_ref is not None, "ADMITTED_SOURCE_MISSING")
    require(admission.source_image_ref.sha256 == SOURCE_SHA, "ADMITTED_HASH_MISMATCH")
    require(admission.normalization_policy == "IDENTITY_V1", "NORMALIZATION_MISMATCH")
    persist(HERE / "admission.json", admission.model_dump(mode="json"), exclusive=True)
    state.update(
        stage="ADMITTED",
        session_id=session_id,
        source_image_ref=admission.source_image_ref.model_dump(mode="json"),
        understanding_command=command(
            session_id,
            uploaded.observed_session_version,
            "RUN_UNDERSTANDING",
            user_initiated=True,
            narration={"kind": "NONE"},
        ),
    )
    persist(STATE, state)
    record(
        "PREPARE",
        status="ADMITTED",
        create_http_status=201,
        upload_http_status=200,
        observed_session_version=uploaded.observed_session_version,
        source_sha256=SOURCE_SHA,
        model_requests_sent=0,
    )


def understand() -> None:
    state = json.loads(STATE.read_text(encoding="utf-8"))
    require(state.get("stage") == "ADMITTED", "PREPARATION_NOT_READY")
    require(not state.get("understanding_reserved"), "SINGLE_REQUEST_BUDGET_ALREADY_USED")
    value = MobileWorkflowCommandV1.model_validate(state["understanding_command"])
    require(
        value.payload
        == {
            "operation": "RUN_UNDERSTANDING",
            "user_initiated": True,
            "narration": {"kind": "NONE"},
        },
        "UNEXPECTED_UNDERSTANDING_COMMAND",
    )
    require(value.session_id == state["session_id"], "STATE_SESSION_MISMATCH")
    persist(
        RESERVATION,
        {"request_id": value.request_id, "session_id": value.session_id, "max_requests": 1},
        exclusive=True,
    )
    state.update(stage="UNDERSTANDING_RESERVED", understanding_reserved=True)
    persist(STATE, state)
    record("UNDERSTAND", status="RESERVED_BEFORE_SEND", max_requests=1)
    started = time.monotonic()
    code, response = post_command(
        f"/v1/sessions/{value.session_id}/understanding",
        value.model_dump(mode="json"),
    )
    elapsed = round(time.monotonic() - started, 3)
    payload = response.payload or {}
    if code != 200 or response.status != "SUCCEEDED":
        failure_metadata = {}
        if response.failure is not None:
            failure_metadata["workflow_error_code"] = response.failure.code
            failure_metadata["retryable"] = response.failure.retryable
        if (
            payload.get("contract_name") == "RawUnderstandingResultV1"
            and payload.get("status") == "FAILED"
        ):
            failed = RawUnderstandingFailureV1.model_validate(
                {
                    key: item
                    for key, item in payload.items()
                    if key in RawUnderstandingFailureV1.model_fields
                }
            )
            failure_metadata["raw_error_code"] = failed.failure.code
            failure_metadata["retryable"] = failed.failure.retryable
        record(
            "UNDERSTAND",
            status=response.status,
            http_status=code,
            client_wall_seconds=elapsed,
            **failure_metadata,
        )
        raise ProbeStopped("UNDERSTANDING_NOT_SUCCEEDED")
    require(
        payload.get("contract_name") == "RawUnderstandingResultV1"
        and payload.get("contract_version") == "1.0"
        and payload.get("status") == "SUCCEEDED"
        and payload.get("gate_a_required") is True
        and payload.get("narration_status") == "NOT_SUPPLIED",
        "RAW_WIRE_CONTRACT_MISMATCH",
    )
    raw = RawUnderstandingSuccessV1.model_validate(
        {
            key: item
            for key, item in payload.items()
            if key in RawUnderstandingSuccessV1.model_fields
        }
    )
    require(raw.session_id == value.session_id, "RAW_SESSION_MISMATCH")
    require(raw.correlation_id == value.request_id, "RAW_CORRELATION_MISMATCH")
    require(
        raw.source_image_ref.model_dump(mode="json") == state["source_image_ref"],
        "RAW_SOURCE_MISMATCH",
    )
    require(raw.narration_status == "NOT_SUPPLIED" and not raw.asr_claims, "NARRATION_MISMATCH")
    catalog = vision_profile_catalog_v2()
    profile = catalog.resolve(VisionProfileIdV2.QWEN3_VL_8B_INSTRUCT_BF16_V1)
    provenance = raw.provenance
    require(provenance.profile_id == profile.profile_id, "PROFILE_MISMATCH")
    require(
        provenance.profile_catalog_hash == vision_profile_catalog_hash_v2(catalog),
        "CATALOG_MISMATCH",
    )
    require(provenance.config_hash == vision_profile_config_hash_v2(profile), "CONFIG_MISMATCH")
    require(provenance.adapter_version == profile.adapter_version, "ADAPTER_MISMATCH")
    require(provenance.model_provenance == profile.model_provenance, "MODEL_PROVENANCE_MISMATCH")
    progress = payload.get("understanding_progress", {})
    require(
        progress.get("stage") == "TOPIC_READY" and progress.get("gate_a_ready") is True,
        "GATE_NOT_READY",
    )
    require(progress.get("provider_attempt_count") == 1, "ATTEMPT_MISMATCH")
    state["stage"] = "COMPLETED"
    persist(STATE, state)
    record(
        "UNDERSTAND",
        status="SUCCEEDED",
        http_status=code,
        client_wall_seconds=elapsed,
        observed_session_version=response.observed_session_version,
        source_sha256=SOURCE_SHA,
        upstream_contract=provenance.upstream_contract,
        upstream_contract_version=provenance.upstream_contract_version,
        profile_id=provenance.profile_id,
        model_identifier=profile.model_provenance.model_identifier,
        model_revision=profile.model_provenance.model_revision,
        profile_catalog_hash=provenance.profile_catalog_hash,
        config_hash=provenance.config_hash,
        adapter_version=provenance.adapter_version,
        gate_a_required=raw.gate_a_required,
        gate_a_ready=True,
        provider_attempt_count=1,
        repair_attempted=progress.get("repair_attempted"),
        entities_count=len(raw.entities),
        actions_count=len(raw.actions),
        relations_count=len(raw.relations),
        themes_count=len(raw.themes),
        narration_status=raw.narration_status,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=("prepare", "understand"))
    phase = parser.parse_args().phase
    try:
        prepare() if phase == "prepare" else understand()
    except (ProbeStopped, ValidationError, OSError, ValueError) as error:
        check = str(error) if isinstance(error, ProbeStopped) else type(error).__name__
        record(phase.upper(), status="STOPPED_NO_RETRY", check=check)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
