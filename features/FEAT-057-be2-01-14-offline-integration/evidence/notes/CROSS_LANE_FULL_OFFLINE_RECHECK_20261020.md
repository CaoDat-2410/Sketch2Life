# Cross-lane offline recheck — 2026-10-20

## Outcome

The complete BE2 backend unit + contract batch collected **6,866 tests**:

- **6,839 passed**
- **22 failed**
- **5 skipped**
- **0 collection errors / runtime errors**

This broad batch is **not green**. The failures are in untouched test modules and
include absent fixture files and legacy logging/render expectations. They need
their own owner review; this integration slice did not change those modules.
The full raw output and JUnit are under
`evidence/raw/full-offline-unit-contract-20261020/`.

The complete regression set closest to this change was then run as one command:
X01 plus the BE2-07/08 producer and consumer suites. It passed **296/296**, with
zero failures, errors, or skips. X01 remains **PARTIAL** because the consumer
does not commit a BE2-01 job/artifact lineage and the producer's durable fence
is not held through a cross-lane commit. X02–X09 remain `NOT_IMPLEMENTED`.

The publishable JUnit/log copies have host-specific paths redacted; test names,
assertions, counts, and failure messages are preserved. Byte-exact
pre-redaction copies remain in the ignored local evidence directory.

## Broad batch failures

| Test module | Failures | Observed reason |
| --- | ---: | --- |
| `test_semantic_personalization_v2` | 7 | Required `backend/data/activity-catalog/golden/v1/semantic-anchor-profiles.v1.json` is absent in this checkout. |
| `test_vision_v3_quality_benchmark` | 8 | Phase 8 fixture image references do not resolve inside the packaged benchmark fixture directory. |
| `test_vision_v3_quality_execution` | 1 | Same unresolved Phase 8 image fixture condition. |
| `test_pixi_motion_cycles` | 3 | Expected capability/frame-read log messages are absent from `caplog`. |
| `test_live_image_demo_api` | 2 | Expected validation log fields are absent from `caplog`. |
| `test_lightning_whiteboard_provider_parser` | 1 | Expected `DRAW_BEATS_INVALID`; observed `WHITEBOARD_RENDER_FAILED`. |

Five parametrized cases in `test_vision_phase_b_b1_contracts` were skipped by
their existing test condition (“input details are covered by the attempt-zero
row”). No database, SQL execution, provider, Lightning, server, or GPU test was
included.

## Scoped X01 + producer/consumer regression

The single scoped run contains:

- X01 cross-lane behavior and edge-registry tests: 14 passed.
- BE2-07/08 adjacent producer/consumer tests: 282 passed.
- Total: **296 passed, 0 failed, 0 skipped**.

JUnit and console logs are in
`evidence/raw/full-offline-unit-contract-20261020/`. The previous source-bound
X01 receipt remains at `evidence/metrics/CROSS_LANE_X01_20261020.json`.

The upload ZIP was also extracted into a fresh temporary directory and the same
296-test command passed against that extracted snapshot. This checks the actual
Notebook payload's file completeness. The hosted Modal Notebook itself is still
`NOT_RUN`; no Modal account, cloud kernel, or Modal function was invoked here.

## Modal Notebook

The reusable Notebook is
`evidence/notes/BE2_CROSS_LANE_X01_MODAL_NOTEBOOK_20261020.ipynb`. It runs the
same 296-test scope on a CPU kernel. Upload it with the ignored source snapshot
`evidence/local/modal-notebook-x01-20261020/be2-cross-lane-x01-source.zip`.
The ZIP SHA256 is
`5e7d3e10c8ef5439efc6a39dd6a17774ec40e746b054153b004215f6479ca9e8`. It contains
source, selected tests, synthetic example JSON, and the X01 registry metrics;
it excludes Git history, virtual environments, secrets, model weights, and
local evidence. The notebook needs no Modal secret or GPU. Download its JUnit,
log, and JSON receipt before stopping the kernel unless a persistent Volume is
attached.

## Environment and boundary

Python was 3.12.10 in the ignored worktree-local `backend/.venv`. The local
profile used exact pins for Pydantic 2.13.4, pytest 8.4.2, PyAV 18.1.0,
SQLAlchemy 2.0.52, Alembic 1.19.1, and Pillow 12.3.0. To make the broad unit
batch collect, NumPy 1.26.4, imageio 2.38.1, and imageio-ffmpeg 0.6.0 were
installed into that ignored environment only; `pip check` passed. Product
source was not modified for this recheck. Harness, repository security,
architecture, skeleton, Ruff, strict mypy, `git diff --check`, Notebook JSON,
and source-ZIP checks all passed after host paths were scrubbed from the
publishable test logs.

This does not complete cross-lane integration or change any card acceptance.
The working tree remains local and uncommitted; no push, merge, or deployment
occurred.
