# FEAT-086 status

**State:** Rev1 and Rev2 implementation complete; real video validation pending runtime availability.
**Plan:** Rev2, `plan/PLAN_REV2_DETAILED_LTX_SCENE_PROMPTS.md`; Rev1 history: `plan/PLAN_REV1_PARENT_VIDEO_QUALITY.md`.
**Approval:** `approvals/TASK_APPROVAL.md`.

### Rev1 — Parent video quality repair

| Milestone | Status | Evidence |
|---|---|---|
| M0 baseline/provenance | Complete | Existing FEAT-085 candidate and FEAT-061 synthetic crayon provenance inspected. |
| M1 story JSON/prompt | Complete | Stable JSON fields/version; initial 420-character prompt cap. Superseded by Rev2's 900-character internal prompt limit. |
| M2 LTX conditioning/prompt | Complete | `story-i2v-v6`; removed redundant full-frame SVG guide conditioning. Superseded by Rev2 compiler `story-i2v-v7`. |
| M3 mobile player metadata | Complete | Removed the visible duration/scene-count/no-audio footer. |

### Rev2 — Detailed LTX scene prompts

| Milestone | Status | Evidence |
|---|---|---|
| R2-M0 research/authority and plan | Complete | Official LTX I2V and prompting guides reviewed; approved plan hash is recorded in the approval file. |
| R2-M1 detailed Qwen `visual_prompt` | Complete | 3–4 concise English action sentences; max 900 characters; public story keys/version unchanged. |
| R2-M2 backend adapter and LTX compiler | Complete | Backend adapter and worker-plan limits aligned to 900; compiler is `story-i2v-v7` and produces a flowing 7–8 sentence prompt. |
| R2-M3 focused contract verification | Complete | 98 passed, 4 skipped across Qwen story output, visual-plan compiler, silent-video prompt, video contract, and backend manifest tests. |
| R2-M4 one synthetic live video review | Pending availability | Previous bounded environment check could not reach the Docker daemon and Modal app listing did not return. No inference request was sent and no new video was produced. |

No SRS target changes, no real-child data, no commit/push. Prompt-contract tests do not prove visual quality; do not mark output-quality acceptance complete until a fresh synthetic video is generated and reviewed with existing gates enabled.
