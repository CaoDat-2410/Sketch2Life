"""Independent, deterministic P2-T5 metric and oracle scoring functions."""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Iterable, Mapping
from decimal import Decimal
from typing import Any

from sketch2life.contracts.schemas.p2_t5_evaluation import (
    MeasurementStatus,
    P2T5MeasurementV1,
    decimal_value,
)


def normalize_semantic(value: str) -> str:
    """Apply only the approved B4 semantic matching view."""

    normalized = unicodedata.normalize("NFC", value).casefold().replace("-", " ")
    return " ".join(normalized.split())


def levenshtein(left: tuple[str, ...], right: tuple[str, ...]) -> int:
    previous = list(range(len(right) + 1))
    for index, left_item in enumerate(left, start=1):
        current = [index]
        for right_index, right_item in enumerate(right, start=1):
            current.append(
                min(
                    current[-1] + 1,
                    previous[right_index] + 1,
                    previous[right_index - 1] + (left_item != right_item),
                )
            )
        previous = current
    return previous[-1]


def _measurement(
    metric_id: str,
    *,
    numerator: int,
    denominator: int,
    unit: str,
    eligibility_rule_id: str,
) -> P2T5MeasurementV1:
    if denominator == 0:
        return P2T5MeasurementV1(
            metric_id=metric_id,
            status=MeasurementStatus.NOT_MEASURED,
            numerator=0,
            denominator=0,
            unit=unit,
            reason_code="NO_ELIGIBLE_CASES",
            eligibility_rule_id=eligibility_rule_id,
        )
    ratio = Decimal(numerator) / Decimal(denominator)
    return P2T5MeasurementV1(
        metric_id=metric_id,
        status=MeasurementStatus.MEASURED,
        value=decimal_value(ratio),
        numerator=numerator,
        denominator=denominator,
        unit=unit,
        eligibility_rule_id=eligibility_rule_id,
    )


def score_asr(
    reference: str | None, hypothesis: str | None
) -> tuple[P2T5MeasurementV1, P2T5MeasurementV1]:
    if not reference or hypothesis is None:
        return (
            _measurement(
                "wer",
                numerator=0,
                denominator=0,
                unit="ratio",
                eligibility_rule_id="P2T5.ASRMetricRuleV1",
            ),
            _measurement(
                "cer",
                numerator=0,
                denominator=0,
                unit="ratio",
                eligibility_rule_id="P2T5.ASRMetricRuleV1",
            ),
        )
    wer_reference = tuple(re.findall(r"\S+", normalize_asr(reference)))
    wer_hypothesis = tuple(re.findall(r"\S+", normalize_asr(hypothesis)))
    cer_reference = tuple(normalize_asr(reference).replace(" ", ""))
    cer_hypothesis = tuple(normalize_asr(hypothesis).replace(" ", ""))
    return (
        _measurement(
            "wer",
            numerator=levenshtein(wer_reference, wer_hypothesis),
            denominator=len(wer_reference),
            unit="ratio",
            eligibility_rule_id="P2T5.ASRMetricRuleV1",
        ),
        _measurement(
            "cer",
            numerator=levenshtein(cer_reference, cer_hypothesis),
            denominator=len(cer_reference),
            unit="ratio",
            eligibility_rule_id="P2T5.ASRMetricRuleV1",
        ),
    )


def normalize_asr(value: str) -> str:
    value = unicodedata.normalize("NFC", value).casefold()
    value = re.sub(r"[^\w\s\u0111]", " ", value, flags=re.UNICODE)
    return " ".join(value.split())


def _keys(values: Iterable[Mapping[str, Any]]) -> set[tuple[str, str]]:
    return {(str(item["reason_code"]), str(item["fused_observation_id"])) for item in values}


def score_conflicts(
    predicted: Iterable[Mapping[str, Any]],
    reference: Iterable[Mapping[str, Any]],
) -> tuple[
    P2T5MeasurementV1, P2T5MeasurementV1, P2T5MeasurementV1, P2T5MeasurementV1, P2T5MeasurementV1
]:
    predicted_keys = _keys(predicted)
    reference_keys = _keys(reference)
    tp = len(predicted_keys & reference_keys)
    fp = len(predicted_keys - reference_keys)
    fn = len(reference_keys - predicted_keys)
    precision_denominator = tp + fp
    recall_denominator = tp + fn
    precision = _measurement(
        "conflict_precision",
        numerator=tp,
        denominator=precision_denominator,
        unit="ratio",
        eligibility_rule_id="P2T5.ConflictMatchingRuleV1",
    )
    recall = _measurement(
        "conflict_recall",
        numerator=tp,
        denominator=recall_denominator,
        unit="ratio",
        eligibility_rule_id="P2T5.ConflictMatchingRuleV1",
    )
    return (
        _measurement(
            "conflict_tp",
            numerator=tp,
            denominator=1,
            unit="count",
            eligibility_rule_id="P2T5.ConflictMatchingRuleV1",
        ),
        _measurement(
            "conflict_fp",
            numerator=fp,
            denominator=1,
            unit="count",
            eligibility_rule_id="P2T5.ConflictMatchingRuleV1",
        ),
        _measurement(
            "conflict_fn",
            numerator=fn,
            denominator=1,
            unit="count",
            eligibility_rule_id="P2T5.ConflictMatchingRuleV1",
        ),
        precision,
        recall,
    )
