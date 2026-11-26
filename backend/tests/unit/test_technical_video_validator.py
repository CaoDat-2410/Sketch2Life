"""FEAT-093: technical validation from ffprobe facts."""

from __future__ import annotations

from sketch2life.application.video_pipeline.age_profile import profile_for_age_months
from sketch2life.application.video_pipeline.story_timeline import parse_timeline
from sketch2life.application.video_pipeline.timeline_planner import assign_timing
from sketch2life.application.video_pipeline.video_plan import build_video_plan
from sketch2life.infrastructure.story_video.technical_validator import TechnicalVideoValidator

FASTSTART = b"ftypisom" + b"moov" + b"mdat" + b"x" * 20
SLOW = b"ftypisom" + b"mdat" + b"x" * 20 + b"moov"


def _plan():
    profile = profile_for_age_months(48)
    scenes = [
        {"title": f"Cảnh {i}", "action": "Rùa đi.", "visual_prompt": "A turtle walks, crayon style.",
         "background_prompt": "A sunny garden, crayon texture.", "narration": "Rùa con bò đi.", "dialogue": [],
         "subjects": ["main"], "interactions": []}
        for i in range(1, 6)
    ]
    timeline = parse_timeline(
        assign_timing(profile, {"title": "Rùa con", "scenes": scenes}), profile=profile, entity_ids={"main"}
    )
    return build_video_plan(timeline, story_sha256="a" * 64, main_entity_id="main")


def _facts(plan, **override):
    facts = {
        "streams": [
            {"codec_type": "video", "codec_name": "h264", "width": 1280, "height": 720, "avg_frame_rate": "24/1"},
            {"codec_type": "audio", "codec_name": "aac"},
        ],
        "format": {"duration": f"{plan.total_frames / 24:.3f}"},
    }
    facts.update(override)
    return facts


def _validate(plan, facts, video=FASTSTART):
    return TechnicalVideoValidator(probe=lambda _p: facts).validate(video, plan)


def test_a_good_video_passes_and_names_the_pending_vision_checks() -> None:
    plan = _plan()

    report = _validate(plan, _facts(plan))

    assert report.technical_ok and report.failure_code is None
    assert report.finding_codes == ("VIDEO_VISION_CHECKS_PENDING",)


def test_each_technical_rule_has_its_own_code() -> None:
    plan = _plan()
    good = _facts(plan)
    cases = {
        "VIDEO_VALIDATE_NO_AUDIO": {**good, "streams": good["streams"][:1]},
        "VIDEO_VALIDATE_RESOLUTION": {**good, "streams": [{**good["streams"][0], "width": 640}, good["streams"][1]]},
        "VIDEO_VALIDATE_FRAME_RATE": {**good, "streams": [{**good["streams"][0], "avg_frame_rate": "30/1"}, good["streams"][1]]},
        "VIDEO_VALIDATE_DURATION_MISMATCH": {**good, "format": {"duration": "45.000"}},
        "VIDEO_VALIDATE_OUTSIDE_SRS_WINDOW": {**good, "format": {"duration": "10.0"}},
    }
    for code, facts in cases.items():
        report = _validate(plan, facts)
        assert not report.technical_ok and code in report.finding_codes, code
    assert "VIDEO_VALIDATE_NOT_FASTSTART" in _validate(plan, good, SLOW).finding_codes


def test_a_container_one_frame_off_the_window_edge_still_passes() -> None:
    plan = _plan()  # 30 s, the lower edge of the SRS window

    report = _validate(plan, {**_facts(plan), "format": {"duration": "29.98"}})

    assert report.technical_ok, report.finding_codes
