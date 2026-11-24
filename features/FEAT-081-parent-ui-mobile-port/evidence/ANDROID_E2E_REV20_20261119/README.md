# Parent Expo Android E2E evidence — Rev20

- **Evidence ID:** `EV-081-REV20-E2E-01`
- **Captured:** 2026-11-19, approximately 10:01–10:51 Asia/Ho_Chi_Minh (file modification times).
- **Environment:** real Expo Android app, visual-preview harness disabled; local disposable Docker backend; Firebase Authentication dev project; Modal Qwen3.5 drawing worker.
- **Data:** synthetic Parent/profile and generated synthetic turtle drawing only. No real child data or fake consent.
- **Outcome:** flow reached one real drawing-understanding inference and stopped on terminal invalid/truncated model JSON. The screenshots do not represent a successful VLM result.

## Files

- 34 retained Android screen PNGs. Gaps in the capture numbering are intentional; sensitive login/retry and unrelated gallery captures were removed.
- Matching accessibility XML is retained for screens where it contains no account identifier or secret.
- `synthetic_turtle_drawing.png` is the separately generated input artwork, not an AI output of the tested runtime call.
- Synthetic artwork SHA-256: `43596C821E6D80B3792F227F684B1C30DEA5D84653BB7D504C873F2F3B3F5A40`.
- `28-svg-guide-result.png` SHA-256: `80145F106EF4114117C0BEF7516C7B003EBBE38B3F8E53C35B3C34A66332CAB3`.
- `35-svg-guide-stage-6.png` SHA-256: `E080863621683FC7DDEAE3F55DEC2023DD4AAA55896D044A786ED19B57CCFFD0`.
- `40-drawing-analysis-result.png` SHA-256: `05561FFA2183378F128651CCA18CEC8BAF49AB86CEC7ABBEB74116C4E4EE491E`.
- `41-run-status-poll.png` SHA-256: `B9A94F47D8A3EB14DA511B8FDB1694B578E9B6D88CAFA80AA75957080612A153`.

## Flow map

| Evidence | What it shows |
|---|---|
| `11-after-register.png` | Home after Parent authentication. |
| `12-profiles.png`–`17-profile-selected.png` | Profile picker, synthetic profile creation, and profile selection. |
| `18-topic-choice.png`–`25-subject-validation-result.png` | Topic cards, topic/object suggestion, and custom-subject validation. |
| `26-sketch-guide.png`–`36-guide-approved.png` | SVG guide screen, rendered result, progressive steps, and approval. This is a catalog-backed SVG guide, not a FLUX inference. |
| `37-capture-screen.png`–`39-image-picker-return.png` | Required artwork selection through the Android picker. `38-gallery-picker.png` was removed because it included unrelated gallery content. |
| `40-drawing-analysis-result.png` | Synthetic artwork attached to the run; backend reports that the analysis result was not returned. |
| `41-run-status-poll.png` | Run still pending; there is no valid subject/activity/story output. |

Screens containing the synthetic account email or login retry state were removed during evidence sanitization. Retained XML/Markdown text was scanned for email/API-key/token patterns. Do not treat any screenshot after `40-drawing-analysis-result.png` as proof of a successful AI result.

The detailed timing, Modal call ID, worker error, tests, code changes, and cleanup are in `../IMPLEMENTATION_REPORT_REV20_E2E_CHECKPOINT_20261119.md`.

