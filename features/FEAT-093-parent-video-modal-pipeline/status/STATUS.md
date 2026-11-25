# FEAT-093 status

**State:** APPROVED (Rev 2 + Amendment A + Amendment B, 2026-11-25). M0 partly done; M1 and M2 implemented (not yet live-checked).

| Milestone | Status | Notes |
|---|---|---|
| M0 spikes and freeze | partly done | LTX spike (488 s for 5 x 6 s) and SRS reconciliation done. C2 memory/swap cost, Qwen decoding profile and Modal GPU concurrency are measured when C2 is built (M3-M5). |
| M1 recognition v2 backend | implemented | Analyzer result carries main/secondary subjects with boxes; stored with entity ids; `subject_role_scoring.propose_roles`; client view adds `suggested_included` and `needs_choice`; 14 unit tests. Eval set R6 (30 drawings) not built yet. |
| M2 recognition UI | implemented | `UnderstandingScreen` choice card and gate, scenery starts off, controller state; 4 vitest tests. Emulator run U1-U3 pending. Crop thumbnails are not done (boxes are not sent to the client by design); decision needed if wanted. |
| M3-M11 | not started | |

GPU budget used: 1 video (5 scene renders) of 12 videos / 40 scene renders.
