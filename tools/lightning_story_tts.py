"""Generate four local Vietnamese narration clips and a sentence-level timeline.

VieNeu SDK 2.7.0. Standard 0.3B or explicitly selected public v2 Turbo assets.
First execution downloads model/codec/preset assets; no remote speech API is used.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
from datetime import datetime
from importlib.metadata import version
from pathlib import Path

TEXTS = [
    "Trước ngôi nhà mái đỏ, em ở bên bố mẹ.",
    "Em bước theo con đường nhỏ vào vườn hoa.",
    "Em cúi xuống, nhẹ nhàng hái một bông hoa.",
    "Bỗng em nhìn thấy một chú bướm cam xanh!",
]
MODEL = "pnnbao-ump/VieNeu-TTS-0.3B"
GGUF = "VieNeu-TTS-0.3B-Q4_K_M.gguf"
EXTENDED_TEXTS = [
    "Trước ngôi nhà mái đỏ, em đứng giữa bố và mẹ. Bố mẹ nắm tay em, cả nhà cùng mỉm cười. Bên cạnh là cây xanh, còn phía trước có những bông hoa nhỏ.",
    "Em bước theo con đường nhỏ vào vườn hoa. Hai bên đường, những bông hoa nhiều màu đang nở. Em nhìn ngắm từng bông, vừa đi vừa cảm thấy thật vui trong khu vườn xinh đẹp.",
    "Em dừng lại bên một bông hoa màu hồng. Rồi em nhẹ nhàng cúi xuống, đưa tay chọn lấy bông hoa.",
    "Bỗng em nhìn thấy một chú bướm cam xanh ở gần bên. Em đứng lên, cầm bông hoa và mỉm cười ngắm chú bướm.",
]


def stamp(value):
    ms = round(value * 1000)
    return f"{ms//3600000:02}:{ms//60000%60:02}:{ms//1000%60:02},{ms%1000:03}"


def build_timeline(clips, sample_rate, gap_samples, texts=None):
    cursor = 0
    rows = []
    for index, clip in enumerate(clips):
        frames = len(clip)
        rows.append({
            "scene": index + 1, "text": (texts or TEXTS)[index],
            "audio_file": f"scene-{index + 1}.wav",
            "start_seconds": cursor / sample_rate,
            "speech_end_seconds": (cursor + frames) / sample_rate,
            "scene_end_seconds": (cursor + frames + gap_samples) / sample_rate,
            "speech_frames": frames, "pause_frames": gap_samples,
        })
        cursor += frames + gap_samples
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--voice", help="Preset ID from --list-voices; default uses the SDK preset")
    parser.add_argument("--list-voices", action="store_true")
    parser.add_argument("--offline", action="store_true", help="Use already cached assets only")
    parser.add_argument("--turbo-public", action="store_true",
                        help="Use public v2 Turbo GGUF + its matching VieNeu-Codec, not gated NeuCodec")
    parser.add_argument("--extended", action="store_true", help="Longer story matching the same four pictures")
    parser.add_argument("--render-scenes", type=Path,
                        help="After TTS, render an outline/color candidate using this scene folder")
    parser.add_argument("--reuse-tts", type=Path,
                        help="Reuse matching sentences from this prior run; changed sentences regenerate")
    args = parser.parse_args()
    # Local inference only; public repositories are for asset downloads, not speech APIs.
    os.environ["HF_HUB_OFFLINE"] = "1" if args.offline else "0"
    os.environ["TRANSFORMERS_OFFLINE"] = "1" if args.offline else "0"
    import numpy as np
    import soundfile as sf
    from vieneu import Vieneu

    model = "pnnbao-ump/VieNeu-TTS-v2-Turbo-GGUF" if args.turbo_public else MODEL
    gguf = "vieneu-tts-v2-turbo.gguf" if args.turbo_public else GGUF
    previous = None
    if args.reuse_tts:
        previous = json.loads((args.reuse_tts / "timeline.json").read_text(encoding="utf-8"))
        if previous.get("model") != model or previous.get("voice") != (args.voice or "SDK_DEFAULT_PRESET"):
            raise ValueError("Cannot reuse audio from a different model or voice")
    print(f"VieNeu SDK {version('vieneu')}; backbone {model}; GGUF CPU + ONNX CPU", flush=True)
    if args.turbo_public:
        # Validate the public codec BEFORE allocating the llama model: failed codec
        # downloads otherwise leave the native backbone allocated during unwinding.
        from huggingface_hub import hf_hub_download
        import onnxruntime as ort
        decoder_repo = "pnnbao-ump/VieNeu-Codec"
        decoder_name = "vieneu_decoder.onnx"
        print("Downloading/checking public decoder first...", flush=True)
        decoder = hf_hub_download(repo_id=decoder_repo, filename=decoder_name,
                                  token=False, local_files_only=args.offline)
        session = ort.InferenceSession(decoder, providers=["CPUExecutionProvider"])
        inputs = {entry.name for entry in session.get_inputs()}
        if inputs != {"content_ids", "voice_embedding"}:
            raise RuntimeError(f"Public codec inputs {inputs} do not match the SDK Turbo interface")
        print("PUBLIC_DECODER_OK", flush=True)
        del session
        tts = Vieneu(mode="turbo", backbone_repo=model, backbone_filename=gguf,
                     decoder_repo=decoder, decoder_filename=decoder_name,
                     encoder_repo=decoder_repo, device="cpu")
    else:
        tts = Vieneu(mode="standard", backbone_repo=model,
                     gguf_filename=gguf, backbone_device="cpu", codec_device="cpu",
                     emotion="storytelling")
    try:
        voices = tts.list_preset_voices()
        for description, voice_id in voices:
            print(f"VOICE: {voice_id} | {description}", flush=True)
        if args.list_voices:
            return
        voice = tts.get_preset_voice(args.voice) if args.voice else None
        out = Path.cwd() / ".runtime/story-tts" / datetime.now().strftime("%Y%m%d-%H%M%S-%f")
        out.mkdir(parents=True, exist_ok=False)
        texts = EXTENDED_TEXTS if args.extended else TEXTS
        (out / "script.txt").write_text("\n".join(texts) + "\n", encoding="utf-8")
        clips = []
        sample_rate = None
        for index, text in enumerate(texts, 1):
            print(f"Narration {index}/4: {text}", flush=True)
            kwargs = {"voice": voice} if voice is not None else {}
            path = out / f"scene-{index}.wav"
            old_row = next((row for row in previous["scenes"]
                            if row["scene"] == index and row["text"] == text), None) if previous else None
            if old_row is not None:
                old_path = (args.reuse_tts / f"scene-{index}.wav").resolve()
                shutil.copy2(old_path, path)
                print(f"Reused unchanged narration {index}", flush=True)
            else:
                audio = tts.infer(text=text, **kwargs)
                tts.save(audio, str(path))
            clip, rate = sf.read(path, dtype="float32")
            if clip.ndim != 1 or not len(clip) or not np.isfinite(clip).all():
                raise RuntimeError(f"Invalid mono narration: {path}")
            if float(np.max(np.abs(clip))) < 1e-5:
                raise RuntimeError(f"Silent narration: {path}")
            sample_rate = rate if sample_rate is None else sample_rate
            if sample_rate != rate:
                raise RuntimeError("Narration sample rates differ")
            clips.append(clip)
            print(f"Saved: {path} ({len(clip)/rate:.2f}s)", flush=True)
        speech_seconds = sum(len(clip) for clip in clips) / sample_rate
        # Aim for 36s without time-stretching speech or excessive silent padding.
        pause = max(.6, min(2.5, (36 - speech_seconds) / 4)) if args.extended else .4
        gap_samples = round(pause * sample_rate)
        rows = build_timeline(clips, sample_rate, gap_samples, texts)
        joined = np.concatenate([part for clip in clips
                                 for part in (clip, np.zeros(gap_samples, dtype=np.float32))])
        sf.write(out / "narration.wav", joined, sample_rate, subtype="PCM_16")
        report = {
            "model": model, "gguf": gguf, "sdk_version": version("vieneu"),
            "mode": "PUBLIC_V2_TURBO" if args.turbo_public else "STANDARD_0.3B",
            "voice": args.voice or "SDK_DEFAULT_PRESET", "available_voices": voices,
            "sample_rate": sample_rate, "duration_seconds": len(joined)/sample_rate,
            "timing": "SENTENCE_BOUNDARIES_FROM_AUDIO_LENGTH_NOT_WORD_ALIGNMENT",
            "audio_qa": "PENDING_LISTENING_REVIEW", "scenes": rows,
            "script_variant": "EXTENDED_FOUR_SCENES" if args.extended else "SHORT",
            "reuse_source": str(args.reuse_tts) if args.reuse_tts else None,
            "duration_target_met": 35 <= len(joined)/sample_rate <= 40 if args.extended else None,
        }
        (out / "timeline.json").write_text(json.dumps(report, ensure_ascii=False, indent=2),
                                            encoding="utf-8")
        (out / "captions.srt").write_text("\n\n".join(
            f"{row['scene']}\n{stamp(row['start_seconds'])} --> "
            f"{stamp(row['speech_end_seconds'])}\n{row['text']}" for row in rows) + "\n",
            encoding="utf-8")
        print(f"DONE: {out / 'narration.wav'}", flush=True)
        print(f"Timeline: {out / 'timeline.json'}", flush=True)
        if args.extended:
            duration = len(joined) / sample_rate
            print(f"Measured duration: {duration:.2f}s; target 35-40s", flush=True)
            if not 35 <= duration <= 40:
                print("DURATION_REVIEW_REQUIRED: revise the script; do not slow/stretch the voice.", flush=True)
        print("Listen before approving; images/video have not been modified.")
    finally:
        tts.close()
    if args.render_scenes:
        if args.extended and not report["duration_target_met"]:
            print("VIDEO_NOT_RENDERED: audio is outside the approved 35-40s target.", flush=True)
            return
        from lightning_render_narrated import render
        print("Rendering a REVIEW CANDIDATE with narration; not a production approval.", flush=True)
        render(args.render_scenes.resolve(), out, Path.cwd())


if __name__ == "__main__":
    main()
