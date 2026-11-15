# Plan Rev87.24 — Parent guide first step from a simple source contour

**Date:** 2026-11-15<br>
**Status:** APPROVED under the owner's continuing direct instruction: “fix tiếp đi, cho chạy tới nào chạy đc thì th, nào trả đc kết quả thì tính”.<br>
**SRS authority:** FEAT-063 v2.7-draft, §§1–31; implementation evidence only in §32.<br>
**Predecessor:** Rev87.23 used two real synthetic Parent → Modal requests. The first exposed a parser mismatch; the second passed Qwen parsing and source coverage but failed the existing first-step construction gate. Both requests and logs are preserved in EV-063-119.

## 1. Problem

The actual `con mèo` request returned a complete 20-segment/8-stage source assignment, but the first stage contained source chunks with more than eight SVG commands. The existing hard gate correctly rejected it. The source atlas shows why prompt-only limits were insufficient: the current chunks can combine separate subpaths and Qwen's JSON schema permits any segment to be assigned to stage 1.

## 2. Goal

Use only exact geometry from the sanitized selected catalog SVG, while deterministically creating a small, connected opening contour from two adjacent source-derived chunks. Constrain Qwen's stage assignment so those two chunks are the only marks in stage 1. Qwen continues to choose and describe later stages; it never writes geometry. Preserve every existing hard gate and the Parent API response contract.

## 3. Bounded implementation

1. Choose a supported source chunk with at least eight consecutive drawable commands that remain in one original SVG subpath. Among eligible chunk starts, select the one with the largest normalized control-point bounding-box area; use source order as the stable tie-break. Fail over to another safe candidate if no eligible chunk can be made within existing limits.
2. Split the selected eight source commands into two consecutive four-command segments, followed by any remaining commands from that original chunk. Each segment starts at the exact source endpoint with its own `M`; no connector is synthesized, and no source command is omitted. Select a base chunk limit only when the final total remains within the existing 8–20 stroke bound, each path remains under the existing length/coordinate bounds, and the source manifest still accounts for every command.
3. Pin the two new segment IDs to stage 1 in the constrained JSON schema. Restrict every other segment ID to stages 2–8. Validate the same assignment rule after decoding. Update the prompt to say that stage 1 contains only these two connected contour segments and to describe only the visible contour. Do not relax the first-step gate (maximum three paths, each at most eight SVG commands), stage count, source identity, coverage, or final-feature gates.
4. Add bounded diagnostics for first-stage segment count and maximum command count. Add focused worker regression tests for deterministic starter selection, exact source-command coverage, two-piece continuity, schema pinning, parser enforcement and preservation of the source/color reference.
5. Run focused worker, backend, mobile and compile checks; inspect the diff only for approved paths. Deploy only `deployment/modal/srs_v23/language_audio_app.py` to Modal `dev`, then require CPU `/health` to report Qwen and the catalog ready without GPU allocation or inference.
6. Execute at most two sequential real synthetic Parent route → Modal requests for `con mèo`; each request uses the real catalog, pinned Qwen3.5 worker and existing Parent response assembly. No child profile/image/voice, account, consent, database, video, fixture response, retry or concurrent inference. After any HTTP 200, render every cumulative stage and the unchanged color reference and inspect them visually. Stop early when all visual checks pass.
7. Stop the Modal app and verify it is stopped. Record actual route/worker logs, response, render set, timings and tests in EV-063-119. Append implementation-only evidence to SRS §32 and update FEAT-063 context/status/decision/evidence records; do not modify §§1–31.

## 4. Acceptance criteria

- [ ] Every source drawable command remains represented exactly once; all returned geometry is source-derived and lineage remains valid.
- [ ] Stage 1 contains exactly the two pinned adjacent source chunks, each has at most eight commands, and the existing first-step validator passes without relaxation.
- [ ] The remaining source segments are assigned exactly once across 4–8 nonempty stages; existing construction, complexity, coordinate, source, coverage and final-feature checks pass.
- [ ] Focused worker/backend/mobile checks and Python compilation pass.
- [ ] A real synthetic Parent API → Modal response returns HTTP 200. Cumulative renders depict the same catalog cat, each stage only adds its assigned marks, and Vietnamese copy describes visible marks. HTTP 200 alone is insufficient.
- [ ] No more than two real requests are sent; no child data or video is used; Modal is stopped and verified stopped.
- [ ] Evidence and FEAT-063 records state pass/partial/fail accurately. No commit or push.

## 5. Limits

- Maximum two new real Parent route → Modal requests. A second request is allowed only after a specific first-request failure, a code correction, passing focused checks and a fresh deploy. No unchanged retry, no concurrent request and no third request.
- No child/profile/photo/voice/consent/personal or production data, video, account/seed/database/secret/`.env` change, dataset or Modal Volume mutation, Docker/UI/Teacher change, workload-wide enablement, SRS §§1–31 change, commit, push or merge.
- Preserve all earlier failed revisions and evidence. Do not claim visual acceptance from an API status alone.

## 6. Allowed files

- `deployment/modal/srs_v23/language_audio_app.py`
- `deployment/modal/srs_v23/tests/test_svg_topic_stroke_guide_contract.py`
- This plan and `features/FEAT-063-system-architecture-rearchitecture/approvals/TASK_APPROVAL.md`
- `features/FEAT-063-system-architecture-rearchitecture/evidence/EV-063-119_PARENT_SOURCE_SEGMENT_GUIDE_20261115/**`
- FEAT-063 `CONTEXT.md`, `DECISIONS.md`, `status/STATUS.md`, `evidence/README.md`
- FEAT-063 SRS §32 only and `docs/context/SRS_AUTHORITY.md`

No other paths may be edited without a new plan amendment.
