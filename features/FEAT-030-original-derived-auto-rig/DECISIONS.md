# FEAT-030 feature decisions

## Accepted owner decisions

| ID | Decision | State | Rationale |
|---|---|---|---|
| D-030-11 | Start spatial grounding/segmentation after Gate A; wait for Gate B before compiling the final motion and experience-specific plan. | ACCEPTED 2026-09-25 | Hides preparation latency without weakening Gate B authority. |
| D-030-12 | Cover every drawing topic through the complete archetype registry and mandatory generic/rigid/unknown fallbacks. | ACCEPTED 2026-09-25 | No valid drawing is left without a safe path; specialized movement remains evidence-bounded. |
| D-030-13 | Run auto-rig as an isolated worker/service on the same Lightning L4 host, subject to measured VRAM and GPU scheduling. | ACCEPTED 2026-09-25 | Separates lifecycle/failure while reusing available GPU infrastructure. |

## Architecture decisions awaiting plan approval

| ID | Decision | State | Rationale |
|---|---|---|---|
| D-030-01 | Keep `RendererLoadCommandV1` and whole-drawing fallback during migration. | PROPOSED | Rollback and old-client safety. |
| D-030-02 | Do not restore `/v2/localize` as an unconditional second Qwen call. Introduce replaceable spatial-grounding and segmentation ports. | PROPOSED | The prior path doubled model work and produced invalid regions/503s. |
| D-030-03 | Track auto-rig with an independent job; do not add `GENERATING_EXPERIENCE` to the business session state machine. | PROPOSED | Current session state is already `EXPERIENCE_READY`; media preparation is orthogonal and must not block session validity. |
| D-030-04 | Send V2 package references/capabilities through the bridge, not mesh arrays. | PROPOSED | The current bridge message limit is 4096 bytes; meshes and weights exceed it. |
| D-030-05 | Start with CPU skinning in PixiJS and animate bones/parameters through GSAP. | PROPOSED | Easier validation and deterministic fallback before custom shaders/GPU skinning. |
| D-030-06 | Allow motion only up to safety level 2 by default; motion must be justified by selected subject, observed relation/action, and learning objective. | PROPOSED | Prevents invented, distracting, or unsafe behavior. |
| D-030-07 | Use fallback order `FULL_AUTO_RIG → CUTOUT_MICRO_MOTION → BBOX_VISUAL_FOCUS → WHOLE_DRAWING_V1`. | PROPOSED | Each degradation preserves the child's original and completes the flow. |
| D-030-08 | Classify masks/cutouts/meshes as `ORIGINAL_DERIVED`, separate from creative supplemental assets. | PROPOSED | They require provenance/integrity review, not the same visual-approval semantics as generated decoration. |
| D-030-09 | For MVP, avoid destructive background inpainting. Translation is allowed only when a validated background patch exists; otherwise use internal deformation, pivot motion, camera focus, or V1. | PROPOSED | Prevents visible holes and fabricated drawing content. |
| D-030-10 | Split delivery into separately approved milestones; a plan approval does not authorize every model/dependency at once. | PROPOSED | The feature crosses AI, backend, storage, mobile, renderer, and governance boundaries. |

## Clarification of full-topic coverage

The initial registry must include `butterfly`, `bird`, `flower`, `tree_branch`, `fish`, `biped`, `rigid`, `generic_organic`, and `unknown`. Topic aliases map into this registry using canonical Gate A semantics. A topic without a trustworthy specialized fit goes to `generic_organic`, `rigid`, or `unknown`, then to an appropriate lower visual tier. “Full-topic coverage” therefore means a defined, safe, testable outcome for every input—not unrestricted skeleton or motion generation.

These owner decisions and the remaining proposed architecture must be recorded in the relevant ADR before implementation that depends on them.
