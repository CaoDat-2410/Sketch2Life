"""Compile learning objectives into bounded generation briefs."""

from __future__ import annotations

from .schemas import GenerationBrief, LearningObjective


class GenerationBriefCompiler:
    """Builds deterministic, single-objective prompts for a video provider."""

    _scene_rules: dict[str, dict[str, list[str]]] = {
        "butterfly_proboscis": {
            "show": ["butterfly", "flower", "proboscis", "nectar"],
            "avoid": ["fantasy anatomy", "extra animals", "text overlays", "scary imagery"],
        }
    }

    def __init__(
        self,
        duration_sec: int = 8,
        profile: dict[str, str | int | float | bool] | None = None,
    ) -> None:
        if not 5 <= duration_sec <= 10:
            raise ValueError("duration_sec must be between 5 and 10")
        self._duration_sec = duration_sec
        self._profile = profile or {
            "width": 1280,
            "height": 704,
            "fps": 24,
            "offload_model": True,
        }

    def compile(self, objective: LearningObjective) -> GenerationBrief:
        rules = self._scene_rules.get(
            objective.objective_id,
            {"show": [objective.concept], "avoid": ["unsafe imagery", "text overlays"]},
        )
        return GenerationBrief(
            objective_id=objective.objective_id,
            objective_version=objective.version,
            locale=objective.locale,
            age_band=objective.age_band,
            duration_sec=self._duration_sec,
            prompt=(
                f"Simple educational illustration for children aged {objective.age_band}: "
                f"{objective.concept}. Show only the approved learning concept."
            ),
            show=rules["show"],
            avoid=rules["avoid"],
            profile=self._profile,
        )
