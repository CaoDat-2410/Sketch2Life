# FEAT-086 Rev1 implementation and verification

Date: 2026-11-24
Worktree: `.codex-worktrees/fe`
Branch: `feature/fe-mobile-remediation`
Baseline HEAD: `77635688deed0114ac62c28c3f936da62144d59c`

## Changes verified in source

- Qwen Parent story JSON keeps `sketch2life.story-revision.v1` and its existing keys. The existing English `visual_prompt` is capped at 420 characters and requests a compact start pose → approved physical action → visible end result progression.
- LTX prompt template advanced to `story-i2v-v6`, with an action-first single-shot instruction, source-art identity/composition preservation, fixed background/camera guidance, and explicit bans on duplicate artwork/insets/cards and readable text.
- The video worker no longer renders or sends the secondary SVG-composited full-frame conditioning image. It submits one conditioning image per scene and preserves the existing scene continuity frame behavior.
- The Parent ready-player card no longer displays the duration/scene count/no-audio metadata row below the player.
- `git diff --check` passed. Git printed only CRLF normalization warnings for existing modified files.

## Automated checks

| Check | Result | Notes |
|---|---|---|
| Focused Modal story/video contract tests | **90 passed, 4 skipped** | Four skips require optional `lmformatenforcer`, which is not installed in this local Python environment. |
| UI copy/recovery validation | **Passed** | `node scripts/validate-ui-copy.mjs` returned `UI_COPY_AND_RECOVERY_VALID`. |
| Mobile Vitest suite | **Blocked before test collection** | Vite failed to resolve files with Windows `EPERM: operation not permitted, realpath`; no UI assertions ran. |
| Mobile TypeScript typecheck | **Failed on existing worktree/environment errors** | Missing generated `env` properties and Node type declarations plus errors in unrelated test files; no reported error points to `VideoCandidateScreen.tsx`. |
| Docker status | **Unavailable** | `docker ps` was denied access to `npipe:////./pipe/dockerDesktopLinuxEngine`. |
| Modal app status | **Unverified** | `modal app list --env dev` produced no response within the bounded wait and was stopped. No request was dispatched. |

## Image provenance

Potential visual-validation input: `features/FEAT-061-modal-qwen-vl-endpoint/assets/generated/crayon-controls-v1/03-house-and-sun.png`
SHA-256: `2846a1b6a710e931da6abccf8c9858a938cbd021c0325bbd3f0c98d513fd0c36`
Provenance: FEAT-061 `evidence/CRAYON_CONTROLS_PROVENANCE_20261029.json` labels it synthetic AI-generated crayon artwork, not authentic child art.

This image was selected as a better synthetic style-validation source than the clean vector-like turtle. **It has not been sent through the changed video worker in this verification**, because no fresh end-to-end run was available.

## Live inference and acceptance

- New Modal inference calls: **0**.
- New video candidate: **none**.
- Video source-art fidelity, inset removal in rendered output, scene-action adherence, and MP4 text absence: **not empirically verified on this revision**.
- The screenshot footer was UI metadata and has been removed in source. This does not establish that another generation has no model-rendered text.
- No video retry, gate bypass, data deletion, real-child input, commit, or push was performed.

## Repository/skill review

- LTX's official I2V guide says prompts should describe motion after the provided source image and notes that the image itself provides the scene's visual information: https://docs.ltx.io/open-source-model/usage-guides/image-to-video
- The official prompting guide recommends action verbs and a chronological beginning-to-end sequence; the implementation adopts that principle while intentionally omitting creative styling that could restyle children's artwork: https://docs.ltx.io/open-source-model/usage-guides/prompting-guide/
- `benjiyaya/LTX-2.5-Agent-Prompt-Skill` is a prompt-writing aid that expands concepts into cinematic prompts. It is not an LTX worker/model adapter, so it was not installed in the runtime: https://github.com/benjiyaya/LTX-2.5-Agent-Prompt-Skill
- Lightricks' official ComfyUI repository contains an LTX-2.5 motion-track ICLoRA workflow. This is a possible future controlled-motion experiment, but it was not added because it requires a new conditioning path/weights and separate compatibility, cost, and quality validation: https://github.com/Lightricks/ComfyUI-LTXVideo/tree/master/example_workflows/2.5
