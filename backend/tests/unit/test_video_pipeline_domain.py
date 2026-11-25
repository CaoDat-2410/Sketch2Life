"""FEAT-093 block A: age profile, story timeline, captions, narration QC and the video plan."""

from __future__ import annotations

import copy
import io
import math
import struct
import wave

import pytest

from sketch2life.application.video_pipeline.age_profile import (
    AGE_BANDS,
    profile_for_age_months,
    snap_ms_to_frame,
)
from sketch2life.application.video_pipeline.caption_plan import (
    CLAUSE_GAP_MS,
    LineAudio,
    build_cues,
    cue_words_match_script,
    extend_short_cues,
    lint_cues,
    split_clauses,
    to_webvtt,
    wrap_caption,
)
from sketch2life.application.video_pipeline.narration_qc import (
    analyse_wav,
    audio_problems,
    fit_window,
    normalize_for_tts,
    number_to_vietnamese,
)
from sketch2life.application.video_pipeline.story_timeline import (
    TIMELINE_SCHEMA,
    TimelineError,
    parse_timeline,
)
from sketch2life.application.video_pipeline.video_plan import build_video_plan, nearest_model_frames

PROFILE = profile_for_age_months(48)  # 36-71: 5 scenes x 6 s
ENTITIES = {"main", "sec-1", "sec-2"}


def _frame(ms: int) -> int:
    return snap_ms_to_frame(ms)


def _timeline(profile=PROFILE) -> dict:
    bounds = [0]
    for _ in range(profile.scene_count):
        bounds.append(_frame(bounds[-1] + profile.scene_seconds * 1000))
    texts = [
        "Rùa con bò ra khỏi hang.",
        "Rùa thấy một chiếc lá xanh.",
        "Rùa cắn một miếng lá.",
        "Chiếc lá còn một nửa.",
        "Rùa ăn xong và mỉm cười.",
    ]
    ladders = [(1.0, 1.0), (1.0, 1.0), (1.0, 0.5), (0.5, 0.25), (0.25, 0.0)]
    scenes = []
    for i in range(profile.scene_count):
        start, end = bounds[i], bounds[i + 1]
        scenes.append(
            {
                "index": i + 1,
                "start_ms": start,
                "end_ms": end,
                "title": f"Cảnh {i + 1}",
                "action": "Rùa con đi tìm thức ăn.",
                "visual_prompt": "A small turtle walks on green grass and looks at a leaf, crayon drawing style.",
                "background_prompt": "A sunny garden with soft green hills, crayon texture, no characters.",
                "narration": {"text": texts[i % 5], "start_ms": start + 500, "end_ms": start + 4_500},
                "dialogue": [],
                "subjects": ["main", "sec-1"],
                "interactions": (
                    [{"kind": "consume", "actor": "main", "target": "sec-1", "verb": "ăn",
                      "from_state": ladders[i][0], "to_state": ladders[i][1]}]
                    if ladders[i][0] != ladders[i][1]
                    else []
                ),
            }
        )
    # the leaf is gone only in the last scene; drop it from no earlier scene
    return {"schema_version": TIMELINE_SCHEMA, "title": "Rùa con và chiếc lá", "age_band": profile.band, "scenes": scenes}


def _parse(raw=None):
    return parse_timeline(raw or _timeline(), profile=PROFILE, entity_ids=ENTITIES)


def test_the_age_table_obeys_the_srs_window() -> None:
    assert [(p.band, p.scene_count, p.total_seconds) for p in AGE_BANDS] == [
        ("36-71", 5, 30),
        ("72-107", 7, 56),
        ("108-120", 9, 72),
    ]
    with pytest.raises(ValueError):
        profile_for_age_months(30)


def test_the_longest_allowed_voice_always_fits_its_scene() -> None:
    from sketch2life.application.video_pipeline.age_profile import SCENE_VOICE_MARGIN_MS, worst_case_voice_ms

    for profile in AGE_BANDS:
        assert worst_case_voice_ms(profile) <= profile.scene_seconds * 1000 - SCENE_VOICE_MARGIN_MS, profile.band


def test_a_valid_timeline_parses_and_is_frame_exact() -> None:
    timeline = _parse()

    assert len(timeline.scenes) == 5
    assert timeline.scenes[0].start_ms == 0
    assert all(a.end_ms == b.start_ms for a, b in zip(timeline.scenes, timeline.scenes[1:], strict=False))
    assert timeline.total_ms == timeline.scenes[-1].end_ms


@pytest.mark.parametrize(
    ("mutate", "code"),
    [
        (lambda raw: raw["scenes"].pop(), "TIMELINE_SCENE_COUNT"),
        (lambda raw: raw["scenes"][1].__setitem__("start_ms", raw["scenes"][1]["start_ms"] + 42), "SCENE_NOT_CONTIGUOUS"),
        (lambda raw: raw["scenes"][0]["narration"].__setitem__("text", "Rùa con đang bò và"), "LINE_TEXT_DANGLING_WORD"),
        (lambda raw: raw["scenes"][0]["narration"].__setitem__("text", "这是一个故事。"), "LINE_TEXT_NON_LATIN_SCRIPT"),
        (lambda raw: raw["scenes"][0]["narration"].__setitem__(
            "text", "Rùa con bò ra khỏi cái hang nhỏ ở trong khu vườn."), "LINE_TOO_MANY_WORDS"),
        (lambda raw: raw["scenes"][0]["narration"].__setitem__("end_ms", raw["scenes"][0]["end_ms"] + 1), "LINE_OUTSIDE_SCENE"),
        (lambda raw: raw["scenes"][0].__setitem__("subjects", ["main", "sec-9"]), "SCENE_SUBJECTS_INVALID"),
        (lambda raw: raw["scenes"][3]["interactions"][0].__setitem__("from_state", 0.4), "INTERACTION_LADDER_DISCONTINUITY"),
        (lambda raw: raw["scenes"][2]["interactions"][0].__setitem__("to_state", 1.0), "INTERACTION_CONSUME_MUST_REDUCE"),
        (lambda raw: raw["scenes"][0].__setitem__("title", ""), "SCENE_TITLE_INVALID"),
        (lambda raw: raw["scenes"][1].__setitem__("subjects", ["sec-1"]), "SCENE_MAIN_SUBJECT_MISSING"),
    ],
)
def test_broken_timelines_name_the_first_broken_rule(mutate, code) -> None:
    raw = copy.deepcopy(_timeline())
    mutate(raw)

    with pytest.raises(TimelineError) as error:
        _parse(raw)

    assert error.value.code == code


def test_a_subject_cannot_come_back_after_it_is_gone() -> None:
    raw = copy.deepcopy(_timeline())
    # shorten: make the leaf gone in scene 4 and still present in scene 5
    raw["scenes"][3]["interactions"][0]["to_state"] = 0.0
    raw["scenes"][4]["interactions"] = []

    with pytest.raises(TimelineError) as error:
        _parse(raw)

    assert error.value.code == "TARGET_REAPPEARS_AFTER_GONE"


def test_narration_and_dialogue_share_one_voice_and_cannot_overlap() -> None:
    raw = copy.deepcopy(_timeline())
    scene = raw["scenes"][0]
    scene["dialogue"] = [{"speaker_ref": "rua", "text": "Chào lá nhé.", "start_ms": scene["start_ms"] + 1_000, "end_ms": scene["start_ms"] + 2_000}]

    with pytest.raises(TimelineError) as error:
        _parse(raw)

    assert error.value.code == "SCENE_1_VOICE_OVERLAP"


def test_clauses_split_at_punctuation_and_keep_words() -> None:
    clauses = split_clauses("Rùa con bò ra khỏi hang, rồi nhìn quanh. Trời thật đẹp!")

    assert clauses == ["Rùa con bò ra khỏi hang,", "rồi nhìn quanh.", "Trời thật đẹp!"]
    assert split_clauses("Chào nhé.") == ["Chào nhé."]


def test_caption_wrap_is_two_short_lines() -> None:
    assert wrap_caption("Rùa con bò ra khỏi hang rồi nhìn quanh khu vườn") == [
        "Rùa con bò ra khỏi hang rồi nhìn",
        "quanh khu vườn",
    ]


def test_cues_use_the_measured_clause_audio_and_match_the_script_words() -> None:
    timeline = _parse()
    narration = timeline.scenes[0].narration
    line = type(narration)("Rùa con bò ra khỏi hang, rồi nhìn quanh.", narration.start_ms, narration.end_ms)
    placed = LineAudio(line=line, lane="narration", placed_start_ms=narration.start_ms, clause_durations_ms=(1_600, 1_300))

    cues = build_cues([placed])

    assert [cue.text for cue in cues] == ["Rùa con bò ra khỏi hang,", "rồi nhìn quanh."]
    assert cues[0].start_ms == narration.start_ms
    assert cues[1].start_ms == narration.start_ms + 1_600 + CLAUSE_GAP_MS
    assert cue_words_match_script([line], cues)


def test_cues_without_audio_share_the_line_window_by_word_count() -> None:
    timeline = _parse()
    narration = timeline.scenes[0].narration
    line = type(narration)("Rùa con bò ra khỏi hang, rồi nhìn quanh.", 1_000, 5_000)

    cues = build_cues([LineAudio(line=line, lane="narration", placed_start_ms=1_000)])

    assert cues[0].start_ms == 1_000 and cues[-1].end_ms == 5_000
    assert all(a.end_ms == b.start_ms for a, b in zip(cues, cues[1:], strict=False))


def test_dialogue_cues_carry_the_speaker_label_once() -> None:
    line = type(_parse().scenes[0].narration)("Chào bạn lá, hôm nay đẹp quá.", 1_000, 4_000, "rua")

    cues = build_cues([LineAudio(line=line, lane="dialogue", placed_start_ms=1_000)], speaker_labels={"rua": "Rùa"})

    assert cues[0].text.startswith("Rùa: ") and not cues[1].text.startswith("Rùa")
    assert cue_words_match_script([line], cues, speaker_labels={"rua": "Rùa"})


def test_lint_flags_overlap_speed_and_stretches_short_cues() -> None:
    line = type(_parse().scenes[0].narration)("Rùa nhìn lá.", 0, 600)
    short = build_cues([LineAudio(line=line, lane="narration", placed_start_ms=0)])

    assert "CUE_0_TOO_SHORT" in lint_cues(short, duration_ms=30_000, max_cps=14)
    stretched = extend_short_cues(short, duration_ms=30_000)
    assert lint_cues(stretched, duration_ms=30_000, max_cps=14) == []
    overlapping = [stretched[0], type(stretched[0])(500, 2_500, "Một câu khác.", "narration")]
    assert "CUE_1_OVERLAP" in lint_cues(overlapping, duration_ms=30_000, max_cps=14)


def test_webvtt_has_cue_timing_and_text() -> None:
    line = type(_parse().scenes[0].narration)("Rùa nhìn lá xanh.", 1_000, 3_500)

    vtt = to_webvtt(build_cues([LineAudio(line=line, lane="narration", placed_start_ms=1_000)]))

    assert vtt.startswith("WEBVTT") and "00:00:01.000 --> 00:00:03.500" in vtt and "Rùa nhìn lá xanh." in vtt


def test_numbers_are_spoken_in_vietnamese_but_captions_keep_digits() -> None:
    assert [number_to_vietnamese(n) for n in (0, 5, 10, 15, 21, 25, 100, 105, 110, 321)] == [
        "không", "năm", "mười", "mười lăm", "hai mươi mốt", "hai mươi lăm", "một trăm",
        "một trăm lẻ năm", "một trăm mười", "ba trăm hai mươi mốt",
    ]
    normalized = normalize_for_tts("Rùa có 3 người bạn 🐢")

    assert normalized.display == "Rùa có 3 người bạn 🐢"
    assert normalized.spoken == "Rùa có ba người bạn" and normalized.changed


def _wav(seconds: float, *, amplitude: int = 8000, rate: int = 24_000, lead: float = 0.0, tail: float = 0.0) -> bytes:
    frames = bytearray()
    for i in range(int(rate * (lead + seconds + tail))):
        t = i / rate
        in_voice = lead <= t < lead + seconds
        value = int(amplitude * math.sin(2 * math.pi * 220 * t)) if in_voice else 0
        frames += struct.pack("<h", value)
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as writer:
        writer.setnchannels(1)
        writer.setsampwidth(2)
        writer.setframerate(rate)
        writer.writeframes(bytes(frames))
    return buffer.getvalue()


def test_audio_checks_accept_clean_speech_and_flag_the_usual_faults() -> None:
    text = "Rùa con bò ra khỏi hang"  # 19 letters
    clean = analyse_wav(_wav(2.0, lead=0.1, tail=0.1))
    assert audio_problems(clean, spoken_text=text, profile=PROFILE, expected_sample_rate=24_000) == []

    assert "AUDIO_CLIPPING" in audio_problems(analyse_wav(_wav(2.0, amplitude=32_767)), spoken_text=text, profile=PROFILE)
    assert "AUDIO_EDGE_SILENCE" in audio_problems(analyse_wav(_wav(2.0, lead=1.0)), spoken_text=text, profile=PROFILE)
    assert "AUDIO_SPEECH_RATE_OUT_OF_BAND" in audio_problems(analyse_wav(_wav(8.0)), spoken_text=text, profile=PROFILE)
    assert "AUDIO_EMPTY_OR_TOO_QUIET" in audio_problems(analyse_wav(_wav(2.0, amplitude=10)), spoken_text=text, profile=PROFILE)
    assert "AUDIO_SAMPLE_RATE" in audio_problems(clean, spoken_text=text, profile=PROFILE, expected_sample_rate=16_000)
    with pytest.raises(ValueError):
        analyse_wav(b"not a wav")


def test_window_fit_decisions() -> None:
    assert fit_window(3_500, 4_000).decision == "OK"
    assert fit_window(4_400, 4_000).decision == "STRETCH_SCENE"
    assert fit_window(6_000, 4_000).decision == "SHORTEN_TEXT"


def test_model_frames_are_one_plus_eight_k() -> None:
    assert [nearest_model_frames(n) for n in (144, 145, 150, 153)] == [145, 145, 153, 153]


def test_the_video_plan_is_frame_exact_and_keeps_the_leaf_ladder() -> None:
    timeline = _parse()
    plan = build_video_plan(timeline, story_sha256="a" * 64, main_entity_id="main")

    assert plan.total_frames == sum(scene.target_frames for scene in plan.scenes)
    assert plan.scenes[0].start_frame == 0
    assert plan.scenes[2].ladders[0].target == "sec-1" and plan.scenes[2].ladders[0].end == 0.5
    assert plan.scenes[4].ladders[0].end == 0.0
    assert {scene.seed for scene in plan.scenes} and all(0 <= scene.seed < 2**31 for scene in plan.scenes)
    assert len(plan.line_placements()) == 5
    assert plan.scenes[0].model_frames % 8 == 1


def test_a_cue_stays_long_enough_to_read_without_passing_the_next_cue() -> None:
    from sketch2life.application.video_pipeline.caption_plan import Cue, extend_short_cues, lint_cues

    fast = Cue(0, 1_700, "Gà con nhìn xuống sân đất nâu.", "narration")  # 30 characters in 1.7 s
    later = Cue(4_000, 6_000, "Gà con bước đi.", "narration")

    cues = extend_short_cues([fast, later], duration_ms=10_000, max_cps=14.0)

    assert cues[0].end_ms >= 2_143 and cues[0].end_ms <= later.start_ms - 40
    assert lint_cues(cues, duration_ms=10_000, max_cps=14.0) == []
    boxed = extend_short_cues([fast, Cue(1_900, 3_000, "Tiếp theo.", "narration")], duration_ms=10_000, max_cps=14.0)
    assert boxed[0].end_ms <= 1_900 - 40  # never into the next cue
