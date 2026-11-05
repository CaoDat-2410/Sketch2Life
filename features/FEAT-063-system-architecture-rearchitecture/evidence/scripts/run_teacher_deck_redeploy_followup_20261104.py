from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
FEATURE = SCRIPT.parents[2]
sys.path.insert(0, str(SCRIPT.parent))
MAIN_PATH = SCRIPT.parent / "run_ai_nonvideo_30min_queue_retest_20261104.py"
spec = importlib.util.spec_from_file_location("nonvideo_30min_retest", MAIN_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError("Could not load the approved 30-minute retest helpers")
flow = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = flow
spec.loader.exec_module(flow)


def main() -> int:
    output_dir = flow.OUT_DIR
    output_dir.mkdir(parents=True, exist_ok=True)
    intent_path = output_dir / "teacher_sketch-deck_generate_dispatch_intent.json"
    result_path = output_dir / "teacher_sketch-deck_generate_result.json"
    if not intent_path.is_file() or not result_path.is_file():
        raise SystemExit("No previous pre-dispatch Teacher Deck failure was found to recover.")
    previous = json.loads(result_path.read_text(encoding="utf-8"))
    if previous.get("outcome") != "DISPATCH_FAILED_NO_CALL" or previous.get("call_id") is not None:
        raise SystemExit("Refusing another Teacher Deck attempt after a real call was dispatched.")
    (output_dir / "teacher_deck_pre_dispatch_notfound.json").write_text(
        json.dumps({"intent": json.loads(intent_path.read_text(encoding="utf-8")), "result": previous}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    import modal

    function = modal.Function.from_name(
        "sketch2life-srs23-language-audio-dev",
        "generate-teacher-sketch-deck",
        environment_name="dev",
    )
    function.hydrate()
    plan = flow.flow.synthetic_approved_plan()
    result = flow.invoke_generic(
        workload="teacher.sketch-deck.generate",
        app="sketch2life-srs23-language-audio-dev",
        function="generate-teacher-sketch-deck",
        request_data=plan,
    )
    (output_dir / "teacher_deck_followup_result.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"workload": "teacher.sketch-deck.generate", "outcome": result.get("outcome"), "call_id": result.get("call_id"), "wait_limit_seconds": flow.WAIT_SECONDS}, ensure_ascii=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
