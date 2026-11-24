# FEAT-082 decisions

## D082-01 — Use Qwen3.8-27B-FP8 as the shared development text checkpoint

- **Decision:** Pin the Modal language/audio development app to `Qwen/Qwen3.8-27B-FP8@c3a462cc3d38cf351f3b26cbd763469eeb74ef81` for its shared Qwen text workloads. Keep drawing VLM on its separate existing model.
- **Reason:** Owner directly requested the upgrade; FP8 is the candidate representation for fitting the 27B model on Modal L40S.
- **Boundary:** This is a development implementation choice pending the one-request POC. It does not amend the unsigned FEAT-063 product SRS or claim production readiness.
- **Status:** Approved; awaiting implementation evidence.

## D082-02 — Keep story output duration and scene count stable

- **Decision:** Keep the current five-scene, 30-second output in this prompt iteration. Five is inside the SRS's 5–15 scene range; changing timing/composition would confound prompt quality with video behavior.
- **Status:** Approved for this task.

## D082-03 — Do not synthesize a missing activity selection (historical)

- **Decision:** Do not pick an arbitrary catalog activity or fabricate one. Reuse the current worktree's persisted adult selection and its run/revision/hash checks.
- **Status:** The original observation is historical and superseded by Plan Rev1 Amendments F–G, which found and authorized reuse of the existing selection contract in `feature/fe-mobile-remediation`.

## D082-04 — Exclude free-text profile interests from the model request

- **Decision:** Do not send `interests_summary` to Modal until an allowlist normalizer exists. Include only the approved topic and exact lesson snapshot fields already authorized for the run.
- **Reason:** The database accepts unrestricted free text, while SRS BR-21 permits only explicitly allowlisted AI context.
- **Status:** Approved security narrowing in Plan Rev1 Amendment A; the stale checklist wording is corrected in Amendment B.

## D082-05 — Pin and narrowly allowlist the FP8 kernel after publisher lookup failure

- **Decision:** Preload `kernels-community/finegrained-fp8` from immutable revision `3c8fcc86c0e42b7abe5bcf666d3a3afdce93a0e8`, allowlisting only that exact repository ID, validate its required functions, and register it in the Transformers FP8 kernel cache.
- **Reason:** The one synthetic inference failed because the publisher overview lookup failed before the model emitted any tokens. Hugging Face documents exact repository allowlists; the selected repository is shown as a trusted publisher and Apache-2.0.
- **Boundary:** Do not allow all Hub kernels or arbitrary remote code. This fixes worker initialization only; it does not authorize a second inference, video, or real child data.
- **Status:** Implemented and deployed; static checks pass. Runtime verification requires a separately approved inference.

## D082-06 — Reuse the active Parent activity-selection contract

- **Decision:** The active Parent UI worktree already persists suggestions and adult selections. Do not add another selection schema, route, or migration. Send only the exact server-owned selected activity snapshot and bounded session context to story generation.
- **Authority:** Approved Plan Rev1 Amendment G.
- **Status:** Implemented in the FEAT-081 worktree; focused unit/contract checks pass. Android/Modal verification is recorded separately in the FEAT-082 evidence folder.

## D082-07 — Scope Hugging Face metadata to the pinned FP8 bootstrap

- **Decision:** Keep Hugging Face telemetry disabled by default. Temporarily enable only generic package/runtime metadata while resolving the exact allowlisted FP8 kernel, then restore the original flag in `finally`.
- **Reason:** `kernels==0.17.3` passes an empty user-agent when telemetry is disabled; with `huggingface_hub==1.32.0`, `httpx` rejects the resulting trailing separator. The User-Agent must never contain request, profile, child, prompt, artwork, or generated-content data.
- **Boundary:** This fixes only the observed bootstrap header construction. Offline unit tests and CPU decoder readiness do not prove live FP8 kernel resolution or successful text generation. No retry is allowed until the owner separately approves another inference.
- **Status:** Implemented and deployed; focused test suite passes; live inference verification remains open.

## D082-08 — Record Amendment J as a development E2E result

- **Decision:** The successful synthetic Android → API → Modal run proves the exercised development path works through silent video playback. It does not change the unsigned FEAT-063 SRS or claim product readiness.
- **Evidence:** The LTX-2.5 worker succeeded and playback reached 0:30, but the UI says safety was not checked. Review also found a transient text-like artifact and relative-position drift/overlap. The silent candidate does not meet the current SRS narration/subtitle target.
- **Boundary:** Do not treat technical media validation as the automatic SRS video-safety gate. Keep existing safety gates; handle quality and safety acceptance separately.
- **Status:** Recorded from the real synthetic E2E on 2026-11-23.

## D082-08 — Record the Amendment J result as a development E2E only

- **Decision:** The successful synthetic Android → API → Modal run proves the exercised development path works through silent video playback. It does not change the unsigned FEAT-063 SRS or claim product readiness.
- **Evidence:** The final LTX-2.5 call succeeded and played to 0:30, but the UI says safety was not checked; video review also found a transient text-like artifact and relative-position drift/overlap. The silent candidate does not satisfy the current SRS narration/subtitle target.
- **Boundary:** Do not treat technical worker validation as the automatic SRS video-safety gate. Keep the existing safety gates; handle quality and safety acceptance as separate work.
- **Status:** Recorded from the real synthetic E2E on 2026-11-23.
