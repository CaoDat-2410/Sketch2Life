# Later chat authorization: bounded dev-backend Modal smoke check

- Status: APPROVED for the bounded test described below.
- Date recorded: 2026-10-29 (Asia/Saigon).
- Authority: direct owner instructions and continuing setup/startup outputs in the current conversation.
- Supplemental plan: `../plan/BACKEND_DEMO_MODAL_SMOKE_PLAN_20261029.md`.

## Direct owner instructions

The owner asked: “Backend ở nhánh dev và nhánh hiện tại xem có chạy phần AI trên này đc như lighing k ?” The owner selected the dev-based test path and requested one-step-at-a-time guidance: “đc á chỉ từng bước đi”. The owner had assigned execution roles: “v bạn đưa cho tôi lệnh khởi động đi còn chạy test bạn chạy”. Subsequent explicit continuation and supplied worktree, runtime preparation and backend startup outputs continue that test request.

This records the later authorization to guide the owner through local setup and run the bounded test. It does not claim the owner reviewed these supplemental documents or approved a displayed plan hash. The limits below conservatively bound execution of the requested test.

## Authorized scope and limits

- Inspect loopback demo OpenAPI, prepare one synthetic demo session and one image upload/admission, and implement any necessary feature-local test helper/state/evidence.
- After owner-controlled Modal startup, send at most **one** explicit backend understanding command with narration `NONE` through the existing `lightning_dev` Vision V2 adapter to the existing Qwen-only service.
- Persist the command and reserve/consume the single-request budget before its HTTP call; do not retry, replay, requery or bypass it with new IDs/session after an uncertain result.
- Check typed statuses, versions, source/correlation identity, model/profile/config provenance, single attempt and Gate A readiness. Permit legitimate in-memory repair metadata. Record failures as failures; claim no integration success before response evidence.
- Stop before Gate A confirmation and every later AI stage. No audio/ASR, preference classification, ranking, SAM, planner, recommendation, video, mobile integration or quality experiment is included.
- Keep provider startup/shutdown with the owner, the existing Modal configuration in the original checkout, and the tested backend in the dev-based worktree. Do not change source/provider/schema/prompt/model, deploy an endpoint, install dependencies, merge branches, alter production, read/print secrets or actual `.env` contents, commit or push under this authorization.

## Original revision-1 records preserved

The original revision-1 approval excluded backend/mobile integration and cloud/model execution. This later chat authorization supplies the separate bounded test scope; it does not rewrite the original approval or claim those exclusions were absent.

Protected-file SHA-256 values checked when preparing this record:

- `../plan/PLAN.md`: `EB88B4DC8D231BF7D825B974719637A0B652450EE710C2514B82382CCF819A18`.
- `TASK_APPROVAL.md`: `A9E890D5F9F3175D4E1162873A95FF1110902453E9C0DB5C736E92CA1DD608CB`.

Neither protected file was edited. The feature's existing review/quality/production gates remain separate from this single smoke check.
