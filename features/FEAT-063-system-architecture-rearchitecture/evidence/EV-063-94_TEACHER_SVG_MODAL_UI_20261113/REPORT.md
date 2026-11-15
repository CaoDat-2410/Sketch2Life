# EV-063-94 — Real Teacher SVG generation through Modal

Date: 2026-11-13 (Asia/Saigon)<br>
Plan: Rev84, approved hash 78F5A781FD34F0FEBA7683E3E352A0603245F9F3F79856C55FDF61921CD9A05C<br>
Outcome: PASS for one real UI → API → Modal → sanitized SVG → browser render. This is a single-sample integration result, not broad quality approval.

## Test path

- Started an isolated Docker Compose project with PostgreSQL, Firebase Auth Emulator, MinIO, ClamAV and the real API. Used only the local synthetic Teacher seed and a non-personal topic; no child profile or real-child data was involved.
- Signed into Teacher Web through Firebase Auth Emulator in a separate headless Chrome profile. The in-app browser tool was disabled by Work settings, so no user desktop/browser was used.
- Opened /library/svg-illustrations, entered topic con hươu sao, age 60 months and the default warm_storybook style, then submitted exactly once.
- UI request: POST /api/teacher/v1/organizations/local-rev82-teacher-organization/ai/svg-illustrations.
- No fixture, canned response, existing SVG, external dataset, FLUX or other image model was used. Qwen3.5 generated the structured vector document.

## Result

- API: HTTP 200; contract TeacherSvgIllustrationDraftV1; title Con Hươu Sao Nhỏ; state DRAFT; review_required=true; persisted=false.
- Modal call: fc-01M791DGGZ2MV3Q5BPKPQ8F0XV; request ID 0c075cbb-85bd-493e-ade8-81bbd6218ef8.
- Model: Qwen/Qwen3.5-9B, revision c202236235762e1c871ad0ccb60c8ee5ba337b9a.
- API/browser elapsed time: 221,684 ms (3m 41.684s).
- Worker phases: scratch refresh 500 ms; input manifest read 829 ms; checkpoint verification 177 ms; model load 20,412 ms; prompt encoding 59 ms; constrained decoder setup 3,668 ms; model inference 180,536 ms; output parse/contract validation 1 ms.
- Sanitized document: 18 paths, SHA-256 6edbb4ff7e0dfd088c666e950fabfbfc437078b1ff873267ee410ea0ad85b9ae.
- CPU /health before inference returned status=ok, gpu_allocated=false, inference_executed=false, and the pinned checkpoint ready.
- Modal app was absent from the configured dev environment before deployment. One deployment created sketch2life-srs23-language-audio-dev; its GPU function uses min_containers=0. After the request, modal container list for this app returned [].

## Visual review

The browser rendered the actual generated output and displayed the required “Bản nháp AI · cần giáo viên xem lại” status. It reads as a stylized young deer, but the shapes are geometric and the grass details are detached. This is a usable render-path proof, not a claim of educator-approved illustration quality. Keep the result as a review-required draft.

Screenshot: [teacher-svg-draft.png](teacher-svg-draft.png)<br>
Standalone SVG serialized from the generated API document (same 18 paths as rendered in browser): [generated-svg-draft.svg](generated-svg-draft.svg)<br>
API response with model provenance and canonical document: [generated-svg-draft.json](generated-svg-draft.json)

## Issues and limits

1. GET /openapi.json returned HTTP 500 because runtime OpenAPI generation raised ValueError: Rev37 response schema 'SVG catalog contract' is not present in OpenAPI components. The new route itself mounted and returned HTTP 200 from the authenticated UI. Swagger/OpenAPI remains broken until the existing contract registry is reconciled.
2. The API immediate worker-log summary reported worker_terminal_event=none because Modal log indexing lagged. A subsequent read-only query of the same call found worker_succeeded; its inference and output-validation phases had already succeeded. This is a log-observation delay, not an inference failure.
3. One topic cannot establish quality across subjects, age bands, or styles. The result was not saved to a lesson/catalog or published. No presentation editor integration or Teacher approval workflow was exercised.

## Cleanup

- Local SVG capability flag was returned to false and API health returned HTTP 200 before shutdown.
- Isolated Docker project, its API/UI processes, and the temporary headless Chrome profile were stopped/removed. Named Docker volumes were not removed.
- Modal app remains deployed because it contains shared language/audio functions; min_containers=0 and no live Modal containers remained. No shared Modal app was stopped.
- No .env values were changed or recorded. No commit or push was made.
