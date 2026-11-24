# Rev58 M0 — runtime and ambiguous-call diagnostics

- **Evidence ID:** EV-081-REV58-M0-01
- **Date/environment:** 2026-11-21, Windows host; Docker Compose project `s2l-feat081-rev23`; Modal profile `docaodat24-10`, environment `dev`; Android emulator target retained from the active Parent E2E.
- **Plan/approval:** Plan Rev58, SHA-256 `32EBEE6E4C41A6B00AFC9D55B69F252085445633CACF8F320146F7066EB6C23B`, Addendum 106.
- **Data boundary:** Synthetic run only. No provider request, database write, account change, volume-content read, model download, or GPU inference was performed during M0.

## Run state

Read-only PostgreSQL command:

```powershell
docker exec s2l-feat081-rev23-postgres-1 psql -U sketch2life -d sketch2life -Atc "SELECT run_id,run_state,job_state,retryable,error_code,action_required,provider_job_id,provider_attempt_id,dispatch_gate_open,(active_owner_parent_account_id IS NOT NULL),updated_at FROM story.runs WHERE run_id='b05c2b46-e760-4643-824b-b30b5387453f'; SELECT revision_no,status,(provider_call_id IS NOT NULL),created_at FROM story.story_revisions WHERE run_id='b05c2b46-e760-4643-824b-b30b5387453f' ORDER BY revision_no;"
```

Output summary: run `SCRIPT_GENERATION_UNKNOWN`, job `AWAITING_RECONCILIATION`, `retryable=false`, error `STORY_OUTCOME_UNKNOWN`, dispatch gate closed, active-owner lock present. Revision 1 is `FAILED`; revision 2 is `AWAITING_RECONCILIATION`; neither has a provider call ID. One activity selection exists and no video candidate exists. The run remains untouched.

## Backend dispatch log

Read-only command:

```powershell
docker logs --since '2026-11-21T16:13:38' --until '2026-11-21T16:14:00' s2l-feat081-rev23-api-1 2>&1 | Select-String -Pattern 'modal_worker_|parent_modal_outcome_unknown|47dc5788-3852-45e1-b5b5-9dd2db1abc94'
```

Observed sequence: `modal_worker_scratch_upload_started` at 16:13:41 +07; upload completed at 16:13:46 after 5,151 ms; `modal_worker_spawn_started`; then `parent_modal_outcome_unknown` at 16:13:47 with HTTP 504 and no Modal call ID. Safe references were logged only as short refs (`job_ref=95ffca8f4157e655`, `generation_ref=ae9bbcdc80391042`, `attempt_ref=2b0b9868a84c232a`). No prompt, drawing, or worker output was read.

## Modal evidence

- `modal app info sketch2life-srs23-language-audio-dev --profile docaodat24-10 --env dev --json`: deployed version 15, currently stopped, zero tasks; the story-generation function is present in the deployed function registry.
- `modal app logs ap-9nYDslYbKdqlewkqnkRxfw --since 2026-11-21T16:08:00 --until 2026-11-21T16:18:30 --tail 200 --timestamps --show-function-id --show-function-call-id --profile docaodat24-10 --env dev`: only the 16:18:23 user-stop event was returned; no matching story worker event or call ID was observed.
- `modal app list --profile docaodat24-10 --env dev --json`: drawing app deployed with zero tasks; language/audio app stopped with zero tasks; no video app deployed.
- `modal volume list --profile docaodat24-10 --env dev --json`: model and scratch Volumes exist. `modal volume ls sketch2life-dev-model-weights-v2 ltx-2.5 --profile docaodat24-10 --env dev --json` returned “path does not exist”. The pinned LTX-2.5 checkpoint is not present at the worker’s configured path.
- Scratch-volume root metadata listing for the 16:10 window found no timestamp-matching path. This does not prove that `spawn` did not reach Modal; the exact full attempt path is unavailable from safe backend logs.

## Docker and source checks

- `docker ps`: task API, PostgreSQL, MinIO, and ClamAV are running; task API health returned HTTP 200 from `http://127.0.0.1:58100/health`.
- `docker inspect s2l-feat081-rev23-api-1`: `SKETCH2LIFE_PARENT_VIDEO_DEV_CANDIDATE_ENABLED=false`.
- FEAT-081 `deployment/modal/srs_v23/video_app.py` is a scaffold that returns not-configured for generation. FEAT-081 has the private synthetic candidate API/service/Modal adapter and Android `VideoCandidateScreen`; the candidate remains `product_playable=false`, `safety_validation=NOT_RUN`.
- The pinned LTX-2.5 worker plus deterministic `story_image_guides.py` and `story_visual_plan.py` are present only in the separate FEAT-067 worktree. That worktree has prior synthetic candidate evidence, but no evidence of a deployment in the current Modal environment.

## M0 interpretation and decision

The prior story request is **unresolved**, not proven absent. A missing call ID, no worker logs, and a stopped app do not establish whether the provider accepted the request before the client failed to retrieve its reference. Keep the run and owner lock intact; do not replay it. Continue with a different synthetic profile/account for any fresh UI run.

The video path cannot run from the current FEAT-081 runtime: the worker is not implemented/deployed, the candidate feature flag is off, and the pinned checkpoint is absent from its configured Volume path. M1/M2 must correct these concrete gaps and verify CPU-only readiness before a video inference.

## Reproduction commands

- `docker ps --format '{{.Names}} {{.Status}} {{.Ports}}'`
- `Invoke-WebRequest -UseBasicParsing http://127.0.0.1:58100/health`
- `& '<local-machine-path>' app list --profile docaodat24-10 --env dev --json`
- `& '<local-machine-path>' app info sketch2life-srs23-language-audio-dev --profile docaodat24-10 --env dev --json`
- `& '<local-machine-path>' volume list --profile docaodat24-10 --env dev --json`
- `& '<local-machine-path>' volume ls sketch2life-dev-model-weights-v2 ltx-2.5 --profile docaodat24-10 --env dev --json`
