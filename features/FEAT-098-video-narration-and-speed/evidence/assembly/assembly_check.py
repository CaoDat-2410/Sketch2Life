"""FEAT-098 part C: assemble a full learning video locally from saved clips (no model, no GPU).

Run from backend/ with tests/unit on the path. Scene motion is a saved LTX clip looped to each scene's planned length;
the voice is a tone as long as the live voice would take (about 16 letters a second, FEAT-094 run 4).
"""

import json
import re
import subprocess
import sys
import tempfile
from dataclasses import replace
from pathlib import Path

import imageio_ffmpeg

sys.path.insert(0, "tests/unit")
from sketch2life.application.video_pipeline.orchestrator import VideoPipeline  # noqa: E402
from sketch2life.application.video_pipeline.ports import SceneClip  # noqa: E402
from sketch2life.infrastructure.story_video.ffmpeg_assembler import FfmpegAssembler  # noqa: E402
from test_video_pipeline_orchestrator import (  # noqa: E402
    _Generator,
    _Prep,
    _source,
    _Validator,
    _wav,
    _draft,
)

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
CLIP = Path("../features/FEAT-094-learning-video-redesign/evidence/M1_experiments/speed_decode/long-10s.mp4").resolve()
OUT = Path(sys.argv[1])

YOUNG = [
    "Đây là bạn rùa con. Rùa là loài bò sát. Trên lưng bạn có cái mai rất cứng. Bạn bò chậm trong vườn xanh.",
    "Khi sợ, rùa rút đầu vào trong mai. Cái mai che thân thể thật kỹ. Bạn nằm nghỉ yên dưới bóng cây mát.",
    "Miệng rùa không hề có răng. Rùa dùng cái mỏ cứng để cắn lá rau. Bạn nhai thật chậm rãi và ngon lành.",
    "Bốn chân rùa vừa ngắn vừa khỏe. Chân giúp rùa bò đi trên đất. Bạn đi chậm rãi về phía hồ nước mát.",
    "Rùa thở bằng phổi giống chúng mình. Bơi một lúc, bạn lại ngoi đầu lên. Tối đến, rùa con đi ngủ ngon.",
]
OLDER = [
    "Rùa là loài bò sát, nghĩa là thân nhiệt của bạn thay đổi theo môi trường. Buổi sáng, rùa thường nằm sưởi nắng "
    "để cơ thể ấm lên.",
    "Cái mai gồm hai phần là mai lưng và yếm bụng. Hai phần này nối với xương sống nên rùa không thể chui ra khỏi "
    "mai của mình.",
    "Rùa không có răng. Thay vào đó, bạn có cái mỏ cứng và bén để cắt lá, quả và đôi khi cả những con vật nhỏ trong "
    "nước.",
    "Chân của rùa cạn ngắn, to và khỏe để đỡ cái mai nặng. Rùa nước lại có màng giữa các ngón để bơi nhanh hơn.",
    "Rùa thở bằng phổi giống con người. Khi lặn lâu, một số loài còn lấy thêm được một ít oxy qua da và họng.",
    "Rùa mẹ đào hố trong cát để đẻ trứng rồi lấp lại. Nhiệt độ của cát quyết định rùa con nở ra là đực hay cái.",
    "Nhiều loài rùa sống rất lâu, có loài hơn một trăm năm. Chúng mình bảo vệ rùa bằng cách giữ sạch ao hồ.",
]


def source(texts, age_months):
    scenes = [
        {"title": f"Cảnh {index}", "narration": text, "action_en": "The turtle walks slowly on the grass.",
         "setting_en": "A sunny garden with soft green grass."}
        for index, text in enumerate(texts, start=1)
    ]
    return replace(_source(), age_months=age_months, learning={"title": "Rùa con và cái mai", "scenes": scenes})


class Voice:
    def __init__(self):
        self.seconds = 0.0

    def synthesize(self, spoken):
        seconds = max(0.6, sum(ch.isalnum() for ch in spoken) / 16.0)
        self.seconds += seconds
        return _wav(seconds)


class SavedClips:
    """The worker's output shape: exactly the planned frames at 1280x720, 24 fps."""

    def __init__(self):
        self.lengths = {}

    def render(self, job):
        frames = job.scene.target_frames
        self.lengths[job.scene.index] = frames
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory) / "scene.mp4"
            subprocess.run(
                [FFMPEG, "-y", "-loglevel", "error", "-stream_loop", "-1", "-i", str(CLIP), "-an", "-vf",
                 f"fps=24,trim=end_frame={frames},setpts=N/(24*TB)", "-frames:v", str(frames), "-r", "24",
                 "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p", str(out)],
                check=True,
            )
            return SceneClip(job.scene.index, out.read_bytes(), frames)


def probe(path):
    listing = subprocess.run(
        [FFMPEG, "-loglevel", "error", "-i", str(path), "-map", "0:v:0", "-f", "framemd5", "-"],
        check=True, capture_output=True, text=True,
    ).stdout.splitlines()
    info = subprocess.run([FFMPEG, "-hide_banner", "-i", str(path)], capture_output=True, text=True,
                          encoding="utf-8", errors="replace").stderr
    frames = len([line for line in listing if not line.startswith("#")])
    return {
        "frames": frames,
        "size": next(line.split(": ")[1] for line in listing if line.startswith("#dimensions")),
        "tb": next(line.split(": ")[1] for line in listing if line.startswith("#tb")),
        "duration": re.search(r"Duration: ([0-9:.]+)", info)[1],
        "audio": "Audio:" in info,
    }


OUT.mkdir(parents=True, exist_ok=True)
report = {}
for name, texts, age in (("age-4y", YOUNG, 48), ("age-9y", OLDER, 114)):
    voice, clips = Voice(), SavedClips()
    pipeline = VideoPipeline(
        timeline_generator=_Generator(_draft()),
        preparation=_Prep(),
        renderer=clips,
        narration=voice,
        assembler=FfmpegAssembler(executable=FFMPEG, label_font="C:/Windows/Fonts/arialbd.ttf"),
        validator=_Validator(),
    )
    result = pipeline.run(source(texts, age))
    video = OUT / f"assembly-{name}.mp4"
    video.write_bytes(result.video)
    plan = result.plan
    total = plan.total_frames / 24
    report[name] = {
        "words": sum(len(text.split()) for text in texts),
        "words_per_scene": [len(text.split()) for text in texts],
        "total_seconds": round(total, 2),
        "voice_seconds": round(voice.seconds, 2),
        "voice_share": round(voice.seconds / total, 3),
        "scene_seconds": [round(scene.target_frames / 24, 2) for scene in plan.scenes],
        "held_seconds": [round(scene.hold_frames / 24, 2) for scene in plan.scenes],
        "planned_frames": plan.total_frames,
        "captions": len(result.cues),
        "file": probe(video),
    }
(OUT / "assembly-report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
print(json.dumps(report, indent=2, ensure_ascii=False))
