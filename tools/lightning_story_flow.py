"""Variable-length local storyboard -> VieNeu -> FLUX -> narrated drawing preview.

The automatic planner splits narration into sentence beats; it is rule-based, not
an LLM screenplay author. --plan accepts a manually authored JSON beat list.
All new images/audio/video require human review. No installs or paid services.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
from datetime import datetime
from pathlib import Path

from PIL import Image, ImageDraw, ImageOps

from lightning_complete_story import fit, font
from lightning_story_tts import EXTENDED_TEXTS, build_timeline, stamp
from lightning_render_narrated import render

MODEL = "pnnbao-ump/VieNeu-TTS-v2-Turbo-GGUF"
VOICE = "Thục Đoan (Nữ - Miền Nam)"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def plan_text(text):
    paragraphs = re.split(r"\n\s*\n", text.strip())
    beats = []
    for paragraph in paragraphs:
        for sentence in re.split(r"(?<=[.!?…])\s+", paragraph.strip()):
            sentence = sentence.strip()
            if sentence:
                beats.append({"narration": sentence, "visual_prompt": sentence})
    return beats


def validate(beats):
    if not isinstance(beats, list) or not 1 <= len(beats) <= 24:
        raise ValueError("Plan must contain 1-24 beats (safety bound, not a fixed scene count)")
    for beat in beats:
        if not isinstance(beat, dict):
            raise ValueError("Each beat must be a JSON object")
        if not all(isinstance(beat.get(key), str) and beat[key].strip()
                   for key in ("narration", "visual_prompt")):
            raise ValueError("Each beat needs narration and visual_prompt text")
        if len(beat["narration"]) > 700:
            raise ValueError("A beat is too long; split it at an action change")
    return beats


def reuse_choice(text, available):
    # Only the already reviewed family-story actions qualify; custom stories don't
    # inherit these scenes merely because they contain a common word like 'flower'.
    mapping = [("bước theo con đường nhỏ vào vườn hoa", 2),
               ("cúi xuống", 3), ("chú bướm cam xanh", 4)]
    for phrase, index in mapping:
        if phrase in text.lower() and index in available:
            available.remove(index)
            return index
    return None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--script", type=Path, help="UTF-8 narration; split into sentence beats")
    parser.add_argument("--plan", type=Path, help="JSON array of narration + visual_prompt beat objects")
    parser.add_argument("--voice", default=VOICE)
    parser.add_argument("--resume", type=Path, help="Resume this exact plan in an existing output folder")
    parser.add_argument("--offline", action="store_true")
    parser.add_argument("--model", type=Path,
                        default=Path("/teamspace/studios/this_studio/models/FLUX.2-klein-4B"))
    args = parser.parse_args()
    if args.script and args.plan:
        parser.error("Choose --script or --plan, not both")
    root = Path.cwd().resolve()
    boy_path = root / ".runtime/flux-boy-proof/20261010-034707/boy-flux-candidate.png"
    source_path = root / ".runtime/flux-scene1-proof/20261010-035033/scene1-candidate.png"
    reuse_dir = root / ".runtime/complete-story-demo/20261010-040933"
    for path in (boy_path, source_path, args.model / "model_index.json"):
        if not path.is_file():
            raise FileNotFoundError(f"Required pinned input missing: {path}")
    default_story = not args.script and not args.plan
    if args.plan:
        beats = validate(json.loads(args.plan.read_text(encoding="utf-8")))
    else:
        text = args.script.read_text(encoding="utf-8") if args.script else "\n\n".join(EXTENDED_TEXTS)
        beats = validate(plan_text(text))
    signature = hashlib.sha256(json.dumps({
        "beats": beats, "voice": args.voice, "tts": MODEL, "flux": str(args.model),
        "boy_sha256": sha(boy_path), "source_sha256": sha(source_path),
        "reuse_existing_family_story": default_story,
    }, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    out = (args.resume or root / ".runtime/story-flow" /
           datetime.now().strftime("%Y%m%d-%H%M%S-%f")).resolve()
    if args.resume:
        old = json.loads((out / "plan.json").read_text(encoding="utf-8"))
        if old["signature"] != signature:
            raise ValueError("Resume inputs differ. Start a new run instead.")
    else:
        out.mkdir(parents=True, exist_ok=False)
        (out / "plan.json").write_text(json.dumps({"signature": signature, "beats": beats,
            "planner": "SENTENCE_SPLIT_RULE_BASED", "voice": args.voice,
            "default_family_story": default_story}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"STORYBOARD: {len(beats)} beats determined by the script; output: {out}", flush=True)
    tts_dir, scenes_dir = out / "tts", out / "scenes"
    tts_dir.mkdir(exist_ok=True)
    scenes_dir.mkdir(exist_ok=True)
    os.environ["HF_HUB_OFFLINE"] = "1" if args.offline else "0"
    os.environ["TRANSFORMERS_OFFLINE"] = "1" if args.offline else "0"
    import numpy as np
    import soundfile as sf
    tts = None
    try:
        clips = []
        sample_rate = None
        for index, beat in enumerate(beats, 1):
            path = tts_dir / f"scene-{index}.wav"
            if not path.is_file():
                if tts is None:
                    from vieneu import Vieneu
                    from huggingface_hub import hf_hub_download
                    import onnxruntime as ort
                    decoder = hf_hub_download("pnnbao-ump/VieNeu-Codec", "vieneu_decoder.onnx",
                                              token=False, local_files_only=args.offline)
                    session = ort.InferenceSession(decoder, providers=["CPUExecutionProvider"])
                    if {p.name for p in session.get_inputs()} != {"content_ids", "voice_embedding"}:
                        raise ValueError("Decoder interface does not match VieNeu Turbo")
                    del session
                    tts = Vieneu(mode="turbo", backbone_repo=MODEL,
                                 backbone_filename="vieneu-tts-v2-turbo.gguf", decoder_repo=decoder,
                                 encoder_repo="pnnbao-ump/VieNeu-Codec", device="cpu")
                    voice = tts.get_preset_voice(args.voice)
                print(f"TTS beat {index}/{len(beats)}", flush=True)
                tts.save(tts.infer(text=beat["narration"], voice=voice), str(path))
            clip, rate = sf.read(path, dtype="float32")
            if clip.ndim != 1 or not len(clip) or not np.isfinite(clip).all() or np.max(np.abs(clip)) < 1e-5:
                raise ValueError(f"Invalid narration: {path}; inspect before resuming")
            sample_rate = rate if sample_rate is None else sample_rate
            if sample_rate != rate:
                raise ValueError("Sample rates differ")
            clips.append(clip)
    finally:
        if tts is not None:
            tts.close()
    # Only short phrase breaks; no fixed duration gate, audio stretching or cutting.
    gap = round(sample_rate * .10)
    rows = build_timeline(clips, sample_rate, gap, [b["narration"] for b in beats])
    audio = np.concatenate([p for clip in clips for p in (clip, np.zeros(gap, np.float32))])
    sf.write(tts_dir / "narration.wav", audio, sample_rate, subtype="PCM_16")
    (tts_dir / "timeline.json").write_text(json.dumps({"scenes": rows,
        "duration_seconds": len(audio)/sample_rate, "voice": args.voice,
        "audio_qa": "PENDING_LISTENING_REVIEW"}, ensure_ascii=False, indent=2), encoding="utf-8")
    (out / "captions.srt").write_text("\n\n".join(
        f"{r['scene']}\n{stamp(r['start_seconds'])} --> {stamp(r['speech_end_seconds'])}\n{r['text']}"
        for r in rows) + "\n", encoding="utf-8")
    print(f"Measured narration: {len(audio)/sample_rate:.2f}s; duration follows script, not a hard gate", flush=True)
    boy = fit(Image.open(boy_path), (768, 768))
    source = fit(Image.open(source_path), (1024, 768))
    available = {2, 3, 4} if default_story else set()
    pipe = None
    image_report = []
    try:
        for index, beat in enumerate(beats, 1):
            path = scenes_dir / f"scene-{index}.png"
            reused = reuse_choice(beat["narration"], available)
            original = reuse_dir / f"scene-{reused}.png" if reused else None
            if not path.is_file():
                if original and original.is_file():
                    shutil.copy2(original, path)
                    if sha(path) != sha(original):
                        raise RuntimeError("Reused artwork changed unexpectedly")
                    print(f"Beat {index}: reuses reviewed image {reused}", flush=True)
                else:
                    if pipe is None:
                        import torch
                        from diffusers import Flux2KleinPipeline
                        if not torch.cuda.is_available():
                            raise RuntimeError("Image generation requires the Lightning GPU")
                        pipe = Flux2KleinPipeline.from_pretrained(str(args.model), dtype=torch.bfloat16,
                                                                local_files_only=True)
                        pipe.enable_model_cpu_offload()
                    parent_beat = any(word in beat["narration"].lower() for word in ("bố", "mẹ", "gia đình", "cả nhà"))
                    context = source if parent_beat or index == 1 else fit(
                        Image.open(scenes_dir / f"scene-{index-1}.png"), (1024, 768))
                    prompt = (
                        "ONE landscape illustration for a continuous Vietnamese whiteboard story. "
                        "Image 1 fixes the child identity: preserve his face, orange-brown hair, "
                        "blue shirt with orange pocket, purple shorts and green shoes. Image 2 is "
                        "continuity context ONLY, not a layout to blindly copy. Illustrate the "
                        "current narrative beat with an appropriate new pose or camera view: " +
                        beat["visual_prompt"] + ". Keep the same garden, flowers and house when visible. "
                        "Natural dark pencil contours, bright colored-pencil fills, clean white "
                        "background. Coherent face contours, aligned eyes, anatomically plausible "
                        "hands. No text, labels, collage, panels or borders. " +
                        ("Mother: brown bob, orange shirt/red skirt; father: black hair, glasses, "
                         "orange shirt/green collar, gray trousers. Keep all three identities consistent."
                         if parent_beat else "Do not add parents or extra people. A detail shot may show "
                         "flowers or the butterfly without a person if that best matches the beat.")
                    )
                    (scenes_dir / f"scene-{index}-prompt.txt").write_text(prompt, encoding="utf-8")
                    print(f"FLUX beat {index}/{len(beats)}", flush=True)
                    with torch.inference_mode():
                        result = pipe(image=[boy, context], prompt=prompt, width=1024, height=768,
                            num_inference_steps=4, guidance_scale=1.0,
                            generator=torch.Generator(device="cpu").manual_seed(120+index)).images[0]
                    result.save(path)
            matches_reviewed = original is not None and original.is_file() and sha(path) == sha(original)
            image_report.append({"beat": index, "sha256": sha(path),
                "reused_source": str(original) if matches_reviewed else None,
                "status": "USER_APPROVED_SOURCE_REUSED" if matches_reviewed else "NEW_PENDING_REVIEW"})
    finally:
        if pipe is not None:
            del pipe
            torch.cuda.empty_cache()
    columns = 3
    sheet = Image.new("RGB", (columns*480, ((len(beats)+columns-1)//columns)*340), "white")
    for index, beat in enumerate(beats, 1):
        x, y = ((index-1)%columns)*480, ((index-1)//columns)*340
        sheet.paste(fit(Image.open(scenes_dir / f"scene-{index}.png"), (480, 300)), (x, y))
        ImageDraw.Draw(sheet).text((x+10, y+309), f"Beat {index} - REVIEW REQUIRED", font=font(16), fill="black")
    sheet.save(out / "storyboard-review.png")
    (out / "images.json").write_text(json.dumps(image_report, indent=2), encoding="utf-8")
    video_out = render(scenes_dir, tts_dir, root)
    (out / "result.json").write_text(json.dumps({"video": str(video_out / "story-narrated.mp4"),
        "beats": len(beats), "duration_seconds": len(audio)/sample_rate,
        "approval": "PENDING_HUMAN_REVIEW", "alignment": "NARRATIVE_BEAT_NOT_WORD_LEVEL"}, indent=2), encoding="utf-8")
    print(f"Review storyboard: {out / 'storyboard-review.png'}", flush=True)


if __name__ == "__main__":
    main()
