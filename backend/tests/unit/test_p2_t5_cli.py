import json
from pathlib import Path

from sketch2life.interfaces.cli.p2_t5_evaluation import main

ROOT = Path(__file__).resolve().parents[3]
MANIFEST = (
    "features/FEAT-003-multimodal-understanding/fixtures/"
    "p2-t5-evaluation-v1/manifest-v1.json"
)
FIXTURES = "features/FEAT-003-multimodal-understanding/fixtures/p2-t5-evaluation-v1"


def test_cli_validate_writes_closed_envelope(tmp_path: Path) -> None:
    output = tmp_path / "validate.json"
    arguments = [
        "validate",
        "--manifest",
        MANIFEST,
        "--fixture-root",
        FIXTURES,
        "--output",
        str(output),
    ]
    assert main(arguments) == 0
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["success"] is True
    assert payload["payload"]["entry_count"] == 20


def test_cli_rejects_non_fixture_provider(tmp_path: Path) -> None:
    output = tmp_path / "failure.json"
    arguments = [
        "validate",
        "--provider",
        "qwen",
        "--manifest",
        MANIFEST,
        "--fixture-root",
        FIXTURES,
        "--output",
        str(output),
    ]
    assert main(arguments) == 2
    assert (
        json.loads(output.read_text(encoding="utf-8"))["failure"]["code"]
        == "UNSUPPORTED_PROVIDER"
    )
