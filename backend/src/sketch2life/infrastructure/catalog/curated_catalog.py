"""Loader and typed bridge for the authored FEAT-022 catalog revision.

The curated revision is deliberately separate from the 100-record MVP catalog.
This module only loads authored records; it never asks an AI provider to invent
activities or mutates the catalog at runtime.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from sketch2life.contracts.schemas.p1_experience import (
    ActivityTemplateV1,
    PedagogicalAlignmentV1,
    VersionedRefV1,
)
from sketch2life.contracts.schemas.workflow_demo import AgeBand


class CuratedCatalogError(ValueError):
    """Raised when the authored expansion revision is unsafe to load."""


_AGE_BANDS: tuple[AgeBand, ...] = ("0-3", "3-6", "6-9", "9-12")
_AGE_MONTHS: dict[AgeBand, tuple[int, int]] = {
    "0-3": (0, 35),
    "3-6": (36, 71),
    "6-9": (72, 107),
    "9-12": (108, 155),
}
_INTERACTION_MODES: dict[str, str] = {
    "movement": "TRANSFER",
    "sensorial": "SORTING",
    "practical_life": "SEQUENCE",
    "language": "RESEARCH",
    "mathematics": "RESEARCH",
    "science": "OBSERVATION",
    "social_studies": "RESEARCH",
}


@dataclass(frozen=True, slots=True)
class CuratedActivityVariant:
    activity_id: str
    activity_version: int
    activity_family_id: str
    variant_id: str
    catalog_revision: str
    age_band: AgeBand
    concept_ids: tuple[str, ...]
    allowed_objective_ids: tuple[str, ...]
    primary_objective_id: str
    secondary_objective_ids: tuple[str, ...]
    pedagogical_alignment: PedagogicalAlignmentV1
    area: str
    title_vi: str
    phrases_vi: tuple[str, ...]
    aliases_vi: tuple[str, ...]
    action_vi: str
    challenge_vi: str
    material_option_ids: tuple[str, ...]
    minimum_supervision: Literal["NONE", "NEARBY", "DIRECT"]
    safety_vi: tuple[str, ...]
    policy_constraints: tuple[str, ...]
    duration_minutes: int
    duration_type: Literal["SINGLE_SESSION", "MULTI_DAY"]
    initial_session_minutes: int | None
    daily_observation_minutes: int | None
    min_days: int | None
    max_days: int | None
    continuity_mode: Literal["DIRECT_CONTINUATION", "RELATED_EXPANSION"]
    expansion_bridge_required: bool
    direct_observation_concept_ids: tuple[str, ...]
    age_specific_goal_vi: str
    video_setup_vi: str
    video_focus_cues_vi: tuple[str, ...]
    video_handoff_prompt_vi: str
    offscreen_instruction_vi: str
    provenance_source: str
    provenance_sha256: str

    @property
    def objective_ids(self) -> tuple[str, ...]:
        """Compatibility view; new code should use primary/secondary fields."""

        return (self.primary_objective_id, *self.secondary_objective_ids)

    @property
    def age_months(self) -> tuple[int, int]:
        return _AGE_MONTHS[self.age_band]

    @property
    def steps_vi(self) -> tuple[str, ...]:
        return (
            "Người lớn chuẩn bị khay vật liệu, kiểm tra không gian và nhắc quy tắc an toàn.",
            self.action_vi,
            self.challenge_vi,
            "Trẻ cùng người lớn thu dọn vật liệu và nói hoặc chỉ điều mình đã quan sát.",
        )

    def to_template(self) -> ActivityTemplateV1:
        minimum, maximum = self.age_months
        return ActivityTemplateV1(
            template_id=f"TPL-{self.activity_id}-V{self.activity_version}",
            template_version=1,
            activity_ref=VersionedRefV1(
                id=self.activity_id,
                version=self.activity_version,
            ),
            objective_refs=tuple(
                VersionedRefV1(id=objective_id, version=1)
                for objective_id in self.objective_ids
            ),
            supported_anchor_labels=tuple(
                dict.fromkeys((*self.phrases_vi, *self.aliases_vi, self.title_vi))
            ),
            supported_anchor_kinds=("subject", "action", "visual_feature", "story"),
            interaction_mode=_INTERACTION_MODES.get(self.area, "OBSERVATION"),  # type: ignore[arg-type]
            age_months_min=minimum,
            age_months_max=maximum,
            readiness_ids=(),
            prerequisite_activity_ids=(),
            material_option_ids=self.material_option_ids,
            minimum_supervision=self.minimum_supervision,
            policy_constraints=self.policy_constraints,
            safety_rule_ids=tuple(
                f"{self.activity_id}:SAFETY:{index + 1}"
                for index, _ in enumerate(self.safety_vi)
            ),
            steps_vi=self.steps_vi,
            personalization_slots=("material_substitute", "support_variant"),
            provenance_source=self.provenance_source,
            provenance_sha256=self.provenance_sha256,
            review_status="DEMO_ELIGIBLE",
            production_eligible=False,
        )


@dataclass(frozen=True, slots=True)
class CuratedCatalogV2:
    catalog_revision: str
    variants: tuple[CuratedActivityVariant, ...]

    def by_activity_id(self) -> dict[str, CuratedActivityVariant]:
        return {item.activity_id: item for item in self.variants}

    def by_family_id(self) -> dict[str, tuple[CuratedActivityVariant, ...]]:
        grouped: dict[str, list[CuratedActivityVariant]] = {}
        for item in self.variants:
            grouped.setdefault(item.activity_family_id, []).append(item)
        return {key: tuple(value) for key, value in grouped.items()}


def load_curated_catalog_v2(
    root: Path,
    *,
    revision: str | None = None,
) -> CuratedCatalogV2:
    directory = root / "data" / "activity-catalog" / "curated" / "v2"
    paths = tuple(sorted(directory.glob("activity-families.v2.part*.json")))
    if not paths:
        raise CuratedCatalogError("curated V2 catalog parts are missing")

    raw_families: list[dict[str, Any]] = []
    base_revision: str | None = None
    for path in paths:
        try:
            document = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise CuratedCatalogError(f"cannot read curated catalog part: {path}") from exc
        if document.get("schema_version") != 2:
            raise CuratedCatalogError(f"invalid curated catalog schema: {path}")
        part_revision = document.get("catalog_revision")
        if not isinstance(part_revision, str) or not part_revision:
            raise CuratedCatalogError(f"missing catalog revision: {path}")
        if base_revision is None:
            base_revision = part_revision
        elif base_revision != part_revision:
            raise CuratedCatalogError("curated catalog parts use different revisions")
        families = document.get("families")
        if not isinstance(families, list):
            raise CuratedCatalogError(f"curated catalog families must be a list: {path}")
        raw_families.extend(item for item in families if isinstance(item, dict))

    assert base_revision is not None
    requested_revision = revision
    if requested_revision not in {None, base_revision}:
        raise CuratedCatalogError(
            f"requested catalog revision is unavailable: {requested_revision}"
        )
    if requested_revision == "catalog-2026-09-expansion-1":
        raw_families = _restore_expansion_one_families(raw_families)
        overrides: dict[str, dict[str, Any]] = {}
        effective_revision = requested_revision
    else:
        overrides, effective_revision = _load_variant_contract_overrides(
            directory, base_revision
        )
    variants: list[CuratedActivityVariant] = []
    family_ids: set[str] = set()
    activity_ids: set[str] = set()
    for family in raw_families:
        family_id = _required_str(family, "family_id")
        if family_id in family_ids:
            raise CuratedCatalogError(f"duplicate activity family: {family_id}")
        family_ids.add(family_id)
        concept_ids = _required_tuple(family, "concept_ids")
        objective_key = (
            "allowed_objective_ids"
            if "allowed_objective_ids" in family
            else "objective_ids"
        )
        objective_ids = _required_tuple(family, objective_key)
        area = _required_str(family, "area")
        phrases = _required_tuple(family, "phrases_vi")
        aliases = tuple(str(item) for item in family.get("aliases_vi", []))
        materials = _required_tuple(family, "material_option_ids")
        supervision = _literal_supervision(family.get("minimum_supervision"))
        safety = _required_tuple(family, "safety_vi")
        policies = tuple(str(item) for item in family.get("policy_constraints", []))
        raw_variants = family.get("variants")
        if not isinstance(raw_variants, list) or len(raw_variants) != 4:
            raise CuratedCatalogError(f"{family_id} must provide exactly four age variants")
        seen_bands: set[str] = set()
        for _index, raw_variant in enumerate(raw_variants):
            if not isinstance(raw_variant, dict):
                raise CuratedCatalogError(f"{family_id} contains a non-object variant")
            activity_id = _required_str(raw_variant, "activity_id")
            if activity_id in activity_ids:
                raise CuratedCatalogError(f"duplicate curated activity ID: {activity_id}")
            activity_ids.add(activity_id)
            age_band = raw_variant.get("age_band")
            if age_band not in _AGE_BANDS or age_band in seen_bands:
                raise CuratedCatalogError(f"{family_id} has invalid or duplicate age band")
            seen_bands.add(age_band)
            title = _required_str(raw_variant, "title_vi")
            action = _required_str(raw_variant, "action_vi")
            challenge = _required_str(raw_variant, "challenge_vi")
            duration = raw_variant.get("duration_minutes")
            if not isinstance(duration, int) or not 1 <= duration <= 60:
                raise CuratedCatalogError(f"{activity_id} has invalid duration")
            if effective_revision != base_revision and activity_id not in overrides:
                raise CuratedCatalogError(
                    f"{activity_id} is missing from the active variant contract manifest"
                )
            override = overrides.get(activity_id, {})
            primary_objective_id = str(
                override.get("primary_objective_id", objective_ids[0])
            ).strip()
            secondary_objective_ids = tuple(
                str(item).strip()
                for item in override.get("secondary_objective_ids", objective_ids[1:])
            )
            variant_objectives = (primary_objective_id, *secondary_objective_ids)
            if any(
                not objective_id or objective_id not in objective_ids
                for objective_id in variant_objectives
            ):
                raise CuratedCatalogError(
                    f"{activity_id} objective override is outside family allowed_objective_ids"
                )
            if len(set(variant_objectives)) != len(variant_objectives):
                raise CuratedCatalogError(f"{activity_id} has duplicate objective IDs")
            pedagogical_payload = override.get("pedagogical_alignment")
            if not isinstance(pedagogical_payload, dict):
                pedagogical_payload = {
                    "primary_objective_id": primary_objective_id,
                    "expected_observable_behavior_vi": (
                        f"{action}; kiểm tra kết quả theo gợi ý: {challenge}"
                    ),
                    "reviewer_status": "DEMO_REVIEWED",
                }
            try:
                pedagogical_alignment = PedagogicalAlignmentV1.model_validate(
                    pedagogical_payload
                )
            except ValueError as exc:
                raise CuratedCatalogError(
                    f"{activity_id} has invalid pedagogical alignment"
                ) from exc
            if pedagogical_alignment.primary_objective_id != primary_objective_id:
                raise CuratedCatalogError(
                    f"{activity_id} pedagogical alignment objective does not match variant"
                )
            duration_type = override.get("duration_type", "SINGLE_SESSION")
            if duration_type == "SINGLE_SESSION":
                initial_session_minutes = None
                daily_observation_minutes = None
                min_days = None
                max_days = None
            elif duration_type == "MULTI_DAY":
                initial_session_minutes = override.get(
                    "initial_session_minutes", duration
                )
                daily_observation_minutes = override.get(
                    "daily_observation_minutes", duration
                )
                min_days = override.get("min_days")
                max_days = override.get("max_days")
                if not all(
                    isinstance(value, int) and value >= 1
                    for value in (
                        initial_session_minutes,
                        daily_observation_minutes,
                        min_days,
                        max_days,
                    )
                ):
                    raise CuratedCatalogError(f"{activity_id} has invalid multi-day duration")
                assert isinstance(min_days, int) and isinstance(max_days, int)
                if max_days < min_days:
                    raise CuratedCatalogError(f"{activity_id} has invalid multi-day duration")
            else:
                raise CuratedCatalogError(f"{activity_id} has invalid duration_type")
            continuity_mode = override.get(
                "continuity_mode",
                "RELATED_EXPANSION" if activity_id == "ACT-0116" else "DIRECT_CONTINUATION",
            )
            if continuity_mode not in {"DIRECT_CONTINUATION", "RELATED_EXPANSION"}:
                raise CuratedCatalogError(f"{activity_id} has invalid continuity_mode")
            expansion_bridge_required = bool(
                override.get("expansion_bridge_required", continuity_mode == "RELATED_EXPANSION")
            )
            if continuity_mode == "RELATED_EXPANSION" and not expansion_bridge_required:
                raise CuratedCatalogError(
                    f"{activity_id} related expansion must require an explicit bridge"
                )
            direct_observation_concept_ids = tuple(
                str(item).strip()
                for item in override.get("direct_observation_concept_ids", concept_ids)
            )
            if not direct_observation_concept_ids:
                raise CuratedCatalogError(f"{activity_id} must declare direct observation concepts")
            age_specific_goal_vi = str(
                override.get(
                    "age_specific_goal_vi",
                    f"Trẻ {action.lower()} theo cách phù hợp với lứa tuổi.",
                )
            ).strip()
            video_setup_vi = str(
                override.get(
                    "video_setup_vi",
                    f"Người lớn chuẩn bị vật liệu an toàn cho hoạt động {title.lower()}.",
                )
            ).strip()
            video_focus_cues_vi = tuple(
                str(item).strip()
                for item in override.get(
                    "video_focus_cues_vi",
                    (f"Chú ý đến {title.lower()}.",),
                )
                if str(item).strip()
            )
            video_handoff_prompt_vi = str(
                override.get(
                    "video_handoff_prompt_vi",
                    f"Bây giờ cùng người lớn thử {title.lower()}.",
                )
            ).strip()
            offscreen_instruction_vi = str(
                override.get(
                    "offscreen_instruction_vi",
                    f"{action} {challenge}.",
                )
            ).strip()
            if not all(
                (
                    age_specific_goal_vi,
                    video_setup_vi,
                    video_focus_cues_vi,
                    video_handoff_prompt_vi,
                    offscreen_instruction_vi,
                )
            ):
                raise CuratedCatalogError(f"{activity_id} has incomplete bridge metadata")
            payload = {
                "activity_id": activity_id,
                "activity_version": 1,
                "activity_family_id": family_id,
                "variant_id": f"{family_id}-{age_band}",
                "catalog_revision": effective_revision,
                "age_band": age_band,
                "concept_ids": concept_ids,
                "allowed_objective_ids": objective_ids,
                "primary_objective_id": primary_objective_id,
                "secondary_objective_ids": secondary_objective_ids,
                "pedagogical_alignment": pedagogical_alignment.model_dump(mode="json"),
                "area": area,
                "title_vi": title,
                "phrases_vi": phrases,
                "aliases_vi": aliases,
                "action_vi": action,
                "challenge_vi": challenge,
                "material_option_ids": materials,
                "minimum_supervision": supervision,
                "safety_vi": safety,
                "policy_constraints": policies,
                "duration_minutes": duration,
                "duration_type": duration_type,
                "initial_session_minutes": initial_session_minutes,
                "daily_observation_minutes": daily_observation_minutes,
                "min_days": min_days,
                "max_days": max_days,
                "continuity_mode": continuity_mode,
                "expansion_bridge_required": expansion_bridge_required,
                "direct_observation_concept_ids": direct_observation_concept_ids,
                "age_specific_goal_vi": age_specific_goal_vi,
                "video_setup_vi": video_setup_vi,
                "video_focus_cues_vi": video_focus_cues_vi,
                "video_handoff_prompt_vi": video_handoff_prompt_vi,
                "offscreen_instruction_vi": offscreen_instruction_vi,
            }
            digest = hashlib.sha256(
                json.dumps(payload, ensure_ascii=False, sort_keys=True).encode()
            ).hexdigest()
            payload["pedagogical_alignment"] = pedagogical_alignment
            variants.append(
                CuratedActivityVariant(
                    **payload,
                    provenance_source=f"data/activity-catalog/curated/v2/{family_id}#{activity_id}",
                    provenance_sha256=digest,
                )
            )
        if seen_bands != set(_AGE_BANDS):
            raise CuratedCatalogError(f"{family_id} does not cover all age bands")

    unknown_overrides = set(overrides) - activity_ids
    if unknown_overrides:
        raise CuratedCatalogError(
            "variant contract manifest contains unknown activities: "
            + ",".join(sorted(unknown_overrides))
        )
    if len(family_ids) != 50:
        raise CuratedCatalogError(
            f"curated V2 catalog must contain 50 activity families, found {len(family_ids)}"
        )
    if len(variants) != 200:
        raise CuratedCatalogError(
            f"curated V2 catalog must contain 200 variants, found {len(variants)}"
        )
    return CuratedCatalogV2(effective_revision, tuple(variants))


def _restore_expansion_one_families(
    families: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    restored: list[dict[str, Any]] = []
    for family in families:
        family_id = family.get("family_id")
        if family_id == "FAM-ANIMAL-BUTTERFLY":
            restored.append(
                {
                    "family_id": "FAM-ANIMAL-HABITAT",
                    "concept_ids": ["ANIMAL_GENERIC", "NATURE_OBSERVATION"],
                    "objective_ids": ["OBJ_COSMIC_INTERCONNECTION"],
                    "area": "science",
                    "phrases_vi": ["con vật", "nơi sống", "môi trường sống"],
                    "aliases_vi": ["nhà của con vật", "sống ở đâu"],
                    "material_option_ids": ["MAT_PICTURE_CARDS", "MAT_NATURE_OBJECTS"],
                    "minimum_supervision": "NEARBY",
                    "safety_vi": [
                        (
                            "chỉ dùng tranh hoặc vật mẫu sạch; không thu gom mẫu tự nhiên "
                            "có thể gây dị ứng"
                        )
                    ],
                    "policy_constraints": ["SAFE_MATERIALS_ONLY"],
                    "variants": [
                        {
                            "activity_id": "ACT-0113",
                            "age_band": "0-3",
                            "title_vi": "Tìm con vật trong nơi sống",
                            "action_vi": (
                                "Trẻ tìm hình con vật lớn trong tranh môi trường đơn giản."
                            ),
                            "challenge_vi": (
                                "Trẻ chỉ vào con vật khi người lớn gọi tên và chờ lượt."
                            ),
                            "duration_minutes": 6,
                        },
                        {
                            "activity_id": "ACT-0114",
                            "age_band": "3-6",
                            "title_vi": "Ghép con vật với môi trường",
                            "action_vi": "Trẻ ghép thẻ con vật với đất, nước hoặc cây theo tranh.",
                            "challenge_vi": "Trẻ kể một điều con vật có thể tìm thấy ở nơi sống.",
                            "duration_minutes": 12,
                        },
                        {
                            "activity_id": "ACT-0115",
                            "age_band": "6-9",
                            "title_vi": "Vẽ bản đồ nơi sống",
                            "action_vi": (
                                "Trẻ vẽ các yếu tố cần thiết trong nơi sống của một con vật."
                            ),
                            "challenge_vi": "Trẻ đánh dấu thức ăn, chỗ trú hoặc nguồn nước.",
                            "duration_minutes": 20,
                        },
                        {
                            "activity_id": "ACT-0116",
                            "age_band": "9-12",
                            "title_vi": "Phân tích thay đổi môi trường sống",
                            "action_vi": (
                                "Trẻ lập sơ đồ mối quan hệ giữa con vật và điều kiện sống."
                            ),
                            "challenge_vi": (
                                "Trẻ đưa ra dự đoán có điều kiện nếu một yếu tố thay đổi."
                            ),
                            "duration_minutes": 30,
                        },
                    ],
                }
            )
            continue
        clone = dict(family)
        if family_id in {
            "FAM-ANIMAL-OBSERVE",
            "FAM-ANIMAL-CLASSIFY",
            "FAM-ANIMAL-MOVEMENT",
        }:
            clone["concept_ids"] = [
                concept
                for concept in family.get("concept_ids", [])
                if concept != "ANIMAL_BUTTERFLY"
            ]
        if family_id == "FAM-PLANT-CARE":
            clone.pop("allowed_objective_ids", None)
            clone["objective_ids"] = ["OBJ_INDEPENDENCE_SELF_CARE"]
        if family_id == "FAM-PLANT-COMPARE":
            clone.pop("allowed_objective_ids", None)
            clone["objective_ids"] = ["OBJ_SCIENTIFIC_INQUIRY"]
        restored.append(clone)
    return restored


def _load_variant_contract_overrides(
    directory: Path,
    base_revision: str,
) -> tuple[dict[str, dict[str, Any]], str]:
    path = directory / "variant-contract-overrides.v1.json"
    if not path.exists():
        return {}, base_revision
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CuratedCatalogError(f"cannot read variant contract overrides: {path}") from exc
    if document.get("schema_version") != 1:
        raise CuratedCatalogError("invalid variant contract overrides schema")
    revision = document.get("catalog_revision")
    if not isinstance(revision, str) or not revision:
        raise CuratedCatalogError("variant contract overrides revision is missing")
    raw_variants = document.get("variants")
    if not isinstance(raw_variants, list):
        raise CuratedCatalogError("variant contract overrides must be a list")
    overrides: dict[str, dict[str, Any]] = {}
    for item in raw_variants:
        if not isinstance(item, dict) or not isinstance(item.get("activity_id"), str):
            raise CuratedCatalogError("variant contract override must identify activity_id")
        activity_id = item["activity_id"].strip()
        if activity_id in overrides:
            raise CuratedCatalogError(f"duplicate variant contract override: {activity_id}")
        overrides[activity_id] = dict(item)
    return overrides, revision


def _required_str(value: dict[str, Any], key: str) -> str:
    item = value.get(key)
    if not isinstance(item, str) or not item.strip():
        raise CuratedCatalogError(f"missing curated field: {key}")
    return item.strip()


def _required_tuple(value: dict[str, Any], key: str) -> tuple[str, ...]:
    item = value.get(key)
    if not isinstance(item, list) or not item:
        raise CuratedCatalogError(f"curated field must be a non-empty list: {key}")
    result = tuple(str(entry).strip() for entry in item)
    if any(not entry for entry in result):
        raise CuratedCatalogError(f"curated field contains an empty entry: {key}")
    return result


def _literal_supervision(value: object) -> Literal["NONE", "NEARBY", "DIRECT"]:
    if value not in {"NONE", "NEARBY", "DIRECT"}:
        raise CuratedCatalogError("curated supervision must be NONE, NEARBY or DIRECT")
    return value  # type: ignore[return-value]


__all__ = [
    "CuratedActivityVariant",
    "CuratedCatalogError",
    "CuratedCatalogV2",
    "load_curated_catalog_v2",
]
