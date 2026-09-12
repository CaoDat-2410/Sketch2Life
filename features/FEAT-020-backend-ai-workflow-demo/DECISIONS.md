# FEAT-020 — Decisions and Open Questions

## Plan-time decisions

### D-020-01 — Main runtime is direct in-process Lightning execution

**Status:** proposed
**Date:** 2026-09-12

The demo will pull the repository from GitHub and run the backend CLI inside Lightning Studio. The main acceptance path will load model adapters in the same process. A separately operated HTTP provider server is not required for this feature.

This follows the user’s execution requirement and keeps the backend workflow as one command. The existing provider wrapper may remain useful for diagnostics or a later deployment topology, but it cannot be the only way to satisfy acceptance.

### D-020-02 — Two declared input modes

**Status:** proposed
**Date:** 2026-09-12

`IMAGE_ONLY` is the default and accepts one arbitrary real image. ASR is then `NOT_PROVIDED`. `MULTIMODAL` accepts the same image plus real narration audio and executes ASR. The manifest must always state the selected mode.

This is necessary because the target workflow includes voice while the requested demo input is one image.

### D-020-03 — Demo autopilot is explicit and non-production

**Status:** proposed
**Date:** 2026-09-12

The unattended command may use `DEMO_AUTOPILOT` for Gate A, Gate B, and the example feedback record, but every decision must include actor, reason, timestamp, and decision mode. Without the flag, the workflow stops at the human gate. No production path may silently reuse this behavior.

### D-020-04 — Strict completion requires real video

**Status:** proposed
**Date:** 2026-09-12

The terminal success status `WORKFLOW_COMPLETE` requires a real generated and validated 5–10 second micro-video. A cache hit, fallback still/narration, or supervised handoff is a valid degraded outcome for a future mode but is not complete success for this feature.

### D-020-05 — Demo feedback/history are in memory

**Status:** proposed
**Date:** 2026-09-12

The one-run demo may keep session, observation, feedback, and history records in memory. Durable persistence is excluded and must be addressed by a separate approved feature.

## Open decisions requiring approval before implementation

1. Exact Qwen/VLM model revision and local weight location.
2. Exact faster-whisper revision and whether the acceptance run includes real audio.
3. Exact video model, checkpoint, license, VRAM budget, and maximum acceptable runtime.
4. Demo actor identity and the minimum declared demo context profile (age/readiness/material/supervision).
5. Whether the first acceptance run must be `IMAGE_ONLY` or `MULTIMODAL`; the architecture supports both.
6. Final package/module names if repository conventions require paths different from the tentative names in `PLAN.md`.
