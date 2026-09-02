# Phase 11 - Wan2.2 generator adapter

## Responsibility

`Wan2Generator` translates a validated `GenerationBrief` into an argument list
for the official Wan2.2 `generate.py` entry point. It does not use a shell and
does not embed credentials. The adapter records the exact output path and basic
model/config provenance in `GeneratedVideo`.

## Runtime flow

```text
GenerationBrief
  -> build argv (--task ti2v-5B, --size, --ckpt_dir, --prompt)
  -> subprocess.run with timeout
  -> verify --save_file exists
  -> GeneratedVideo metadata
```

The adapter is unit-tested with a fake subprocess. A real run is intentionally
separate because Wan2.2 requires a prepared checkpoint, CUDA environment, and
substantial GPU memory.

`frame_num` is optional in the brief profile. When supplied, it must satisfy
Wan2.2's `4n+1` frame constraint.
