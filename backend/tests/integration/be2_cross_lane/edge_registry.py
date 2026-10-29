"""Planning registry for BE2 cross-lane integration proof.

This inventory is not evidence that any producer and consumer are wired.
Behavior tests must replace the initial NOT_IMPLEMENTED state only when they
exercise the real owner services through public contracts.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass
from enum import StrEnum

_SOURCE_BOUND_EVIDENCE = re.compile(r"[^#\s]+#source_sha256=[0-9a-f]{64}\Z")


class EdgeStatus(StrEnum):
    """Evidence state for one planned cross-lane handoff."""

    NOT_IMPLEMENTED = "NOT_IMPLEMENTED"
    NOT_RUN = "NOT_RUN"
    PARTIAL = "PARTIAL"
    PASS = "PASS"
    FAIL = "FAIL"


@dataclass(frozen=True, slots=True)
class CrossLaneEdge:
    """Owned producer-to-consumer edge and the evidence needed to claim it."""

    edge_id: str
    producer_tasks: tuple[int, ...]
    consumer_tasks: tuple[int, ...]
    planned_test_module: str
    required_scenarios: tuple[str, ...]
    status: EdgeStatus = EdgeStatus.NOT_IMPLEMENTED
    behavior_test_module: str | None = None
    evidence_ref: str | None = None


EXPECTED_EDGE_IDS = frozenset({"X01", "X02", "X03", "X04", "X05", "X06", "X07", "X08", "X09"})

CROSS_LANE_EDGES = (
    CrossLaneEdge(
        edge_id="X01",
        producer_tasks=(7,),
        consumer_tasks=(8,),
        planned_test_module="test_source_generation.py",
        required_scenarios=("producer_created_exact_export", "source_change_before_commit"),
        status=EdgeStatus.PARTIAL,
        behavior_test_module="test_source_generation.py",
        evidence_ref=(
            "features/FEAT-057-be2-01-14-offline-integration/evidence/metrics/"
            "CROSS_LANE_X01_20261020.json#source_sha256="
            "0a22e50557b3ac57b9913b80b273d0a672423946277af3e7cfa9a0829e7f6f42"
        ),
    ),
    CrossLaneEdge(
        edge_id="X02",
        producer_tasks=(7,),
        consumer_tasks=(9,),
        planned_test_module="test_source_invalidation.py",
        required_scenarios=("source_invalidation_delivery", "stale_playback_denied"),
    ),
    CrossLaneEdge(
        edge_id="X03",
        producer_tasks=(12,),
        consumer_tasks=(8,),
        planned_test_module="test_source_generation.py",
        required_scenarios=("published_exact_version", "recall_denied_before_dispatch"),
    ),
    CrossLaneEdge(
        edge_id="X04",
        producer_tasks=(12,),
        consumer_tasks=(9, 11),
        planned_test_module="test_publication_consumers.py",
        required_scenarios=("exact_published_ref_consumed", "recall_or_authority_change_denied"),
    ),
    CrossLaneEdge(
        edge_id="X05",
        producer_tasks=(8,),
        consumer_tasks=(9,),
        planned_test_module="test_video_review_playback.py",
        required_scenarios=("success_artifact_lineage", "explicit_review_before_playback"),
    ),
    CrossLaneEdge(
        edge_id="X06",
        producer_tasks=(8,),
        consumer_tasks=(10,),
        planned_test_module="test_video_failure_disposition.py",
        required_scenarios=("controlled_failed_completion", "duplicate_and_late_result"),
    ),
    CrossLaneEdge(
        edge_id="X07",
        producer_tasks=(13,),
        consumer_tasks=(1, 14),
        planned_test_module="test_preset_policy_dispatch.py",
        required_scenarios=("exact_preset_job_lineage", "policy_generation_race"),
    ),
    CrossLaneEdge(
        edge_id="X08",
        producer_tasks=(14,),
        consumer_tasks=(3, 4, 8, 13),
        planned_test_module="test_policy_gates.py",
        required_scenarios=("deny_before_side_effect", "copy_receipt_scope_is_explicit"),
    ),
    CrossLaneEdge(
        edge_id="X09",
        producer_tasks=(1,),
        consumer_tasks=(2, 3, 4, 8, 13),
        planned_test_module="test_job_type_routing.py",
        required_scenarios=("supported_job_type_routes", "unknown_type_fails_closed"),
    ),
)


def validate_edge_registry(edges: Iterable[CrossLaneEdge]) -> tuple[str, ...]:
    """Return structural errors without treating registry rows as behavior proof."""

    registry = tuple(edges)
    errors: list[str] = []
    edge_ids = [edge.edge_id for edge in registry]

    if len(edge_ids) != len(set(edge_ids)):
        errors.append("edge IDs must be unique")
    if set(edge_ids) != EXPECTED_EDGE_IDS:
        errors.append("registry must contain exactly X01 through X09")

    for edge in registry:
        if not edge.producer_tasks or not edge.consumer_tasks:
            errors.append(f"{edge.edge_id} requires producer and consumer task IDs")
        if not edge.planned_test_module:
            errors.append(f"{edge.edge_id} requires a planned test module")
        if not edge.required_scenarios:
            errors.append(f"{edge.edge_id} requires at least one behavior scenario")
        if edge.status is EdgeStatus.PASS and not edge.behavior_test_module:
            errors.append(f"{edge.edge_id} PASS requires a behavior-test module")
        if edge.status is EdgeStatus.PARTIAL and not edge.behavior_test_module:
            errors.append(f"{edge.edge_id} PARTIAL requires a behavior-test module")
        if edge.status is EdgeStatus.PASS and (
            edge.evidence_ref is None
            or _SOURCE_BOUND_EVIDENCE.fullmatch(edge.evidence_ref) is None
        ):
            errors.append(f"{edge.edge_id} PASS requires a source-bound evidence reference")
        if edge.status is EdgeStatus.PARTIAL and (
            edge.evidence_ref is None
            or _SOURCE_BOUND_EVIDENCE.fullmatch(edge.evidence_ref) is None
        ):
            errors.append(f"{edge.edge_id} PARTIAL requires a source-bound evidence reference")

    return tuple(errors)
