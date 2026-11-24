# FEAT-082 source register

- Canonical product SRS: `features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md`, v2.7-draft Rev67, unsigned; routed through `docs/context/SRS_AUTHORITY.md`.
- Model reference: official [`Qwen/Qwen3.8-27B-FP8` Hugging Face model card](https://huggingface.co/Qwen/Qwen3.8-27B-FP8), exact repository revision `c3a462cc3d38cf351f3b26cbd763469eeb74ef81`.
- Sampling reference: official [`Qwen/Qwen3.8-27B` model card](https://huggingface.co/Qwen/Qwen3.8-27B), non-thinking/instruct recommendation; applied only where the pinned Transformers generation path supports it.
- Modal GPU reference: [Modal GPU documentation](https://modal.com/docs/guide/gpu); L40S reports 48 GB GPU memory.
- Implementation source: `deployment/modal/srs_v23/language_audio_app.py`, backend Modal adapter and Parent story reservation listed in Plan Rev1.
- Owner approval and exact plan hash: `approvals/TASK_APPROVAL.md`.
- Fine-grained FP8 kernel: official [Transformers FP8 guide](https://huggingface.co/docs/transformers/quantization/finegrained_fp8), [kernels security/API documentation](https://huggingface.co/docs/kernels/security), and the version 4 [kernel repository card](https://huggingface.co/kernels-community/finegrained-fp8); exact source revision pinned in Amendment D.
- Kernel bootstrap header diagnosis: pinned [`kernels` v0.17.3 `hf_hub.py`](https://raw.githubusercontent.com/huggingface/kernels/v0.17.3/kernels/src/kernels/hf_hub.py) and [`huggingface_hub` v1.32.0 `_headers.py`](https://raw.githubusercontent.com/huggingface/huggingface_hub/v1.32.0/src/huggingface_hub/utils/_headers.py). With telemetry disabled, the former supplies an empty user-agent; the latter concatenates the supplied user-agent separator, which produced the observed invalid header.
- Kernel loader behavior: [`kernels` v0.17.3 `load.py`](https://raw.githubusercontent.com/huggingface/kernels/v0.17.3/kernels/src/kernels/load.py), which constructs the Hub API before resolving the exact allowlisted repository.
- Current Parent UI/API target: `feature/fe-mobile-remediation`; its persisted activity-selection contract is reused under Amendment G. The worktree is dirty and must be preserved.
- Story input contract: internal `sketch2life.story-generation-input.v3`; topic and lesson fields are bounded, while profile interests and identity are excluded.
