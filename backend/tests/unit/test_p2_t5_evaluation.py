from datetime import UTC, datetime
from pathlib import Path

from sketch2life.contracts.schemas.p2_t5_evaluation import Split
from sketch2life.interfaces.cli.p2_t5_evaluation import build_harness

ROOT = Path(__file__).resolve().parents[3]
MANIFEST = (
    "features/FEAT-003-multimodal-understanding/fixtures/"
    "p2-t5-evaluation-v1/manifest-v1.json"
)
FIXTURES = "features/FEAT-003-multimodal-understanding/fixtures/p2-t5-evaluation-v1"


def test_evaluates_both_splits_and_preserves_mutation_precedence() -> None:
    harness = build_harness(ROOT)
    for split, expected in ((Split.DEVELOPMENT, 12), (Split.HELD_OUT, 8)):
        report = harness.evaluate(
            MANIFEST,
            FIXTURES,
            split,
            f"run-{split.value.lower().replace('_', '-')}",
            datetime(2026, 9, 20, 12, 0, tzinfo=UTC),
        )
        assert len(report.deterministic_core["case_results"]) == expected
    heldout = harness.evaluate(
        MANIFEST,
        FIXTURES,
        Split.HELD_OUT,
        "run-heldout-check",
        datetime(2026, 9, 20, 12, 0, tzinfo=UTC),
    )
    by_id = {row["fixture_id"]: row for row in heldout.deterministic_core["case_results"]}
    assert by_id["heldout-006"]["fusion"]["rejection_phase"] == "ADMISSIBILITY"
    assert by_id["heldout-008"]["fusion"]["rejection_phase"] == "CORRELATION"
