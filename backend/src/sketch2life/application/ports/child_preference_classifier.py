"""Provider-neutral application boundary for adult preference suggestions."""

from __future__ import annotations

from typing import Protocol

from sketch2life.contracts.schemas.child_preference_classification import (
    ChildPreferenceClassificationRequestV1,
    ChildPreferenceClassificationV1,
)


class ChildPreferenceClassifierPort(Protocol):
    def classify(
        self, request: ChildPreferenceClassificationRequestV1
    ) -> ChildPreferenceClassificationV1: ...


__all__ = ["ChildPreferenceClassifierPort"]
