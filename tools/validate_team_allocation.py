from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = (
    ROOT / "docs" / "SYSTEM_BASELINE.md",
    ROOT / "docs" / "adr" / "ADR-0006-parallel-sprint-allocation.md",
    ROOT / "features" / "FEAT-001-stack-and-team-plan" / "TEAM_ALLOCATION.md",
)

REQUIRED_BASELINE_MARKERS = (
    "## 21. Four-person Sprint 1 allocation",
    "Person 1 — BA / Montessori",
    "Person 2 — AI Understanding",
    "Person 3 — Art Animation",
    "Person 4 — Learning Media",
    "### Integration Sprint",
    "## 26. Project roadmap (dependency-driven)",
    "It is not the four-person task assignment",
)

REQUIRED_ALLOCATION_MARKERS = (
    "versioned input fixture manifest",
    "standalone runner or test harness",
    "No single person is the default integration owner",
    "`PROJECT ROADMAP` is dependency-driven",
    "`TEAM SPRINT TASK` is workstream-driven",
)

FORBIDDEN_LEGACY_MARKERS = (
    "Person 4 | Backend orchestration",
    "Person 3 | Android mobile",
    "Person 3 | Mobile app + personalized art animation",
    "Person 4 | Backend orchestration + learning media",
    "Person 4 owns the end-to-end join",
    "Integrates all outputs; deployment/e2e evidence",
)


def fail(message: str) -> None:
    raise SystemExit(f"TEAM_ALLOCATION_INVALID: {message}")


def main() -> None:
    missing_files = [path.relative_to(ROOT).as_posix() for path in REQUIRED_FILES if not path.is_file()]
    if missing_files:
        fail(f"missing required files: {', '.join(missing_files)}")

    baseline = REQUIRED_FILES[0].read_text(encoding="utf-8")
    allocation = REQUIRED_FILES[2].read_text(encoding="utf-8")
    combined = baseline + "\n" + allocation

    missing_baseline = [marker for marker in REQUIRED_BASELINE_MARKERS if marker not in baseline]
    if missing_baseline:
        fail(f"baseline markers missing: {missing_baseline}")

    missing_allocation = [marker for marker in REQUIRED_ALLOCATION_MARKERS if marker not in allocation]
    if missing_allocation:
        fail(f"allocation markers missing: {missing_allocation}")

    stale = [marker for marker in FORBIDDEN_LEGACY_MARKERS if marker in combined]
    if stale:
        fail(f"legacy ownership returned: {stale}")

    print("TEAM_ALLOCATION_VALID")
    print("sprint_1_workstreams=4-independent")
    print("integration_sprint=separate-reallocation")
    print("project_roadmap=not-team-assignment")


if __name__ == "__main__":
    main()
