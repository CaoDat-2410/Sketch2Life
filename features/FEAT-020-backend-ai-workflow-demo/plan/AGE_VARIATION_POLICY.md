# FEAT-020 Age Coverage and Variation Policy

**Date:** 2026-10-06
**Status:** owner-amended supported product range; catalog retains historical/future coverage beyond the target

## 1. Supported age coverage

The golden source catalog still contains four bands, with five reviewed candidate activities per band. The supported product and GenAI workflow uses only the first three:

| Age band | Catalog guidance window | Golden records |
|---|---:|---:|
| `0-3` | 8–35 months across the selected records | 5 |
| `3-6` | 42–71 months across the selected records | 5 |
| `6-9` | 72–107 months across the selected records | 5 |
| `9-12` | 108–155 months across the selected records | 5 — retained in source catalog; outside current product target |

Supported child age is `<9`: 0–107 completed months inclusive. Product bands are `0-3` (0–35), `3-6` (36–71), and `6-9` (72–107). At 108 months, profile/session and age-sensitive GenAI requests are rejected before provider execution. The existing `9-12` records remain unchanged in `data/activity-catalog/golden/v1/activities.v2.json` and `selection-manifest.v1.json`; they are not selected by the current product workflow. Bands are guidance, not diagnostic developmental claims; authored safety rules remain authoritative.

## 2. Demo execution mode

The backend E2E runs one age matrix containing all three supported product bands:

```text
same committed image + same Vietnamese WAV
    ├── 0-3 run
    ├── 3-6 run
    └── 6-9 run
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

Variation must be observable in the contract. Across the three sub-runs, `age_band` must differ; `selected_activity_id`, `objective_id`, or the age-specific activity/render intent must differ when the eligible catalog permits it. The source image checksum and confirmed semantic anchor must not be randomized.

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

1. all three supported age bands execute; no `9-12` request is issued;
2. every band passes the hard age/readiness/safety/material filters;
3. each band produces an explicit `DEMO_OPERATOR` Gate A and Gate B record;
4. no run uses a fixed first activity/objective;
5. all three results contain a run seed and age-aware output;
6. two unseeded matrix executions do not produce identical selection vectors when multiple eligible candidates exist;
7. a fixed seed reproduces the same selection vector for debugging;
8. video is present as `VIDEO_DEFERRED`, never falsely marked generated;
9. PixiJS output is asset IDs/render intents only, with no runtime AI asset generation.
