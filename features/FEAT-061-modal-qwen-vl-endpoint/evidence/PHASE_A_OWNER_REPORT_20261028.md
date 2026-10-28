# Phase A: owner-reported local preparation

- Date: 2026-10-28 (Asia/Saigon). Source: command output the owner shared in the task conversation; these actions were performed by the owner, not by the assistant.
- The owner created a separate local virtual environment and installed Modal CLI 1.6.3 and `huggingface_hub` 2.3.0. Package-cache warnings occurred, while both installation outputs reported success.
- `modal setup` reported successful token verification for the selected workspace. A subsequent `modal token info` output shared in chat contained only Python deprecation warnings; no separate successful result for that command is asserted. Credentials and token values are not recorded here.
- The owner selected an external SSD outside the repository, reported exFAT and 799.7 GiB free, and downloaded `Qwen/Qwen3-VL-8B-Instruct` at revision `0c351dd01ed87e9c1b53cbc748cba10e6187ff3b`. The download output reported 16 files and 17.5 GB reconstructed.
- The owner's directory listing showed `config.json`, `preprocessor_config.json`, tokenizer files, `model.safetensors.index.json`, and all four numbered safetensors shards at the snapshot root. This listing is not an independent checksum verification.
- The owner removed the snapshot's `.cache/huggingface` directory; a subsequent path-existence check returned false. Model weights remain outside the repository.
- No Modal Volume, model upload, Secret, serving session, GPU allocation, HTTP request, or inference was reported. Phase B remains pending clarification and an appropriate approval record. No quality or production-readiness claim follows from Phase A.
