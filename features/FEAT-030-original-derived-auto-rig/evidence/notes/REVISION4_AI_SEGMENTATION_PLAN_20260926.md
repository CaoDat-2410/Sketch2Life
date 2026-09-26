# Revision 4 AI segmentation planning evidence — 2026-09-26

## Outcome

Revision 4 proposes a backend-only AI perception stage for subject and semantic-part masks. It does not delegate skeletons or motion to an unconstrained generative model. Geometry, rigging, validation and PixiJS animation remain deterministic and bounded.

## Candidate rationale

- The owner selected Meta SAM 2.1 Hiera Small as the MVP point/box-prompt model. Its official model card publishes a 184 MB safetensors checkpoint under Apache-2.0.
- Gated SAM 3 is excluded from the MVP. The selected path uses deterministic proposals and optional bounded spatial hints from the original Qwen inference, never another Qwen call.
- NVIDIA's official Ada architecture specification identifies the L4 as a 24 GB GPU. The plan therefore defaults to serialized GPU admission with the current Qwen3-VL 8B BF16 runtime and requires measured headroom before concurrency.

## Official sources reviewed

- `https://github.com/facebookresearch/sam3`
- `https://github.com/facebookresearch/sam3/blob/main/RELEASE_SAM3p1.md`
- `https://huggingface.co/facebook/sam2.1-hiera-small`
- `https://github.com/facebookresearch/sam2`
- `https://huggingface.co/docs/transformers/model_doc/sam2`
- `https://huggingface.co/Qwen/Qwen3-VL-8B-Instruct`
- `https://images.nvidia.com/aem-dam/Solutions/geforce/ada/nvidia-ada-gpu-architecture.pdf`

## Repository findings

- `SubjectSegmentationPort` already provides a replaceable application boundary, but its result carries only one subject region/mask and cannot represent semantic parts.
- `AutoRigService` already starts an idempotent Gate-A preparation job and downgrades when no adapter is available.
- ADR-0009 already requires a same-L4 replaceable worker, serialized admission until measured safe, V1 fallback, and no unconditional second Qwen localization request.
- Revision 3 supplies a deterministic local component-scan baseline and butterfly part composition but does not claim semantic model segmentation.

## Public benchmark findings

- The official Qwen model tree reports about 17.5 GB of checkpoint files. This is not a CUDA-memory measurement, but it makes unmeasured concurrent residency on a 24 GB L4 unsafe as a default.
- The official SAM 2.1 table reports Hiera Small at 46M parameters and 84.8 FPS on an A100 using PyTorch 2.5.1/CUDA 12.4. This is a useful relative size/speed signal, not an L4 or child-drawing benchmark.
- SAM 3/3.1 findings were retained only as rejection rationale; gated access and unrelated high-count video benchmarks do not justify the MVP integration cost.
- No authoritative public benchmark was found for SAM 2.1 subject/part segmentation of children's crayon drawings on an NVIDIA L4. A local benchmark remains mandatory.

## Implementation boundary

The plan is now approved and its contract/adapter/worker path is implemented in the repository.
No SAM2 dependency or checkpoint was installed/downloaded and no live model inference was run in
this change. Live default activation therefore remains benchmark-gated; see
`REVISION4_SAM21_IMPLEMENTATION_20260926.md` for the implementation and unit-test evidence.
