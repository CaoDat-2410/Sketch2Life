"""Load the reviewed P1 catalog into immutable ActivityTemplateV1 records.

This adapter is the only layer that knows the committed JSON layout.  The
domain/application compiler receives typed templates and never reads files or
calls a provider directly.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from sketch2life.contracts.schemas.p1_experience import (
    ActivityTemplateV1,
    VersionedRefV1,
)


class CatalogLoadError(ValueError):
    """Raised when the committed P1 catalog cannot be used safely."""


_CATALOG_AREA_TERMS = frozenset({
    "language",
    "mathematics",
    "practical_life",
    "science",
    "sensorial",
})


@dataclass(frozen=True, slots=True)
class P1TemplateLibrary:
    templates: tuple[ActivityTemplateV1, ...]
    objective_titles_vi: dict[str, str]
    catalog_source: str

    def get(self, template_id: str) -> ActivityTemplateV1 | None:
        return next((item for item in self.templates if item.template_id == template_id), None)

    def by_activity(self, activity_id: str) -> tuple[ActivityTemplateV1, ...]:
        return tuple(item for item in self.templates if item.activity_ref.id == activity_id)


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CatalogLoadError(f"cannot read catalog artifact: {path}") from exc
    if not isinstance(value, dict):
        raise CatalogLoadError(f"catalog artifact must be an object: {path}")
    return value


def _digest_record(record: dict[str, Any]) -> str:
    encoded = json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def _slug_tokens(text: str) -> tuple[str, ...]:
    tokens = re.findall(r"[\w-]+", text.casefold(), flags=re.UNICODE)
    return tuple(token for token in tokens if len(token) > 2)


def _interaction_mode(
    record: dict[str, Any],
) -> Literal[
    "OBJECT_PERMANENCE",
    "TRANSFER",
    "SEQUENCE",
    "CARE",
    "SORTING",
    "TRACING",
    "OBSERVATION",
    "RESEARCH",
]:
    activity_id = record["id"]
    if activity_id == "ACT-0004":
        return "OBJECT_PERMANENCE"
    if activity_id in {"ACT-0019", "ACT-0026", "ACT-0032", "ACT-0033"}:
        return "SEQUENCE"
    if activity_id in {"ACT-0016", "ACT-0020", "ACT-0023", "ACT-0030", "ACT-0034"}:
        return "CARE"
    if activity_id == "ACT-0039":
        return "SORTING"
    if activity_id == "ACT-0046":
        return "TRACING"
    if record["area"] in {"science", "cosmic_education"}:
        return "OBSERVATION"
    if record["area"] in {"mathematics", "language", "cultural_studies", "social_studies"}:
        return "RESEARCH"
    return "TRANSFER"


def _template_from_record(
    record: dict[str, Any],
    groups_by_id: dict[str, dict[str, Any]],
) -> ActivityTemplateV1:
    activity_id = record["id"]
    objective_refs = [
        record["objective_mapping"]["primary"],
        *record["objective_mapping"]["secondary"],
    ]
    material_ids = tuple(
        option_id
        for group_id in record["material_group_ids"]
        for option_id in groups_by_id[group_id]["any_of"]
    )
    objective_labels = {ref["id"].casefold() for ref in objective_refs}
    labels = set(_slug_tokens(record["title"]["vi-VN"]))
    labels.update(_slug_tokens(record["purpose_vi"]))
    labels.update(_slug_tokens(record["direct_aim_vi"]))
    labels = {
        label.strip().casefold()
        for label in labels
        if label.strip()
        and label.strip().casefold() not in _CATALOG_AREA_TERMS
        and label.strip().casefold() not in objective_labels
    }
    if not labels:
        raise CatalogLoadError(f"activity {activity_id} has no meaningful anchor labels")
    return ActivityTemplateV1(
        template_id=f"TPL-{activity_id}-V{record['version']}",
        template_version=1,
        activity_ref=VersionedRefV1(id=activity_id, version=record["version"]),
        objective_refs=tuple(
            VersionedRefV1(id=ref["id"], version=ref["version"]) for ref in objective_refs
        ),
        supported_anchor_labels=tuple(sorted(labels)),
        supported_anchor_kinds=("subject", "action", "visual_feature", "story"),
        interaction_mode=_interaction_mode(record),
        age_months_min=record["age_months"]["min"],
        age_months_max=record["age_months"]["max"],
        readiness_ids=tuple(item["id"] for item in record["readiness_criteria"]),
        prerequisite_activity_ids=tuple(record["prerequisite_activity_ids"]),
        material_option_ids=material_ids,
        minimum_supervision=record["safety"]["minimum_supervision"],
        policy_constraints=tuple(record["policy_constraints"]),
        safety_rule_ids=tuple(
            f"{activity_id}:HAZARD:{index + 1}"
            for index, _ in enumerate(record["safety"]["hazards_vi"])
        )
        + tuple(
            f"{activity_id}:STOP:{index + 1}"
            for index, _ in enumerate(record["safety"]["stop_conditions_vi"])
        ),
        steps_vi=tuple(record["presentation_steps_vi"]),
        personalization_slots=("material_substitute", "support_variant"),
        provenance_source=f"data/activity-catalog/golden/v1/activities.v2.json#{activity_id}",
        provenance_sha256=_digest_record(record),
        review_status=record["review"]["status"],
        production_eligible=False,
    )


def load_p1_template_library(root: Path) -> P1TemplateLibrary:
    golden = root / "data" / "activity-catalog" / "golden" / "v1"
    activity_doc = _read_json(golden / "activities.v2.json")
    material_doc = _read_json(golden / "material-registry.v1.json")
    objective_doc = _read_json(
        root / "data" / "activity-catalog" / "mvp" / "learning-objectives.v1.json"
    )
    records = activity_doc.get("activities")
    if (
        activity_doc.get("schema_version") != 2
        or not isinstance(records, list)
        or len(records) != 20
    ):
        raise CatalogLoadError("golden catalog must contain exactly 20 schema-v2 activities")
    groups = {item["id"]: item for item in material_doc.get("groups", [])}
    if len(groups) != 20:
        raise CatalogLoadError("golden material registry must contain 20 groups")
    templates = tuple(_template_from_record(record, groups) for record in records)
    if len({template.template_id for template in templates}) != 20:
        raise CatalogLoadError("golden template IDs must be unique")
    objectives = {
        item["id"]: item["title"]["vi-VN"]
        for item in objective_doc.get("objectives", [])
        if item.get("version") == 1
    }
    if len(objectives) != 20:
        raise CatalogLoadError("MVP objective catalog must contain 20 version-1 objectives")
    known_objectives = set(objectives)
    if any(
        ref.id not in known_objectives for template in templates for ref in template.objective_refs
    ):
        raise CatalogLoadError("golden template contains an unknown objective reference")
    if any(
        not objectives.get(ref.id, "").strip()
        for template in templates
        for ref in template.objective_refs
    ):
        raise CatalogLoadError("golden template contains an objective without a title")
    return P1TemplateLibrary(
        templates=templates,
        objective_titles_vi=objectives,
        catalog_source="golden/v1:activities.v2.json+material-registry.v1.json",
    )
