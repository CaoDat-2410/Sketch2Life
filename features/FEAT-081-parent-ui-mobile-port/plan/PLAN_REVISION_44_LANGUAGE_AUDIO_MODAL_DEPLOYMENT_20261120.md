# FEAT-081 — Plan Revision 44: deploy Parent activity Modal app

**Status:** APPROVED by the owner's direct instruction on 2026-11-20: “sao lại thiếu, thiếu thì tự chạy thêm powershell up lên đi”.  
**Worktree:** `<local-machine-path>, branch `feature/fe-mobile-remediation`.  
**Product authority:** FEAT-063 canonical working SRS v2.7-draft / Rev67; unsigned.  
**Related run:** Plan Revision 43, Addendum 70/71; activity suggestion stopped before Modal created a call because the configured `dev` environment did not contain the language/audio app.

## Goal

Deploy the existing language/audio Modal app so the Parent activity-suggestion workload is registered in the configured Modal `dev` environment. The deployed function `suggest-parent-activities` is the missing worker identified in the Rev43 run report.

## Authorized scope

1. Deploy only `deployment/modal/srs_v23/language_audio_app.py` as `sketch2life-srs23-language-audio-dev` to Modal environment `dev`, using the already configured Modal CLI identity.
2. Verify deployment by checking the Modal `dev` app inventory and confirming the named app is listed.
3. Save sanitized command outcome and timestamp in the Rev43 E2E evidence folder; update FEAT-081 context and status.

## Boundaries

- Do not edit source, Docker, `.env`, Modal secrets, Volumes, database, accounts, or quota.
- Do not invoke any Modal function, including `suggest-parent-activities`, decoder readiness, model readiness, or a warm-up. This plan authorizes deployment only; it does not authorize another AI inference or continuation of story/video E2E.
- Do not deploy, stop, warm, or otherwise modify drawing, video, or any other Modal app.
- Keep all app functions at their existing `min_containers=0` settings. Do not leave a GPU worker warm.
- If the Modal deployment succeeds remotely but the first local command exits only because Windows cannot encode Modal's `✓` output, set `PYTHONUTF8=1` for the CLI and make exactly one deployment retry. Do not retry for any other failure; capture it and stop.
- Preserve all existing staged, unstaged, and untracked worktree content. No commit or push.

## Acceptance

- The deploy command exits successfully.
- `sketch2life-srs23-language-audio-dev` appears in Modal `dev` app inventory after deployment.
- No Modal function call or inference is issued as part of this plan.
- Evidence records the deployment result without credential values.

## Evidence path

`features/FEAT-081-parent-ui-mobile-port/evidence/PARENT_VIDEO_CANDIDATE_E2E_REV43_20261120/`
