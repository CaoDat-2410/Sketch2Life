from sketch2life.application.services.p2_t5_scoring import score_asr, score_conflicts
from sketch2life.contracts.schemas.p2_t5_evaluation import MeasurementStatus


def test_asr_metrics_are_decimal_and_empty_sets_are_not_measured() -> None:
    wer, cer = score_asr("hello world", "hello word")
    assert wer.status is MeasurementStatus.MEASURED
    assert cer.status is MeasurementStatus.MEASURED
    empty, _ = score_asr(None, None)
    assert empty.status is MeasurementStatus.NOT_MEASURED


def test_conflict_metrics_use_independent_key_sets() -> None:
    metrics = score_conflicts(
        [{"reason_code": "R1", "fused_observation_id": "a"}],
        [{"reason_code": "R1", "fused_observation_id": "a"}],
    )
    assert metrics[0].numerator == 1
    assert metrics[3].value == "1.000000"
