# FEAT-020 Age Coverage and Variation Policy

**Date:** 2026-09-12
**Status:** owner-confirmed requirement; implementation pending approval

## 1. Supported age coverage

The current golden catalog supports four age bands, with five reviewed candidate activities per band:

| Age band | Catalog guidance window | Golden records |
|---|---:|---:|
| `0-3` | 8–35 months across the selected records | 5 |
| `3-6` | 42–71 months across the selected records | 5 |
| `6-9` | 72–107 months across the selected records | 5 |
| `9-12` | 108–155 months across the selected records | 5 |

These are the bands actually present in `data/activity-catalog/golden/v1/activities.v2.json` and `selection-manifest.v1.json`. They are guidance, not diagnostic developmental claims; readiness and safety rules remain authoritative.

## 2. Demo execution mode

The first backend E2E remains one public test, but it runs an age matrix containing all four bands:

```text
same committed image + same Vietnamese WAV
    ├── 0-3 run
    ├── 3-6 run
    ├── 6-9 run
    └── 9-12 run
```

Each sub-run must execute the real VLM/ASR/fusion path and the same Gate A/B demo protocol. The input identity/anchor is allowed to remain stable; the age-dependent context, eligible candidate set, activity, objective, story complexity, material guidance, and render intent must be age-aware.

## 3. Non-repeat requirement

The demo must not always return the first catalog record or a fixed hard-coded answer.

- Generate a fresh `run_seed` with a cryptographically secure/random source when no seed is supplied.
- Record the seed in private run metadata and a safe seed fingerprint in the manifest.
- Shuffle eligible candidates using the run seed after hard age/readiness/safety/material filters.
- Apply a no-immediate-repeat rule inside one matrix run and across the in-memory demo session when a previous selection is known.
- Select the candidate and objective from the eligible set, not from a fixed first-match path.
- Keep the same optional `--seed` for deterministic debugging and evidence replay.
- Never mutate catalog data to manufacture variation.

Variation must be observable in the contract. Across the four sub-runs, `age_band` must differ; `selected_activity_id`, `objective_id`, or the age-specific activity/render intent must differ when the eligible catalog permits it. The source image checksum and confirmed semantic anchor must not be randomized.

## 4. Command contract update

The intended matrix command is:

```bash
python -m sketch2life.workflow_demo \
  --image ./features/FEAT-020-backend-ai-workflow-demo/test-assets/input-image.png \
  --narration-audio ./features/FEAT-020-backend-ai-workflow-demo/test-assets/narration.wav \
  --age-mode all \
  --demo-autopilot \
  --output ./runtime-output/workflow-result.json
```

For debugging one band only:

```bash
python -m sketch2life.workflow_demo \
  --image ./features/FEAT-020-backend-ai-workflow-demo/test-assets/input-image.png \
  --narration-audio ./features/FEAT-020-backend-ai-workflow-demo/test-assets/narration.wav \
  --age-band 6-9 \
  --seed 123456 \
  --demo-autopilot \
  --output ./runtime-output/workflow-result.json
```

`--age-mode all` is the default for the acceptance demo. `--age-band` and `--seed` are explicit debug/replay controls.

## 5. E2E assertions

The single public E2E test must assert:

1. all four age bands execute;
2. every band passes the hard age/readiness/safety/material filters;
3. each band produces an explicit `DEMO_OPERATOR` Gate A and Gate B record;
4. no run uses a fixed first activity/objective;
5. the four results contain a run seed and age-aware output;
6. two unseeded matrix executions do not produce identical selection vectors when multiple eligible candidates exist;
7. a fixed seed reproduces the same selection vector for debugging;
8. video is present as `VIDEO_DEFERRED`, never falsely marked generated;
9. PixiJS output is asset IDs/render intents only, with no runtime AI asset generation.
