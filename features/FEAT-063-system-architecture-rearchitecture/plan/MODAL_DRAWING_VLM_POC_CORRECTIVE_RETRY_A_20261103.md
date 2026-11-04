# Modal drawing VLM POC — corrective retry A

## Status and authority

- Status: `APPROVED` as a narrowly scoped correction to `MODAL_DRAWING_VLM_L4_POC_20261103.md`.
- Feature/SRS: FEAT-063, canonical SRS v2.3-draft; the model remains an experimental candidate, not a production selection.
- Owner instruction: the owner directed us to continue after Modal environment setup and host the AI workloads required by the system (direct chat instruction, 2026-11-03).
- The first synthetic L4 function call was accepted by Modal, started after a queue delay, and failed during processor loading before model inference because `torchvision` was absent. No automatic retry occurred.

## Exact corrective scope

1. Add `torchvision==0.22.1` alongside the already pinned `torch==2.7.1` in the inference image. The official PyTorch version matrix pairs these versions.
2. Redeploy the same `drawing_vlm_app.py` to Modal `dev`, using the existing pinned Qwen2.5-VL revision, existing Volume v2 resources, and the same one synthetic butterfly fixture.
3. Run exactly one corrective synthetic inference. The total is therefore two Modal function calls: the recorded failed call and this single corrective call. If the corrective call fails, stop; no third call is authorized by this amendment.
4. Record both call IDs, the initial missing-dependency failure, the corrected dependency set, final result or failure, elapsed time, billing summary, and cleanup in the task evidence.

## Explicit exclusions

- No model, GPU, precision, generation settings, limits, payload, test data, secret, region, or Modal environment changes.
- No retry loop, alternate GPU, second fixture, real child data, backend integration, other AI workload, SRS/ADR change, commit, push, or merge.

## Acceptance criteria

- The inference image pins the compatible PyTorch/torchvision pair `2.7.1` / `0.22.1`.
- The same private Modal `dev` app is redeployed with no HTTP endpoint or added Secret.
- Exactly one corrective synthetic call is made; its result explicitly requires adult confirmation. If it fails, record the failure and stop without another attempt.
- The task evidence preserves the first failure and the corrective outcome, and the repository security validator passes.

## Source basis

- Official PyTorch compatibility matrix: https://pytorch.org/get-started/previous-versions/
- Qwen2.5-VL Transformers 4.53.0 processor documentation: https://huggingface.co/docs/transformers/v4.53.0/en/model_doc/qwen2_5_vl
- Modal GPU configuration: https://modal.com/docs/guide/gpu
