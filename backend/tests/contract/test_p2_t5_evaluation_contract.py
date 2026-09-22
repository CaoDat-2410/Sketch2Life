from datetime import UTC, datetime

from sketch2life.contracts.schemas.p2_t5_evaluation import (
    P2T5RunRecordV1,
    Split,
    canonical_json_bytes,
    correlation_id,
    format_utc,
)


def test_run_contract_canonicalizes_utc_and_correlation() -> None:
    run = P2T5RunRecordV1(
        run_id="contract-run",
        manifest_id="p2-t5-evaluation-v1",
        manifest_version="1.0",
        manifest_sha256="0" * 64,
        oracle_sha256="1" * 64,
        fixture_split=Split.DEVELOPMENT,
        executed_at=format_utc(datetime(2026, 9, 20, 12, 0, tzinfo=UTC)),
    )
    assert run.executed_at.endswith(".000000Z")
    assert correlation_id(
        manifest_id=run.manifest_id,
        manifest_version=run.manifest_version,
        fixture_id="dev-001",
        split=Split.DEVELOPMENT,
    ).startswith("p2t5-corr-")
    assert canonical_json_bytes(run.model_dump(mode="json")) == canonical_json_bytes(
        run.model_dump(mode="json")
    )
