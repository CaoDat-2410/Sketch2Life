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
    objective_ids: tuple[str, ...]
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
    provenance_source: str
    provenance_sha256: str

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
            production_eligible=True,
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


def load_curated_catalog_v2(root: Path) -> CuratedCatalogV2:
    directory = root / "data" / "activity-catalog" / "curated" / "v2"
    paths = tuple(sorted(directory.glob("activity-families.v2.part*.json")))
    if not paths:
        raise CuratedCatalogError("curated V2 catalog parts are missing")

    raw_families: list[dict[str, Any]] = []
    revision: str | None = None
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
        if revision is None:
            revision = part_revision
        elif revision != part_revision:
            raise CuratedCatalogError("curated catalog parts use different revisions")
        families = document.get("families")
        if not isinstance(families, list):
            raise CuratedCatalogError(f"curated catalog families must be a list: {path}")
        raw_families.extend(item for item in families if isinstance(item, dict))

    assert revision is not None
    variants: list[CuratedActivityVariant] = []
    family_ids: set[str] = set()
    activity_ids: set[str] = set()
    for family in raw_families:
        family_id = _required_str(family, "family_id")
        if family_id in family_ids:
            raise CuratedCatalogError(f"duplicate activity family: {family_id}")
        family_ids.add(family_id)
        concept_ids = _required_tuple(family, "concept_ids")
        objective_ids = _required_tuple(family, "objective_ids")
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
            payload = {
                "activity_id": activity_id,
                "activity_version": 1,
                "activity_family_id": family_id,
                "variant_id": f"{family_id}-{age_band}",
                "catalog_revision": revision,
                "age_band": age_band,
                "concept_ids": concept_ids,
                "objective_ids": objective_ids,
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
            }
            digest = hashlib.sha256(
                json.dumps(payload, ensure_ascii=False, sort_keys=True).encode()
            ).hexdigest()
            variants.append(
                CuratedActivityVariant(
                    **payload,
                    provenance_source=f"data/activity-catalog/curated/v2/{family_id}#{activity_id}",
                    provenance_sha256=digest,
                )
            )
        if seen_bands != set(_AGE_BANDS):
            raise CuratedCatalogError(f"{family_id} does not cover all age bands")

    if len(family_ids) != 50:
        raise CuratedCatalogError(
            f"curated V2 catalog must contain 50 activity families, found {len(family_ids)}"
        )
    if len(variants) != 200:
        raise CuratedCatalogError(
            f"curated V2 catalog must contain 200 variants, found {len(variants)}"
        )
    return CuratedCatalogV2(revision, tuple(variants))


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
