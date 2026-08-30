# P2-T2 Phase B Round-1 fixture-source provenance

- Evidence ID: EV-003-T2-04
- Date: 2026-08-30
- Scope: resolves the `DECISION_REQUIRED` fixture-source item left open by
  `evidence/notes/P2_T2_PHASE_B_BENCHMARK_READINESS.md` and `plan/P2_T2_ASR_RESEARCH_PLAN.md`
  ("Next gated action after readiness"). No real child data was used anywhere in this package.

## Decision

Fixture source: **SYNTHETIC (TTS)**, as declared per-fixture by `data_provenance: "SYNTHETIC"`
in `fixtures/asr-round1/manifest.json`. No licensed speech corpus was used.

## Tooling (local, D:-drive only, not added to `backend/pyproject.toml`)

| Tool | Version/build | Location | Verification |
|---|---|---|---|
| `edge-tts` | `7.2.8` (exact-pinned, per explicit authorization) | `D:\AIModels\Sketch2Life\fixture-tools\.venv` (isolated venv, Python 3.12.10) | Installed via `pip install edge-tts==7.2.8`; `pip show edge-tts` confirms `Version: 7.2.8`. |
| `ffmpeg` (static, x64) | `N-126335-gb32f8d1c23-20260830`, `BtbN/FFmpeg-Builds` `ffmpeg-master-latest-win64-gpl` | `D:\AIModels\Sketch2Life\fixture-tools\ffmpeg\ffmpeg-master-latest-win64-gpl\bin\` | Archive SHA-256 `3b7b7cabc0bb66eba45c40194dddb7287d249f3c7030b76973044e7f1cb71838`; extracted `ffmpeg.exe` SHA-256 `765c096588827ba21605e16446b0871be20f73a73c7700c3d5a677383bf24687`. |

Neither tool was installed to `C:`, added to the global Windows PATH, or added to
`backend/pyproject.toml`. An initial attempt to fetch `ffmpeg-release-essentials.zip` from
`gyan.dev` was intercepted by local endpoint-security software and returned an HTML warning
page instead of the archive (caught before extraction, by hash/content-type inspection); the
`BtbN/FFmpeg-Builds` GitHub release was used instead and downloaded cleanly.

## Voices used

| Voice | Provider label | Language |
|---|---|---|
| `vi-VN-HoaiMyNeural` | Microsoft Edge neural TTS | Vietnamese (female) |
| `vi-VN-NamMinhNeural` | Microsoft Edge neural TTS | Vietnamese (male) |
| `en-US-JennyNeural` | Microsoft Edge neural TTS | English, US (female) |
| `en-GB-SoniaNeural` | Microsoft Edge neural TTS | English, UK (female) |

`edge-tts` synthesizes via Microsoft Edge's public neural TTS service; no account credential
was used or required. Synthesized MP3 output was converted to mono 16 kHz PCM WAV with the
local `ffmpeg` build (`-ac 1 -ar 16000 -sample_fmt s16`), matching the Round-1 profile input
expectations. No raw audio or transcript content is included in this note or any other
evidence file — only references, hashes, and this generation methodology.

## Non-speech fixtures

- `silence`: `ffmpeg`'s `anullsrc` filter (`channel_layout=mono:sample_rate=16000`) — literal
  digital silence, 2 and 4 seconds.
- `noise`: `ffmpeg`'s `anoisesrc` filter, two conditions — `white-noise-v1` (white noise,
  low amplitude) and `room-tone-v1` (brown noise, low amplitude) — each mono 16 kHz.
- `noisy_speech`: one Vietnamese and one non-Vietnamese clear-speech source, each mixed with
  both noise conditions via `ffmpeg`'s `amix` filter (noise attenuated to a fixed relative
  volume against the speech track), producing 4 fixtures across the 2 noise conditions.

## Fixture inventory (21 fixtures, all `split: HELD_OUT`)

| Scenario | Count | Language-accuracy eligible | WER/CER eligible |
|---|---:|---|---|
| `vi_clear` | 5 | yes (all 5) | yes (all 5) |
| `non_vi_clear` | 5 | yes (all 5) | yes (all 5) |
| `vi_en_code_switch` | 3 | no (by contract) | yes (all 3) |
| `silence` | 2 | n/a | n/a |
| `noise` | 2 (`white-noise-v1`, `room-tone-v1`) | n/a | n/a |
| `noisy_speech` | 4 (vi×2 noise conditions, en×2 noise conditions) | no | yes (all 4) |

The manifest (`fixtures/asr-round1/manifest.json`) is `status: "READY"` and validates against
the strict `AsrRound1FixtureManifestV1` contract, including the noise/noisy-speech coverage
cross-checks. It contains only relative references, SHA-256 hashes, and metadata — no audio or
transcript payload. The raw audio (`fixtures/asr-round1/audio/**`) and transcript
(`fixtures/asr-round1/transcripts/**`) directories remain locally generated and gitignored, per
the existing `.gitignore` rules; neither was committed.

## Limitation

This is synthetic/TTS speech only. It is not evidence of ASR performance on real child speech
(pitch, articulation, and disfluency differ materially), per the synthetic-only limitation
already recorded in `plan/P2_T2_ASR_RESEARCH_PLAN.md` R3 and repeated in the Round-1 report.
