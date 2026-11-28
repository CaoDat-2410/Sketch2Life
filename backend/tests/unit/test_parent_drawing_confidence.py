"""The drawing worker sends no confidence; the Parent route must not reject its result for that."""

from __future__ import annotations

from sketch2life.interfaces.http.routers.parent_ai import _drawing_confidence


def test_missing_worker_confidence_means_unknown() -> None:
    assert _drawing_confidence({"candidate_subject": "con ca", "visible_features": ["vay"]}) == 0.0


def test_reported_confidence_is_passed_through_for_validation() -> None:
    assert _drawing_confidence({"confidence": 0.5}) == 0.5
    assert _drawing_confidence({"confidence": "high"}) == "high"
