# Rev43 Parent E2E — sanitized run events

All times below are the timestamps emitted by the task API container. No credentials, tokens, email address, image bytes, or generated story text are included.

| Time | Event | Safe details |
|---|---|---|
| 07:37:48 | Drawing scratch upload started | workload drawing.analyze; job af02a711c788d6fc; attempt 4955b9d1df15f2f0; 266122 bytes |
| 07:37:58 | Drawing scratch upload completed | 9461 ms |
| 07:37:59 | Drawing Modal call started | Modal call fc-01M7VY8CNDZ2YS4PSBE0XRGPXY; Qwen/Qwen3.5-9B |
| 07:38:31 | Drawing Modal call completed | remote result succeeded; elapsed 40573 ms; model load 13270 ms; UI/API elapsed 42.34 s; subject confidence 90% |
| 07:40:51 | Activity catalog prepared | request a9b4086d-b5e3-4351-82f8-93043e63e646; accessible lessons 0; age-eligible lessons 0; age-eligible activities 0; candidates sent to model 0 |
| 07:40:51 | Activity fallback scratch upload started | workload parent.activity.suggest; job 73a0ea1b76c77ba5; attempt 4695293748d093a6; 704 bytes |
| 07:40:55 | Activity fallback scratch upload completed | 4522 ms |
| 07:40:56 | Activity Modal invocation failed | NotFoundError; Modal call ID absent; workload parent.activity.suggest |
| 07:40:56 | Activity API returned failure | POST /api/parent/v1/ai/story-runs/{run_id}/activity-suggestions → HTTP 504 |

Other observed API results:

- POST /api/auth/v1/registrations → HTTP 201.
- First GET /api/auth/v1/me → HTTP 401; Firebase verifier logged InvalidIdTokenError with structurally valid, matching-audience/issuer and unexpired claims.
- Second sign-in on the same synthetic account: GET /api/auth/v1/me → HTTP 200.
- GET /api/parent/v1/topics/suggestions → HTTP 200.
- GET /api/parent/v1/topics/ocean/drawing-subject-suggestions → HTTP 200.
- POST /api/parent/v1/ai/sketch-guides → HTTP 404 for the selected subject; no inference occurred.

Modal dev inventory at run end listed sketch2life-srs23-drawing-vlm-dev and sketch2life-srs23-dev-video; sketch2life-srs23-language-audio-dev was absent. The activity request did not receive a Modal call ID. No story, LTX request, video candidate, quota access, or retry followed.

## Rev45 continuation after the authorized language/audio app deploy

The entries below supersede the “no story/video” outcome above. All application calls after deployment were made through the real Android Parent UI. The earlier Rev43 activity failure had no Modal call ID and did not run inference.

| Time | Event | Safe details |
|---|---|---|
| 2026-11-20 08:46:08 | Activity inference started | request `0ea6399b-a71b-4a00-843a-bd4adbaa6503`; workload `parent.activity.suggest`; accessible lessons 0; eligible catalog activities 0; fallback sent to Qwen3.5. |
| 2026-11-20 08:48:04 | Activity inference completed | HTTP 200; Modal call `fc-01M7W257RZTNZF7QG01ZX1N7X3`; worker 114.349 s; service elapsed 116.081 s; 3 generated fallback activities persisted. |
| after activity response | Activity selection saved | UI saved “Phân loại thẻ rùa”; the selected snapshot is the activity described by the generated story. |
| 2026-11-20 08:54:33 | Story Modal request completed | request `a887c371-d189-4fae-aa78-8ef622c3791c`; call `fc-01M7W2G6BHQ09QMF5DA2HV40SM`; workload `story.generate`; worker 147.754 s; API HTTP 200; revision 1. One preceding HTTP 409 did not create a Modal call. |
| after story response | Adult review completed | Real UI showed “Khám Phá Hình Dáng Con Rùa” with five scenes about turtle shapes and sorting turtle cards. UI confirmation posted to `/v1/story-runs/{run_id}/script-confirmation` and returned HTTP 200. |
| read-only DB check | Story state verified | run `16002cde-42b1-4198-a7d0-a04de85fea9b`; `SCRIPT_REVIEW` / `SUCCEEDED`; revision 1 `CONFIRMED`; story hash `2539c2363244b8114b306663e3f3e8b307d1b6e2374380c3abee30d311988349`; selected activity “Phân loại thẻ rùa”; no video-candidate row. |
| after UI bundle inspection | Video still not sent | Expo app was restarted to verify it loaded the active worktree bundle and returned to sign-in. No LTX call, video candidate, retry, or quota access occurred. Manual sign-in is needed to resume this same server-side run in the UI. |

Modal inventory now lists `sketch2life-srs23-language-audio-dev` as deployed (app `ap-3jclT2On5Hd1hVbRMuJ6dk`, zero tasks at inventory time) alongside the already-deployed drawing and video apps. No secrets or child-real data were logged.

## Rev46 live UI run — sanitized correlation and timings

All timestamps are UTC from task API/worker logs. The story worker and API log events are asynchronous; elapsed durations below are the service-reported durations. No generated story body, auth token, credential, email, or image bytes are recorded.

| Time (UTC) | Event | Safe details |
|---|---|---|
| 2026-11-20 12:12:38 | Drawing Modal call started | StoryRun `ff1021f5-e9e6-4343-9da3-ced08ad9de69`; request `43f20076-a63d-473e-8c13-a029552501c6`; call `fc-01M7WDZA1DC13HPM3R3B567F7H`; Qwen3.5-9B. |
| 2026-11-20 12:13:15 | Drawing result returned | HTTP 200; 40.498 s; detected subject “con rùa”, confidence 90%; adult confirmed through UI. |
| 2026-11-20 12:15:53 | Activity inference started | Request `6a010e64-9d03-45e2-98b5-e47606977380`; catalog had zero accessible/age-eligible activity candidates; one permitted AI fallback. |
| 2026-11-20 12:18:08 | Activity inference completed | HTTP 200; 134.546 s; call `fc-01M7WE5DQA3P56YDFY3XZ0ZPZ7`; 3 suggestions; set `d9a63010-3c14-45dc-8dee-37eb71842de5`. Adult selected and UI persisted “Vận động mô phỏng rùa” (HTTP 200). |
| 2026-11-20 12:21:31 | Story inference started | Request `c1e79b24-39eb-450a-8ec0-8e0aa986482a`; one permitted inference; Qwen3.5-9B. |
| 2026-11-20 12:23:46 | Story response returned | HTTP 200; 134.394 s; Modal call `fc-01M7WEFR1BV3P2WNN4M3ZV2PSD`; revision 1. UI review found non-Vietnamese CJK text, so no confirmation or video request followed. |

Safe profile/database diagnostic outcome: the initial profile insert returned a SQLAlchemy `DataError`; the approved server log enhancement recorded only exception class/module and SQLSTATE, not SQL text or personal values. A read confirmed the profile list was empty. The same synthetic profile form was submitted once more under the approved amendment and returned HTTP 201; the UI then read the saved profile. Profile ID `f37bfa36-44be-4176-a474-b767bf26c183`; age 60 months; synthetic label `E2E Profile R46`.

Input image provenance: synthetic asset `synthetic-sea-turtle-drawing-rev43.png`; SHA-256 `96983E11AB3DEF971E2842A2309C350CCEAAE11786BA9BC37C01ABA7C8F66477`; selected via Android Photo Picker. No image content was copied into this log.

Terminal outcome: story API succeeded but adult-review language gate failed. Video was not submitted because confirmation is a required precondition. No inference was retried, no quota/billing state was accessed, and no Modal app was stopped.
