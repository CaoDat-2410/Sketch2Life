# Rev58 M5 — Firebase configuration and owner-scope check

**Time:** 2026-11-21 21:13 +07  
**Result:** BLOCKED before candidate recovery; no video inference or account/run mutation.

## Firebase/API runtime repair

- Root `<local-machine-path> was passed to the existing task Compose project explicitly with `--env-file`; the file was not edited or printed.
- Only `s2l-feat081-rev23-api-1` was recreated. Postgres, MinIO, ClamAV, volumes, project name, and API port `58100` were preserved.
- Container settings now report `env=local`, `auth_provider=firebase`, Firebase project configured, Firebase Admin credential present (value withheld), `ai_provider=modal_dev`, synthetic pilot enabled, and Parent video-candidate flag enabled for this task container. Firebase Admin initialized for the configured project; `/health` returned HTTP 200; API container is healthy with restart count 0.
- Android email/password sign-in with the existing local seed Parent succeeded and reached Home. No registration or new account was performed.

## Ownership verification

- The intended existing run is `e54a3543-ccab-4c3b-8a19-51aca314cd46`; its already-completed Modal call remains `fc-01M7Z3S0AAJ89HCJ6Q8CM2STT0`.
- Android account-scoped profile picker contains `SyntheticRev58Turtle`. Selecting it and opening the real Story History UI returned the empty state “Chưa có buổi nào”. Evidence: `57_target_home.png`, `58_target_history.png` and matching XML.
- On the user's follow-up, the emulator was checked again. It remained on the authenticated Parent Home for `SyntheticRev58Turtle`; opening the real `Câu chuyện` tab returned “Chưa có buổi nào”. Evidence: `59_current_ui.png` and `60_story_tab.png` with `59_current_ui.xml` and `60_story_tab.xml`.
- A read-only task-DB check compared the signed-in seed Parent principal and its `SyntheticRev58Turtle` profile against the existing run: `run_exists=true`, `seed_owner_matches_run=false`, `seed_owns_target_profile=true`, `run_matches_target_profile=false`, `candidate_found_for_seed=false`. No row was changed.
- A second read-only lookup linked the target run's profile owner to an enabled Firebase Auth user. The user has an email/password provider (no Google provider). No email, UID, credential, token, or account data was written to evidence; no password reset or account change was made.
- After the owner selected the existing-account path, a redacted comparison checked the Parent email configured in the root `.env` against the target owner's Firebase UID. Both Parent credential fields are configured, but the email currently resolves to a different Firebase user. No sign-in attempt or credential disclosure occurred.
- The same seed account has a separate pending run under `SyntheticTurtleRev22` (“Đang xác minh kết quả”). It was not canceled, retried, or modified.
- After the owner asked to continue with the currently logged-in account, Home's active-run card was opened through the real UI. It resolves to run `b05c2b46-e760-4643-824b-b30b5387453f`: `SCRIPT_GENERATION_UNKNOWN`, `AWAITING_RECONCILIATION`, `STORY_OUTCOME_UNKNOWN`, `retryable=false`, and no provider job ID. Read-only database timestamps show its last update was 2026-11-21 16:13:47 +07. The UI says not to resend; after a further status-only wait it remained pending. Evidence: `61_home_with_open_run.xml`, `62_open_run.xml`, `63_open_run_after_wait.xml`, `63_open_run_waiting.png`.
- This unresolved run holds the account's active-owner lock. No new run, retry, cancellation, direct status mutation, or video request was attempted.

## Stop and resume conditions

The authenticated account does not own the target run/profile, so the one-shot authenticated recovery allowed by Addendum 112 cannot be called from this account. The target owner's Firebase account still exists and is enabled, but its password is not available in the configured seed account. The UI did not issue a video status request for the target run after sign-in; no AI or video inference was sent. The exact target candidate, saved call, and one-shot recovery marker were not changed. Modal inventory was checked read-only: the drawing app is deployed with 0 tasks, language/audio is stopped, and the expected video-candidate app is not found in this `dev` environment. The old call was not fetched.

To continue, either:

1. Configure the existing synthetic Firebase account that owns the target run in the root `.env` seed Parent email/password variables and tell me it is ready; do not send the password in chat. Then I can sign into that existing account and recover/play the same saved call, with no new inference.
2. Authorize a new bounded synthetic Parent run and one video inference under the seed account. This is outside Addendum 112 and would consume another Modal GPU run.

Modal inventory in the current `dev` profile: drawing app deployed with 0 tasks, language/audio app stopped, and the expected `sketch2life-srs23-video-candidate-dev` app name is not present. No live GPU task was listed. Retrieval of the old call was not attempted. No commit or push.

