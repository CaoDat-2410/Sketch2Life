# E01–E04 source and scope review

- Evidence date: 2026-10-10, Asia/Saigon; exact user-message timestamp not available.
- Reviewer: primary Codex agent plus independent backend/AI and frontend/renderer audit agents.
- Related criteria: AC-D01–AC-D06.
- Environment: Windows PowerShell, repository workspace, working copy with pre-existing modified/untracked files.

## Inputs and provenance

1. User attachment: `0a08f84b-6e68-4b59-b2a3-31d0d3390b41/Pasted text.txt`, resolved from the local attachment path supplied by owner. Machine-specific absolute path is intentionally excluded from publishable records.
2. SHA-256 attachment: `2241D1306215C67DFCE14DB8B60E8DAD7F8BE7997A1183DD116065B10A8FC3A8`.
3. Exact old SRS backup: artifacts/Sketch2Life_Master_SRS_v2.0_preserved_20261010.md, SHA-256 `28EB8B890D8E950FEC6AA0DF87F9B29851A7E41AA871C3DD6EB4205CD807801E`.
4. Backup copied from the pre-existing working-copy SRS v2.0, preserving its uncommitted content, before canonical replacement. User explicitly authorized replacement in the asynchronous answer.
5. Attachment remains local; no original handbook/workbook is copied/published. No real child data or secrets were read or generated.

Commands: Get-Content -LiteralPath attachment -Raw; rg --files with document/source filters; git status --short; Get-FileHash -Algorithm SHA256; source/config/ADR reads by exact path. Default exec/Node sandbox failed to launch with `helper_unknown_error: setup refresh had errors`; approved shell escalation succeeded. No auto-review rejection occurred.

## Owner answers and authority

- Initial request authorizes current-system analysis, reuse list, architecture proposal and SRS revision.
- "Thay thế scope hiện tại" explicitly replaces product scope.
- "Tablet/điện thoại Android" fixes child platform.
- "giữ fastapi, reactnative" fixes two technologies. It does not choose Expo/bare RN, versions, canvas engine, sync, AI model/provider, tenancy or capacity.
- Additional owner answers received 2026-10-10: review each Sketch first; shared tablet chooses active child by turn; after exhausted video failure Teacher chooses retry/skip/end. They resolve OD02/OD03/OD01 respectively in principle; exact switching/retry parameters remain refinement. No timeout or elapsed-time assumption was used.

## Audits E02/E03

Backend evidence is indexed in REUSE_AND_ARCHITECTURE.md sections 2/11: FastAPI/Pydantic source, Qwen/Lightning adapters, admission, activity catalog, Gate patterns/provenance, ephemeral state/demo identity, DeferredVideo, infrastructure declarations and missing durable adapters. Frontend source review distinguishes apps/ui-mobile Expo52/RN0.76.9 demo from apps/mobile RN0.87 fixture skeleton and Pixi8.20/GSAP3.13 playback. No freehand/collaborative canvas or Teacher/Admin desktop runtime was established.

Additional frontend exact pointers: apps/ui-mobile/src/demo/childAge.mjs min0/max107; AppContext.tsx mock/volatile profile initialization and launchImageLibraryAsync; Flow1Screens.tsx parent Dashboard; Flow2Screens.tsx Pixi WebView playback. Existing DRAW_REVEAL animates art and is not a drawing-input capability. apps/child-app and apps/parent-web are inactive/historical placeholders.

Maturity labels describe source availability, fixtures/demo and scaffolds. No real inference, model loading, Android visual test, cost/load/learning-efficacy result or production release was run for this audit. Existing FEAT-037 age guard review and FEAT-038 launch-script syntax evidence remain historical and bounded.

## E04 official documentation verification

Checked via web tools on 2026-10-10; used only for supported capability and design tradeoffs, not numerical performance or a version freeze:

- FastAPI WebSocket: https://fastapi.tiangolo.com/advanced/websockets/ (support and dependency/auth integration).
- Yjs: https://docs.yjs.dev/ and https://docs.yjs.dev/api/undo-manager (shared types, transport-independent updates, scoped origins for undo; authorization still application responsibility).
- Firebase verification: https://firebase.google.com/docs/auth/admin/verify-id-tokens (backend verification, not class authorization).
- RQ: https://python-rq.org/docs/ (Redis-backed workers/jobs).
- Pixi Graphics: https://pixijs.com/8.x/guides/components/scene-objects/graphics (render primitives, not completed canvas editing).
- Qwen model card: https://huggingface.co/Qwen/Qwen3-VL-8B-Instruct; Wan card: https://huggingface.co/Wan-AI/Wan2.2-TI2V-5B (existing candidates, no classroom quality/latency claim).
- React Native Skia official repository: https://github.com/wcandillon/react-native-skia (current upstream candidate; exact compatible version TBD). Former Shopify docs redirected; direct new installation page was unavailable to web tool and is not used as verified installation guidance.

## Scope conflict resolution

Old age/role/Parent/payment/video duration/provider decisions are preserved historically rather than carried as confirmed new requirements. Video waiting is confirmed; subsequent owner answers resolve permanent-failure choice as explicit Teacher retry/skip/end. Source PROPOSED permission matrix/state/rubric/preset fields remain PROPOSED unless owner answers resolve the named behavior. M01–M14 and AC01–AC18 have explicit SRS mappings. New functional Child actor does not imply a personal Firebase login. Original/provenance/security continue, but numeric retention and consent process remain open.
