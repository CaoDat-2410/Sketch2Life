# FEAT-009 validation evidence

- Date: 2026-08-24
- Environment: Windows, Node 24.18.1, pnpm 11.19.0, Java 21.0.12, Python 3.12 project virtual environment
- Data: no real child data; no model/provider request

## Harness and architecture

Command:

```powershell
python tools/validate_harness.py
python tools/validate_skeleton.py
python tools/validate_architecture.py
```

Result: PASS.

```text
HARNESS_VALID
approval_gate=enabled
frontend_asset_gate=enabled
SKELETON_VALID
mobile_target=android-only
android_sdk=min29-target36-compile37
ARCHITECTURE_VALID
python_dependency_direction=valid
mobile_feature_isolation=valid
frontend_asset_gate=valid
mobile_ai_boundary=valid
```

## JavaScript/TypeScript

Commands:

```powershell
$env:CI='true'
pnpm install --frozen-lockfile
pnpm typecheck
pnpm test
pnpm --dir apps/mobile lint
```

Result: PASS. Frozen lockfile was already up to date; both workspace typechecks passed; the mobile Pixi bridge suite passed 2/2 tests; ESLint exited 0.

React Native CLI configuration also exited 0 and reported:

```text
reactNativeVersion=0.87
project.ios=null
project.android.packageName=com.sketch2life.mobile
project.android.applicationId=com.sketch2life.mobile
project.android.mainActivity=.MainActivity
```

## Python

Commands:

```powershell
backend/.venv/Scripts/python -m ruff check backend/src backend/tests tools
backend/.venv/Scripts/python -m mypy backend/src
backend/.venv/Scripts/python -m pytest backend/tests
```

Result: PASS. Ruff passed, Mypy found no issues in 24 source files, and Pytest passed 2/2 tests.

## Native Gradle evaluation

Command:

```powershell
$env:GRADLE_USER_HOME='<workspace>/.gradle-user-home'
apps/mobile/android/gradlew.bat tasks --no-daemon
```

Result: PARTIAL ENVIRONMENT CHECK. Gradle 9.4.1 downloaded, the React Native 0.87 Gradle plugins compiled, and project `:app` configuration began. It then stopped with `SDK location not found` because this machine has no Android SDK/`ANDROID_HOME`. This is a local toolchain prerequisite, not a dependency-resolution or project-layout failure. `local.properties` is intentionally ignored and must be created by Android Studio on the developer machine.

## Security and visual checks

- Main Android manifest has `usesCleartextTraffic=false`; debug overrides it only for Metro.
- Release block has no debug signing configuration.
- No active iOS project or iOS npm script exists.
- No Lightning endpoint/credential exists in mobile code.
- Template launcher PNGs were removed and manifest references deleted; no unapproved visual was applied.
- Live Lightning connectivity remains intentionally unimplemented.

## Version-control foundation

`git init` completed locally and the default branch was renamed to `main`. No commit, remote, credential, or push was created. Under the Codex sandbox identity, status inspection requires a per-command `safe.directory` override because the workspace belongs to the Windows user; the repository itself is valid.
