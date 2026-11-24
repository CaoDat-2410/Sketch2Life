# FEAT-083 decisions

## D083-01 — Use Qwen3.8 for every active Qwen workload

- **Decision:** Use the exact FEAT-082 Qwen3.8-27B-FP8 model/revision for active text and vision inference, including drawing analysis. Do not silently fall back to Qwen3.5.
- **Non-Qwen models:** Whisper ASR, VieNeu TTS, and LTX-2.5 video stay on their dedicated workloads.
- **Status:** Owner-directed; implementation approved.

## D083-02 — Maintain an 18-topic first-party catalog

- **Decision:** Ship 18 Vietnamese topic groups, each with at least nine distinct child-drawable subjects. Show three cards at a time. Rotate topics and subjects per authenticated adult without repetition until their respective catalog cycle is exhausted; then begin a new cycle.
- **Status:** Owner-directed; catalog content is an internal curated resource with versioned revision.

## D083-03 — Custom topics outside the catalog require an adult-entered subject

- **Decision:** If a typed topic resolves to a catalog topic, show that topic’s rotating catalog subjects. Otherwise ask the adult to enter the desired object/animal; Qwen3.8 checks whether it belongs to the topic. Out-of-topic or unclear answers remain on the input step with a clear correction path.
- **Status:** Owner-directed.

## D083-04 — Grounded, child-relatable generation

- **Decision:** Prompt and validate concrete narrative progression, age-appropriate everyday contexts, meaningful child actions, specific materials/steps for generated activities, and visual continuity with all recognized drawing elements. Avoid repetitive “look/observe/name” scenes without a story event.
- **Quality gates:** Preserve schema, privacy, safety, age, adult-review, and SRS hard gates. Improve content through richer prompts and moderate structural/semantic checks; do not turn a soft writing preference into a brittle hard failure.
- **Status:** Owner-directed; acceptance is implementation evidence, not a claim of general model quality.

## D083-05 — Database-backed rotation, no raw topic history

- **Decision:** Persist only catalog IDs, account UUID, draft UUID, catalog revision, cycle counters, and suggestion-set replay metadata. Never persist custom topic text or child/session content for this feature. A duplicate draft request replays the same cards and does not advance the rotation twice.
- **Status:** Chosen implementation design; use a forward Alembic migration and keep existing product data untouched.

## D083-06 — Align stale Qwen registry contract assertions

- **Decision:** Update the existing current-registry assertions that still expected Qwen3.5 vision, and rename the affected drawing assertion to avoid labeling its input-shape check as Qwen3.5-specific.
- **Status:** Source updated under approved Rev4; the test remains unexecuted.

## D083-07 — Record the legacy Teacher visual exception (superseded by D083-08)

- **Decision:** FEAT-083 claims Qwen3.8 for active Qwen-backed workloads only. The existing Teacher `/lesson-visuals` handler still dispatches FLUX and is not changed by this feature because that route was outside the approved file allowlist.
- **Status:** Superseded by D083-08. This remains as the historical Rev1–Rev4 decision; no FLUX request was sent under those amendments.

## D083-08 — Remove legacy Teacher FLUX lesson-visual API

- **Decision:** Remove the Teacher `/lesson-visuals` route and UI caller, backend FLUX dispatch/provenance, L4 workload allowlist entry, current registry row, and stale contract expectations. Keep the old Teacher lesson-visual worker function and dated outputs as historical provenance; the shared request parser rejects the retired workload. Leave the separate Parent sketch-guide workload unchanged. Do not claim that SVG illustration generation replaces it.
- **Authority:** Owner’s direct instruction, recorded in approved Plan Rev5.
- **Status:** Source change applied; no tests, runtime calls, or deployment performed.
