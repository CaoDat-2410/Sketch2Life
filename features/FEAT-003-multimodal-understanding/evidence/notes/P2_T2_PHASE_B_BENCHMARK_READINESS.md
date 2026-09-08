# P2-T2 Phase B benchmark-readiness evidence

- Evidence ID: `EV-003-T2-03`
- Date: 2026-08-30
- Type: implementation, contract test, and privacy/config review
- Scope: approved P2-T2 Phase B benchmark-readiness preparation only; no live benchmark

## Delivered preparation

- `contracts/schemas/asr_benchmark.py` defines the strict provider-neutral
  `AsrRound1FixtureManifestV1` contract. It enforces stable IDs, lowercase SHA-256 formats,
  paired transcript reference/hash fields for every speech fixture, explicit Vietnamese and
  non-Vietnamese speech scenarios, exact `vi`/`en` code-switch metadata, `SYNTHETIC`/`LICENSED`
  provenance, and coherent silence/noise eligibility rules.
- `fixtures/asr-round1/README.md` documents the local audio/transcript layout and
  `manifest.example.json` is an empty metadata-only template. No payload, transcript content,
  model file, credential, endpoint, or real-child data was created.
- `benchmark/asr_scoring.py` implements `vi-asr-normalizer-v1` as pure WER-token and CER-
  character views. It applies NFC, casefolding, punctuation-to-space, and whitespace
  normalization while preserving Vietnamese diacritics and `đ`; it never changes raw ASR
  transcript data.
- `benchmark/asr_readiness.py` accepts only a `READY` manifest, validates the exact Round-1
  settings, plans the two Turbo profiles deterministically, and marks quality, language, latency, VRAM,
  success/failure, and control-alternative measurements `NOT_MEASURED`. It has no CLI, model
  SDK import, model load, GPU access, HTTP/API, queue, or P2-T5 behavior.
- `P2_T2_PHASE_B_ASR_REPORT_TEMPLATE.md` provides the required report sections for manifest and
  profile config hashes, WER, CER, language accuracy, latency p50/p95, VRAM, schema and
  success/failure counts, control coverage, synthetic-only limitation, and explicit
  `NOT_MEASURED` values.

## Regression correction (2026-08-30)

`NON_VI_CLEAR` now rejects any valid language tag whose primary subtag is `vi`, including
`vi-vn`, while continuing to accept locale-qualified non-Vietnamese tags such as `en-us`.
The focused tests cover rejection of `vi` and `vi-vn` plus acceptance of `en-us`.

## Config/privacy review

The ignored local ASR env was inspected by key name only: it contains the three allowed ASR
runtime keys and no generic application keys, unknown keys, or duplicate keys. The shared
backend env owns the four generic application keys. The versioned example contains blank
placeholders only. No value, secret, absolute local path, raw audio, or transcript content is
included in this evidence.

## Limitation and decision required (historical; resolved 2026-08-30)

At the time of this package, the live Round-1 benchmark was intentionally `NOT_MEASURED`: no
concrete fixture source or reference transcript set existed yet. That `DECISION_REQUIRED` item
was later resolved as `SYNTHETIC` (TTS), and the controlled live Round-1 execution was run — see
`P2_T2_PHASE_B_FIXTURE_PROVENANCE.md` and `P2_T2_PHASE_B_ROUND1_ASR_REPORT.md` for the measured
WER/CER, language accuracy, latency, VRAM, and typed-failure results. This package's own
NOT_MEASURED planner contract and tests are unchanged and still apply to any future unrun plan;
this note is left as-is as the historical readiness record.

## Verification record

Executed on 2026-08-30 from the repository worktree:

```text
backend/.venv/Scripts/python.exe -m pytest tests -q
93 passed

backend/.venv/Scripts/python.exe -m ruff check src tests
All checks passed!

backend/.venv/Scripts/python.exe -m mypy src/sketch2life
Success: no issues found in 39 source files

python tools/validate_harness.py
HARNESS_VALID

python tools/validate_repository_security.py
REPOSITORY_SECURITY_VALID (publishable_files_scanned=458, absolute_machine_paths=absent)

python tools/validate_architecture.py
ARCHITECTURE_VALID

git diff --check
clean
```

Ruff used a task-local `RUFF_CACHE_DIR` only to avoid the pre-existing cache-permission
issue. The focused additions are 32 passing tests (4 normalizer and 28 readiness tests). The
readiness suite covers TEMPLATE rejection, every missing required slice, explicit
non-Vietnamese speech, speech language/transcript requirements, code-switch exclusions,
silence/noise exclusions, noise coverage, exact two-profile planning, and all-
`NOT_MEASURED` metrics. All tests are metadata/fixture-contract tests; they do not require
the ASR optional dependency, a GPU, network access, generated audio, or transcript payloads.
