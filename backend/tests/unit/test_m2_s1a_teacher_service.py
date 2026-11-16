from __future__ import annotations

import pytest

from sketch2life.domain.core_foundation import (
    CoreErrorCode,
    CoreRuleViolation,
    validate_age_months,
)


def test_existing_age_validation_default_remains_36_to_155() -> None:
    validate_age_months(36)
    validate_age_months(120)
    validate_age_months(121)
    validate_age_months(155)

    with pytest.raises(CoreRuleViolation) as error:
        validate_age_months(35)
    assert error.value.code is CoreErrorCode.AGE_OUT_OF_RANGE

    with pytest.raises(CoreRuleViolation) as error:
        validate_age_months(156)
    assert error.value.code is CoreErrorCode.AGE_OUT_OF_RANGE


@pytest.mark.parametrize("age_months", (36, 120))
def test_teacher_age_validation_accepts_only_new_value_boundaries(age_months: int) -> None:
    validate_age_months(age_months, maximum_months=120)


@pytest.mark.parametrize("age_months", (35, 121, 155, 156))
def test_teacher_age_validation_rejects_outside_36_to_120(age_months: int) -> None:
    with pytest.raises(CoreRuleViolation) as error:
        validate_age_months(age_months, maximum_months=120)
    assert error.value.code is CoreErrorCode.AGE_OUT_OF_RANGE
