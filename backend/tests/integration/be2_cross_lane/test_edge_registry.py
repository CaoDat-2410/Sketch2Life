from dataclasses import replace

import pytest
from edge_registry import (
    CROSS_LANE_EDGES,
    EXPECTED_EDGE_IDS,
    CrossLaneEdge,
    EdgeStatus,
    validate_edge_registry,
)


def test_registry_lists_every_planned_edge_once_with_scoped_statuses() -> None:
    assert {edge.edge_id for edge in CROSS_LANE_EDGES} == EXPECTED_EDGE_IDS
    assert len(CROSS_LANE_EDGES) == len(EXPECTED_EDGE_IDS)
    assert CROSS_LANE_EDGES[0].status is EdgeStatus.PARTIAL
    assert CROSS_LANE_EDGES[0].behavior_test_module == "test_source_generation.py"
    assert CROSS_LANE_EDGES[0].evidence_ref is not None
    assert all(
        edge.status is EdgeStatus.NOT_IMPLEMENTED for edge in CROSS_LANE_EDGES[1:]
    )
    assert validate_edge_registry(CROSS_LANE_EDGES) == ()


@pytest.mark.parametrize(
    "updated_edge, expected_error",
    [
        (replace(CROSS_LANE_EDGES[0], edge_id="X02"), "edge IDs must be unique"),
        (replace(CROSS_LANE_EDGES[0], producer_tasks=()), "requires producer and consumer"),
        (replace(CROSS_LANE_EDGES[0], required_scenarios=()), "requires at least one behavior"),
    ],
)
def test_registry_rejects_incomplete_or_duplicated_edges(
    updated_edge: CrossLaneEdge, expected_error: str
) -> None:
    registry = (updated_edge, *CROSS_LANE_EDGES[1:])

    assert any(expected_error in error for error in validate_edge_registry(registry))


@pytest.mark.parametrize(
    "behavior_test_module, evidence_ref, expected_error",
    [
        (None, "metrics/final.json#X01", "PASS requires a behavior-test module"),
        (
            "test_source_generation.py",
            None,
            "PASS requires a source-bound evidence reference",
        ),
        (
            "test_source_generation.py",
            "metrics/final.json#X01",
            "PASS requires a source-bound evidence reference",
        ),
    ],
)
def test_registry_never_accepts_pass_without_executable_evidence(
    behavior_test_module: str | None,
    evidence_ref: str | None,
    expected_error: str,
) -> None:
    passing_edge = replace(
        CROSS_LANE_EDGES[0],
        status=EdgeStatus.PASS,
        behavior_test_module=behavior_test_module,
        evidence_ref=evidence_ref,
    )
    registry = (passing_edge, *CROSS_LANE_EDGES[1:])

    assert any(expected_error in error for error in validate_edge_registry(registry))


def test_pass_with_behavior_test_and_evidence_satisfies_registry_gate() -> None:
    passing_edge = replace(
        CROSS_LANE_EDGES[0],
        status=EdgeStatus.PASS,
        behavior_test_module="test_source_generation.py",
        evidence_ref=(
            "metrics/cross-lane-final.json#source_sha256=" + "a" * 64
        ),
    )
    registry = (passing_edge, *CROSS_LANE_EDGES[1:])

    assert validate_edge_registry(registry) == ()


@pytest.mark.parametrize(
    "behavior_test_module, evidence_ref",
    [
        (None, "metrics/cross-lane-partial.json#source_sha256=" + "a" * 64),
        ("test_source_generation.py", None),
    ],
)
def test_partial_edge_requires_behavior_and_source_bound_evidence(
    behavior_test_module: str | None, evidence_ref: str | None
) -> None:
    partial_edge = replace(
        CROSS_LANE_EDGES[0],
        behavior_test_module=behavior_test_module,
        evidence_ref=evidence_ref,
    )
    registry = (partial_edge, *CROSS_LANE_EDGES[1:])

    assert validate_edge_registry(registry)
