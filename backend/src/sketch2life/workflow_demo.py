"""Command-line entry point for the backend-only AI workflow demonstration."""

from sketch2life.interfaces.cli.workflow_demo import build_real_workflow, inspect_real_runtime, main

__all__ = ["build_real_workflow", "inspect_real_runtime", "main"]


if __name__ == "__main__":  # pragma: no cover - exercised by the CLI smoke test
    raise SystemExit(main())
