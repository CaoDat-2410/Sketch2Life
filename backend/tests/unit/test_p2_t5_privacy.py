from pathlib import Path


def test_fixture_package_contains_no_provider_or_raw_text_literals() -> None:
    root = (
        Path(__file__).resolve().parents[3]
        / "features"
        / "FEAT-003-multimodal-understanding"
        / "fixtures"
        / "p2-t5-evaluation-v1"
    )
    text = "\n".join(path.read_text(encoding="utf-8") for path in root.glob("*.json"))
    assert "qwen" not in text.casefold()
    assert "whisper" not in text.casefold()
    sentinel = "synthetic-" + "noncanonical-match-view-sentinel-v0"
    assert sentinel not in text
