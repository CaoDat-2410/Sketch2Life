# FEAT-084 Android Parent UI screenshots

**Captured:** 2026-11-23, approximately 11:01 Asia/Saigon (04:01 UTC)
**Branch:** `feature/fe-mobile-remediation`
**App:** real Expo dev app, `com.sketch2life.parentexpo.dev`
**Device:** Android Emulator `emulator-5554`, Pixel_10 AVD (`sdk_gphone16k_x86_64`), Android 17, 1080×2424
**Capture method:** ADB `screencap`; PNGs are raw emulator captures.

## Captured screens

| File | Screen | State |
|---|---|---|
| `screenshots/android/00-initial.png` | Parent sign-in | Blank form; no account data |
| `screenshots/android/01-signup.png` | Parent sign-up | Blank form; registration not submitted |
| `screenshots/android/02-forgot-password.png` | Password recovery | Blank email form; reset not submitted |

SHA-256:

- `00-initial.png`: `2DB09014162EE52D8F48B18B0DB3395F6B45FA41FA328119147AA1CEF60F6D09`
- `01-signup.png`: `6B928DB0CF54EE83FAB700BB14FABD19030F8CE2B550F10B3BF935FFE620F60D`
- `02-forgot-password.png`: `5FD63C05D4D961EB7FD709F3C74D22B9278412C16A443EE6DA111AF464279A92`

## Reachability and blocker

The existing Parent synthetic seed credentials were read from the ignored root `.env` without printing or saving their values. A single sign-in attempt through the real UI was rejected with the app message “Email hoặc mật khẩu chưa đúng. Hãy kiểm tra rồi thử lại.” The Parent auth adapter calls Firebase first and only calls the backend after Firebase returns an ID token, so this failure happened before backend role resolution. Therefore the authenticated home, profile, topic/lesson, drawing-guide, capture, activity, story, and video screens could not be reached. No account, profile, consent, session, or other backend record was created or changed to work around this gate.

### Backend preflight after owner follow-up

Docker showed the backend stacks were already running; `sketch2life-api-1` reported `healthy`. The configured mobile base URL in the ignored root `.env` pointed to `10.0.2.2:58100`, where no service was listening. The separate `rev87-parent-authfix` API was healthy on host port `58000`; an unauthenticated read-only `GET /api/auth/v1/me` returned `401` there (expected for a missing token), while port `8000` returned `404` for that route. The root `.env` mobile URL was corrected to `http://10.0.2.2:58000`. This local configuration correction does not resolve the Firebase credential rejection, and no repeated sign-in attempt was made.

The signup and password-recovery forms were opened only for screenshots; neither action was submitted. No AI/Modal call, video request, quota/payment action, business API behavior test, test suite, or typecheck was run. Read-only Docker health/OpenAPI/auth-route preflight was performed after the owner follow-up. Metro and the emulator were shut down after capture; pre-existing Docker services were left running.

## Retry after backend URL correction — 2026-11-23 06:04 UTC

The owner asked to retry after the backend check. Pixel_10 and Metro were restarted; the Parent form received the existing synthetic credentials without exposing or saving them. The root `.env` mobile API URL had already been corrected to the running Parent Auth API at `10.0.2.2:58000`. Two UI tap attempts were made while troubleshooting; neither produced a visible error, authenticated home, or other screen transition. The login button remained enabled, and the app-process log did not contain the `parent_auth_submit_pressed` callback. The selected backend logs also contained no `/api/auth/v1/me` or registration-completion request for this retry. No further submission was made. This retry does **not** establish that Firebase accepted the credentials or that the backend auth endpoint was called. Docker still reported the selected API healthy. Metro and Pixel_10 are now stopped; Docker services were left running.

## Visual note

The password-recovery screen appears to place its back control too close to/under the Android status bar. This is a screenshot observation only; no source change was made in this capture task.
