# Complete topic- and age-matched activity discovery

Evidence ID: `FEAT033-EV-20260930-29`
Date: 2026-09-30
Scope: approved FEAT-033 revision 6 / SRS v1.8 B33

## Change verified

- Added the additive `POST /v1/sessions/{session_id}/p1/activity-suggestions` flow and `ActivityRecommendationSetV2`; legacy V1/V2 contracts remain available.
- Discovery returns every displayable, reviewed semantic match for the confirmed Gate-A topic and exact age. It does not cap the result at three or deduplicate separate activities into one family.
- Adult-confirmed interests/dislikes influence ordering and the explanation shown with a card; they do not suppress otherwise matching activities. Unconfirmed tags remain excluded from the request.
- Removed readiness, activity-history, and current-material-availability questions/filters from discovery. Material and policy information remains attached to cards for adult preparation; adult participation remains required, with caregiver participation required below 36 months.
- Kept strict topic matching in the new flow without changing the legacy resolver. It no longer treats incidental words such as “tree/branch” as a second recommendation topic when the confirmed subject is a bird. It also corrects three catalog concept mismatches in this flow only: `ACT-0043`/`ACT-0044` are letter activities, and `ACT-0114` is butterfly-specific, not a generic bird match.
- The mobile path directly requests and renders the complete set, then submits only the selected activity to additive `P1ContextV4`; the intermediate readiness/material checklist is bypassed.

For a synthetic 60-month bird-on-branch topic with movement evidence, the resolver returns five relevant options: `ACT-0102`, `ACT-0106`, `ACT-0110`, `ACT-0118`, and `ACT-0218`. It excludes letter activities, butterfly-specific matching, and unrelated plant/color/weather activities. The contract test additionally verifies the real request boundary returns more than three cards and includes the adult-confirmed interest explanation.

## Verification

- Backend focused unit + contract tests: **40 passed** (`test_topic_activity_matching.py`, `test_child_learning_profile_contract.py`, `test_live_image_demo_api.py`). Includes complete list, exact age/topic, profile preferences, and P1ContextV4 selection/filter/prepare flow.
- Full backend unit + contract suite: **passed**. The default Windows pytest temp root was not writable in this environment, so the run used a task-local `--basetemp` directory; no test failures or errors.
- Mobile UI-copy validation: **passed** (`UI_COPY_AND_RECOVERY_VALID`).
- Mobile TypeScript: **passed** (`pnpm --dir apps/ui-mobile exec tsc --noEmit`).
- Ruff on changed backend implementation/tests: **passed**.
- Repository security validator: **passed** (`REPOSITORY_SECURITY_VALID`, 1,732 publishable files scanned).
- `git diff --check`: **passed**; only existing line-ending normalization warnings were reported in other dirty governance files.

No emulator/native interaction, deployed Lightning request, commit, or push was performed in this task. Those are not claimed as verified here. Feature status remains `IN_PROGRESS` for the separate external classifier, qualified content review, and native responsiveness gates.
