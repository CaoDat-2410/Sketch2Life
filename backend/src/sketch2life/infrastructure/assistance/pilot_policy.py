"""Fixed synthetic-only assistance policy for local/test pilot execution."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

from sketch2life.domain.assistance import PolicySnapshot


@dataclass(frozen=True, slots=True)
class SyntheticPilotPolicySnapshot(PolicySnapshot):
    age_policy_ref: str
    region_policy_revision: int
    regions: Mapping[str, frozenset[str] | None]


PILOT_SYNTHETIC_POLICY_V1 = SyntheticPilotPolicySnapshot(
    policy_id="PILOT_SYNTHETIC_POLICY_V1",
    version="1",
    status="PILOT_SYNTHETIC_ONLY_NOT_PRODUCTION",
    assistance_enabled=True,
    allowed_levels=frozenset({"level_fx_1", "level_fx_2"}),
    debounce_seconds=5,
    per_target_limit=3,
    per_session_limit=20,
    cache_enabled=True,
    purpose_code="ai_drawing_assistance",
    age_policy_ref="age-policy:36-155-months:proposed",
    region_policy_revision=2,
    regions=MappingProxyType({"region_fx_open": None}),
)


class PilotSyntheticPolicy:
    """Return the immutable pilot profile only in an explicitly enabled local/test process."""

    def __init__(self, *, environment: str, pilot_enabled: bool) -> None:
        self._allowed = environment in {"local", "test"} and pilot_enabled is True

    def current(self, organization_id: str, session_id: str) -> PolicySnapshot | None:
        if not self._allowed or not organization_id or not session_id:
            return None
        return PILOT_SYNTHETIC_POLICY_V1


__all__ = ["PILOT_SYNTHETIC_POLICY_V1", "PilotSyntheticPolicy"]
