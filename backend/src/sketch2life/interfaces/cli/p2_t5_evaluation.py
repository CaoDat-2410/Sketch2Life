"""Offline-only command line entry point for the P2-T5 evaluation harness."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

from pydantic import BaseModel

from sketch2life.application.services.media_validation import DeterministicMediaValidator
from sketch2life.application.services.p2_t5_evaluation import (
    P2T5EvaluationHarness,
    atomic_write_json,
)
from sketch2life.contracts.schemas.p2_t5_evaluation import (
    P2T5CommandEnvelopeV1,
    P2T5ErrorCode,
    P2T5FailureV1,
    Split,
    canonical_sha256,
)
from sketch2life.infrastructure.ai.fake_asr import (
    DeterministicFixtureAsrAdapter,
    FakeAsrFixture,
    FakeAsrScenario,
)
from sketch2life.infrastructure.ai.fake_vision import (
    DeterministicFixtureVisionAdapter,
    FakeVisionFixture,
    FakeVisionScenario,
)
from sketch2life.infrastructure.ai.p2_t5_fixture_loader import load_fixture_package
from sketch2life.infrastructure.ai.vision_lexical_policy import (
    LexicalRegressionContentPolicy,
    synthetic_prohibited_lexicon,
)
from sketch2life.infrastructure.media_validation.file_inspector import FileMediaSignalInspector


def build_harness(repository_root: Path) -> P2T5EvaluationHarness:
    policy = LexicalRegressionContentPolicy(synthetic_prohibited_lexicon())

    def asr_factory(audio_ref: str, scenario: str) -> DeterministicFixtureAsrAdapter:
        return DeterministicFixtureAsrAdapter(
            {audio_ref: FakeAsrFixture(FakeAsrScenario[scenario], "tree near house")}
        )

    def vision_factory(
        image_ref: str, scenario: str, image_path: Path, raw_output: str
    ) -> DeterministicFixtureVisionAdapter:
        return DeterministicFixtureVisionAdapter(
            {image_ref: FakeVisionFixture(FakeVisionScenario[scenario], image_path, raw_output)},
            content_policy=policy,
        )

    return P2T5EvaluationHarness(
        repository_root,
        validator=DeterministicMediaValidator(FileMediaSignalInspector()),
        loader=load_fixture_package,
        asr_factory=asr_factory,
        vision_factory=vision_factory,
        vision_policy=policy,
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="p2-t5-evaluation")
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("validate", "understand", "evaluate"):
        command = commands.add_parser(name)
        command.add_argument("--provider", default="fixture")
        command.add_argument("--manifest", required=True)
        command.add_argument("--fixture-root", required=True)
        command.add_argument("--output", required=True)
        if name == "understand":
            command.add_argument("--fixture-id", required=True)
        if name == "evaluate":
            command.add_argument("--split", choices=[item.value for item in Split], required=True)
            command.add_argument("--run-id", required=True)
            command.add_argument("--executed-at", required=True)
            command.add_argument("--run-dir", required=False)
    return parser


def _failure(command: str, code: P2T5ErrorCode, phase: str) -> P2T5CommandEnvelopeV1:
    return P2T5CommandEnvelopeV1(
        command=command,
        success=False,
        failure=P2T5FailureV1(code=code, phase=phase, reason_code=code.value),
    )


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.provider != "fixture":
        envelope = _failure(args.command, P2T5ErrorCode.UNSUPPORTED_PROVIDER, "CLI")
        atomic_write_json(Path(args.output), envelope)
        print(json.dumps(envelope.model_dump(mode="json"), sort_keys=True))
        return 2
    repository_root = Path(__file__).resolve().parents[5]
    harness = build_harness(repository_root)
    try:
        result: BaseModel
        if args.command == "validate":
            result = harness.validate(args.manifest, args.fixture_root)
        elif args.command == "evaluate":
            result = harness.evaluate(
                args.manifest,
                args.fixture_root,
                Split(args.split),
                args.run_id,
                datetime.fromisoformat(args.executed_at.replace("Z", "+00:00")),
            )
        else:
            package = harness.load(args.manifest, args.fixture_root)
            selected = next(
                (case for case in package.cases if case.fixture_id == args.fixture_id), None
            )
            if selected is None:
                result = _failure(args.command, P2T5ErrorCode.INVALID_ARGUMENT, "CLI")
            else:
                report = harness.evaluate(
                    args.manifest,
                    args.fixture_root,
                    Split(selected.split),
                    f"understand-{selected.fixture_id}",
                    datetime(2026, 9, 20, 12, 0, 0, tzinfo=UTC),
                )
                filtered_core = {
                    **report.deterministic_core,
                    "case_results": [
                        item
                        for item in report.deterministic_core["case_results"]
                        if item["fixture_id"] == args.fixture_id
                    ],
                }
                result = report.model_copy(
                    update={
                        "deterministic_core": filtered_core,
                        "deterministic_core_sha256": canonical_sha256(filtered_core),
                    }
                )
        atomic_write_json(Path(args.output), result)
        print(json.dumps(result.model_dump(mode="json"), ensure_ascii=False, sort_keys=True))
        return 0
    except Exception:  # closed CLI boundary; details never leave the process
        envelope = _failure(args.command, P2T5ErrorCode.UNEXPECTED_HARNESS_ERROR, "EXECUTION")
        atomic_write_json(Path(args.output), envelope)
        print(json.dumps(envelope.model_dump(mode="json"), sort_keys=True))
        return 1


if __name__ == "__main__":
    sys.exit(main())
